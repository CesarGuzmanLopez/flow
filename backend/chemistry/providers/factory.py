"""Backward-compat shim for factory module.

Tests and legacy code import from chemistry.providers.factory.
This module re-exports the factory/registry from the new infrastructure package.
"""

from .infrastructure.factory import (
    PropertyProviderFactory,
    PropertyProviderRegistry,
    auto_register_providers,
    factory,
    registry,
)

__all__ = [
    "PropertyProviderFactory",
    "PropertyProviderRegistry",
    "auto_register_providers",
    "factory",
    "registry",
]
