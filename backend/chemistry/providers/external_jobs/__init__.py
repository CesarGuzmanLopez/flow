"""Backward-compat package alias for external_jobs.

This package forwards imports to background_jobs.* modules.
"""

import sys as _sys
from importlib import import_module as _import_module

# Preload and alias common submodules
for _name in ("models", "persistence", "worker", "interfaces", "telemetry"):
    _mod = _import_module(f"chemistry.providers.background_jobs.{_name}")
    _sys.modules[f"chemistry.providers.external_jobs.{_name}"] = _mod

__all__ = ["models", "persistence", "worker", "interfaces", "telemetry"]
