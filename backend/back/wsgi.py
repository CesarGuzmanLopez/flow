"""
Configuración WSGI para el proyecto ChemFlow.

Expone la aplicación WSGI como variable de módulo llamada ``application``.
Usado para servidores WSGI como Gunicorn, uWSGI o mod_wsgi.

Para más información, consulta:
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")

application = get_wsgi_application()
