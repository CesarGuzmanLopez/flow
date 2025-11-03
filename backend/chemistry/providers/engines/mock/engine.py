from typing import Literal, Union, overload

from chemistry.providers.core.interfaces import ChemEngineInterface
from chemistry.type_definitions import (
    InvalidSmilesError,
    MolecularProperties,
    MolecularPropertiesDict,
    StructureIdentifiers,
    StructureIdentifiersDict,
    SubstitutionResult,
)


class MockChemEngine(ChemEngineInterface):
    """Lightweight mock of a chemistry engine (substitute for RDKit in tests)."""

    @overload
    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: Literal[True] = True
    ) -> StructureIdentifiers: ...

    @overload
    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: Literal[False]
    ) -> StructureIdentifiersDict: ...

    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> Union[StructureIdentifiers, StructureIdentifiersDict]:
        """Deterministic fake conversion for testing."""
        if not smiles or not str(smiles).strip():
            raise InvalidSmilesError(smiles)
        if "INVALID" in str(smiles).upper():
            raise InvalidSmilesError(smiles)
        # deterministic fake conversion
        inchi = f"InChI=1S/{smiles[::-1]}"
        inchikey = f"IK_{hash(smiles) & 0xFFFFFFFF:08x}"
        canonical_smiles = smiles

        if return_dataclass:
            return StructureIdentifiers(
                inchi=inchi,
                inchikey=inchikey,
                canonical_smiles=canonical_smiles,
                molecular_formula=None,  # Mock doesn't provide formula
            )
        else:
            return {
                "inchi": inchi,
                "inchikey": inchikey,
                "canonical_smiles": canonical_smiles,
                "molecular_formula": None,
            }

    @overload
    def calculate_properties(
        self, smiles: str, *, return_dataclass: Literal[True] = True
    ) -> MolecularProperties: ...

    @overload
    def calculate_properties(
        self, smiles: str, *, return_dataclass: Literal[False]
    ) -> MolecularPropertiesDict: ...

    def calculate_properties(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> Union[MolecularProperties, MolecularPropertiesDict]:
        """Fake deterministic properties covering ADMETSA set."""
        if not smiles or not str(smiles).strip():
            raise InvalidSmilesError(smiles)
        if "INVALID" in str(smiles).upper():
            raise InvalidSmilesError(smiles)
        # Fake deterministic properties covering ADMETSA set
        base = abs(hash(smiles)) % 10000
        # helpers

        def f(mod: int, off: int = 0) -> float:
            return float((base % mod) + off)

        if return_dataclass:
            return MolecularProperties(
                log_p=round((base % 100) / 10.0, 2),
                tpsa=f(120, 10),
                atom_count=f(7),
                hba=f(10),
                hbd=f(5),
                rotatable_bonds=f(12),
                molar_refractivity=round((base % 200) / 3.0, 2),
                ld50=f(300, 50),
                mutagenicity=float((base % 2)),
                developmental_toxicity=float((base // 2) % 2),
                synthetic_accessibility=round((base % 90) / 10.0, 1),
            )
        else:
            return {
                "LogP": round((base % 100) / 10.0, 2),
                "PSA": f(120, 10),
                "AtX": f(7),
                "HBA": f(10),
                "HBD": f(5),
                "RB": f(12),
                "MR": round((base % 200) / 3.0, 2),
                "LD50": f(300, 50),
                "Mutagenicity": float((base % 2)),
                "DevelopmentalToxicity": float((base // 2) % 2),
                "SyntheticAccessibility": round((base % 90) / 10.0, 1),
            }

    @overload
    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: Literal[True] = True
    ) -> SubstitutionResult: ...

    @overload
    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: Literal[False]
    ) -> list[str]: ...

    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: bool = True
    ) -> Union[SubstitutionResult, list[str]]:
        """Return mock variations."""
        if count <= 0:
            raise ValueError("Count must be positive")

        # return variations
        substitutions = [f"{smiles}-sub{i}" for i in range(1, count + 1)]

        if return_dataclass:
            return SubstitutionResult(
                substitutions=substitutions,
                original_smiles=smiles,
                count_requested=count,
            )
        else:
            return substitutions


mock_engine = MockChemEngine()
