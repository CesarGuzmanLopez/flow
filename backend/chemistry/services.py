"""
Servicios de dominio para Chemistry (capa de aplicación - arquitectura hexagonal).

Define funciones para filtrar y validar acceso a entidades químicas por usuario.
Implementa la lógica de negocio separada de los adaptadores (views).
"""

from typing import Any

from django.db.models import QuerySet

from .models import Molecule


def filter_molecules_for_user(qs: QuerySet[Molecule], user: Any) -> QuerySet[Molecule]:
    """
    Restringe moléculas a las creadas por el usuario si no tiene permisos globales.

    Args:
        qs: QuerySet de moléculas a filtrar
        user: Usuario autenticado

    Returns:
        QuerySet filtrado según permisos del usuario

    Por simplicidad, reutilizamos el permiso de lectura de química para decidir
    si ve todas o solo las propias.
    """
    if getattr(user, "is_superuser", False) or user.has_permission("chemistry", "read"):
        return qs
    return qs.filter(created_by=user)


__all__ = ["filter_molecules_for_user"]
