"""Compatibility exceptions module for chemistry providers.

Some code (including tests) imports exceptions from
`chemistry.providers.exceptions`. Historically exception classes lived
near the providers; they are now defined in `chemistry.types`. This
module re-exports the relevant exception classes for backwards
compatibility.
"""

from __future__ import annotations

from ..types import InvalidSmilesError  # re-export for backwards compatibility

__all__ = ["InvalidSmilesError"]
