"""Backward-compat shim for interface module (singular).

Re-exports ChemEngineInterface from core.interfaces.
"""

from .core.interfaces import ChemEngineInterface

__all__ = ["ChemEngineInterface"]
