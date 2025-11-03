"""
Proveedor durable para AMBIT-SA ejecutado en segundo plano.

Implementa ExternalJobProvider con:
- start: crea o devuelve Execution idempotente y encola el trabajo
- resume: reanuda desde último checkpoint
- status/cancel/heartbeat: operaciones de mantenimiento

El worker `run_ambit_execution` ejecuta el cálculo usando el provider
sincrónico `chemistry.providers.ambit_sa` y persiste checkpoints.

Nota: AMBIT-SA no soporta reanudación interna; la reanudación aquí es
idempotente a nivel de orquestación (re-ejecuta de forma segura el trabajo).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from chemistry.providers.synthetic_accessibility.ambit import get_ambit_provider
from chemistry.type_definitions import SyntheticAccessibilityResultDict

from .interfaces import (
    Checkpoint as CP,
)
from .interfaces import (
    ExecutionMetadata,
    ExecutionStatus,
    ExternalJobProvider,
)
from .models import Checkpoint, Execution
from .models import ExecutionStatus as DBStatus
from .persistence import persist_execution_with_outbox
from .worker import MAX_RETRIES, _actor


@dataclass(frozen=True)
class AmbitCheckpoint(dict):
    """Tipo de checkpoint para AMBIT (estructura libre)."""


def _to_metadata(exec_obj: Execution) -> ExecutionMetadata:
    last_cp: Optional[Checkpoint] = exec_obj.checkpoints.first()
    cp_val: Optional[CP] = None
    if last_cp is not None:
        cp_val = CP(
            execution_id=exec_obj.execution_id,
            step=last_cp.step,
            data=last_cp.data,
            created_at=last_cp.created_at,
            version=last_cp.version,
        )
    status_map = {
        DBStatus.PENDING: ExecutionStatus.PENDING,
        DBStatus.RUNNING: ExecutionStatus.RUNNING,
        DBStatus.SUCCEEDED: ExecutionStatus.SUCCEEDED,
        DBStatus.FAILED: ExecutionStatus.FAILED,
        DBStatus.CANCELLED: ExecutionStatus.CANCELLED,
        DBStatus.WAITING_RETRY: ExecutionStatus.WAITING_RETRY,
        DBStatus.WAITING_RESUME: ExecutionStatus.WAITING_RESUME,
        DBStatus.BROKEN: ExecutionStatus.BROKEN,
    }
    return ExecutionMetadata(
        execution_id=exec_obj.execution_id,
        idempotency_key=exec_obj.idempotency_key,
        provider_name=exec_obj.provider_name,
        created_at=exec_obj.created_at,
        updated_at=exec_obj.updated_at,
        status=status_map[DBStatus(exec_obj.status)],
        last_checkpoint=cp_val,
        payload=exec_obj.payload,
        error=exec_obj.error,
        version=exec_obj.version,
    )


class AmbitSAExternalJobProvider(ExternalJobProvider[AmbitCheckpoint]):
    provider_name = "ambit-sa"

    def start(self, payload: Dict[str, Any], idempotency_key: str) -> ExecutionMetadata:
        existing = Execution.objects.filter(
            provider_name=self.provider_name, idempotency_key=idempotency_key
        ).first()
        if existing is not None:
            return _to_metadata(existing)
        exec_obj = Execution(
            execution_id=uuid4(),
            idempotency_key=idempotency_key,
            provider_name=self.provider_name,
            status=DBStatus.PENDING,
            payload=payload,
        )
        persist_execution_with_outbox(
            exec_obj,
            checkpoint_data={"step": "created", "data": {"progress": 0}},
            outbox_events=[
                {
                    "event_type": "execution_created",
                    "payload": {"id": str(exec_obj.execution_id)},
                }
            ],
        )
        run_ambit_execution.send(str(exec_obj.execution_id))
        return _to_metadata(exec_obj)

    def resume(
        self, execution_id: UUID, checkpoint: Optional[AmbitCheckpoint] = None
    ) -> ExecutionMetadata:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        if exec_obj.status in [DBStatus.SUCCEEDED, DBStatus.CANCELLED]:
            return _to_metadata(exec_obj)
        exec_obj.status = DBStatus.WAITING_RESUME
        persist_execution_with_outbox(exec_obj)
        run_ambit_execution.send(str(exec_obj.execution_id))
        return _to_metadata(exec_obj)

    def status(self, execution_id: UUID) -> ExecutionMetadata:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        return _to_metadata(exec_obj)

    def cancel(self, execution_id: UUID) -> None:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        exec_obj.status = DBStatus.CANCELLED
        persist_execution_with_outbox(exec_obj)

    def heartbeat(self, execution_id: UUID) -> None:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        persist_execution_with_outbox(exec_obj)  # updated_at se refresca al guardar

    def get_checkpoint(self, execution_id: UUID) -> Optional[AmbitCheckpoint]:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        last_cp = exec_obj.checkpoints.first()
        if last_cp is None:
            return None
        return AmbitCheckpoint(last_cp.data)

    def list_checkpoints(self, execution_id: UUID) -> list[AmbitCheckpoint]:
        exec_obj = Execution.objects.get(execution_id=execution_id)
        return [AmbitCheckpoint(c.data) for c in exec_obj.checkpoints.all()]

    def get_logs(self, execution_id: UUID) -> list[str]:
        # TODO: Persistir logs en otra tabla o almacenamiento externo
        return []

    def health(self) -> Dict[str, Any]:
        # TODO: Comprobar disponibilidad de Java/JAR y broker Dramatiq
        return {"provider": self.provider_name, "status": "ok"}


@_actor(max_retries=MAX_RETRIES)
def run_ambit_execution(execution_id: str) -> None:
    exec_obj = Execution.objects.get(execution_id=execution_id)
    if exec_obj.status == DBStatus.CANCELLED:
        return
    try:
        # Paso 1: preparación
        exec_obj.status = DBStatus.RUNNING
        persist_execution_with_outbox(
            exec_obj, checkpoint_data={"step": "prepare", "data": {"progress": 10}}
        )
        # Paso 2: ejecución AMBIT
        smiles = exec_obj.payload.get("smiles")
        provider = get_ambit_provider()
        result: SyntheticAccessibilityResultDict = provider.calculate_sa(
            smiles
        ).to_dict()
        # Paso 3: persistir resultados
        new_payload = dict(exec_obj.payload)
        new_payload["result"] = result
        exec_obj.payload = new_payload
        persist_execution_with_outbox(
            exec_obj, checkpoint_data={"step": "computed", "data": {"progress": 90}}
        )
        # Paso final
        exec_obj.status = DBStatus.SUCCEEDED
        persist_execution_with_outbox(
            exec_obj, checkpoint_data={"step": "done", "data": {"progress": 100}}
        )
    except Exception as e:
        exec_obj.status = DBStatus.WAITING_RETRY
        exec_obj.error = str(e)
        persist_execution_with_outbox(exec_obj)
        raise
