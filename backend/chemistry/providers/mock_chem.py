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
        # Fake deterministic properties covering ADMETSA set
        base = abs(hash(smiles)) % 10000
        # helpers

        def f(mod: int, off: int = 0) -> float:
            return float((base % mod) + off)

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

    def generate_substitutions(self, smiles: str, count: int = 3) -> List[str]:
        # return variations
        return [f"{smiles}-sub{i}" for i in range(1, count + 1)]


mock_engine = MockChemEngine()
