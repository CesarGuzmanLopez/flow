"""
Servicios de dominio para ejecución de flujos con notificaciones.

Integra el sistema de notificaciones en la ejecución de flujos y steps.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from django.contrib.auth import get_user_model
from flows.models import ExecutionSnapshot, Flow, Step, StepExecution
from flows.sse import step_log_broker
from notifications.container import container
from notifications.domain.events import (
    FlowCompleted,
    FlowStepCompleted,
    FlowStepFailed,
    FlowStepStarted,
)

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()


class FlowExecutionService:
    """
    Servicio de dominio para ejecución de flujos.

    Gestiona la ejecución de flujos y steps, emitiendo eventos y notificaciones.
    """

    @staticmethod
    def start_step_execution(
        step: Step,
        execution_snapshot: ExecutionSnapshot,
        send_email: bool = False,
        webhook_url: Optional[str] = None,
    ) -> StepExecution:
        """
        Inicia la ejecución de un step.

        Args:
            step: Step a ejecutar
            execution_snapshot: Snapshot de ejecución
            send_email: Si debe enviar email
            webhook_url: URL de webhook para notificaciones

        Returns:
            StepExecution creado
        """
        # Crear ejecución de step
        step_execution = StepExecution.objects.create(
            execution_snapshot=execution_snapshot,
            step=step,
            status="running",
            inputs=step.config.get("params", {}),
        )

        # Emitir evento y notificar
        event = FlowStepStarted(
            event_id=uuid4(),
            flow_id=step.flow_version.flow.id,
            step_id=step.id,
            step_name=step.name,
            user_id=int(getattr(step.flow_version.flow.owner, "id", 0)),
        )

        use_case = container.notify_step_started_use_case()
        use_case.execute(event=event, send_email=send_email, send_webhook=webhook_url)

        return step_execution

    @staticmethod
    def complete_step_execution(
        step_execution: StepExecution,
        output: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ) -> None:
        """
        Completa la ejecución de un step.

        Args:
            step_execution: Ejecución de step
            output: Output del step
            webhook_url: URL de webhook para notificaciones
        """
        step_execution.status = "completed"
        step_execution.completed_at = datetime.now()
        if output is not None:
            # Store raw output text under outputs.raw if provided
            outs = dict(step_execution.outputs or {})
            outs["raw"] = output
            step_execution.outputs = outs
        step_execution.save(update_fields=["status", "completed_at", "outputs"])

        # Calcular duración
        duration = 0.0
        if step_execution.started_at and step_execution.completed_at:
            delta = step_execution.completed_at - step_execution.started_at
            duration = delta.total_seconds()

        # Emitir evento y notificar
        event = FlowStepCompleted(
            event_id=uuid4(),
            flow_id=step_execution.step.flow_version.flow.id,
            step_id=step_execution.step.id,
            step_name=step_execution.step.name,
            user_id=int(getattr(step_execution.step.flow_version.flow.owner, "id", 0)),
            duration=duration,
        )

        use_case = container.notify_step_completed_use_case()
        use_case.execute(event=event, send_webhook=webhook_url)

    @staticmethod
    def log_step_output(
        step_execution: StepExecution, line: str, event: str = "log"
    ) -> None:
        """Publica una línea de log al stream SSE del StepExecution."""
        step_log_broker.publish(
            str(step_execution.id),
            event=event,
            data={"line": str(line), "at": datetime.now().isoformat()},
        )

    @staticmethod
    def fail_step_execution(
        step_execution: StepExecution,
        error_message: str,
        webhook_url: Optional[str] = None,
    ) -> None:
        """
        Marca un step como fallido.

        Args:
            step_execution: Ejecución de step
            error_message: Mensaje de error
            webhook_url: URL de webhook para notificaciones
        """
        step_execution.status = "failed"
        step_execution.completed_at = datetime.now()
        step_execution.error_message = error_message
        step_execution.save(update_fields=["status", "completed_at", "error_message"])
        # Emitir evento de fallo
        event = FlowStepFailed(
            event_id=uuid4(),
            flow_id=step_execution.step.flow_version.flow.id,
            step_id=step_execution.step.id,
            step_name=step_execution.step.name,
            user_id=int(getattr(step_execution.step.flow_version.flow.owner, "id", 0)),
            error_message=error_message,
        )

        user_email = str(
            getattr(step_execution.step.flow_version.flow.owner, "email", "")
        )
        use_case = container.notify_step_failed_use_case()
        use_case.execute(event=event, user_email=user_email, send_webhook=webhook_url)

    @staticmethod
    def complete_flow_execution(
        execution_snapshot: ExecutionSnapshot,
        webhook_url: Optional[str] = None,
    ) -> None:
        """
        Completa la ejecución de un flujo.

        Args:
            execution_snapshot: Snapshot de ejecución
            webhook_url: URL de webhook para notificaciones
        """
        execution_snapshot.status = "completed"
        execution_snapshot.save(update_fields=["status"])

        # Calcular duración
        duration = 0.0
        # Without started/completed timestamps on snapshot, compute duration from steps if possible
        first = (
            StepExecution.objects.filter(execution_snapshot=execution_snapshot)
            .order_by("started_at")
            .first()
        )
        last = (
            StepExecution.objects.filter(execution_snapshot=execution_snapshot)
            .order_by("-completed_at")
            .first()
        )
        if first and first.started_at and last and last.completed_at:
            delta = last.completed_at - first.started_at
            duration = delta.total_seconds()

        # Contar steps
        total_steps = StepExecution.objects.filter(
            execution_snapshot=execution_snapshot
        ).count()

        # Emitir evento y notificar
        event = FlowCompleted(
            event_id=uuid4(),
            flow_id=execution_snapshot.flow_version.flow.id,
            flow_name=execution_snapshot.flow_version.flow.name,
            user_id=int(getattr(execution_snapshot.flow_version.flow.owner, "id", 0)),
            total_steps=total_steps,
            duration=duration,
        )

        user_email = str(
            getattr(execution_snapshot.flow_version.flow.owner, "email", "")
        )
        use_case = container.notify_flow_completed_use_case()
        use_case.execute(event=event, user_email=user_email, send_webhook=webhook_url)

    @staticmethod
    def complete_step_logs(step_execution: StepExecution) -> None:
        """Marca el stream SSE de logs del StepExecution como completado."""
        step_log_broker.complete(str(step_execution.id))


class FlowPermissionService:
    """Servicio para verificación de permisos sobre flujos."""

    @staticmethod
    def can_user_read_flow(user: User, flow: Flow) -> bool:
        """
        Verifica si un usuario puede leer un flujo.
        Args:
            user: Usuario
            flow: Flujo
        Returns:
            True si puede leerlo
        """
        if user.is_superuser:
            return True
        if flow.owner == user:
            return True
        return user.has_permission("flows", "read")

    @staticmethod
    def can_user_write_flow(user: User, flow: Flow) -> bool:
        """
        Verifica si un usuario puede modificar un flujo.

        Args:
            user: Usuario
            flow: Flujo

        Returns:
            True si puede modificarlo
        """
        if user.is_superuser:
            return True
        # Solo el propietario o usuarios con permiso flows.write
        if flow.owner == user:
            return True
        return user.has_permission("flows", "write")

    @staticmethod
    def can_user_delete_flow(user: User, flow: Flow) -> bool:
        """
        Verifica si un usuario puede eliminar un flujo.
        Args:
            user: Usuario
            flow: Flujo
        Returns:
            True si puede eliminarlo
        """
        if user.is_superuser:
            return True

        # Solo el propietario puede eliminar
        return flow.owner == user

    @staticmethod
    def can_user_execute_flow(user: User, flow: Flow) -> bool:
        """
        Verifica si un usuario puede ejecutar un flujo.

        Args:
            user: Usuario
            flow: Flujo

        Returns:
            True si puede ejecutarlo
        """
        if user.is_superuser:
            return True
        # Propietario o usuarios con permiso flows.execute
        if flow.owner == user:
            return True
        return user.has_permission("flows", "execute")
