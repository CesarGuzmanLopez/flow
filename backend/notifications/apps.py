"""
Configuración de la aplicación Notifications para Django.

Esta app gestiona el sistema de notificaciones con arquitectura hexagonal:
- Domain: Entidades y value objects
- Application: Use cases y servicios de aplicación
- Infrastructure: Adaptadores de email, webhooks, WebSockets
- Interfaces: API REST y serializers
"""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuración de la app Notifications."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"
