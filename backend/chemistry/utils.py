"""
Utilidades para la gestión de usuarios del sistema Chemistry.

Funciones auxiliares para crear y obtener usuarios del sistema,
especialmente el usuario administrador por defecto.
"""

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from users.models import User
else:
    User = get_user_model()


def get_or_create_admin_user() -> "User":
    """
    Obtiene o crea el usuario administrador principal del sistema.

    Este usuario se usa como valor por defecto en migraciones y
    para operaciones del sistema que requieren un usuario.

    Returns:
        Usuario administrador del sistema
    """
    user_model = get_user_model()
    # Primero buscar el usuario administrador específico de ChemFlow
    try:
        admin_exact = user_model.objects.get(username="chemflow_admin")
        return admin_exact
    except user_model.DoesNotExist:
        pass

    # Si no existe, buscar cualquier superusuario
    admin_opt = user_model.objects.filter(is_superuser=True).first()
    if admin_opt is not None:
        return admin_opt

    # Como último recurso, crear el usuario administrador
    admin_user = user_model.objects.create_superuser(
        username="chemflow_admin",
        email="admin@chemflow.local",
        password="ChemFlow2024!",
        is_active=True,
    )

    return admin_user


def get_default_user_id() -> int:
    """
    Obtiene el ID del usuario administrador por defecto.

    Usado especialmente en migraciones de datos.

    Returns:
        ID del usuario administrador
    """
    admin_user = get_or_create_admin_user()
    return int(getattr(admin_user, "id"))

