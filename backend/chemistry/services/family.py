"""
Servicios de dominio para gestión de familias de moléculas.

Este módulo encapsula la lógica de negocio para crear y administrar familias,
que son agregados de moléculas relacionadas. Útil para flujos de screening,
generación combinatoria y análisis grupal de propiedades.

Reglas de negocio implementadas:
- Familia = grupo inmutable de moléculas con hash determinista (basado en SMILES canónicos ordenados).
- Deduplicación automática: moléculas repetidas (por InChIKey/SMILES) se agregan una sola vez.
- Validación transaccional: creación atómica de familia + moléculas + membresías.
- Auditoría: todas las familias llevan created_by y metadata con tamaño/contexto.

Objetivos:
- Crear familias desde listas de SMILES (para importar/migrar datos).
- Soportar generación combinatoria (sustituciones) para expansión de librerías.
- Facilitar agregación de propiedades a nivel de familia (ej. media de LogP).
- Integración con flujos: metadata puede incluir "flow_id" para contexto.

Resumen en inglés:
Domain services for managing molecular families (aggregates of molecules).
"""

# mypy: disable-error-code="attr-defined"

import hashlib
import logging
from typing import Any, Dict, Iterable, List, Optional, Sequence

from django.core.exceptions import ValidationError
from django.db import transaction

from .. import providers as providers
from ..models import Family, FamilyMember, Molecule
from .molecule import create_molecule_from_smiles

logger = logging.getLogger(__name__)


def _family_hash(smiles_list: Iterable[str]) -> str:
    """Calcula hash determinista de familia (SMILES ordenados y normalizados).

    Helper interno para garantizar que familias con mismo conjunto de moléculas
    tengan el mismo hash (útil para deduplicación o comparación).
    """
    norm = ",".join(sorted(s.strip() for s in smiles_list if s and s.strip()))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def create_family_from_smiles(
    *,
    name: str,
    smiles_list: List[str],
    created_by: Any,
    provenance: str = "user",
    frozen: bool | None = None,
    metadata: Dict[str, Any] | None = None,  # compatibility alias for tests
) -> Family:
    """Crea una familia a partir de una lista de SMILES, con deduplicación automática.

    Servicio transaccional que:
    1. Normaliza y crea/busca cada molécula por InChIKey (idempotente)
    2. Deduplica moléculas repetidas dentro de la familia
    3. Crea la familia con hash determinista y marca como frozen (inmutable si True)
    4. Crea membresías (FamilyMember) en bulk

    Usado desde:
    - API REST (views/families.py endpoint from_smiles)
    - Scripts de importación/migración
    - Servicios de generación combinatoria

    Args:
        name: Nombre de la familia (requerido, no vacío)
        smiles_list: Lista de SMILES (al menos uno válido)
        created_by: Usuario que crea la familia (requerido)
        provenance: Origen de la familia (ej. "user", "import", "substitutions")

    Returns:
        Instancia de Family con membresías creadas

    Raises:
        ValidationError: Si nombre vacío, lista vacía, o SMILES inválidos
        ValueError: Si created_by es None o ninguna molécula válida tras normalización

    Examples:
        >>> # Crear familia con 3 moléculas
        >>> fam = create_family_from_smiles(
        ...     name="Test Family",
        ...     smiles_list=["CCO", "CCN", "CCC"],
        ...     created_by=user,
        ...     provenance="user"
        ... )
        >>> print(fam.metadata["size"])
        3

        >>> # Con duplicados (deduplica automáticamente)
        >>> fam = create_family_from_smiles(
        ...     name="Dedup Test",
        ...     smiles_list=["CCO", "CCO", "CCN"],
        ...     created_by=user
        ... )
        >>> print(fam.metadata["size"])  # Solo 2
        2
    """
    if not name or not name.strip():
        raise ValidationError("Family name cannot be empty")

    if not smiles_list:
        raise ValidationError("SMILES list cannot be empty")

    if not created_by:
        raise ValueError("created_by is required")

    with transaction.atomic():
        mols: List[Molecule] = []
        seen: set[str] = set()
        for smi in smiles_list:
            if not smi or not smi.strip():
                continue
            mol = create_molecule_from_smiles(smiles=smi, created_by=created_by)
            key = mol.inchikey or mol.smiles
            if key in seen:
                continue
            seen.add(key)
            mols.append(mol)

        if not mols:
            raise ValueError("No valid molecules could be created from SMILES list")

        fam_hash = _family_hash([m.canonical_smiles or m.smiles for m in mols])

        # Merge metadata with defaults
        meta: Dict[str, Any] = {
            "size": len(mols),
            "created_by": getattr(created_by, "id", None),
        }
        if metadata:
            meta.update(metadata)

        # Deduplicate by family_hash regardless of name order/content
        fam, created = Family.objects.get_or_create(
            family_hash=fam_hash,
            defaults={
                "name": name.strip(),
                "description": "",
                "provenance": provenance,
                # If explicit value provided use it, default to True for backward compatibility
                "frozen": True if frozen is None else bool(frozen),
                "created_by": created_by,
                "metadata": meta,
            },
        )
        FamilyMember.objects.bulk_create(
            [FamilyMember(family=fam, molecule=m) for m in mols], ignore_conflicts=True
        )
        logger.info(f"Created family '{name}' with {len(mols)} molecules")
        return fam


def create_single_molecule_family(
    *,
    name: str | None,
    molecule: Molecule,
    created_by: Any,
    provenance: str = "reference",
) -> Family:
    """Crea una familia con una sola molécula (wrapper conveniente).

    Helper para casos donde se quiere encapsular una molécula como familia,
    útil para flujos que operan siempre con familias o para referencia.

    Args:
        name: Nombre de la familia (opcional; usa nombre/fórmula de molécula si None)
        molecule: Instancia de Molecule a encapsular
        created_by: Usuario que crea la familia
        provenance: Origen (por defecto "reference")

    Returns:
        Instancia de Family con un solo miembro

    Examples:
        >>> mol = Molecule.objects.get(inchikey="IK_...")
        >>> fam = create_single_molecule_family(
        ...     name="Single Ref",
        ...     molecule=mol,
        ...     created_by=user
        ... )
        >>> print(fam.metadata["size"])
        1
    """
    smiles = molecule.canonical_smiles or molecule.smiles
    fam = Family.objects.create(
        name=name or molecule.name or molecule.molecular_formula or "",
        description="",
        family_hash=_family_hash([smiles]),
        provenance=provenance,
        frozen=True,
        created_by=created_by,
        metadata={"size": 1, "created_by": getattr(created_by, "id", None)},
    )
    FamilyMember.objects.get_or_create(family=fam, molecule=molecule)
    return fam


# --- Membership administration services -------------------------------------------------


class FamilyFrozenError(ValidationError):
    pass


def _ensure_family_not_frozen(family: Family) -> None:
    if getattr(family, "frozen", False):
        raise FamilyFrozenError("Family is frozen; cannot modify members")


def _resolve_member_spec(
    spec: Dict[str, Any],
    *,
    created_by: Any,
    allow_create: bool,
) -> Molecule:
    """Resolve a member specification to a Molecule instance.

    Supported keys in spec:
      - id: int
      - inchikey: str
      - smiles: str

    Rules:
      - If id is provided, fetch or raise DoesNotExist
      - If inchikey provided, try lookup by inchikey (case-insensitive).
        If not found and allow_create is True AND a 'smiles' is also provided,
        create from smiles; otherwise, raise ValidationError (no creation from
        inchikey alone to preserve chemical integrity).
      - If only smiles provided, create or get by computed InChIKey.
    """
    mol_id = spec.get("id")
    inchikey = (spec.get("inchikey") or "").strip() or None
    smiles = (spec.get("smiles") or "").strip() or None

    if mol_id:
        try:
            return Molecule.objects.get(id=int(mol_id))
        except (Molecule.DoesNotExist, ValueError):
            raise ValidationError(f"Molecule with id={mol_id} does not exist")

    if inchikey:
        try:
            return Molecule.objects.get(inchikey__iexact=inchikey)
        except Molecule.DoesNotExist:
            # creation from inchikey alone is not allowed
            if allow_create and smiles:
                # Validate that smiles maps to the same inchikey if possible
                try:
                    struct = providers.engine.smiles_to_inchi(
                        smiles, return_dataclass=True
                    )
                    if struct.inchikey and struct.inchikey != inchikey:
                        raise ValidationError(
                            "Provided inchikey does not match the one computed from smiles"
                        )
                except Exception:
                    # Defer to molecule service for detailed error
                    pass
                return create_molecule_from_smiles(smiles=smiles, created_by=created_by)
            raise ValidationError(
                "Cannot create molecule from inchikey alone; include 'smiles' or use an existing 'id'"
            )

    if smiles:
        return create_molecule_from_smiles(smiles=smiles, created_by=created_by)

    raise ValidationError("Member spec must include one of: id, inchikey, smiles")


def add_members_to_family(
    *,
    family_id: int,
    members: Sequence[Dict[str, Any]],
    created_by: Any,
) -> Dict[str, Any]:
    """Add one or more molecules as members of a family.

    - Resolves members by id/inchikey/smiles (creates molecules from smiles when needed)
    - Enforces frozen family rule
    - Ignores duplicate memberships

    Returns a summary dict: {added: int, skipped: int, member_ids: [..]}
    """
    if not created_by:
        raise ValueError("created_by is required")

    if not isinstance(members, (list, tuple)) or not members:
        raise ValidationError("'members' must be a non-empty list")

    with transaction.atomic():
        try:
            family = Family.objects.select_for_update().get(id=family_id)
        except Family.DoesNotExist:
            raise ValidationError(f"Family with id={family_id} does not exist")

        _ensure_family_not_frozen(family)

        added = 0
        skipped = 0
        member_ids: list[int] = []

        for spec in members:
            mol = _resolve_member_spec(
                spec or {}, created_by=created_by, allow_create=True
            )
            _, created = FamilyMember.objects.get_or_create(family=family, molecule=mol)
            if created:
                added += 1
                member_ids.append(mol.id)
            else:
                skipped += 1

        # Update family metadata size if present
        try:
            family.metadata = dict(family.metadata or {})
            family.metadata["size"] = family.members.count()
            family.save(update_fields=["metadata", "updated_at"])
        except Exception:
            pass

        return {
            "family_id": family.id,
            "added": added,
            "skipped": skipped,
            "member_ids": member_ids,
        }


def remove_members_from_family(
    *,
    family_id: int,
    members: Sequence[Dict[str, Any]],
    requested_by: Any,
) -> Dict[str, Any]:
    """Remove one or more molecules from a family.

    - Resolves members by id/inchikey/smiles (NO creation on remove)
    - Enforces frozen family rule
    - Ignores non-existent memberships

    Returns: {removed: int, attempted: int}
    """
    if not requested_by:
        raise ValueError("requested_by is required")

    if not isinstance(members, (list, tuple)) or not members:
        raise ValidationError("'members' must be a non-empty list")

    with transaction.atomic():
        try:
            family = Family.objects.select_for_update().get(id=family_id)
        except Family.DoesNotExist:
            raise ValidationError(f"Family with id={family_id} does not exist")

        _ensure_family_not_frozen(family)

        removed = 0
        attempted = 0

        for spec in members:
            attempted += 1
            # Resolve without creating: for smiles, compute inchikey and try lookup
            mol_id = spec.get("id") if isinstance(spec, dict) else None
            inchikey = (
                (spec.get("inchikey") or "").strip() if isinstance(spec, dict) else ""
            )
            smiles = (
                (spec.get("smiles") or "").strip() if isinstance(spec, dict) else ""
            )

            mol: Optional[Molecule] = None
            try:
                if mol_id:
                    mol = Molecule.objects.get(id=int(mol_id))
                elif inchikey:
                    mol = Molecule.objects.get(inchikey__iexact=inchikey)
                elif smiles:
                    try:
                        struct = providers.engine.smiles_to_inchi(
                            smiles, return_dataclass=True
                        )
                        if struct.inchikey:
                            mol = Molecule.objects.get(inchikey__iexact=struct.inchikey)
                    except Molecule.DoesNotExist:
                        mol = None
                    except Exception:
                        mol = None
            except (Molecule.DoesNotExist, ValueError):
                mol = None

            if not mol:
                continue

            deleted, _ = FamilyMember.objects.filter(
                family=family, molecule=mol
            ).delete()
            if deleted:
                removed += 1

        # Update family metadata size if present
        try:
            family.metadata = dict(family.metadata or {})
            family.metadata["size"] = family.members.count()
            family.save(update_fields=["metadata", "updated_at"])
        except Exception:
            pass

        return {"family_id": family.id, "removed": removed, "attempted": attempted}


def generate_substituted_family(
    *,
    name: str,
    created_by: Any,
    base_family_id: int | None = None,
    base_molecule_ids: List[int] | None = None,
    substituent_family_id: int | None = None,
    substituent_molecule_ids: List[int] | None = None,
    substituent_smiles_list: List[str] | None = None,
    positions: List[int] | None = None,
    provenance: str = "substitutions",
) -> Dict[str, Any]:
    if not name:
        raise ValueError("name is required")

    base_qs = Molecule.objects.none()
    if base_family_id is not None:
        base_qs = Molecule.objects.filter(families__family_id=base_family_id)
    if base_molecule_ids:
        base_qs = base_qs.union(Molecule.objects.filter(id__in=base_molecule_ids))
    base_list = list(base_qs.distinct())
    if not base_list:
        raise ValueError("No base molecules provided (family_id or molecule_ids)")

    subs_smiles: List[str] = []
    if substituent_family_id is not None:
        subs_smiles.extend(
            list(
                Molecule.objects.filter(
                    families__family_id=substituent_family_id
                ).values_list("smiles", flat=True)
            )
        )
    if substituent_molecule_ids:
        subs_smiles.extend(
            list(
                Molecule.objects.filter(id__in=substituent_molecule_ids).values_list(
                    "smiles", flat=True
                )
            )
        )
    if substituent_smiles_list:
        subs_smiles.extend(list(substituent_smiles_list))

    subs_smiles = [s for s in subs_smiles if s]
    if not subs_smiles:
        raise ValueError(
            "No substituents provided (family_id, molecule_ids, or smiles_list)"
        )

    pos_list = positions or [1]

    variant_smiles: List[str] = []
    for base in base_list:
        bsmiles = base.smiles or base.canonical_smiles or base.inchi or base.inchikey
        for pos in pos_list:
            for sub in subs_smiles:
                variant = f"{bsmiles}.{sub}"
                variant_smiles.append(variant)

    family = create_family_from_smiles(
        name=name,
        smiles_list=variant_smiles,
        created_by=created_by,
        provenance=provenance,
    )

    return {
        "family_id": family.id,
        "family_name": family.name,
        "count": len(variant_smiles),
        "positions": pos_list,
        "substitution_metadata": {
            "base_molecules": len(base_list),
            "substituents": len(subs_smiles),
            "total_variants": len(variant_smiles),
        },
    }


def rehydrate_family_properties(family: Family) -> Dict[str, Any]:
    from ..services import molecule as _molecule_svc

    family_props = {}
    for prop in family.properties.all():
        try:
            family_props[prop.property_type] = float(prop.value)
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid family property value for family {family.id}, property {prop.property_type}: {prop.value}"
            )
            continue

    member_properties = []
    for member in family.members.select_related("molecule").all():
        mol_props = _molecule_svc.rehydrate_molecule_properties(member.molecule)
        member_properties.append(
            {
                "molecule_id": member.molecule.id,
                "properties": mol_props,
            }
        )

    from .utils import _compute_property_statistics

    return {
        "family_id": family.id,
        "family_properties": family_props,
        "member_count": len(member_properties),
        "member_properties": member_properties,
        "aggregated_stats": _compute_property_statistics(member_properties),
    }
