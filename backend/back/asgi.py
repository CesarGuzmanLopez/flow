"""
Configuración ASGI para el proyecto ChemFlow.

Expone la aplicación ASGI como variable de módulo llamada ``application``.
Usado para servidores ASGI como Daphne, Uvicorn o Hypercorn.

Para más información, consulta:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")

# Django ASGI application
django_asgi_app = get_asgi_application()

# Importar enrutamiento WebSocket después de configurar Django
from back.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        # HTTP y otros protocolos
        "http": django_asgi_app,
        # WebSocket
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
