"""
Servicio de WebSocket para colaboración en tiempo real en flujos.

Gestiona:
- Conexiones de múltiples usuarios
- Sincronización de cambios de flujos
- Indicadores de presencia (quién está editando)
- Locks de elementos (prevenir conflictos)
- Cursores compartidos en tiempo real
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


@dataclass
class UserPresence:
    """Información de presencia de un usuario"""

    user_id: int
    username: str
    flow_id: int
    cursor_position: Dict[str, float] = field(default_factory=dict)
    selected_node_id: Optional[str] = None
    locked_elements: Set[str] = field(default_factory=set)
    last_activity: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "flow_id": self.flow_id,
            "cursor_position": self.cursor_position,
            "selected_node_id": self.selected_node_id,
            "locked_elements": list(self.locked_elements),
        }


class FlowCollaborationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer para colaboración en tiempo real de flujos.

    Maneja la sincronización de múltiples usuarios editando el mismo flujo.
    """

    # Almacenamiento global de presencias por flujo
    flow_users: Dict[int, Dict[int, UserPresence]] = {}
    # flow_id -> {element_id: user_id}
    element_locks: Dict[int, Dict[str, int]] = {}

    async def connect(self):
        """Maneja conexión de nuevo usuario"""
        # Obtener información del usuario
        user = self.scope["user"]
        self.user_id = user.id if user.is_authenticated else None
        self.username = user.username if user.is_authenticated else "anonymous"
        self.flow_id = int(self.scope["url_route"]["kwargs"]["flow_id"])
        self.room_group_name = f"flow_{self.flow_id}"

        # Unirse al grupo del flujo
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Registrar presencia del usuario
        if self.flow_id not in self.flow_users:
            self.flow_users[self.flow_id] = {}

        presence = UserPresence(
            user_id=self.user_id,
            username=self.username,
            flow_id=self.flow_id,
        )
        self.flow_users[self.flow_id][self.user_id] = presence

        # Notificar a otros usuarios que se conectó alguien
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_joined",
                "user_id": self.user_id,
                "username": self.username,
                "presence": presence.to_dict(),
            },
        )

        # Enviar presencias actuales al usuario que se conecta
        await self.send_current_presences()

        logger.info(f"Usuario {self.username} conectado al flujo {self.flow_id}")

    async def disconnect(self, close_code):
        """Maneja desconexión de usuario"""
        # Remover presencia del usuario
        if self.flow_id in self.flow_users:
            if self.user_id in self.flow_users[self.flow_id]:
                presence = self.flow_users[self.flow_id][self.user_id]
                # Liberar locks del usuario
                await self.release_locks(presence.locked_elements)
                del self.flow_users[self.flow_id][self.user_id]

        # Salir del grupo
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Notificar a otros usuarios
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_left",
                "user_id": self.user_id,
                "username": self.username,
            },
        )

        logger.info(f"Usuario {self.username} desconectado del flujo {self.flow_id}")

    async def receive(self, text_data):
        """Recibe mensajes del cliente"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "node_changed":
                await self.handle_node_changed(data)
            elif message_type == "cursor_moved":
                await self.handle_cursor_moved(data)
            elif message_type == "lock_element":
                await self.handle_lock_element(data)
            elif message_type == "unlock_element":
                await self.handle_unlock_element(data)
            elif message_type == "select_node":
                await self.handle_select_node(data)
            else:
                logger.warning(f"Tipo de mensaje desconocido: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Formato JSON inválido")
        except Exception as e:
            logger.error(f"Error procesando mensaje: {str(e)}")
            await self.send_error(str(e))

    # ============================================
    # HANDLERS DE MENSAJES
    # ============================================

    async def handle_node_changed(self, data: Dict[str, Any]):
        """Maneja cambios en nodos"""
        node_id = data.get("node_id")
        node_data = data.get("node_data")
        operation = data.get("operation")  # 'create', 'update', 'delete'

        # Verificar si el elemento está lockeado por otro usuario
        if self.is_locked_by_other(node_id):
            await self.send_error(
                f"Elemento {node_id} está siendo editado por otro usuario"
            )
            return

        # Guardar cambio en la BD
        await self.save_node_change(node_id, node_data, operation)

        # Transmitir cambio a otros usuarios
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "node_changed_broadcast",
                "user_id": self.user_id,
                "username": self.username,
                "node_id": node_id,
                "node_data": node_data,
                "operation": operation,
            },
        )

    async def handle_cursor_moved(self, data: Dict[str, Any]):
        """Maneja movimiento del cursor (posición en canvas)"""
        position = data.get("position", {})

        # Actualizar presencia
        if (
            self.flow_id in self.flow_users
            and self.user_id in self.flow_users[self.flow_id]
        ):
            self.flow_users[self.flow_id][self.user_id].cursor_position = position

        # Transmitir a otros usuarios (sin guardar en BD)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "cursor_moved_broadcast",
                "user_id": self.user_id,
                "username": self.username,
                "position": position,
            },
        )

    async def handle_lock_element(self, data: Dict[str, Any]):
        """Maneja lock de elemento (evitar edición simultánea)"""
        element_id = data.get("element_id")

        # Verificar si ya está lockeado
        if self.is_locked_by_other(element_id):
            await self.send_error(f"Elemento {element_id} ya está lockeado")
            return

        # Crear lock
        if self.flow_id not in self.element_locks:
            self.element_locks[self.flow_id] = {}

        self.element_locks[self.flow_id][element_id] = self.user_id

        # Actualizar presencia
        if (
            self.flow_id in self.flow_users
            and self.user_id in self.flow_users[self.flow_id]
        ):
            self.flow_users[self.flow_id][self.user_id].locked_elements.add(element_id)

        # Notificar a todos
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "element_locked",
                "user_id": self.user_id,
                "username": self.username,
                "element_id": element_id,
            },
        )

    async def handle_unlock_element(self, data: Dict[str, Any]):
        """Maneja unlock de elemento"""
        element_id = data.get("element_id")

        # Liberar lock
        if (
            self.flow_id in self.element_locks
            and element_id in self.element_locks[self.flow_id]
        ):
            if self.element_locks[self.flow_id][element_id] == self.user_id:
                del self.element_locks[self.flow_id][element_id]

        # Actualizar presencia
        if (
            self.flow_id in self.flow_users
            and self.user_id in self.flow_users[self.flow_id]
        ):
            self.flow_users[self.flow_id][self.user_id].locked_elements.discard(
                element_id
            )

        # Notificar a todos
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "element_unlocked",
                "user_id": self.user_id,
                "username": self.username,
                "element_id": element_id,
            },
        )

    async def handle_select_node(self, data: Dict[str, Any]):
        """Maneja selección de nodo (para highlighting en otros clientes)"""
        node_id = data.get("node_id")

        # Actualizar presencia
        if (
            self.flow_id in self.flow_users
            and self.user_id in self.flow_users[self.flow_id]
        ):
            self.flow_users[self.flow_id][self.user_id].selected_node_id = node_id

        # Transmitir a otros usuarios
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "node_selected",
                "user_id": self.user_id,
                "username": self.username,
                "node_id": node_id,
            },
        )

    # ============================================
    # BROADCAST HANDLERS (reciben del grupo)
    # ============================================

    async def user_joined(self, event):
        """Broadcast: Usuario se conectó"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_joined",
                    "data": event["presence"],
                }
            )
        )

    async def user_left(self, event):
        """Broadcast: Usuario se desconectó"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "user_left",
                    "data": {
                        "user_id": event["user_id"],
                        "username": event["username"],
                    },
                }
            )
        )

    async def node_changed_broadcast(self, event):
        """Broadcast: Cambio en nodo"""
        # No enviar al usuario que hizo el cambio
        if event["user_id"] != self.user_id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "node_changed",
                        "data": {
                            "user_id": event["user_id"],
                            "username": event["username"],
                            "node_id": event["node_id"],
                            "node_data": event["node_data"],
                            "operation": event["operation"],
                        },
                    }
                )
            )

    async def cursor_moved_broadcast(self, event):
        """Broadcast: Movimiento del cursor"""
        if event["user_id"] != self.user_id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "cursor_moved",
                        "data": {
                            "user_id": event["user_id"],
                            "username": event["username"],
                            "position": event["position"],
                        },
                    }
                )
            )

    async def element_locked(self, event):
        """Broadcast: Elemento lockeado"""
        if event["user_id"] != self.user_id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "element_locked",
                        "data": {
                            "user_id": event["user_id"],
                            "username": event["username"],
                            "element_id": event["element_id"],
                        },
                    }
                )
            )

    async def element_unlocked(self, event):
        """Broadcast: Elemento deslockeado"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "element_unlocked",
                    "data": {
                        "user_id": event["user_id"],
                        "element_id": event["element_id"],
                    },
                }
            )
        )

    async def node_selected(self, event):
        """Broadcast: Nodo seleccionado"""
        if event["user_id"] != self.user_id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "node_selected",
                        "data": {
                            "user_id": event["user_id"],
                            "username": event["username"],
                            "node_id": event["node_id"],
                        },
                    }
                )
            )

    # ============================================
    # HELPERS
    # ============================================

    def is_locked_by_other(self, element_id: str) -> bool:
        """Verifica si un elemento está lockeado por otro usuario"""
        if self.flow_id not in self.element_locks:
            return False

        if element_id not in self.element_locks[self.flow_id]:
            return False

        lock_owner = self.element_locks[self.flow_id][element_id]
        return lock_owner != self.user_id

    async def release_locks(self, element_ids: Set[str]):
        """Libera todos los locks de un usuario"""
        if self.flow_id not in self.element_locks:
            return

        for element_id in element_ids:
            if element_id in self.element_locks[self.flow_id]:
                if self.element_locks[self.flow_id][element_id] == self.user_id:
                    del self.element_locks[self.flow_id][element_id]

    async def send_current_presences(self):
        """Envía la lista de usuarios actualmente conectados"""
        presences = []
        if self.flow_id in self.flow_users:
            presences = [
                user.to_dict()
                for user in self.flow_users[self.flow_id].values()
                if user.user_id != self.user_id
            ]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "current_presences",
                    "data": {"presences": presences},
                }
            )
        )

    async def send_error(self, message: str):
        """Envía mensaje de error al cliente"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "data": {"message": message},
                }
            )
        )

    @database_sync_to_async
    def save_node_change(self, node_id: str, node_data: Dict[str, Any], operation: str):
        """Guarda cambio en la base de datos"""
        # Esta función debe ser implementada en lógica de negocio
        # Por ahora es un placeholder
        logger.info(f"Guardando cambio: {operation} en nodo {node_id}")
