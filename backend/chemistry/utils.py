"""
Utilidades para la gestión de usuarios del sistema Chemistry.

Funciones auxiliares para crear y obtener usuarios del sistema,
especialmente el usuario administrador por defecto.
"""

from typing import Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser

# Nota: get_user_model() devuelve un subtipo de AbstractBaseUser, usamos Type para mypy
User: Type[AbstractBaseUser] = get_user_model()


def get_or_create_admin_user() -> AbstractBaseUser:
    """
    Obtiene o crea el usuario administrador principal del sistema.

    Este usuario se usa como valor por defecto en migraciones y
    para operaciones del sistema que requieren un usuario.

    Returns:
        Usuario administrador del sistema
    """
    # Primero buscar el usuario administrador específico de ChemFlow
    try:
        admin_exact = User.objects.get(username="chemflow_admin")
        return admin_exact
    except User.DoesNotExist:
        pass

    # Si no existe, buscar cualquier superusuario
    admin_opt: AbstractBaseUser | None = User.objects.filter(is_superuser=True).first()
    if admin_opt is not None:
        return admin_opt

    # Como último recurso, crear el usuario administrador
    admin_user = User.objects.create_superuser(  # type: ignore[attr-defined]
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
