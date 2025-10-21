from typing import Dict, List

from .interface import ChemEngineInterface


class MockChemEngine(ChemEngineInterface):
    """Lightweight mock of a chemistry engine (substitute for RDKit in tests)."""

    def smiles_to_inchi(self, smiles: str) -> Dict[str, str]:
        # deterministic fake conversion
        inchi = f"InChI=1S/{smiles[::-1]}"
        inchikey = f"IK_{hash(smiles) & 0xFFFFFFFF:08x}"
        return {"inchi": inchi, "inchikey": inchikey, "canonical_smiles": smiles}

    def calculate_properties(self, smiles: str) -> Dict[str, float]:
        # fake properties
        base = abs(hash(smiles)) % 1000
        return {"logP": (base % 10) / 10.0, "psa": (base % 50) + 10}

    def generate_substitutions(self, smiles: str, count: int = 3) -> List[str]:
        # return variations
        return [f"{smiles}-sub{i}" for i in range(1, count + 1)]


mock_engine = MockChemEngine()
