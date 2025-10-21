"""
Servicio de aplicación para notificaciones.

Implementa los casos de uso del sistema de notificaciones,
orquestando entidades de dominio y adaptadores de infraestructura.
"""

from typing import List, Optional
from uuid import UUID

from ..domain.entities import (
    EmailNotification,
    NotificationPriority,
    NotificationStatus,
    RealtimeNotification,
    WebhookNotification,
)
from ..domain.ports import (
    IEmailSender,
    INotificationRepository,
    IRealtimeSender,
    ITemplateRenderer,
    IWebhookSender,
)
from .dtos import (
    NotificationResponseDTO,
    SendEmailDTO,
    SendRealtimeDTO,
    SendWebhookDTO,
)


class NotificationService:
    """
    Servicio de aplicación para gestión de notificaciones.

    Sigue el patrón Application Service y el principio de Inversión de
    Dependencias (DIP) inyectando los adaptadores necesarios.
    """

    def __init__(
        self,
        email_sender: IEmailSender,
        webhook_sender: IWebhookSender,
        realtime_sender: IRealtimeSender,
        repository: INotificationRepository,
        template_renderer: Optional[ITemplateRenderer] = None,
    ):
        """
        Inicializa el servicio con sus dependencias inyectadas.

        Args:
            email_sender: Adaptador para envío de emails
            webhook_sender: Adaptador para envío de webhooks
            realtime_sender: Adaptador para notificaciones en tiempo real
            repository: Repositorio para persistencia
            template_renderer: Renderizador de templates opcional
        """
        self._email_sender = email_sender
        self._webhook_sender = webhook_sender
        self._realtime_sender = realtime_sender
        self._repository = repository
        self._template_renderer = template_renderer

    def send_email(self, dto: SendEmailDTO) -> NotificationResponseDTO:
        """
        Envía una notificación por email.

        Args:
            dto: DTO con los datos del email

        Returns:
            DTO con el resultado del envío
        """
        # Crear entidad de dominio
        notification = EmailNotification(
            recipient=dto.recipient,
            subject=dto.subject,
            message=dto.message,
            html_message=dto.html_message,
            from_email=dto.from_email,
            cc=dto.cc,
            bcc=dto.bcc,
            template_name=dto.template_name,
            context=dto.context,
            priority=NotificationPriority[dto.priority.upper()],
        )

        # Renderizar template si se especifica
        if dto.template_name and self._template_renderer:
            try:
                notification.message = self._template_renderer.render(
                    dto.template_name, dto.context
                )
                notification.html_message = self._template_renderer.render_html(
                    dto.template_name, dto.context
                )
            except Exception as e:
                return NotificationResponseDTO(
                    success=False,
                    error_message=f"Error renderizando template: {str(e)}",
                )

        # Persistir antes de enviar
        notification = self._repository.save(notification)

        # Intentar enviar
        try:
            success = self._email_sender.send(notification)
            if success:
                notification.mark_as_sent()
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=True,
                    notification_id=str(notification.id),
                    sent_at=notification.sent_at.isoformat()
                    if notification.sent_at
                    else None,
                )
            else:
                notification.mark_as_failed("Error desconocido al enviar")
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=False,
                    notification_id=str(notification.id),
                    error_message="Error al enviar notificación",
                )
        except Exception as e:
            notification.mark_as_failed(str(e))
            self._repository.update(notification)
            return NotificationResponseDTO(
                success=False,
                notification_id=str(notification.id),
                error_message=str(e),
            )

    def send_webhook(self, dto: SendWebhookDTO) -> NotificationResponseDTO:
        """
        Envía una notificación por webhook.

        Args:
            dto: DTO con los datos del webhook

        Returns:
            DTO con el resultado del envío
        """
        notification = WebhookNotification(
            recipient=dto.webhook_url,
            webhook_url=dto.webhook_url,
            payload=dto.payload,
            headers=dto.headers,
            http_method=dto.http_method,
            timeout=dto.timeout,
            priority=NotificationPriority[dto.priority.upper()],
        )

        notification = self._repository.save(notification)

        try:
            success = self._webhook_sender.send(notification)
            if success:
                notification.mark_as_sent()
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=True,
                    notification_id=str(notification.id),
                    sent_at=notification.sent_at.isoformat()
                    if notification.sent_at
                    else None,
                )
            else:
                notification.mark_as_failed("Error al enviar webhook")
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=False,
                    notification_id=str(notification.id),
                    error_message="Error al enviar webhook",
                )
        except Exception as e:
            notification.mark_as_failed(str(e))
            self._repository.update(notification)
            return NotificationResponseDTO(
                success=False,
                notification_id=str(notification.id),
                error_message=str(e),
            )

    def send_realtime(self, dto: SendRealtimeDTO) -> NotificationResponseDTO:
        """
        Envía una notificación en tiempo real.

        Args:
            dto: DTO con los datos de la notificación

        Returns:
            DTO con el resultado del envío
        """
        notification = RealtimeNotification(
            recipient=dto.channel,
            channel=dto.channel,
            event_type=dto.event_type,
            context=dto.data,
            user_id=dto.user_id,
            priority=NotificationPriority[dto.priority.upper()],
        )

        notification = self._repository.save(notification)

        try:
            if dto.user_id:
                success = self._realtime_sender.send_to_user(
                    dto.user_id, dto.event_type, dto.data
                )
            else:
                success = self._realtime_sender.send_to_channel(
                    dto.channel, dto.event_type, dto.data
                )

            if success:
                notification.mark_as_sent()
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=True,
                    notification_id=str(notification.id),
                    sent_at=notification.sent_at.isoformat()
                    if notification.sent_at
                    else None,
                )
            else:
                notification.mark_as_failed(
                    "Error al enviar notificación en tiempo real"
                )
                self._repository.update(notification)
                return NotificationResponseDTO(
                    success=False,
                    notification_id=str(notification.id),
                    error_message="Error al enviar notificación en tiempo real",
                )
        except Exception as e:
            notification.mark_as_failed(str(e))
            self._repository.update(notification)
            return NotificationResponseDTO(
                success=False,
                notification_id=str(notification.id),
                error_message=str(e),
            )

    def retry_failed_notifications(self) -> List[NotificationResponseDTO]:
        """
        Reintenta enviar notificaciones fallidas.

        Returns:
            Lista de DTOs con los resultados de los reintentos
        """
        failed = self._repository.find_failed_retriable(limit=50)
        results = []

        for notification in failed:
            if not notification.can_retry():
                continue

            notification.increment_retry()
            self._repository.update(notification)

            try:
                success = False
                if isinstance(notification, EmailNotification):
                    success = self._email_sender.send(notification)
                elif isinstance(notification, WebhookNotification):
                    success = self._webhook_sender.send(notification)
                elif isinstance(notification, RealtimeNotification):
                    if notification.user_id:
                        success = self._realtime_sender.send_to_user(
                            notification.user_id,
                            notification.event_type,
                            notification.context,
                        )
                    else:
                        success = self._realtime_sender.send_to_channel(
                            notification.channel,
                            notification.event_type,
                            notification.context,
                        )

                if success:
                    notification.mark_as_sent()
                    self._repository.update(notification)
                    results.append(
                        NotificationResponseDTO(
                            success=True,
                            notification_id=str(notification.id),
                            sent_at=notification.sent_at.isoformat()
                            if notification.sent_at
                            else None,
                        )
                    )
                else:
                    notification.mark_as_failed("Fallo en reintento")
                    self._repository.update(notification)
                    results.append(
                        NotificationResponseDTO(
                            success=False,
                            notification_id=str(notification.id),
                            error_message="Fallo en reintento",
                        )
                    )
            except Exception as e:
                notification.mark_as_failed(str(e))
                self._repository.update(notification)
                results.append(
                    NotificationResponseDTO(
                        success=False,
                        notification_id=str(notification.id),
                        error_message=str(e),
                    )
                )

        return results

    def get_notification_status(
        self, notification_id: UUID
    ) -> Optional[NotificationResponseDTO]:
        """
        Obtiene el estado de una notificación.

        Args:
            notification_id: ID de la notificación

        Returns:
            DTO con el estado o None si no existe
        """
        notification = self._repository.find_by_id(notification_id)
        if not notification:
            return None

        return NotificationResponseDTO(
            success=notification.status == NotificationStatus.SENT,
            notification_id=str(notification.id),
            error_message=notification.error_message,
            sent_at=notification.sent_at.isoformat() if notification.sent_at else None,
        )
