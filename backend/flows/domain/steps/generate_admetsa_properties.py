"""
Step 2: Generate ADMETSA properties for a molecule family.

Input:
- family_id: int

Output (summary):
- family_id: int
- count: int  # number of molecules
- molecules: List[{ molecule_id: int, properties: Dict[str, float] }]

Produces type: "chemistry.admetsa_set"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from chemistry import services as chem_services

from .interface import StepContext, StepHandler, StepResult, StepSpec, register_step


@dataclass
class GenerateAdmetsaInput:
    family_id: int


@dataclass
class GenerateAdmetsaMolecule:
    molecule_id: int
    properties: Dict[str, float]


@dataclass
class GenerateAdmetsaOutput:
    family_id: int
    count: int
    molecules: List[GenerateAdmetsaMolecule]


class GenerateAdmetsaStep(StepHandler[GenerateAdmetsaInput, GenerateAdmetsaOutput]):
    step_type = "generate_admetsa"

    def execute(self, ctx: StepContext, inp: GenerateAdmetsaInput) -> StepResult:
        summary = chem_services.generate_admetsa_for_family(
            family_id=inp.family_id, created_by=ctx.user
        )

        mols = [
            GenerateAdmetsaMolecule(
                molecule_id=m["molecule_id"], properties=m["properties"]
            )
            for m in summary["molecules"]
        ]
        typed_out = GenerateAdmetsaOutput(
            family_id=summary["family_id"], count=summary["count"], molecules=mols
        )
        outputs = {
            "family_id": typed_out.family_id,
            "count": typed_out.count,
        }
        metadata: Dict[str, Any] = {"properties": chem_services.ADMETSA_PROPERTIES}
        return StepResult(outputs=outputs, metadata=metadata, value=typed_out)


register_step(
    GenerateAdmetsaStep.step_type,
    GenerateAdmetsaStep(),
    spec=StepSpec(
        step_type=GenerateAdmetsaStep.step_type,
        input_cls=GenerateAdmetsaInput,
        output_cls=GenerateAdmetsaOutput,
        produces_type_name="chemistry.admetsa_set",
    ),
)


__all__ = [
    "GenerateAdmetsaStep",
    "GenerateAdmetsaInput",
    "GenerateAdmetsaOutput",
]
