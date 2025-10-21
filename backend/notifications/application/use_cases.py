"""
Use Cases para escenarios específicos de notificaciones.

Cada use case representa una operación de negocio completa,
siguiendo el principio Single Responsibility (SRP) de SOLID.
"""

from typing import Optional

from notifications.domain.events import (
    EmailVerificationRequested,
    FlowCompleted,
    FlowStepCompleted,
    FlowStepFailed,
    FlowStepStarted,
    PasswordResetRequested,
    UserRegistered,
)

from .dtos import NotificationResponseDTO, SendEmailDTO, SendRealtimeDTO, SendWebhookDTO
from .services import NotificationService


class SendPasswordResetEmailUseCase:
    """Use case para enviar email de recuperación de contraseña."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self, event: PasswordResetRequested, reset_url: str
    ) -> NotificationResponseDTO:
        """
        Ejecuta el envío de email de recuperación.

        Args:
            event: Evento de solicitud de recuperación
            reset_url: URL para resetear la contraseña

        Returns:
            Resultado del envío
        """
        dto = SendEmailDTO(
            recipient=event.email,
            subject="Recuperación de contraseña - ChemFlow",
            message=f"Para restablecer tu contraseña, visita: {reset_url}",
            template_name="password_reset",
            context={
                "reset_url": reset_url,
                "email": event.email,
                "token": event.token,
            },
            priority="high",
        )
        return self._service.send_email(dto)


class SendEmailVerificationUseCase:
    """Use case para enviar email de verificación."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self, event: EmailVerificationRequested, verification_url: str
    ) -> NotificationResponseDTO:
        """
        Ejecuta el envío de email de verificación.

        Args:
            event: Evento de solicitud de verificación
            verification_url: URL para verificar el email

        Returns:
            Resultado del envío
        """
        dto = SendEmailDTO(
            recipient=event.email,
            subject="Verifica tu email - ChemFlow",
            message=f"Para verificar tu email, visita: {verification_url}",
            template_name="email_verification",
            context={
                "verification_url": verification_url,
                "email": event.email,
                "token": event.token,
            },
            priority="high",
        )
        return self._service.send_email(dto)


class SendWelcomeEmailUseCase:
    """Use case para enviar email de bienvenida."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(self, event: UserRegistered) -> NotificationResponseDTO:
        """
        Ejecuta el envío de email de bienvenida.

        Args:
            event: Evento de registro de usuario

        Returns:
            Resultado del envío
        """
        dto = SendEmailDTO(
            recipient=event.email,
            subject="Bienvenido a ChemFlow",
            message=f"Hola {event.username}, bienvenido a ChemFlow!",
            template_name="welcome",
            context={
                "username": event.username,
                "email": event.email,
            },
            priority="normal",
        )
        return self._service.send_email(dto)


class NotifyStepStartedUseCase:
    """Use case para notificar inicio de step."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self,
        event: FlowStepStarted,
        send_email: bool = False,
        send_webhook: Optional[str] = None,
    ) -> dict:
        """
        Notifica el inicio de un step.

        Args:
            event: Evento de inicio de step
            send_email: Si debe enviar email
            send_webhook: URL del webhook si debe enviar

        Returns:
            Diccionario con los resultados de las notificaciones
        """
        results = {}

        # Notificación en tiempo real (siempre)
        realtime_dto = SendRealtimeDTO(
            channel=f"flow_{event.flow_id}",
            event_type="step.started",
            data={
                "flow_id": event.flow_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "started_at": event.occurred_at.isoformat(),
            },
            user_id=event.user_id,
            priority="high",
        )
        results["realtime"] = self._service.send_realtime(realtime_dto)

        # Email opcional
        if send_email:
            # Aquí necesitaríamos obtener el email del usuario
            # Por ahora lo dejamos como placeholder
            pass

        # Webhook opcional
        if send_webhook:
            webhook_dto = SendWebhookDTO(
                webhook_url=send_webhook,
                payload={
                    "event": "step.started",
                    "flow_id": event.flow_id,
                    "step_id": event.step_id,
                    "step_name": event.step_name,
                    "started_at": event.occurred_at.isoformat(),
                },
                priority="normal",
            )
            results["webhook"] = self._service.send_webhook(webhook_dto)

        return results


class NotifyStepCompletedUseCase:
    """Use case para notificar completado de step."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self,
        event: FlowStepCompleted,
        send_email: bool = False,
        send_webhook: Optional[str] = None,
    ) -> dict:
        """
        Notifica la completitud de un step.

        Args:
            event: Evento de completado de step
            send_email: Si debe enviar email
            send_webhook: URL del webhook si debe enviar

        Returns:
            Diccionario con los resultados de las notificaciones
        """
        results = {}

        # Notificación en tiempo real
        realtime_dto = SendRealtimeDTO(
            channel=f"flow_{event.flow_id}",
            event_type="step.completed",
            data={
                "flow_id": event.flow_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "duration": event.duration,
                "completed_at": event.occurred_at.isoformat(),
            },
            user_id=event.user_id,
            priority="high",
        )
        results["realtime"] = self._service.send_realtime(realtime_dto)

        # Webhook opcional
        if send_webhook:
            webhook_dto = SendWebhookDTO(
                webhook_url=send_webhook,
                payload={
                    "event": "step.completed",
                    "flow_id": event.flow_id,
                    "step_id": event.step_id,
                    "step_name": event.step_name,
                    "duration": event.duration,
                    "completed_at": event.occurred_at.isoformat(),
                },
                priority="normal",
            )
            results["webhook"] = self._service.send_webhook(webhook_dto)

        return results


class NotifyStepFailedUseCase:
    """Use case para notificar fallo de step."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self,
        event: FlowStepFailed,
        user_email: str,
        send_webhook: Optional[str] = None,
    ) -> dict:
        """
        Notifica el fallo de un step.

        Args:
            event: Evento de fallo de step
            user_email: Email del usuario para notificar
            send_webhook: URL del webhook si debe enviar

        Returns:
            Diccionario con los resultados de las notificaciones
        """
        results = {}

        # Notificación en tiempo real
        realtime_dto = SendRealtimeDTO(
            channel=f"flow_{event.flow_id}",
            event_type="step.failed",
            data={
                "flow_id": event.flow_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "error": event.error_message,
                "failed_at": event.occurred_at.isoformat(),
            },
            user_id=event.user_id,
            priority="urgent",
        )
        results["realtime"] = self._service.send_realtime(realtime_dto)

        # Email (siempre en caso de error)
        email_dto = SendEmailDTO(
            recipient=user_email,
            subject=f"Error en step: {event.step_name}",
            message=f"El step '{event.step_name}' ha fallado: {event.error_message}",
            template_name="step_failed",
            context={
                "flow_id": event.flow_id,
                "step_name": event.step_name,
                "error_message": event.error_message,
            },
            priority="urgent",
        )
        results["email"] = self._service.send_email(email_dto)

        # Webhook opcional
        if send_webhook:
            webhook_dto = SendWebhookDTO(
                webhook_url=send_webhook,
                payload={
                    "event": "step.failed",
                    "flow_id": event.flow_id,
                    "step_id": event.step_id,
                    "step_name": event.step_name,
                    "error": event.error_message,
                    "failed_at": event.occurred_at.isoformat(),
                },
                priority="high",
            )
            results["webhook"] = self._service.send_webhook(webhook_dto)

        return results


class NotifyFlowCompletedUseCase:
    """Use case para notificar completado de flow."""

    def __init__(self, notification_service: NotificationService):
        self._service = notification_service

    def execute(
        self,
        event: FlowCompleted,
        user_email: str,
        send_webhook: Optional[str] = None,
    ) -> dict:
        """
        Notifica la completitud de un flow.

        Args:
            event: Evento de completado de flow
            user_email: Email del usuario
            send_webhook: URL del webhook si debe enviar

        Returns:
            Diccionario con los resultados de las notificaciones
        """
        results = {}

        # Notificación en tiempo real
        realtime_dto = SendRealtimeDTO(
            channel=f"flow_{event.flow_id}",
            event_type="flow.completed",
            data={
                "flow_id": event.flow_id,
                "flow_name": event.flow_name,
                "total_steps": event.total_steps,
                "duration": event.duration,
                "completed_at": event.occurred_at.isoformat(),
            },
            user_id=event.user_id,
            priority="high",
        )
        results["realtime"] = self._service.send_realtime(realtime_dto)

        # Email
        email_dto = SendEmailDTO(
            recipient=user_email,
            subject=f"Flujo completado: {event.flow_name}",
            message=f"El flujo '{event.flow_name}' se ha completado exitosamente.",
            template_name="flow_completed",
            context={
                "flow_id": event.flow_id,
                "flow_name": event.flow_name,
                "total_steps": event.total_steps,
                "duration": event.duration,
            },
            priority="normal",
        )
        results["email"] = self._service.send_email(email_dto)

        # Webhook opcional
        if send_webhook:
            webhook_dto = SendWebhookDTO(
                webhook_url=send_webhook,
                payload={
                    "event": "flow.completed",
                    "flow_id": event.flow_id,
                    "flow_name": event.flow_name,
                    "total_steps": event.total_steps,
                    "duration": event.duration,
                    "completed_at": event.occurred_at.isoformat(),
                },
                priority="normal",
            )
            results["webhook"] = self._service.send_webhook(webhook_dto)

        return results
