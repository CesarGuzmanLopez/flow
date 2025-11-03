"""Backward-compat shim for rdkit_chem module.

Re-exports RDKit engine symbols from engines.rdkit.
"""

from .engines.rdkit import RDKitChemEngine
from .engines.rdkit import engine as engine

__all__ = ["RDKitChemEngine", "engine"]
