"""
Generate a new family by substituting selected positions of base molecule(s)
with substituent molecules, creating all permutations (step-agnostic).

Inputs (one of each source group required):
- name: str (name for the resulting family)
- base_family_id?: int | base_molecule_ids?: List[int]
- substituent_family_id?: int |
    substituent_molecule_ids?: List[int] |
    substituent_smiles_list?: List[str]
- positions?: List[int]  # defaults to [1]

Outputs:
- family_id: int
- family_name: str
- count: int  # number of molecules generated

Produces type: "chemistry.family"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from chemistry import services as chem_services

from .interface import StepContext, StepHandler, StepResult, StepSpec, register_step


@dataclass
class GenerateSubstitutionFamilyInput:
    name: str
    base_family_id: Optional[int] = None
    base_molecule_ids: Optional[List[int]] = None
    substituent_family_id: Optional[int] = None
    substituent_molecule_ids: Optional[List[int]] = None
    substituent_smiles_list: Optional[List[str]] = None
    positions: Optional[List[int]] = None


@dataclass
class GenerateSubstitutionFamilyOutput:
    family_id: int
    family_name: str
    count: int


class GenerateSubstitutionFamilyStep(
    StepHandler[GenerateSubstitutionFamilyInput, GenerateSubstitutionFamilyOutput]
):
    step_type = "generate_substitution_family"

    def execute(
        self, ctx: StepContext, inp: GenerateSubstitutionFamilyInput
    ) -> StepResult:
        # Basic validation of mutually-required groups
        if not inp.name:
            raise ValueError("name is required")

        has_base = bool(inp.base_family_id is not None or inp.base_molecule_ids)
        has_subs = bool(
            (inp.substituent_family_id is not None)
            or (inp.substituent_molecule_ids)
            or (inp.substituent_smiles_list)
        )
        if not has_base:
            raise ValueError(
                "Provide base_family_id or base_molecule_ids for base molecules"
            )
        if not has_subs:
            raise ValueError(
                "Provide substituents: substituent_family_id or "
                "substituent_molecule_ids or substituent_smiles_list"
            )

        summary = chem_services.generate_substituted_family(
            name=inp.name,
            created_by=ctx.user,
            base_family_id=inp.base_family_id,
            base_molecule_ids=inp.base_molecule_ids or None,
            substituent_family_id=inp.substituent_family_id,
            substituent_molecule_ids=inp.substituent_molecule_ids or None,
            substituent_smiles_list=inp.substituent_smiles_list or None,
            positions=inp.positions or None,
        )

        typed_out = GenerateSubstitutionFamilyOutput(
            family_id=summary["family_id"],
            family_name=str(summary.get("family_name", "")),
            count=int(summary.get("count", 0)),
        )
        outputs = {
            "family_id": typed_out.family_id,
            "family_name": typed_out.family_name,
            "count": typed_out.count,
        }
        metadata: Dict[str, Any] = {
            "positions": summary.get("positions", []),
            "created_by": getattr(ctx.user, "id", None),
            "source": "substitution-permutations",
        }
        return StepResult(outputs=outputs, metadata=metadata, value=typed_out)


register_step(
    GenerateSubstitutionFamilyStep.step_type,
    GenerateSubstitutionFamilyStep(),
    spec=StepSpec(
        step_type=GenerateSubstitutionFamilyStep.step_type,
        input_cls=GenerateSubstitutionFamilyInput,
        output_cls=GenerateSubstitutionFamilyOutput,
        produces_type_name="chemistry.family",
    ),
)


__all__ = [
    "GenerateSubstitutionFamilyStep",
    "GenerateSubstitutionFamilyInput",
    "GenerateSubstitutionFamilyOutput",
]
