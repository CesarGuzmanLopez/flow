"""
URLs para la aplicación de notificaciones.

Define los endpoints REST para notificaciones de usuario.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import UserNotificationViewSet

# Crear router para el ViewSet
router = DefaultRouter()
router.register(r"", UserNotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
]
