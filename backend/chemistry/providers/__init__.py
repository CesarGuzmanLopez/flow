"""
Chemistry providers package.

This exposes a default `engine` selected by availability or env override:
- If CHEM_ENGINE=rdkit -> use RDKit provider (error if not available)
- If CHEM_ENGINE=mock -> use mock provider
- Otherwise -> try RDKit, fall back to mock

You can also import specific engines directly:
- from chemistry.providers.rdkit_chem import engine as rdkit_engine
- from chemistry.providers.mock_chem import mock_engine
"""

import os
from typing import Any

# Default to RDKit; allow CHEM_ENGINE override. Always fall back to mock if import fails.
provider_choice = os.environ.get("CHEM_ENGINE", "rdkit").lower()

if provider_choice == "mock":  # explicit mock
    from .mock_chem import mock_engine as _engine  # type: ignore
elif provider_choice == "rdkit":  # prefer rdkit, but fallback if unavailable
    try:
        from .rdkit_chem import engine as _engine  # type: ignore
    except Exception:  # pragma: no cover - if RDKit not present
        from .mock_chem import mock_engine as _engine  # type: ignore
else:  # auto detection (try rdkit first)
    try:
        from .rdkit_chem import engine as _engine  # type: ignore
    except Exception:  # pragma: no cover - if RDKit not present
        from .mock_chem import mock_engine as _engine  # type: ignore


engine: Any = _engine

__all__ = ["engine"]
