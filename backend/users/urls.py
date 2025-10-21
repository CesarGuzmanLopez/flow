"""
Configuración de URLs para la app Users.

Registra todos los endpoints REST de la app usando el router de DRF:
- /api/users/users/ - Gestión de usuarios
- /api/users/roles/ - Gestión de roles
- /api/users/permissions/ - Consulta de permisos (read-only)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PermissionViewSet, RoleViewSet, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"permissions", PermissionViewSet, basename="permission")

urlpatterns = [
    path("", include(router.urls)),
]
