"""
Servicios de dominio para Chemistry (capa de aplicación - arquitectura hexagonal).

Define funciones para filtrar y validar acceso a entidades químicas por usuario.
Implementa la lógica de negocio separada de los adaptadores (views).
"""

import hashlib
from typing import Any, Dict, Iterable, List

from django.db.models import QuerySet

from .models import Family, FamilyMember, FamilyProperty, MolecularProperty, Molecule
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
    """
    mols: List[Molecule] = []
    seen: set[str] = set()
    for smi in smiles_list:
        mol = create_molecule_from_smiles(smiles=smi, created_by=created_by)
        key = mol.inchikey or mol.smiles
        if key in seen:
            continue
        seen.add(key)
        mols.append(mol)

    fam = Family.objects.create(
        name=name,
        description="",
        family_hash=_family_hash([m.canonical_smiles or m.smiles for m in mols]),
        provenance=provenance,
        frozen=True,
        metadata={"size": len(mols), "created_by": getattr(created_by, "id", None)},
    )
    # link members
    FamilyMember.objects.bulk_create(
        [FamilyMember(family=fam, molecule=m) for m in mols], ignore_conflicts=True
    )
    return fam


__all__.append("create_family_from_smiles")


ADMETSA_PROPERTIES = [
    "MolWt",
    "LogP",
    "TPSA",
    "HBA",
    "HBD",
    "RB",
]


def generate_admetsa_for_family(*, family_id: int, created_by: Any) -> Dict[str, Any]:
    """Compute ADMETSA properties per molecule in a family using the provider.

    Returns a dict summary: { family_id, count, molecules: [{id, props}...] }
    Also stores MolecularProperty rows for each value (non-invariant),
    method="rdkit" when CHEM_ENGINE=rdkit.
    """
    fam = Family.objects.get(pk=family_id)
    members = FamilyMember.objects.select_related("molecule").filter(family=fam)
    results: List[Dict[str, Any]] = []
    for mem in members:
        m = mem.molecule
        props = chem_engine.calculate_properties(m.canonical_smiles or m.smiles)
        # persist selected properties
        for k in ADMETSA_PROPERTIES:
            val = props.get(k)
            if val is None:
                continue
            MolecularProperty.objects.update_or_create(
                molecule=m,
                property_type=k,
                method="rdkit",
                defaults={
                    "value": str(val),
                    "is_invariant": False,
                    "units": "",
                    "relation": "",
                    "source_id": "provider:rdkit",
                    "metadata": {},
                },
            )
        results.append(
            {
                "molecule_id": m.id,
                "properties": {k: props.get(k) for k in ADMETSA_PROPERTIES},
            }
        )
    return {"family_id": fam.id, "count": len(results), "molecules": results}


__all__.extend(["ADMETSA_PROPERTIES", "generate_admetsa_for_family"])


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

    # Build variant smiles deterministically
    variant_smiles: List[str] = []
    for base in base_list:
        bsmiles = base.smiles or base.canonical_smiles or base.inchi or base.inchikey
        for p in pos_list:
            for sub in subs_smiles:
                variant_smiles.append(f"{bsmiles}-pos{int(p)}-{sub}")

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
    }


def compute_family_admetsa_aggregates(
    *,
    family_id: int,
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
            },
        )
        saved += 1

    return {"family_id": family_id, "aggregates": aggregates, "count": saved}


__all__.extend(
    [
        "generate_substituted_family",
        "compute_family_admetsa_aggregates",
    ]
)
