"""
Configuración de la aplicación Users para Django.

Esta app gestiona usuarios, autenticación JWT, roles y permisos (RBAC).
Extiende el modelo User de Django con roles many-to-many y campo universidad.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuración de la app Users."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "users"
