"""
Repositorio en memoria para notificaciones.

Implementa INotificationRepository usando un diccionario en memoria.
Para producción, implementar con Django ORM.
"""

from typing import Dict, List, Optional
from uuid import UUID

from notifications.domain.entities import Notification, NotificationStatus
from notifications.domain.ports import INotificationRepository


class InMemoryNotificationRepository(INotificationRepository):
    """
    Repositorio en memoria para notificaciones.

    Útil para desarrollo y testing. En producción usar Django ORM.
    """

    def __init__(self):
        """Inicializa el repositorio vacío."""
        self._notifications: Dict[UUID, Notification] = {}

    def save(self, notification: Notification) -> Notification:
        """
        Persiste una notificación.

        Args:
            notification: Notificación a persistir

        Returns:
            La misma notificación con ID asignado
        """
        self._notifications[notification.id] = notification
        return notification

    def find_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """
        Busca una notificación por ID.

        Args:
            notification_id: ID de la notificación

        Returns:
            La notificación o None si no existe
        """
        return self._notifications.get(notification_id)

    def find_pending(self, limit: int = 100) -> List[Notification]:
        """
        Obtiene notificaciones pendientes.

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de notificaciones pendientes
        """
        pending = [
            n
            for n in self._notifications.values()
            if n.status == NotificationStatus.PENDING
        ]
        return sorted(pending, key=lambda x: x.created_at)[:limit]

    def find_failed_retriable(self, limit: int = 100) -> List[Notification]:
        """
        Obtiene notificaciones fallidas que pueden reintentarse.

        Args:
            limit: Número máximo de resultados

        Returns:
            Lista de notificaciones fallidas reintentables
        """
        failed = [
            n
            for n in self._notifications.values()
            if n.status in [NotificationStatus.FAILED, NotificationStatus.RETRYING]
            and n.can_retry()
        ]
        return sorted(failed, key=lambda x: x.failed_at or x.created_at)[:limit]

    def update(self, notification: Notification) -> Notification:
        """
        Actualiza una notificación.

        Args:
            notification: Notificación a actualizar

        Returns:
            La notificación actualizada
        """
        if notification.id in self._notifications:
            self._notifications[notification.id] = notification
        return notification

    def delete(self, notification_id: UUID) -> bool:
        """
        Elimina una notificación.

        Args:
            notification_id: ID de la notificación

        Returns:
            True si se eliminó, False si no existía
        """
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False

    def count(self) -> int:
        """Retorna el número total de notificaciones."""
        return len(self._notifications)

    def clear(self) -> None:
        """Elimina todas las notificaciones."""
        self._notifications.clear()
