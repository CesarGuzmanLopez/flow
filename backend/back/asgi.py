"""
Configuración ASGI para el proyecto ChemFlow.

Expone la aplicación ASGI como variable de módulo llamada ``application``.
Usado para servidores ASGI como Daphne, Uvicorn o Hypercorn.

Para más información, consulta:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")

application = get_asgi_application()
