"""Type stubs for rdkit.Chem.Descriptors module."""

from rdkit.Chem import Mol

def ExactMolWt(mol: Mol) -> float:
    """Calculate the exact molecular weight of a molecule."""
    ...

def MolLogP(mol: Mol) -> float:
    """Calculate the octanol-water partition coefficient (logP) of a molecule."""
    ...

def MolWt(mol: Mol) -> float:
    """Calculate the molecular weight of a molecule."""
    ...
