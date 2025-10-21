"""
Create Reference Family step.

Params contract:
- mode: "existing" | "new"
  - if existing: { mode: "existing", family_id: int }
  - if new: { mode: "new", name: str, smiles_list: list[str] }

Outputs:
- { family_id, family_name }

Metadata stored:
- { created_by: user.id, mode, family_id }
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from chemistry import services as chem_services
from chemistry.models import Family

from .interface import StepContext, StepHandler, StepResult, StepSpec, register_step


@dataclass
class CreateReferenceFamilyInput:
    mode: str  # "existing" | "new"
    family_id: Optional[int] = None
    name: Optional[str] = None
    smiles_list: Optional[List[str]] = None


@dataclass
class CreateReferenceFamilyOutput:
    family_id: int
    family_name: str


class CreateReferenceFamilyStep(
    StepHandler[CreateReferenceFamilyInput, CreateReferenceFamilyOutput]
):
    step_type = "create_reference_family"

    def execute(
        self, ctx: StepContext, params: CreateReferenceFamilyInput
    ) -> StepResult:
        mode = (params.mode or "").lower()
        if mode not in {"existing", "new"}:
            raise ValueError("mode must be 'existing' or 'new'")

        if mode == "existing":
            fid = params.family_id
            if not fid:
                raise ValueError("family_id is required when mode='existing'")
            family = Family.objects.get(pk=fid)
        else:
            name = params.name
            smiles_list = params.smiles_list or []
            if not name or not smiles_list:
                raise ValueError("name and smiles_list are required when mode='new'")
            family = chem_services.create_family_from_smiles(
                name=name, smiles_list=smiles_list, created_by=ctx.user
            )

        metadata: Dict[str, Any] = {
            "created_by": getattr(ctx.user, "id", None),
            "mode": mode,
            "family_id": family.id,
        }
        outputs = {"family_id": family.id, "family_name": family.name}
        typed_out = CreateReferenceFamilyOutput(
            family_id=family.id, family_name=family.name
        )
        return StepResult(outputs=outputs, metadata=metadata, value=typed_out)


# Register on import
register_step(
    CreateReferenceFamilyStep.step_type,
    CreateReferenceFamilyStep(),
    spec=StepSpec(
        step_type=CreateReferenceFamilyStep.step_type,
        input_cls=CreateReferenceFamilyInput,
        output_cls=CreateReferenceFamilyOutput,
        produces_type_name="chemistry.family",
    ),
)

__all__ = [
    "CreateReferenceFamilyStep",
    "CreateReferenceFamilyInput",
    "CreateReferenceFamilyOutput",
]
