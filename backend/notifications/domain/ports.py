"""
Puertos (interfaces) para el dominio de notificaciones.

Define contratos que deben implementar los adaptadores en la capa de infraestructura.
Siguiendo el principio de Inversión de Dependencias (DIP) de SOLID.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from notifications.domain.entities import Notification


class INotificationSender(ABC):
    """Puerto para envío de notificaciones (Output Port)."""

    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """
        Envía una notificación.

        Args:
            notification: Notificación a enviar

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        pass

    @abstractmethod
    def send_batch(self, notifications: List[Notification]) -> List[bool]:
        """
        Envía un lote de notificaciones.

        Args:
            notifications: Lista de notificaciones a enviar

        Returns:
            Lista de booleanos indicando éxito/fallo de cada notificación
        """
        pass


class IEmailSender(INotificationSender):
    """Puerto específico para envío de emails."""

    @abstractmethod
    def send_html_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        plain_content: str = "",
        from_email: Optional[str] = None,
    ) -> bool:
        """Envía un email con contenido HTML."""
        pass


class IWebhookSender(INotificationSender):
    """Puerto específico para envío de webhooks."""

    @abstractmethod
    def send_webhook(
        self, url: str, payload: dict, headers: Optional[dict] = None
    ) -> bool:
        """Envía un webhook POST a la URL especificada."""
        pass


class IRealtimeSender(INotificationSender):
    """Puerto específico para notificaciones en tiempo real."""

    @abstractmethod
    def send_to_user(self, user_id: int, event: str, data: dict) -> bool:
        """Envía una notificación en tiempo real a un usuario específico."""
        pass

    @abstractmethod
    def send_to_channel(self, channel: str, event: str, data: dict) -> bool:
        """Envía una notificación a un canal de tiempo real."""
        pass


class INotificationRepository(ABC):
    """Puerto para persistencia de notificaciones (Output Port)."""

    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        """Persiste una notificación y retorna la entidad con ID asignado."""
        pass

    @abstractmethod
    def find_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Busca una notificación por su ID."""
        pass

    @abstractmethod
    def find_pending(self, limit: int = 100) -> List[Notification]:
        """Obtiene notificaciones pendientes de envío."""
        pass

    @abstractmethod
    def find_failed_retriable(self, limit: int = 100) -> List[Notification]:
        """Obtiene notificaciones fallidas que pueden reintentarse."""
        pass

    @abstractmethod
    def update(self, notification: Notification) -> Notification:
        """Actualiza una notificación existente."""
        pass

    @abstractmethod
    def delete(self, notification_id: UUID) -> bool:
        """Elimina una notificación."""
        pass


class ITemplateRenderer(ABC):
    """Puerto para renderizado de templates (Output Port)."""

    @abstractmethod
    def render(self, template_name: str, context: dict) -> str:
        """Renderiza un template con el contexto dado."""
        pass

    @abstractmethod
    def render_html(self, template_name: str, context: dict) -> str:
        """Renderiza un template HTML con el contexto dado."""
        pass
