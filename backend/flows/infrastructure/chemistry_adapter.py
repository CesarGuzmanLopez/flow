"""
Adaptador de Chemistry para ser usado como puerto en flows.

Implementa IChemistryPort delegando a chemistry.services.
"""

from typing import Any, Dict, List

from chemistry import services as chem_services

from flows.application.ports import IChemistryPort


class ChemistryAdapter(IChemistryPort):
    """Adaptador que expone chemistry como puerto para flows."""

    def create_family_from_smiles(
        self, name: str, smiles_list: List[str], created_by: Any
    ) -> Any:
        return chem_services.create_family_from_smiles(
            name=name, smiles_list=smiles_list, created_by=created_by
        )

    def get_family(self, family_id: int) -> Any:
        from chemistry.models import Family

        return Family.objects.get(pk=family_id)

    def generate_admetsa_properties(
        self, family_id: int, created_by: Any
    ) -> Dict[str, Any]:
        """Generate ADMETSA properties for a family.

        Args:
            family_id: ID of the family
            created_by: User who triggered the generation

        Returns:
            Dictionary with generation results
        """
        return chem_services.generate_admetsa_properties_for_family(
            family_id=family_id, created_by=created_by
        )

    def create_molecule_from_smiles(self, smiles: str, created_by: Any) -> Any:
        return chem_services.create_molecule_from_smiles(
            smiles=smiles, created_by=created_by
        )
