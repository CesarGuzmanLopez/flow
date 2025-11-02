"""
Eventos de dominio para notificaciones.

Los eventos de dominio representan hechos que han ocurrido en el sistema
y permiten desacoplar componentes siguiendo Event-Driven Architecture.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class DomainEvent:
    """Clase base para eventos de dominio."""

    event_id: UUID
    occurred_at: datetime = field(default_factory=datetime.now)
    event_type: str = ""


@dataclass
class NotificationCreated(DomainEvent):
    """Evento: Se ha creado una nueva notificación."""

    notification_id: Optional[UUID] = None
    notification_type: str = ""
    recipient: str = ""
    event_type: str = field(default="notification.created", init=False)


@dataclass
class NotificationSent(DomainEvent):
    """Evento: Una notificación se ha enviado exitosamente."""

    notification_id: Optional[UUID] = None
    sent_at: datetime = field(default_factory=datetime.now)
    event_type: str = field(default="notification.sent", init=False)


@dataclass
class NotificationFailed(DomainEvent):
    """Evento: Una notificación ha fallado al enviarse."""

    notification_id: Optional[UUID] = None
    error_message: str = ""
    retry_count: int = 0
    event_type: str = field(default="notification.failed", init=False)


@dataclass
class NotificationRetrying(DomainEvent):
    """Evento: Se está reintentando enviar una notificación."""

    notification_id: Optional[UUID] = None
    retry_count: int = 0
    event_type: str = field(default="notification.retrying", init=False)


# Eventos específicos de flujos
@dataclass
class FlowStepStarted(DomainEvent):
    """Evento: Un paso de flujo ha iniciado."""

    flow_id: int = 0
    step_id: int = 0
    step_name: str = ""
    user_id: int = 0
    event_type: str = field(default="flow.step.started", init=False)


@dataclass
class FlowStepCompleted(DomainEvent):
    """Evento: Un paso de flujo se ha completado."""

    flow_id: int = 0
    step_id: int = 0
    step_name: str = ""
    user_id: int = 0
    duration: float = 0.0
    event_type: str = field(default="flow.step.completed", init=False)


@dataclass
class FlowStepFailed(DomainEvent):
    """Evento: Un paso de flujo ha fallado."""

    flow_id: int = 0
    step_id: int = 0
    step_name: str = ""
    user_id: int = 0
    error_message: str = ""
    event_type: str = field(default="flow.step.failed", init=False)


@dataclass
class FlowCompleted(DomainEvent):
    """Evento: Un flujo se ha completado exitosamente."""

    flow_id: int = 0
    flow_name: str = ""
    user_id: int = 0
    total_steps: int = 0
    duration: float = 0.0
    event_type: str = field(default="flow.completed", init=False)


# Eventos de usuarios
@dataclass
class UserRegistered(DomainEvent):
    """Evento: Un nuevo usuario se ha registrado."""

    user_id: int = 0
    username: str = ""
    email: str = ""
    event_type: str = field(default="user.registered", init=False)


@dataclass
class PasswordResetRequested(DomainEvent):
    """Evento: Se ha solicitado un restablecimiento de contraseña."""

    user_id: int = 0
    email: str = ""
    token: str = ""
    event_type: str = field(default="user.password_reset_requested", init=False)


@dataclass
class EmailVerificationRequested(DomainEvent):
    """Evento: Se ha solicitado verificación de email."""

    user_id: int = 0
    email: str = ""
    token: str = ""
    event_type: str = field(default="user.email_verification_requested", init=False)
