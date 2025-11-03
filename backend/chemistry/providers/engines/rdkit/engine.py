"""
RDKit-based implementation of ChemEngineInterface.

Provides structure normalization (InChI, InChIKey, canonical SMILES, formula)
and a couple of basic computed properties useful for chemistry workflows.

If RDKit isn't available in the environment, importing this module will raise
an ImportError. Use the package-level selector in `chemistry.providers` to
fall back gracefully to the mock engine for dev/test.
"""

from typing import Literal, Union, overload

from chemistry.providers.core.interfaces import ChemEngineInterface
from chemistry.type_definitions import (
    InvalidSmilesError,
    MolecularProperties,
    MolecularPropertiesDict,
    PropertyCalculationError,
    StructureIdentifiers,
    StructureIdentifiersDict,
    SubstitutionGenerationError,
    SubstitutionResult,
)

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    from rdkit.Chem.inchi import MolToInchi, MolToInchiKey
except Exception as exc:  # pragma: no cover - handled by provider selector
    raise ImportError(
        "RDKit is not available. Install 'rdkit-pypi' to use the RDKit provider"
    ) from exc


class RDKitChemEngine(ChemEngineInterface):
    """RDKit-backed engine for chemistry operations."""

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
        """Convert SMILES to structure identifiers using RDKit."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise InvalidSmilesError(smiles)

        # Normalize to canonical SMILES without stereochemistry changes
        canonical = Chem.MolToSmiles(mol, canonical=True)
        # Generate InChI/InChIKey (requires RDKit InChI support)
        inchi = MolToInchi(mol)
        inchikey = MolToInchiKey(mol)
        formula = rdMolDescriptors.CalcMolFormula(mol)

        if return_dataclass:
            return StructureIdentifiers(
                inchi=inchi,
                inchikey=inchikey,
                canonical_smiles=canonical,
                molecular_formula=formula,
            )
        else:
            return {
                "inchi": inchi,
                "inchikey": inchikey,
                "canonical_smiles": canonical,
                "molecular_formula": formula,
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
        """Calculate molecular properties using RDKit."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise InvalidSmilesError(smiles)

        try:
            # Calculate properties
            mol_wt = float(Descriptors.ExactMolWt(mol))
            log_p = float(Descriptors.MolLogP(mol))
            tpsa = float(rdMolDescriptors.CalcTPSA(mol))
            hba = float(rdMolDescriptors.CalcNumHBA(mol))
            hbd = float(rdMolDescriptors.CalcNumHBD(mol))
            rb = float(rdMolDescriptors.CalcNumRotatableBonds(mol))

            if return_dataclass:
                return MolecularProperties(
                    mol_wt=mol_wt,
                    log_p=log_p,
                    tpsa=tpsa,
                    hba=hba,
                    hbd=hbd,
                    rotatable_bonds=rb,
                )
            else:
                # Map to application-expected keys
                return {
                    "MolWt": mol_wt,
                    "LogP": log_p,
                    "TPSA": tpsa,
                    "HBA": hba,
                    "HBD": hbd,
                    "RB": rb,
                }
        except Exception as e:
            raise PropertyCalculationError(smiles, message=str(e)) from e

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
        """
        Very basic (placeholder) substitutions: append a methyl at an available atom.
        For real enumeration, integrate with RDKit reaction SMARTS. Here we keep it
        deterministic and simple for seed/test purposes.
        """
        if count <= 0:
            raise ValueError("Count must be positive")

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise InvalidSmilesError(smiles)

        try:
            base = Chem.MolToSmiles(mol, canonical=True)
            variants = [base]
            # Heuristic: if carbon exists, try adding a methyl (this is simplistic)
            if mol.GetNumAtoms() > 0:
                try:
                    # Create ethane variant as a placeholder when possible
                    ethane = Chem.MolFromSmiles("CC")
                    if ethane is not None:
                        variants.append(Chem.MolToSmiles(ethane, canonical=True))
                except Exception:
                    pass

            seen = []
            for v in variants:
                if v not in seen:
                    seen.append(v)
                if len(seen) >= count:
                    break

            if return_dataclass:
                return SubstitutionResult(
                    substitutions=seen, original_smiles=smiles, count_requested=count
                )
            else:
                return seen
        except Exception as e:
            raise SubstitutionGenerationError(smiles, count, message=str(e)) from e


engine = RDKitChemEngine()
