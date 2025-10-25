"""
Interfaces y abstracciones centrales del sistema de generación de propiedades.

Este módulo define contratos estrictos usando Protocol y ABC para garantizar
seguridad de tipos y cumplir SOLID dentro de una arquitectura hexagonal.
Objetivos: desacoplar cálculos de proveedores, facilitar pruebas con DI y
ofrecer una base estable para extender categorías/proveedores sin romper APIs.

Resumen en inglés:
Core interfaces and abstractions for the property generation system.

This module defines strict interfaces using Python's Protocol and ABC (Abstract Base Classes)
to ensure type safety and enforce contracts across all property providers.

Following SOLID principles:
- Single Responsibility: Each interface has one clear purpose
- Open/Closed: Extensible via inheritance, closed for modification
- Liskov Substitution: All implementations are interchangeable
- Interface Segregation: Minimal, focused interfaces
- Dependency Inversion: Depend on abstractions, not concretions

Architecture Pattern: Hexagonal (Ports & Adapters)
- PropertyProviderInterface: Port (interface)
- Concrete providers: Adapters (implementations)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Protocol, runtime_checkable

# ========== Value Objects ==========


@dataclass(frozen=True)
class PropertyInfo:
    """Information about a single property that can be generated.

    Value object representing metadata about a calculable property.
    Immutable to ensure consistency across the system.

    Attributes:
        name: Property key (e.g., "MolWt", "LogP")
        description: Human-readable description
        units: Measurement units (e.g., "g/mol", "dimensionless")
        value_type: Expected value type ("float", "int", "string")
        range_min: Minimum expected value (optional)
        range_max: Maximum expected value (optional)

    Examples:
        >>> prop_info = PropertyInfo(
        ...     name="MolWt",
        ...     description="Molecular Weight",
        ...     units="g/mol",
        ...     value_type="float",
        ...     range_min=0.0,
        ...     range_max=2000.0
        ... )
        >>> print(prop_info.name)
        MolWt
    """

    name: str
    description: str
    units: str
    value_type: str  # "float", "int", "string"
    range_min: float | None = None
    range_max: float | None = None

    def __post_init__(self):
        """Validate property info on creation."""
        if not self.name:
            raise ValueError("Property name cannot be empty")
        if self.value_type not in ("float", "int", "string"):
            raise ValueError(f"Invalid value_type: {self.value_type}")


@dataclass(frozen=True)
class PropertyCategoryInfo:
    """Information about a property category.

    Value object describing what properties are available in a category
    and which providers can calculate them.

    Attributes:
        name: Category identifier (e.g., "admetsa", "physics")
        display_name: Human-readable name
        description: Category description
        properties: List of properties in this category
        available_providers: List of provider names that support this category

    Examples:
        >>> cat_info = PropertyCategoryInfo(
        ...     name="admetsa",
        ...     display_name="ADMET-SA",
        ...     description="Basic ADMET properties",
        ...     properties=[
        ...         PropertyInfo(name="MolWt", description="Molecular Weight",
        ...                      units="g/mol", value_type="float"),
        ...     ],
        ...     available_providers=["rdkit", "manual", "random"]
        ... )
        >>> print(cat_info.name)
        admetsa
    """

    name: str
    display_name: str
    description: str
    properties: List[PropertyInfo]
    available_providers: List[str]

    def __post_init__(self):
        """Validate category info on creation."""
        if not self.name:
            raise ValueError("Category name cannot be empty")
        if not self.properties:
            raise ValueError(f"Category {self.name} must have at least one property")


@dataclass(frozen=True)
class PropertyProviderInfo:
    """Information about a property provider.

    Value object describing a provider's capabilities and requirements.

    Attributes:
        name: Provider identifier (e.g., "rdkit", "manual")
        display_name: Human-readable name
        description: Provider description
        supported_categories: List of category names this provider supports
        requires_external_data: Whether provider needs external input (e.g., manual)
        is_computational: Whether provider computes from SMILES

    Examples:
        >>> provider_info = PropertyProviderInfo(
        ...     name="rdkit",
        ...     display_name="RDKit Computational",
        ...     description="Calculate properties using RDKit library",
        ...     supported_categories=["admetsa", "physics", "admet"],
        ...     requires_external_data=False,
        ...     is_computational=True
        ... )
        >>> print(provider_info.supports_category("admetsa"))
        True
    """

    name: str
    display_name: str
    description: str
    supported_categories: List[str]
    requires_external_data: bool
    is_computational: bool

    def supports_category(self, category: str) -> bool:
        """Check if this provider supports a given category."""
        return category in self.supported_categories


# ========== Protocol (Interface) ==========


@runtime_checkable
class PropertyProviderInterface(Protocol):
    """Protocol defining the contract for all property providers.

    This is a Port in the Hexagonal Architecture pattern. All concrete providers
    must implement these methods to be used by the system.

    Using Protocol instead of ABC allows for structural typing - any class that
    implements these methods is automatically compatible, even without explicit inheritance.
    """

    def get_info(self) -> PropertyProviderInfo:
        """Get metadata about this provider.

        Returns:
            PropertyProviderInfo with provider capabilities and requirements
        """
        ...

    def get_category_info(self, category: str) -> PropertyCategoryInfo:
        """Get information about what properties this provider can generate for a category.

        Args:
            category: Category name (e.g., "admetsa", "physics")

        Returns:
            PropertyCategoryInfo with list of properties and metadata

        Raises:
            ValueError: If category is not supported by this provider
        """
        ...

    def calculate_properties(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Calculate properties for a molecule.

        Args:
            smiles: SMILES string of the molecule
            category: Property category to calculate
            **kwargs: Provider-specific additional arguments

        Returns:
            Dictionary mapping property names to string values

        Raises:
            ValueError: If category not supported or SMILES invalid
            Exception: If calculation fails
        """
        ...

    def validate_input(self, category: str, **kwargs) -> None:
        """Validate input parameters before calculation.

        Args:
            category: Property category
            **kwargs: Provider-specific parameters to validate

        Raises:
            ValueError: If validation fails
        """
        ...


# ========== Abstract Base Class ==========


class AbstractPropertyProvider(ABC):
    """Abstract base class for property providers.

    This class provides a template for implementing property providers following
    the Template Method pattern. Subclasses must implement abstract methods.

    Use this as a base class when you want to enforce implementation at compile time
    and provide shared functionality.

    Attributes:
        _provider_info: Cached provider metadata
        _category_definitions: Mapping of category to PropertyCategoryInfo
    """

    def __init__(self):
        """Initialize provider with metadata."""
        self._provider_info: PropertyProviderInfo | None = None
        self._category_definitions: Dict[str, PropertyCategoryInfo] = {}
        self._initialize_metadata()

    @abstractmethod
    def _initialize_metadata(self) -> None:
        """Initialize provider and category metadata.

        Subclasses MUST implement this to set:
        - self._provider_info
        - self._category_definitions

        Examples:
            >>> def _initialize_metadata(self):
            ...     self._provider_info = PropertyProviderInfo(
            ...         name="rdkit",
            ...         display_name="RDKit",
            ...         description="RDKit computational provider",
            ...         supported_categories=["admetsa"],
            ...         requires_external_data=False,
            ...         is_computational=True
            ...     )
            ...     self._category_definitions["admetsa"] = PropertyCategoryInfo(
            ...         name="admetsa",
            ...         display_name="ADMET-SA",
            ...         description="Basic ADMET properties",
            ...         properties=[...],
            ...         available_providers=["rdkit"]
            ...     )
        """
        pass

    @abstractmethod
    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Internal implementation of property calculation.

        Subclasses MUST implement this with their specific calculation logic.

        Args:
            smiles: SMILES string
            category: Property category
            **kwargs: Additional arguments

        Returns:
            Dictionary of property name -> string value
        """
        pass

    def get_info(self) -> PropertyProviderInfo:
        """Get provider information (implements interface)."""
        if self._provider_info is None:
            raise RuntimeError(
                f"{self.__class__.__name__} did not initialize provider info"
            )
        return self._provider_info

    def get_category_info(self, category: str) -> PropertyCategoryInfo:
        """Get category information (implements interface)."""
        if category not in self._category_definitions:
            raise ValueError(
                f"Category '{category}' not supported by {self._provider_info.name}. "
                f"Supported: {list(self._category_definitions.keys())}"
            )
        return self._category_definitions[category]

    def calculate_properties(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Calculate properties (implements interface with validation).

        Template Method: Validates inputs, then delegates to subclass implementation.
        """
        # Validate category is supported
        if category not in self._category_definitions:
            raise ValueError(
                f"Category '{category}' not supported by {self._provider_info.name}"
            )

        # Validate inputs
        self.validate_input(category, **kwargs)

        # Delegate to subclass implementation
        return self._calculate_properties_impl(smiles, category, **kwargs)

    def validate_input(self, category: str, **kwargs) -> None:
        """Validate input parameters (default implementation).

        Subclasses can override to add specific validation.
        """
        # Base validation: category must be supported
        if category not in self._category_definitions:
            raise ValueError(f"Unsupported category: {category}")

        # Subclasses can add more validation by overriding

    def list_categories(self) -> List[str]:
        """List all supported category names."""
        return list(self._category_definitions.keys())

    def supports_category(self, category: str) -> bool:
        """Check if this provider supports a category."""
        return category in self._category_definitions


# ========== Type Guards ==========


def is_property_provider(obj: object) -> bool:
    """Check if an object implements PropertyProviderInterface.

    Args:
        obj: Object to check

    Returns:
        True if obj implements the interface
    """
    return isinstance(obj, PropertyProviderInterface)


def validate_provider(provider: object) -> None:
    """Validate that an object is a valid property provider.

    Args:
        provider: Object to validate

    Raises:
        TypeError: If provider doesn't implement required interface
    """
    if not is_property_provider(provider):
        raise TypeError(
            f"Provider must implement PropertyProviderInterface. "
            f"Got: {type(provider).__name__}"
        )
