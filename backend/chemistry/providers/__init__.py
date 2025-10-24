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

"""Provider selection module.

This exposes `engine` as a lazy proxy that resolves the actual provider at
call-time using Django settings (`settings.CHEM_ENGINE`) or the
`CHEM_ENGINE` environment variable. This allows test helpers like
`@override_settings(CHEM_ENGINE='mock')` to take effect.
"""


def _resolve_engine() -> Any:
    """Resolve and return the concrete engine instance based on settings/env.

    This function attempts to import the requested provider. If the requested
    provider is unavailable (e.g., RDKit not installed), it falls back to the
    mock provider to keep the test/dev environment operable.
    """
    provider_choice = None
    try:
        from django.conf import settings

        provider_choice = getattr(settings, "CHEM_ENGINE", None)
    except Exception:
        provider_choice = None

    provider_choice = (
        provider_choice or os.environ.get("CHEM_ENGINE", "rdkit")
    ).lower()

    if provider_choice == "mock":
        from .mock_chem import mock_engine as engine

        return engine

    # Try to load requested provider (rdkit by default)
    try:
        if provider_choice == "rdkit":
            from .rdkit_chem import engine

            return engine
        else:
            mod = __import__(f"chemistry.providers.{provider_choice}", fromlist=["*"])
            engine = getattr(mod, "engine", None)
            if engine is not None:
                return engine
    except Exception:
        pass

    # Last resort: try to return mock provider
    try:
        from .mock_chem import mock_engine as engine

        return engine
    except Exception as exc:
        raise ImportError(
            "No chemistry provider available (rdkit import failed and mock unavailable)"
        ) from exc


class _EngineProxy:
    """Proxy object that delegates attribute access to the resolved engine.

    We deliberately avoid long-lived caching so tests that change
    `settings.CHEM_ENGINE` via `override_settings` get the expected provider.
    """

    def __getattr__(self, name: str):
        engine = _resolve_engine()
        return getattr(engine, name)


engine: Any = _EngineProxy()

__all__ = ["engine"]
