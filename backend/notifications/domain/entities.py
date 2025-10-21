"""
Entidades de dominio para notificaciones.

Define las entidades principales del sistema de notificaciones siguiendo
principios de Domain-Driven Design (DDD).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


class NotificationType(Enum):
    """Tipos de notificaciones soportadas."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    REALTIME = "realtime"


class NotificationStatus(Enum):
    """Estados posibles de una notificación."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationPriority(Enum):
    """Niveles de prioridad para notificaciones."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """
    Entidad raíz para notificaciones.

    Representa una notificación que puede enviarse por diferentes canales
    (email, webhook, tiempo real).
    """

    id: UUID = field(default_factory=uuid4)
    notification_type: NotificationType = NotificationType.EMAIL
    recipient: str = ""
    subject: str = ""
    message: str = ""
    template_name: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    status: NotificationStatus = NotificationStatus.PENDING
    priority: NotificationPriority = NotificationPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_as_sent(self) -> None:
        """Marca la notificación como enviada exitosamente."""
        self.status = NotificationStatus.SENT
        self.sent_at = datetime.now()
        self.error_message = None

    def mark_as_failed(self, error: str) -> None:
        """Marca la notificación como fallida."""
        self.status = NotificationStatus.FAILED
        self.failed_at = datetime.now()
        self.error_message = error

    def can_retry(self) -> bool:
        """Verifica si la notificación puede reintentarse."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Incrementa el contador de reintentos."""
        self.retry_count += 1
        self.status = NotificationStatus.RETRYING

    def is_high_priority(self) -> bool:
        """Verifica si la notificación tiene alta prioridad."""
        return self.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT]


@dataclass
class EmailNotification(Notification):
    """Notificación específica para email."""

    notification_type: NotificationType = field(
        default=NotificationType.EMAIL, init=False
    )
    from_email: Optional[str] = None
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    html_message: Optional[str] = None


@dataclass
class WebhookNotification(Notification):
    """Notificación específica para webhooks."""

    notification_type: NotificationType = field(
        default=NotificationType.WEBHOOK, init=False
    )
    webhook_url: str = ""
    http_method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    payload: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30


@dataclass
class RealtimeNotification(Notification):
    """Notificación en tiempo real (WebSocket)."""

    notification_type: NotificationType = field(
        default=NotificationType.REALTIME, init=False
    )
    channel: str = ""
    event_type: str = ""
    user_id: Optional[int] = None
