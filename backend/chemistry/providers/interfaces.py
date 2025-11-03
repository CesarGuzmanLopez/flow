"""Backward-compat shim for interfaces module.

Re-exports property provider interfaces from core.interfaces.
"""

from .core.interfaces import (
    AbstractPropertyProvider,
    PropertyCategoryInfo,
    PropertyInfo,
    PropertyProviderInfo,
    PropertyProviderInterface,
    is_property_provider,
    validate_provider,
)

__all__ = [
    "PropertyProviderInterface",
    "AbstractPropertyProvider",
    "PropertyInfo",
    "PropertyCategoryInfo",
    "PropertyProviderInfo",
    "is_property_provider",
    "validate_provider",
]
