"""
Interfaces tipadas para providers de procesos externos pesados.

Define los contratos para providers que gestionan ejecuciones duraderas,
con soporte para start, resume, status, cancel, heartbeat, y reporting.

Incluye tipos para Execution, Checkpoint, y estados.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, Optional, Protocol, TypeVar
from uuid import UUID

TCheckpoint = TypeVar("TCheckpoint", bound=Dict[str, Any])


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_RETRY = "waiting_retry"
    WAITING_RESUME = "waiting_resume"
    BROKEN = "broken"  # Circuit-breaker


@dataclass(frozen=True)
class ExecutionMetadata:
    execution_id: UUID
    idempotency_key: str
    provider_name: str
    created_at: datetime
    updated_at: datetime
    status: ExecutionStatus
    last_checkpoint: Optional["Checkpoint"]
    payload: Dict[str, Any]
    error: Optional[str] = None
    version: int = 1


@dataclass(frozen=True)
class Checkpoint:
    execution_id: UUID
    step: str
    data: Dict[str, Any]
    created_at: datetime
    version: int = 1


class ExternalJobProvider(Protocol, Generic[TCheckpoint]):
    def start(
        self,
        payload: Dict[str, Any],
        idempotency_key: str,
    ) -> ExecutionMetadata: ...

    def resume(
        self,
        execution_id: UUID,
        checkpoint: Optional[TCheckpoint] = None,
    ) -> ExecutionMetadata: ...

    def status(self, execution_id: UUID) -> ExecutionMetadata: ...

    def cancel(self, execution_id: UUID) -> None: ...

    def heartbeat(self, execution_id: UUID) -> None: ...

    def get_checkpoint(self, execution_id: UUID) -> Optional[TCheckpoint]: ...

    def list_checkpoints(self, execution_id: UUID) -> list[TCheckpoint]: ...

    def get_logs(self, execution_id: UUID) -> list[str]: ...

    def health(self) -> Dict[str, Any]: ...
