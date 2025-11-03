"""Backward-compat shim for mock_chem module.

Re-exports mock engine symbols from engines.mock.
"""

from .engines.mock import MockChemEngine, mock_engine

__all__ = ["MockChemEngine", "mock_engine"]
