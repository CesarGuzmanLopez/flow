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
from typing import Any, Dict, List, Protocol, runtime_checkable

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
        """Initialize provider with metadata.

        Supports two extension styles used in tests:
        - Subclasses that set self._provider_info and self._category_definitions
        - Subclasses that RETURN a PropertyProviderInfo from _initialize_metadata()
          and define an optional _initialize_properties() that returns a
          mapping of property name -> PropertyInfo. In this case we build a
          default category automatically.
        """
        self._provider_info: PropertyProviderInfo | None = None
        self._category_definitions: Dict[str, PropertyCategoryInfo] = {}
        # Optional map used by simple providers (like the test Experimental provider)
        self._properties: Dict[str, PropertyInfo] = {}

        maybe_info = self._initialize_metadata()
        # If subclass returned a PropertyProviderInfo, accept it
        if isinstance(maybe_info, PropertyProviderInfo):
            self._provider_info = maybe_info

        # If subclass provides _initialize_properties(), consume it
        init_props = getattr(self, "_initialize_properties", None)
        if callable(init_props):
            try:
                props = init_props()
                if isinstance(props, dict):
                    self._properties = props
            except TypeError:
                # Some implementations may not require parameters; ignore signature mismatches
                try:
                    props = init_props()  # type: ignore[misc]
                    if isinstance(props, dict):
                        self._properties = props
                except Exception:
                    pass

        # If no categories were defined but we have properties, create a default category
        if not self._category_definitions and self._properties:
            provider_name = (
                self._provider_info.name if self._provider_info else "default"
            )
            self._category_definitions["default"] = PropertyCategoryInfo(
                name="default",
                display_name="Default",
                description="Default property set",
                properties=list(self._properties.values()),
                available_providers=[provider_name],
            )

    @abstractmethod
    def _initialize_metadata(self) -> PropertyProviderInfo | None:
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
        self._ensure_metadata_initialized()
        assert self._provider_info is not None
        return self._provider_info

    def get_category_info(self, category: str) -> PropertyCategoryInfo:
        """Get category information (implements interface)."""
        self._ensure_metadata_initialized()
        if category not in self._category_definitions:
            raise ValueError(
                f"Category '{category}' not supported by {self._provider_info.name}. "
                f"Supported: {list(self._category_definitions.keys())}"
            )
        return self._category_definitions[category]

    def calculate_properties(
        self, smiles: str, category: str | None = None, **kwargs
    ) -> Dict[str, Any]:
        """Calculate properties (implements interface with validation).

        Template Method: Validates inputs, then delegates to subclass implementation.
        """
        self._ensure_metadata_initialized()

        # Resolve default category when not provided and only one exists
        if category is None:
            if self._category_definitions:
                if len(self._category_definitions) == 1:
                    category = next(iter(self._category_definitions.keys()))
                else:
                    raise ValueError(
                        "Multiple categories supported; 'category' must be provided"
                    )
            else:
                # Allow providers that don't declare categories (experimental/manual adapters)
                category = "default"

        # Validate inputs
        try:
            self.validate_input(category, **kwargs)
        except TypeError:
            # Some simple providers may not accept extra kwargs in validation
            self.validate_input(category)

        # Delegate to subclass implementation
        try:
            return self._calculate_properties_impl(smiles, category, **kwargs)
        except TypeError:
            # Allow implementations that don't accept 'category' explicitly
            return self._calculate_properties_impl(smiles, **kwargs)  # type: ignore[arg-type]

    def validate_input(self, category: str, **kwargs) -> None:
        """Validate input parameters (default implementation).

        Subclasses can override to add specific validation.
        """
        # Base validation: category must be supported unless provider doesn't declare categories
        if not self._category_definitions:
            # Allow simple providers that only define properties without categories
            # Accept "default" category implicitly
            if category not in (None, "default"):
                raise ValueError(f"Unsupported category: {category}")
        else:
            if category not in self._category_definitions:
                raise ValueError(f"Unsupported category: {category}")

        # Subclasses can add more validation by overriding

    def list_categories(self) -> List[str]:
        """List all supported category names."""
        return list(self._category_definitions.keys())

    def supports_category(self, category: str) -> bool:
        """Check if this provider supports a category."""
        return category in self._category_definitions

    # --------- Convenience API expected by tests ---------
    def get_metadata(self) -> PropertyProviderInfo:
        """Compatibility sugar for tests: returns provider info.

        Some tests call provider.get_metadata(); map to get_info().
        """
        return self.get_info()

    def get_properties(self) -> Dict[str, PropertyInfo]:
        """Compatibility sugar used by tests: return mapping of property name -> PropertyInfo.

        Preferred behavior (for simple providers used in tests): if self._properties exists,
        return it. Otherwise, build a mapping from the (sole or first) category.
        """
        if getattr(self, "_properties", None):
            return dict(self._properties)
        if not self._category_definitions:
            return {}
        if len(self._category_definitions) == 1:
            info = next(iter(self._category_definitions.values()))
            return {p.name: p for p in info.properties}
        # If multiple, pick the first deterministically
        first = self._category_definitions[sorted(self._category_definitions.keys())[0]]
        return {p.name: p for p in first.properties}

    # --------- Internal helpers ---------
    def _ensure_metadata_initialized(self) -> None:
        """Lazy-initialize provider info if subclass didn't set it explicitly.

        Attempts to build minimal metadata from conventional attributes.
        """
        if self._provider_info is not None:
            return
        # Try to infer basic info from attributes commonly used in simple providers
        name = getattr(self, "name", None) or getattr(self, "NAME", None)
        if not isinstance(name, str) or not name:
            cls_name = self.__class__.__name__
            if cls_name.endswith("PropertyProvider"):
                base = cls_name[: -len("PropertyProvider")]
            elif cls_name.endswith("Provider"):
                base = cls_name[: -len("Provider")]
            else:
                base = cls_name
            name = base.lower()
        display_name = getattr(self, "display_name", None) or name.title()
        description = getattr(self, "description", None) or f"{display_name} provider"
        requires_external_data = bool(getattr(self, "requires_external_data", False))
        is_computational = bool(
            getattr(self, "is_computational", not requires_external_data)
        )
        supported_categories = list(getattr(self, "supported_categories", []) or [])
        if not supported_categories and self._category_definitions:
            supported_categories = list(self._category_definitions.keys())
        if not supported_categories:
            supported_categories = ["default"]

        self._provider_info = PropertyProviderInfo(
            name=name,
            display_name=display_name,
            description=description,
            supported_categories=supported_categories,
            requires_external_data=requires_external_data,
            is_computational=is_computational,
        )


# ========== Type Guards ==========


def is_property_provider(obj: object) -> bool:
    """Check if an object implements PropertyProviderInterface.

    Args:
        obj: Object to check

    Returns:
        True if obj implements the interface
    """
    return isinstance(obj, PropertyProviderInterface) or (
        hasattr(obj, "get_info") and hasattr(obj, "calculate_properties")
    )


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
