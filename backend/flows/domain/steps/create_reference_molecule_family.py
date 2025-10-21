"""
Step 3: Create a reference family from a single molecule provided by the user.

Input:
- mode: "from_smiles" | "from_molecule_id"
- name?: str  # optional family name
- smiles?: str  # when mode=from_smiles
- molecule_id?: int  # when mode=from_molecule_id

Output:
- family_id: int
- family_name: str

Produces type: "chemistry.family" (reusable with other flows)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from chemistry import services as chem_services
from chemistry.models import Molecule

from .interface import StepContext, StepHandler, StepResult, StepSpec, register_step


@dataclass
class CreateReferenceMoleculeFamilyInput:
    mode: str  # "from_smiles" | "from_molecule_id"
    name: Optional[str] = None
    smiles: Optional[str] = None
    molecule_id: Optional[int] = None


@dataclass
class CreateReferenceMoleculeFamilyOutput:
    family_id: int
    family_name: str


class CreateReferenceMoleculeFamilyStep(
    StepHandler[CreateReferenceMoleculeFamilyInput, CreateReferenceMoleculeFamilyOutput]
):
    step_type = "create_reference_molecule_family"

    def execute(
        self, ctx: StepContext, inp: CreateReferenceMoleculeFamilyInput
    ) -> StepResult:
        mode = (inp.mode or "").lower()
        if mode not in {"from_smiles", "from_molecule_id"}:
            raise ValueError("mode must be 'from_smiles' or 'from_molecule_id'")

        # Ensure we have a Molecule instance
        if mode == "from_smiles":
            if not inp.smiles:
                raise ValueError("smiles is required when mode='from_smiles'")
            mol = chem_services.create_molecule_from_smiles(
                smiles=inp.smiles, created_by=ctx.user
            )
        else:
            if not inp.molecule_id:
                raise ValueError("molecule_id is required when mode='from_molecule_id'")
            mol = Molecule.objects.get(pk=inp.molecule_id)

        fam = chem_services.create_single_molecule_family(
            name=inp.name, molecule=mol, created_by=ctx.user
        )

        metadata: Dict[str, Any] = {
            "created_by": getattr(ctx.user, "id", None),
            "mode": mode,
            "molecule_id": mol.id,
            "family_id": fam.id,
        }
        outputs = {"family_id": fam.id, "family_name": fam.name}
        typed_out = CreateReferenceMoleculeFamilyOutput(
            family_id=fam.id, family_name=fam.name
        )
        return StepResult(outputs=outputs, metadata=metadata, value=typed_out)


register_step(
    CreateReferenceMoleculeFamilyStep.step_type,
    CreateReferenceMoleculeFamilyStep(),
    spec=StepSpec(
        step_type=CreateReferenceMoleculeFamilyStep.step_type,
        input_cls=CreateReferenceMoleculeFamilyInput,
        output_cls=CreateReferenceMoleculeFamilyOutput,
        produces_type_name="chemistry.family",
    ),
)


__all__ = [
    "CreateReferenceMoleculeFamilyStep",
    "CreateReferenceMoleculeFamilyInput",
    "CreateReferenceMoleculeFamilyOutput",
]
