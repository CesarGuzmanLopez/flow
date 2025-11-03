"""
Transactional outbox y lógica de persistencia atómica para ejecuciones duraderas.
Incluye helpers para escribir Execution, Checkpoint y OutboxEntry en la misma transacción.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from django.db import transaction

from .models import Checkpoint, Execution, OutboxEntry


def persist_execution_with_outbox(
    execution: Execution,
    checkpoint_data: Optional[Dict[str, Any]] = None,
    outbox_events: Optional[list[Dict[str, Any]]] = None,
) -> None:
    """
    Persiste Execution, Checkpoint y OutboxEntry en la misma transacción atómica.
    """
    with transaction.atomic():
        execution.save()
        if checkpoint_data is not None:
            Checkpoint.objects.create(
                execution=execution,
                step=checkpoint_data["step"],
                data=checkpoint_data["data"],
                version=checkpoint_data.get("version", 1),
            )
        if outbox_events:
            for event in outbox_events:
                OutboxEntry.objects.create(
                    execution=execution,
                    event_type=event["event_type"],
                    payload=event["payload"],
                )
