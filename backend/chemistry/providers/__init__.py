"""
Chemistry providers package.

This exposes a default `engine` selected by environment variable CHEM_ENGINE.

Allowed values:
- CHEM_ENGINE=rdkit -> use RDKit provider (ImportError if not available)
- CHEM_ENGINE=mock -> use mock provider (for tests only)

There is no automatic fallback to the mock engine to avoid "false" data in
production. Set CHEM_ENGINE explicitly in your environment.

You can also import specific engines directly:
- from chemistry.providers.rdkit_chem import engine as rdkit_engine
- from chemistry.providers.mock_chem import mock_engine
"""

import os
from typing import Any

# Require explicit engine selection. Default to rdkit but without fallback.
provider_choice = os.environ.get("CHEM_ENGINE", "rdkit").lower()

if provider_choice == "mock":
    from .mock_chem import mock_engine as _engine  # type: ignore
elif provider_choice == "rdkit":
    from .rdkit_chem import engine as _engine  # type: ignore
else:
    raise ImportError(
        "Unsupported CHEM_ENGINE value. Set CHEM_ENGINE to 'rdkit' or 'mock'."
    )


engine: Any = _engine

__all__ = ["engine"]
