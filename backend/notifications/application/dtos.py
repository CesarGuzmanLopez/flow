"""
DTOs (Data Transfer Objects) para la capa de aplicación.

Los DTOs son objetos simples para transferir datos entre capas,
desacoplando la API REST de las entidades de dominio.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SendEmailDTO:
    """DTO para enviar un email."""

    recipient: str
    subject: str
    message: str
    html_message: Optional[str] = None
    from_email: Optional[str] = None
    cc: List[str] = None
    bcc: List[str] = None
    template_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    priority: str = "normal"

    def __post_init__(self):
        if self.cc is None:
            self.cc = []
        if self.bcc is None:
            self.bcc = []
        if self.context is None:
            self.context = {}


@dataclass
class SendWebhookDTO:
    """DTO para enviar un webhook."""

    webhook_url: str
    payload: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None
    http_method: str = "POST"
    timeout: int = 30
    priority: str = "normal"

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


@dataclass
class SendRealtimeDTO:
    """DTO para enviar notificación en tiempo real."""

    channel: str
    event_type: str
    data: Dict[str, Any]
    user_id: Optional[int] = None
    priority: str = "high"


@dataclass
class NotificationResponseDTO:
    """DTO para respuestas de notificaciones."""

    success: bool
    notification_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[str] = None
