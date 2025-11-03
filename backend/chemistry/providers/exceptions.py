"""Backward-compat shim for exceptions module.

Re-exports exceptions from core.exceptions.
"""

from .core.exceptions import InvalidSmilesError

__all__ = ["InvalidSmilesError"]
