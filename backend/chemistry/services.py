"""
Servicios de dominio para Chemistry (capa de aplicación - arquitectura hexagonal).

Define funciones para filtrar y validar acceso a entidades químicas por usuario.
Implementa la lógica de negocio separada de los adaptadores (views).
"""

from typing import Any, Dict

from django.db.models import QuerySet

from .models import Molecule
from .providers import engine as chem_engine


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


def create_molecule_from_smiles(
    *,
    smiles: str,
    created_by: Any,
    name: str | None = None,
    extra_metadata: Dict[str, Any] | None = None,
) -> Molecule:
    """
    Create and persist a Molecule using the configured chemistry provider.

    - Normalizes SMILES, generates InChI/InChIKey and formula
    - Stores provider-calculated descriptors in metadata under `descriptors`
    - Ensures uniqueness by InChIKey when available
    """
    info = chem_engine.smiles_to_inchi(smiles)
    props = chem_engine.calculate_properties(smiles)

    metadata = {"descriptors": props}
    if extra_metadata:
        metadata.update(extra_metadata)

    defaults = {
        "name": name or info.get("molecular_formula") or "",
        "smiles": smiles,
        "canonical_smiles": info.get("canonical_smiles", ""),
        "inchi": info.get("inchi", ""),
        "molecular_formula": info.get("molecular_formula", ""),
        "created_by": created_by,
        "metadata": metadata,
    }

    inchikey = info.get("inchikey") or None
    if inchikey:
        molecule, _ = Molecule.objects.get_or_create(
            inchikey=inchikey, defaults=defaults
        )
    else:
        molecule = Molecule.objects.create(**defaults)
    return molecule


__all__.append("create_molecule_from_smiles")
