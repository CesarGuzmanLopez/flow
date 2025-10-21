"""
Contenedor de inyección de dependencias para notificaciones.

Implementa el patrón Dependency Injection Container para gestionar
la creación y configuración de servicios y adaptadores.
"""

from typing import Optional

from .application.services import NotificationService
from .application.use_cases import (
    NotifyFlowCompletedUseCase,
    NotifyStepCompletedUseCase,
    NotifyStepFailedUseCase,
    NotifyStepStartedUseCase,
    SendEmailVerificationUseCase,
    SendPasswordResetEmailUseCase,
    SendWelcomeEmailUseCase,
)
from .domain.ports import (
    IEmailSender,
    INotificationRepository,
    IRealtimeSender,
    ITemplateRenderer,
    IWebhookSender,
)
from .infrastructure.email_mock import MockEmailSender
from .infrastructure.realtime_mock import MockRealtimeSender
from .infrastructure.repository import InMemoryNotificationRepository
from .infrastructure.template_renderer import SimpleTemplateRenderer
from .infrastructure.webhook_sender import WebhookSender


class NotificationContainer:
    """
    Contenedor IoC para gestión de dependencias de notificaciones.

    Implementa el patrón Service Locator + Dependency Injection.
    """

    _instance: Optional["NotificationContainer"] = None
    _initialized: bool = False

    def __new__(cls):
        """Implementa el patrón Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa el contenedor una sola vez."""
        if not self._initialized:
            self._email_sender: Optional[IEmailSender] = None
            self._webhook_sender: Optional[IWebhookSender] = None
            self._realtime_sender: Optional[IRealtimeSender] = None
            self._repository: Optional[INotificationRepository] = None
            self._template_renderer: Optional[ITemplateRenderer] = None
            self._notification_service: Optional[NotificationService] = None

            # Use cases
            self._password_reset_use_case: Optional[SendPasswordResetEmailUseCase] = (
                None
            )
            self._email_verification_use_case: Optional[
                SendEmailVerificationUseCase
            ] = None
            self._welcome_email_use_case: Optional[SendWelcomeEmailUseCase] = None
            self._notify_step_started_use_case: Optional[NotifyStepStartedUseCase] = (
                None
            )
            self._notify_step_completed_use_case: Optional[
                NotifyStepCompletedUseCase
            ] = None
            self._notify_step_failed_use_case: Optional[NotifyStepFailedUseCase] = None
            self._notify_flow_completed_use_case: Optional[
                NotifyFlowCompletedUseCase
            ] = None

            NotificationContainer._initialized = True

    def email_sender(self) -> IEmailSender:
        """Obtiene o crea el adaptador de email."""
        if self._email_sender is None:
            self._email_sender = MockEmailSender()
        return self._email_sender

    def webhook_sender(self) -> IWebhookSender:
        """Obtiene o crea el adaptador de webhooks."""
        if self._webhook_sender is None:
            self._webhook_sender = WebhookSender()
        return self._webhook_sender

    def realtime_sender(self) -> IRealtimeSender:
        """Obtiene o crea el adaptador de tiempo real."""
        if self._realtime_sender is None:
            self._realtime_sender = MockRealtimeSender()
        return self._realtime_sender

    def repository(self) -> INotificationRepository:
        """Obtiene o crea el repositorio."""
        if self._repository is None:
            self._repository = InMemoryNotificationRepository()
        return self._repository

    def template_renderer(self) -> ITemplateRenderer:
        """Obtiene o crea el renderizador de templates."""
        if self._template_renderer is None:
            self._template_renderer = SimpleTemplateRenderer()
        return self._template_renderer

    def notification_service(self) -> NotificationService:
        """Obtiene o crea el servicio de notificaciones."""
        if self._notification_service is None:
            self._notification_service = NotificationService(
                email_sender=self.email_sender(),
                webhook_sender=self.webhook_sender(),
                realtime_sender=self.realtime_sender(),
                repository=self.repository(),
                template_renderer=self.template_renderer(),
            )
        return self._notification_service

    def password_reset_use_case(self) -> SendPasswordResetEmailUseCase:
        """Obtiene el use case de reset de contraseña."""
        if self._password_reset_use_case is None:
            self._password_reset_use_case = SendPasswordResetEmailUseCase(
                self.notification_service()
            )
        return self._password_reset_use_case

    def email_verification_use_case(self) -> SendEmailVerificationUseCase:
        """Obtiene el use case de verificación de email."""
        if self._email_verification_use_case is None:
            self._email_verification_use_case = SendEmailVerificationUseCase(
                self.notification_service()
            )
        return self._email_verification_use_case

    def welcome_email_use_case(self) -> SendWelcomeEmailUseCase:
        """Obtiene el use case de email de bienvenida."""
        if self._welcome_email_use_case is None:
            self._welcome_email_use_case = SendWelcomeEmailUseCase(
                self.notification_service()
            )
        return self._welcome_email_use_case

    def notify_step_started_use_case(self) -> NotifyStepStartedUseCase:
        """Obtiene el use case de notificación de inicio de step."""
        if self._notify_step_started_use_case is None:
            self._notify_step_started_use_case = NotifyStepStartedUseCase(
                self.notification_service()
            )
        return self._notify_step_started_use_case

    def notify_step_completed_use_case(self) -> NotifyStepCompletedUseCase:
        """Obtiene el use case de notificación de completado de step."""
        if self._notify_step_completed_use_case is None:
            self._notify_step_completed_use_case = NotifyStepCompletedUseCase(
                self.notification_service()
            )
        return self._notify_step_completed_use_case

    def notify_step_failed_use_case(self) -> NotifyStepFailedUseCase:
        """Obtiene el use case de notificación de fallo de step."""
        if self._notify_step_failed_use_case is None:
            self._notify_step_failed_use_case = NotifyStepFailedUseCase(
                self.notification_service()
            )
        return self._notify_step_failed_use_case

    def notify_flow_completed_use_case(self) -> NotifyFlowCompletedUseCase:
        """Obtiene el use case de notificación de completado de flow."""
        if self._notify_flow_completed_use_case is None:
            self._notify_flow_completed_use_case = NotifyFlowCompletedUseCase(
                self.notification_service()
            )
        return self._notify_flow_completed_use_case

    # Métodos para testing

    def reset(self) -> None:
        """Resetea todas las dependencias (útil para testing)."""
        self._email_sender = None
        self._webhook_sender = None
        self._realtime_sender = None
        self._repository = None
        self._template_renderer = None
        self._notification_service = None
        self._password_reset_use_case = None
        self._email_verification_use_case = None
        self._welcome_email_use_case = None
        self._notify_step_started_use_case = None
        self._notify_step_completed_use_case = None
        self._notify_step_failed_use_case = None
        self._notify_flow_completed_use_case = None

    def configure_email_sender(self, sender: IEmailSender) -> None:
        """Configura un adaptador de email personalizado."""
        self._email_sender = sender
        self._notification_service = None  # Reset service

    def configure_webhook_sender(self, sender: IWebhookSender) -> None:
        """Configura un adaptador de webhook personalizado."""
        self._webhook_sender = sender
        self._notification_service = None

    def configure_realtime_sender(self, sender: IRealtimeSender) -> None:
        """Configura un adaptador de tiempo real personalizado."""
        self._realtime_sender = sender
        self._notification_service = None

    def configure_repository(self, repository: INotificationRepository) -> None:
        """Configura un repositorio personalizado."""
        self._repository = repository
        self._notification_service = None


# Instancia global del contenedor
container = NotificationContainer()
