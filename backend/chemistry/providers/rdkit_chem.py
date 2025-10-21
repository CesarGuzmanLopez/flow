"""
RDKit-based implementation of ChemEngineInterface.

Provides structure normalization (InChI, InChIKey, canonical SMILES, formula)
and a couple of basic computed properties useful for chemistry workflows.

If RDKit isn't available in the environment, importing this module will raise
an ImportError. Use the package-level selector in `chemistry.providers` to
fall back gracefully to the mock engine for dev/test.
"""

from typing import Dict, List

from chemistry.providers.interface import ChemEngineInterface

try:
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, rdMolDescriptors
    from rdkit.Chem.inchi import MolToInchi, MolToInchiKey
except Exception as exc:  # pragma: no cover - handled by provider selector
    raise ImportError(
        "RDKit is not available. Install 'rdkit-pypi' to use the RDKit provider"
    ) from exc


class RDKitChemEngine(ChemEngineInterface):
    """RDKit-backed engine for chemistry operations."""

    def smiles_to_inchi(self, smiles: str) -> Dict[str, str]:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")
        # Normalize to canonical SMILES without stereochemistry changes
        canonical = Chem.MolToSmiles(mol, canonical=True)
        # Generate InChI/InChIKey (requires RDKit InChI support)
        inchi = MolToInchi(mol)
        inchikey = MolToInchiKey(mol)
        formula = rdMolDescriptors.CalcMolFormula(mol)
        return {
            "inchi": inchi,
            "inchikey": inchikey,
            "canonical_smiles": canonical,
            "molecular_formula": formula,
        }

    def calculate_properties(self, smiles: str) -> Dict[str, float]:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")
        # Map to application-expected keys
        return {
            "MolWt": float(Descriptors.MolWt(mol)),
            "LogP": float(Crippen.MolLogP(mol)),
            "TPSA": float(rdMolDescriptors.CalcTPSA(mol)),
            "HBA": float(rdMolDescriptors.CalcNumHBA(mol)),
            "HBD": float(rdMolDescriptors.CalcNumHBD(mol)),
            # Additional simple counts (optional extension):
            "RB": float(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        }

    def generate_substitutions(self, smiles: str, count: int = 3) -> List[str]:
        """
        Very basic (placeholder) substitutions: append a methyl at an available atom.
        For real enumeration, integrate with RDKit reaction SMARTS. Here we keep it
        deterministic and simple for seed/test purposes.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {smiles}")

        # Fallback simple approach: return the original plus up to `count-1` canonical forms
        base = Chem.MolToSmiles(mol, canonical=True)
        variants = [base]
        # Heuristic: if carbon exists, try adding a methyl (this is simplistic)
        if mol.GetNumAtoms() > 0:
            try:
                # Create ethane variant as a placeholder when possible
                ethane = Chem.MolFromSmiles("CC")
                variants.append(Chem.MolToSmiles(ethane, canonical=True))
            except Exception:
                pass
        # Deduplicate and cap
        seen = []
        for v in variants:
            if v not in seen:
                seen.append(v)
            if len(seen) >= count:
                break
        return seen


engine = RDKitChemEngine()
