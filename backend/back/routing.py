"""
Configuración de enrutamiento WebSocket para Django Channels.

Define las rutas de WebSocket para la aplicación.
"""

from django.urls import re_path
from flows.consumers import FlowCollaborationConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/flows/(?P<flow_id>\d+)/$",
        FlowCollaborationConsumer.as_asgi(),
        name="flow_collaboration",
    ),
]
