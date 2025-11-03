"""Core module for chemistry providers.

Contains interfaces, exceptions, and base abstractions.
"""

from . import interfaces
from .exceptions import InvalidSmilesError

# Re-export key interfaces
from .interfaces import (
    AbstractPropertyProvider,
    ChemEngineInterface,
    PropertyCategoryInfo,
    PropertyInfo,
    PropertyProviderInfo,
    PropertyProviderInterface,
)

__all__ = [
    "interfaces",
    "InvalidSmilesError",
    "ChemEngineInterface",
    "PropertyProviderInterface",
    "AbstractPropertyProvider",
    "PropertyInfo",
    "PropertyCategoryInfo",
    "PropertyProviderInfo",
]
