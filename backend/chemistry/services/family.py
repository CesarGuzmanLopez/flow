import hashlib
import logging
from typing import Any, Dict, Iterable, List

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Family, FamilyMember, Molecule
from .molecule import create_molecule_from_smiles

logger = logging.getLogger(__name__)


def _family_hash(smiles_list: Iterable[str]) -> str:
    norm = ",".join(sorted(s.strip() for s in smiles_list if s and s.strip()))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def create_family_from_smiles(
    *, name: str, smiles_list: List[str], created_by: Any, provenance: str = "user"
) -> Family:
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

        fam = Family.objects.create(
            name=name.strip(),
            description="",
            family_hash=_family_hash([m.canonical_smiles or m.smiles for m in mols]),
            provenance=provenance,
            frozen=True,
            created_by=created_by,
            metadata={"size": len(mols), "created_by": getattr(created_by, "id", None)},
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
