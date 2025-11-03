"""RDKit chemistry engine implementation."""

from .engine import RDKitChemEngine

# Create singleton instance
engine = RDKitChemEngine()

__all__ = ["RDKitChemEngine", "engine"]
