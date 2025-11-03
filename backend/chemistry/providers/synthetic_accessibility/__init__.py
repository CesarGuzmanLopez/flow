"""Synthetic Accessibility providers.

Contains implementations for calculating synthetic accessibility scores:
- AMBIT-SA: Java-based reference implementation
- RDKit: Pure Python approximation
- BR-SAScore: Bayesian machine learning model
"""

# Import submodules to make them accessible
from . import ambit, brsascore, rdkit

__all__ = ["ambit", "rdkit", "brsascore"]
