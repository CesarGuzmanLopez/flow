"""Backward-compat shim for utils module.

Re-exports helper functions from infrastructure.utils.
"""

from .infrastructure.utils import enrich_smiles

__all__ = ["enrich_smiles"]
