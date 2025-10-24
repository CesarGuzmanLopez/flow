import logging
from typing import Any, Dict, List

from .. import providers as providers
from ..models import Family, FamilyMember, FamilyProperty, MolecularProperty
from ..types import MolecularProperties

logger = logging.getLogger(__name__)


ADMETSA_PROPERTIES = [
    "MolWt",
    "LogP",
    "TPSA",
    "HBA",
    "HBD",
    "RB",
]


def generate_admetsa_for_family(*, family_id: int, created_by: Any) -> Dict[str, Any]:
    fam = Family.objects.get(pk=family_id)
    members = FamilyMember.objects.select_related("molecule").filter(family=fam)
    results: List[Dict[str, Any]] = []

    for mem in members:
        m = mem.molecule
        smiles = m.canonical_smiles or m.smiles

        try:
            properties: MolecularProperties = providers.engine.calculate_properties(
                smiles, return_dataclass=True
            )

            props_dict = properties.to_dict()

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

            admetsa_props = {k: props_dict.get(k) for k in ADMETSA_PROPERTIES}
            results.append(
                {
                    "molecule_id": m.id,
                    "properties": admetsa_props,
                }
            )

        except Exception as e:
            logger.error(f"Failed to calculate properties for molecule {m.id}: {e}")
            results.append(
                {
                    "molecule_id": m.id,
                    "properties": {},
                    "error": str(e),
                }
            )

    return {"family_id": fam.id, "count": len(results), "molecules": results}


def generate_admetsa_properties_for_family(*, family_id: int) -> Dict[str, Any]:
    return generate_admetsa_for_family(family_id=family_id, created_by=None)


def compute_family_admetsa_aggregates(
    *,
    family_id: int,
    created_by: Any,
    method: str = "flows.family_aggregates",
    tag: str | None = "admetsa_family_aggregates",
) -> Dict[str, Any]:
    member_ids = list(
        FamilyMember.objects.filter(family_id=family_id).values_list(
            "molecule_id", flat=True
        )
    )
    if not member_ids:
        return {"family_id": family_id, "aggregates": {}, "count": 0}

    values: Dict[str, List[float]] = {k: [] for k in ADMETSA_PROPERTIES}
    for mp in MolecularProperty.objects.filter(molecule_id__in=member_ids):
        if mp.property_type in values:
            try:
                v = float(mp.value)
            except (TypeError, ValueError):
                continue
            values[mp.property_type].append(v)

    aggregates: Dict[str, float] = {}
    for k, lst in values.items():
        if lst:
            aggregates[k] = sum(lst) / float(len(lst))

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
