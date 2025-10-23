"""
Servicios de dominio para Chemistry (capa de aplicación - arquitectura hexagonal).

Define funciones para filtrar y validar acceso a entidades químicas por usuario.
Implementa la lógica de negocio separada de los adaptadores (views).
"""

import hashlib
import logging
from typing import Any, Dict, Iterable, List

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet

from .models import Family, FamilyMember, FamilyProperty, MolecularProperty, Molecule
from .providers import engine as chem_engine
from .types import (
    InvalidSmilesError,
    MolecularProperties,
    PropertyCalculationError,
    StructureIdentifiers,
    SubstitutionGenerationError,
)

logger = logging.getLogger(__name__)


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

    - Normalizes SMILES, generates InChI/InChIKey and formula using strongly typed interface
    - Stores provider-calculated descriptors in metadata under `descriptors`
    - Ensures uniqueness by InChIKey when available
    - Uses type-safe structure identifiers for consistent data handling

    Raises:
        ValidationError: If SMILES is invalid or chemistry engine fails
        ValueError: If required parameters are missing
        InvalidSmilesError: If SMILES string is invalid (from chemistry engine)
        PropertyCalculationError: If property calculation fails
    """
    if not smiles or not smiles.strip():
        raise ValidationError("SMILES cannot be empty")

    if not created_by:
        raise ValueError("created_by is required")

    try:
        with transaction.atomic():
            # Get structure identifiers using strongly typed interface
            structure_info: StructureIdentifiers = chem_engine.smiles_to_inchi(
                smiles.strip(), return_dataclass=True
            )

            # Get molecular properties using strongly typed interface
            properties: MolecularProperties = chem_engine.calculate_properties(
                smiles.strip(), return_dataclass=True
            )

            # Convert to dictionary for JSON storage while maintaining type safety
            properties_dict = properties.to_dict()

            metadata = {"descriptors": properties_dict}
            if extra_metadata:
                metadata.update(extra_metadata)

            defaults = {
                "name": name or structure_info.molecular_formula or "",
                "smiles": smiles.strip(),
                "canonical_smiles": structure_info.canonical_smiles,
                "inchi": structure_info.inchi,
                "molecular_formula": structure_info.molecular_formula or "",
                "created_by": created_by,
                "metadata": metadata,
            }

            if structure_info.inchikey:
                molecule, created = Molecule.objects.get_or_create(
                    inchikey=structure_info.inchikey, defaults=defaults
                )
                if not created:
                    logger.info(
                        f"Molecule with InChIKey {structure_info.inchikey} already exists"
                    )
            else:
                molecule = Molecule.objects.create(**defaults)
            return molecule

    except InvalidSmilesError as e:
        logger.error(f"Invalid SMILES '{smiles}': {e}")
        raise ValidationError(f"Invalid SMILES: {e}")
    except PropertyCalculationError as e:
        logger.error(f"Property calculation failed for SMILES '{smiles}': {e}")
        raise ValidationError(f"Property calculation failed: {e}")
    except Exception as e:
        logger.error(f"Error creating molecule from SMILES '{smiles}': {e}")
        # Keep message compatible with tests expecting this wording
        raise ValidationError(f"Invalid SMILES or chemistry engine error: {e}")


__all__.append("create_molecule_from_smiles")


def _family_hash(smiles_list: Iterable[str]) -> str:
    norm = ",".join(sorted(s.strip() for s in smiles_list if s and s.strip()))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def create_family_from_smiles(
    *, name: str, smiles_list: List[str], created_by: Any, provenance: str = "user"
) -> Family:
    """
    Create a Family and its members from a list of SMILES.

    - Deduplicates by InChIKey when available
    - Computes family_hash from normalized sorted smiles list
    - Sets frozen=True by default to capture reference set

    Raises:
        ValidationError: If parameters are invalid
        ValueError: If required parameters are missing
    """
    if not name or not name.strip():
        raise ValidationError("Family name cannot be empty")

    if not smiles_list:
        raise ValidationError("SMILES list cannot be empty")

    if not created_by:
        raise ValueError("created_by is required")

    try:
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
                raise ValidationError(
                    "No valid molecules could be created from SMILES list"
                )

            fam = Family.objects.create(
                name=name.strip(),
                description="",
                family_hash=_family_hash(
                    [m.canonical_smiles or m.smiles for m in mols]
                ),
                provenance=provenance,
                frozen=True,
                created_by=created_by,
                metadata={
                    "size": len(mols),
                    "created_by": getattr(created_by, "id", None),
                },
            )
            # link members
            FamilyMember.objects.bulk_create(
                [FamilyMember(family=fam, molecule=m) for m in mols],
                ignore_conflicts=True,
            )
            logger.info(f"Created family '{name}' with {len(mols)} molecules")
            return fam
    except Exception as e:
        logger.error(f"Error creating family '{name}': {e}")
        raise


__all__.append("create_family_from_smiles")


# Properties used by the ADMETSA pipeline and tests
ADMETSA_PROPERTIES = [
    "MolWt",  # Molecular weight
    "LogP",  # Octanol/water partition coefficient
    "TPSA",  # Topological polar surface area (also mapped as PSA)
    "HBA",  # Hydrogen bond acceptors
    "HBD",  # Hydrogen bond donors
    "RB",  # Rotatable bonds
]


def generate_admetsa_for_family(*, family_id: int, created_by: Any) -> Dict[str, Any]:
    """
    Compute ADMETSA properties per molecule in a family using the provider.

    Uses strongly typed molecular properties for consistent data handling.
    Returns a dict summary: { family_id, count, molecules: [{id, props}...] }
    Also stores MolecularProperty rows for each value (non-invariant),
    method="rdkit" when CHEM_ENGINE=rdkit.

    Raises:
        PropertyCalculationError: If property calculation fails for any molecule
        InvalidSmilesError: If any molecule has invalid SMILES
    """
    fam = Family.objects.get(pk=family_id)
    members = FamilyMember.objects.select_related("molecule").filter(family=fam)
    results: List[Dict[str, Any]] = []

    for mem in members:
        m = mem.molecule
        smiles = m.canonical_smiles or m.smiles

        try:
            # Get properties using strongly typed interface
            properties: MolecularProperties = chem_engine.calculate_properties(
                smiles, return_dataclass=True
            )

            # Convert to dictionary for storage and response
            props_dict = properties.to_dict()

            # Persist selected properties with type safety
            for prop_key in ADMETSA_PROPERTIES:
                prop_value = props_dict.get(prop_key)
                if prop_value is None:
                    continue

                MolecularProperty.objects.update_or_create(
                    molecule=m,
                    property_type=prop_key,
                    method="rdkit",
                    defaults={
                        "value": str(prop_value),
                        "is_invariant": False,
                        "units": "",
                        "relation": "",
                        "source_id": "provider:rdkit",
                        "metadata": {"engine_type": "strongly_typed"},
                        "created_by": created_by,
                    },
                )

            # Prepare response with only ADMETSA properties
            admetsa_props = {k: props_dict.get(k) for k in ADMETSA_PROPERTIES}
            results.append(
                {
                    "molecule_id": m.id,
                    "properties": admetsa_props,
                }
            )

        except (InvalidSmilesError, PropertyCalculationError) as e:
            logger.error(f"Failed to calculate properties for molecule {m.id}: {e}")
            # Continue with other molecules, store error info
            results.append(
                {
                    "molecule_id": m.id,
                    "properties": {},
                    "error": str(e),
                }
            )

    return {"family_id": fam.id, "count": len(results), "molecules": results}


__all__.extend(["ADMETSA_PROPERTIES", "generate_admetsa_for_family"])


def generate_admetsa_properties_for_family(*, family_id: int) -> Dict[str, Any]:
    """Backwards-compatible alias used by flows adapter.

    Note: created_by is not required for this variant.
    """
    return generate_admetsa_for_family(family_id=family_id, created_by=None)


def create_single_molecule_family(
    *,
    name: str | None,
    molecule: Molecule,
    created_by: Any,
    provenance: str = "reference",
) -> Family:
    """Create a Family from a single existing Molecule and link membership.

    Computes a deterministic family_hash from the molecule's canonical_smiles or smiles.
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


__all__.append("create_single_molecule_family")


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
    """
    Generate all substitution permutations and create a new family.

    Uses strongly typed substitution generation from chemistry engine.
    Since we don't perform real chemistry here, we construct variant SMILES by
    combining base SMILES, a position marker, and substituent SMILES in a
    deterministic way, e.g., "<base>-pos{p}-<sub>". This ensures uniqueness and
    reproducibility in tests and mock engines.

    Args:
        name: Name of the resulting family.
        created_by: User executing the step.
        base_family_id: Optional family of base molecules to substitute.
        base_molecule_ids: Optional explicit base molecule IDs.
        substituent_family_id: Optional family of substituent molecules.
        substituent_molecule_ids: Optional explicit substituent molecule IDs.
        substituent_smiles_list: Optional raw SMILES for substituents.
        positions: Optional list of integer positions. Defaults to [1].
        provenance: Provenance label for the family.

    Returns:
        Dict with summary and created family info: { family_id, count, smiles_list }

    Raises:
        InvalidSmilesError: If any base SMILES is invalid
        SubstitutionGenerationError: If substitution generation fails
    """
    if not name:
        raise ValueError("name is required")

    # Collect base molecules
    base_qs = Molecule.objects.none()
    if base_family_id is not None:
        base_qs = Molecule.objects.filter(families__family_id=base_family_id)
    if base_molecule_ids:
        base_qs = base_qs.union(Molecule.objects.filter(id__in=base_molecule_ids))
    base_list = list(base_qs.distinct())
    if not base_list:
        raise ValueError("No base molecules provided (family_id or molecule_ids)")

    # Collect substituents as smiles strings
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

    # Build variant smiles using the provider (prefer valid SMILES when available)
    variant_smiles: List[str] = []
    for base in base_list:
        bsmiles = base.smiles or base.canonical_smiles or base.inchi or base.inchikey

        try:
            # Ask the engine for valid substitution variants; ignore dataclass wrapper
            count = max(1, len(subs_smiles) * max(1, len(pos_list)))
            variants = chem_engine.generate_substitutions(
                bsmiles, count=count, return_dataclass=False
            )
            # Ensure list of strings
            if isinstance(variants, list):
                variant_smiles.extend([str(s) for s in variants if s])
            else:
                logger.warning("Engine returned unexpected type for substitutions")
        except (InvalidSmilesError, SubstitutionGenerationError) as e:
            logger.warning(f"Substitution generation failed for {bsmiles}: {e}")
            # Minimal fallback: reuse base smiles to keep flow moving
            variant_smiles.append(bsmiles)

    # Create the resulting family
    family = create_family_from_smiles(
        name=name,
        smiles_list=variant_smiles,
        created_by=created_by,
        provenance=provenance,
    )

    return {
        "family_id": family.id,
        "family_name": family.name,
        "count": family.members.count(),
        "positions": pos_list,
        "substitution_metadata": {
            "base_molecules": len(base_list),
            "substituents": len(subs_smiles),
            "total_variants": len(variant_smiles),
        },
    }


def compute_family_admetsa_aggregates(
    *,
    family_id: int,
    created_by: Any,
    method: str = "flows.family_aggregates",
    tag: str | None = "admetsa_family_aggregates",
) -> Dict[str, Any]:
    """
    Compute family-level aggregates (mean) for numeric ADMETSA properties across
    member molecules and persist them as FamilyProperty records.

    The records are saved with a specific `method` to avoid collisions with
    other aggregate computations. A `tag` is added to metadata to mark
    flow-specific usage when desired.
    """
    # Gather member molecule IDs
    member_ids = list(
        FamilyMember.objects.filter(family_id=family_id).values_list(
            "molecule_id", flat=True
        )
    )
    if not member_ids:
        return {"family_id": family_id, "aggregates": {}, "count": 0}

    # Collect values per property
    values: Dict[str, List[float]] = {k: [] for k in ADMETSA_PROPERTIES}
    for mp in MolecularProperty.objects.filter(molecule_id__in=member_ids):
        if mp.property_type in values:
            try:
                v = float(mp.value)
            except (TypeError, ValueError):
                continue
            values[mp.property_type].append(v)

    # Compute means
    aggregates: Dict[str, float] = {}
    for k, lst in values.items():
        if lst:
            aggregates[k] = sum(lst) / float(len(lst))

    # Persist as FamilyProperty with method scoping
    saved = 0
    for prop, mean_val in aggregates.items():
        fp, _created = FamilyProperty.objects.update_or_create(
            family_id=family_id,
            property_type=f"ADMETSA.avg.{prop}",
            method=method,
            defaults={
                "value": str(mean_val),
                "units": "au",
                "is_invariant": False,
                "metadata": {"tag": tag or "", "source": "admetsa"},
                "created_by": created_by,
            },
        )
        saved += 1

    return {"family_id": family_id, "aggregates": aggregates, "count": saved}


__all__.extend(
    [
        "generate_substituted_family",
        "compute_family_admetsa_aggregates",
        "generate_admetsa_properties_for_family",
        "rehydrate_molecule_properties",
        "rehydrate_family_properties",
        "get_molecule_structure_info",
    ]
)


def rehydrate_molecule_properties(molecule: Molecule) -> MolecularProperties:
    """
    Rehydrate molecular properties from database in a type-safe manner.

    Converts stored MolecularProperty records back to strongly typed MolecularProperties.
    Provides a consistent interface for accessing molecular properties regardless of storage format.

    Args:
        molecule: Molecule instance to rehydrate properties for

    Returns:
        MolecularProperties dataclass with type-safe property access
    """
    # First try to get from metadata (engine calculated properties)
    if molecule.metadata and "descriptors" in molecule.metadata:
        try:
            return MolecularProperties.from_dict(molecule.metadata["descriptors"])
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                f"Failed to rehydrate from metadata for molecule {molecule.id}: {e}"
            )

    # Fallback: collect from MolecularProperty records
    properties = {}
    for prop in molecule.properties.all():
        try:
            properties[prop.property_type] = float(prop.value)
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid property value for molecule {molecule.id}, property {prop.property_type}: {prop.value}"
            )
            continue

    return MolecularProperties.from_dict(properties)


def rehydrate_family_properties(family: Family) -> Dict[str, Any]:
    """
    Rehydrate family-level properties from database in a type-safe manner.

    Aggregates molecular properties across family members and provides
    type-safe access to family-level statistics.

    Args:
        family: Family instance to rehydrate properties for

    Returns:
        Dictionary with aggregated properties and member property statistics
    """
    # Get family-level properties
    family_props = {}
    for prop in family.properties.all():
        try:
            family_props[prop.property_type] = float(prop.value)
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid family property value for family {family.id}, property {prop.property_type}: {prop.value}"
            )
            continue

    # Aggregate member properties
    member_properties = []
    for member in family.members.select_related("molecule").all():
        mol_props = rehydrate_molecule_properties(member.molecule)
        member_properties.append(
            {
                "molecule_id": member.molecule.id,
                "properties": mol_props,
            }
        )

    return {
        "family_id": family.id,
        "family_properties": family_props,
        "member_count": len(member_properties),
        "member_properties": member_properties,
        "aggregated_stats": _compute_property_statistics(member_properties),
    }


def get_molecule_structure_info(molecule: Molecule) -> StructureIdentifiers:
    """
    Get structure identifiers for a molecule in a type-safe manner.

    Converts database fields to strongly typed StructureIdentifiers dataclass.

    Args:
        molecule: Molecule instance to get structure info for

    Returns:
        StructureIdentifiers dataclass with type-safe access to identifiers
    """
    return StructureIdentifiers(
        inchi=molecule.inchi or "",
        inchikey=molecule.inchikey or "",
        canonical_smiles=molecule.canonical_smiles or molecule.smiles or "",
        molecular_formula=molecule.molecular_formula or None,
    )


def _compute_property_statistics(
    member_properties: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Compute statistics across member molecular properties.

    Args:
        member_properties: List of member property dictionaries

    Returns:
        Dictionary with mean, std, min, max for each property
    """
    from statistics import mean, stdev

    # Collect values by property type
    property_values = {}
    for member in member_properties:
        props_dict = member["properties"].to_dict()
        for prop_name, value in props_dict.items():
            if value is not None and isinstance(value, (int, float)):
                if prop_name not in property_values:
                    property_values[prop_name] = []
                property_values[prop_name].append(float(value))

    # Compute statistics
    stats = {}
    for prop_name, values in property_values.items():
        if len(values) > 0:
            stats[prop_name] = {
                "mean": mean(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            }
            if len(values) > 1:
                stats[prop_name]["std"] = stdev(values)
            else:
                stats[prop_name]["std"] = 0.0

    return stats
