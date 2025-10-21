"""
Adaptador mock para notificaciones en tiempo real.

Implementa IRealtimeSender simulando WebSockets/SSE.
En producción, esto se reemplazaría con Django Channels o similar.
"""

import logging
from typing import List

from notifications.domain.entities import Notification
from notifications.domain.ports import IRealtimeSender

logger = logging.getLogger(__name__)


class MockRealtimeSender(IRealtimeSender):  # noqa: F821
    """
    Adaptador mock para notificaciones en tiempo real.

    Simula el envío de notificaciones WebSocket/SSE registrándolas en logs.
    En producción, usar Django Channels, Pusher, o similar.
    """

    def __init__(self):
        """Inicializa el adaptador mock."""
        self.sent_messages = []

    def send(self, notification: Notification) -> bool:
        """
        Simula el envío de notificación en tiempo real.

        Args:
            notification: Notificación a enviar

        Returns:
            True siempre (simula éxito)
        """
        logger.info("=" * 80)
        logger.info("⚡ MOCK REALTIME NOTIFICATION")
        logger.info(f"Canal: {getattr(notification, 'channel', 'N/A')}")
        logger.info(f"Evento: {getattr(notification, 'event_type', 'N/A')}")
        logger.info(f"Datos: {notification.context}")
        logger.info("=" * 80)

        self.sent_messages.append(
            {
                "channel": getattr(notification, "channel", None),
                "event": getattr(notification, "event_type", None),
                "data": notification.context,
            }
        )
        return True

    def send_batch(self, notifications: List[Notification]) -> List[bool]:
        """
        Simula el envío de lote de notificaciones.

        Args:
            notifications: Lista de notificaciones

        Returns:
            Lista de True (simula éxito)
        """
        return [self.send(n) for n in notifications]

    def send_to_user(self, user_id: int, event: str, data: dict) -> bool:
        """
        Simula envío a usuario específico.

        Args:
            user_id: ID del usuario
            event: Tipo de evento
            data: Datos del evento

        Returns:
            True siempre (simula éxito)
        """
        logger.info("=" * 80)
        logger.info("⚡ MOCK REALTIME TO USER")
        logger.info(f"Usuario: {user_id}")
        logger.info(f"Evento: {event}")
        logger.info(f"Datos: {data}")
        logger.info("=" * 80)

        self.sent_messages.append({"user_id": user_id, "event": event, "data": data})
        return True

    def send_to_channel(self, channel: str, event: str, data: dict) -> bool:
        """
        Simula envío a canal.

        Args:
            channel: Nombre del canal
            event: Tipo de evento
            data: Datos del evento

        Returns:
            True siempre (simula éxito)
        """
        logger.info("=" * 80)
        logger.info("⚡ MOCK REALTIME TO CHANNEL")
        logger.info(f"Canal: {channel}")
        logger.info(f"Evento: {event}")
        logger.info(f"Datos: {data}")
        logger.info("=" * 80)

        self.sent_messages.append({"channel": channel, "event": event, "data": data})
        return True

    def get_sent_count(self) -> int:
        """Retorna el número de mensajes enviados."""
        return len(self.sent_messages)

    def clear_sent(self) -> None:
        """Limpia la lista de mensajes enviados."""
        self.sent_messages.clear()
