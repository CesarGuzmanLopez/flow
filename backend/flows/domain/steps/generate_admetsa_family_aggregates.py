"""
Generate ADMETSA for a family and compute family-level aggregates (step-agnostic).

Process:
- Ensure molecular-level ADMETSA exists for all family members (reusing existing service)
- Compute mean values per ADMETSA property and persist as FamilyProperty with
    method-scoped metadata to avoid collisions with other aggregates

Inputs:
- family_id: int
- method?: str  # override storage method label (default: "flows.family_aggregates")

Outputs:
- family_id: int
- aggregates: Dict[str, float]
- saved: int  # number of FamilyProperty records written/updated

Produces type: "chemistry.family.aggregates"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from chemistry import services as chem_services

from .interface import StepContext, StepHandler, StepResult, StepSpec, register_step


@dataclass
class GenerateAdmetsaFamilyAggregatesInput:
    family_id: int
    method: str | None = None


@dataclass
class GenerateAdmetsaFamilyAggregatesOutput:
    family_id: int
    aggregates: Dict[str, float]
    saved: int


class GenerateAdmetsaFamilyAggregatesStep(
    StepHandler[
        GenerateAdmetsaFamilyAggregatesInput, GenerateAdmetsaFamilyAggregatesOutput
    ]
):
    step_type = "generate_admetsa_family_aggregates"

    def execute(
        self, ctx: StepContext, inp: GenerateAdmetsaFamilyAggregatesInput
    ) -> StepResult:
        # Reuse existing service to ensure molecular properties are present
        chem_services.generate_admetsa_for_family(
            family_id=inp.family_id, created_by=ctx.user
        )

        method = inp.method or "flows.family_aggregates"
        agg = chem_services.compute_family_admetsa_aggregates(
            family_id=inp.family_id, method=method
        )

        typed_out = GenerateAdmetsaFamilyAggregatesOutput(
            family_id=agg["family_id"],
            aggregates=agg.get("aggregates", {}),
            saved=int(agg.get("count", 0)),
        )

        outputs = {
            "family_id": typed_out.family_id,
            "saved": typed_out.saved,
        }
        metadata: Dict[str, Any] = {
            "method": method,
            "properties": chem_services.ADMETSA_PROPERTIES,
            "scope": "family-aggregates",
        }
        return StepResult(outputs=outputs, metadata=metadata, value=typed_out)


register_step(
    GenerateAdmetsaFamilyAggregatesStep.step_type,
    GenerateAdmetsaFamilyAggregatesStep(),
    spec=StepSpec(
        step_type=GenerateAdmetsaFamilyAggregatesStep.step_type,
        input_cls=GenerateAdmetsaFamilyAggregatesInput,
        output_cls=GenerateAdmetsaFamilyAggregatesOutput,
        produces_type_name="chemistry.family.aggregates",
    ),
)


__all__ = [
    "GenerateAdmetsaFamilyAggregatesStep",
    "GenerateAdmetsaFamilyAggregatesInput",
    "GenerateAdmetsaFamilyAggregatesOutput",
]
