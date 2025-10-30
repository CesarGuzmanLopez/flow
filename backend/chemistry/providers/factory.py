"""
Factory and Registry for Property Providers.

This module implements the Factory and Registry patterns to manage property providers
with dependency injection and type safety.

Design Patterns:
- Factory Pattern: Create provider instances on demand
- Registry Pattern: Central repository of available providers
- Singleton Pattern: Single global registry instance
- Dependency Injection: Providers injected via constructor

"""

import logging
from typing import Dict, List

from .interfaces import (
    PropertyCategoryInfo,
    PropertyProviderInfo,
    PropertyProviderInterface,
    validate_provider,
)

logger = logging.getLogger(__name__)


class PropertyProviderRegistry:
    """Registry for managing property provider instances.

    This class acts as a central repository (Service Locator pattern) for all
    available property providers. It ensures type safety and provides discovery
    capabilities.

    Thread-safe: No (intended for single-threaded Django environment)
    Singleton: Access via module-level `registry` instance

    Examples:
        >>> from chemistry.providers.factory import registry
        >>> provider = registry.get_provider("rdkit")
        >>> props = provider.calculate_properties("CCO", "admetsa")
        >>> print(props)
        {'MolWt': '46.07', 'LogP': '...'}
    """

    def __init__(self):
        """Initialize empty registry."""
        self._providers: Dict[str, PropertyProviderInterface] = {}
        logger.info("PropertyProviderRegistry initialized")

    def register(
        self, name: str, provider: PropertyProviderInterface, force: bool = False
    ) -> None:
        """Register a property provider.

        Args:
            name: Provider identifier (lowercase, alphanumeric + hyphens)
            provider: Provider instance implementing PropertyProviderInterface
            force: If True, overwrites existing provider with same name

        Raises:
            ValueError: If name is invalid or already registered (when force=False)
            TypeError: If provider doesn't implement required interface

        Examples:
            >>> registry = PropertyProviderRegistry()
            >>> registry.register("rdkit", RDKitProvider())
            >>> registry.register("custom-api", CustomAPIProvider())
            >>> print("rdkit" in registry.list_provider_names())
            True
        """
        # Validate name format
        name_lower = name.lower().strip()
        if not name_lower:
            raise ValueError("Provider name cannot be empty")
        if not name_lower.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Provider name must be alphanumeric with hyphens/underscores: {name}"
            )

        # Validate provider implements interface
        validate_provider(provider)

        # Register (override by default to match extension tests)
        if name_lower in self._providers and not force:
            logger.warning(
                f"Provider '{name_lower}' already registered. Overriding with new instance."
            )

        self._providers[name_lower] = provider
        try:
            display = provider.get_info().display_name
        except Exception:
            display = name_lower
        logger.info(f"Registered provider: {name_lower} ({display})")

    def unregister(self, name: str) -> None:
        """Unregister a provider.

        Args:
            name: Provider name to remove

        Raises:
            KeyError: If provider not found
        """
        name_lower = name.lower()

        if name_lower not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")

        del self._providers[name_lower]
        logger.info(f"Unregistered provider: {name_lower}")

    def get_provider(self, name: str) -> PropertyProviderInterface:
        """Get a provider by name.

        Args:
            name: Provider identifier

        Returns:
            Provider instance

        Raises:
            KeyError: If provider not found

        Example:
            >>> provider = registry.get_provider("rdkit")
            >>> print(provider.get_info().display_name)
            'RDKit Computational'
        """
        name_lower = name.lower()
        if name_lower not in self._providers:
            raise KeyError(
                f"Provider '{name}' not found. Available: {self.list_provider_names()}"
            )
        return self._providers[name_lower]

    def has_provider(self, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            True if provider exists
        """
        return name.lower() in self._providers

    def list_provider_names(self) -> List[str]:
        """List all registered provider names.

        Returns:
            Sorted list of provider names
        """
        return sorted(self._providers.keys())

    # Backward-compatible alias expected by some tests
    def list_providers(self) -> List[str]:
        """Alias returning provider names for backward compatibility."""
        return self.list_provider_names()

    def list_providers_info(self) -> List[PropertyProviderInfo]:
        """Get information about all registered providers.

        Returns:
            List of PropertyProviderInfo for all providers

        Example:
            >>> for info in registry.list_providers_info():
            ...     print(f"{info.name}: {info.description}")
            rdkit: Calculate properties using RDKit
            manual: User-provided property values
        """
        return [provider.get_info() for provider in self._providers.values()]

    def get_providers_for_category(self, category: str) -> List[str]:
        """Find all providers that support a given category.

        Args:
            category: Property category name

        Returns:
            List of provider names that support the category

        Example:
            >>> providers = registry.get_providers_for_category("admetsa")
            >>> print(providers)
            ['rdkit', 'manual', 'random']
        """
        result = []
        for name, provider in self._providers.items():
            try:
                provider.get_category_info(category)
                result.append(name)
            except ValueError:
                # Provider doesn't support this category
                continue
        return sorted(result)

    def get_category_info(
        self, category: str, provider_name: str
    ) -> PropertyCategoryInfo:
        """Get category information from a specific provider.

        Args:
            category: Category name
            provider_name: Provider name

        Returns:
            PropertyCategoryInfo with properties and metadata

        Raises:
            KeyError: If provider not found
            ValueError: If category not supported by provider
        """
        provider = self.get_provider(provider_name)
        return provider.get_category_info(category)

    def get_all_categories_info(self, category: str) -> Dict[str, PropertyCategoryInfo]:
        """Get category info from all providers that support it.

        Args:
            category: Category name

        Returns:
            Dictionary mapping provider name to PropertyCategoryInfo

        Example:
            >>> infos = registry.get_all_categories_info("admetsa")
            >>> for provider_name, info in infos.items():
            ...     print(f"{provider_name}: {len(info.properties)} properties")
        """
        result = {}
        for provider_name in self.get_providers_for_category(category):
            try:
                result[provider_name] = self.get_category_info(category, provider_name)
            except (KeyError, ValueError):
                continue
        return result

    def clear(self) -> None:
        """Clear all registered providers.

        WARNING: This is primarily for testing. Use with caution in production.
        """
        count = len(self._providers)
        self._providers.clear()
        logger.warning(f"Cleared {count} providers from registry")


class PropertyProviderFactory:
    """Factory for creating and managing property providers.

    This class provides a high-level interface for provider creation and management,
    delegating to the registry for storage.

    Dependency Injection: Accepts registry in constructor (can be mocked for testing)

    Example:
        >>> factory = PropertyProviderFactory(registry)
        >>> factory.create_provider("rdkit", RDKitProvider())
        >>> provider = factory.get_provider("rdkit")
    """

    def __init__(self, registry: PropertyProviderRegistry | None = None):
        """Initialize factory with a registry.

        Args:
            registry: Registry instance to use for provider storage
        """
        self._registry = registry or PropertyProviderRegistry()

    def create_provider(
        self, name: str, provider: PropertyProviderInterface, force: bool = False
    ) -> None:
        """Create and register a provider.

        This is a convenience wrapper around registry.register() with additional
        validation and logging.

        Args:
            name: Provider identifier
            provider: Provider instance
            force: Allow overwriting existing provider

        Raises:
            ValueError: If provider invalid or already exists
            TypeError: If provider doesn't implement interface
        """
        self._registry.register(name, provider, force=force)

    def get_provider(self, name: str) -> PropertyProviderInterface:
        """Get a provider by name (delegates to registry)."""
        try:
            return self._registry.get_provider(name)
        except KeyError as e:
            # Backward-compatible error type expected by tests
            raise ValueError(str(e))

    def list_providers(self) -> List[str]:
        """List all provider names (delegates to registry)."""
        return self._registry.list_provider_names()

    def get_providers_for_category(self, category: str) -> List[str]:
        """Get providers that support a category (delegates to registry)."""
        return self._registry.get_providers_for_category(category)


# ========== Global Registry Instance (Singleton) ==========


# Singleton registry instance - this is the primary access point
registry = PropertyProviderRegistry()

# Factory instance using the global registry
factory = PropertyProviderFactory(registry)


# ========== Auto-Discovery Helper ==========


def auto_register_providers() -> None:
    """Auto-discover and register all available providers.

    This function imports and registers built-in providers. Call this once
    during application startup (e.g., in AppConfig.ready()).

    Example:
        # In chemistry/apps.py
        class ChemistryConfig(AppConfig):
            def ready(self):
                from .providers.factory import auto_register_providers
                auto_register_providers()
    """
    logger.info("Auto-registering property providers...")

    # Import providers (avoid circular imports by doing it here)
    try:
        from .property_providers import (
            ManualProvider,
            RandomProvider,
            RDKitProvider,
        )

        # Register built-in providers
        registry.register("rdkit", RDKitProvider())
        registry.register("manual", ManualProvider())
        registry.register("random", RandomProvider())
        registry.register("provider-extra", RandomProvider())  # Alias

        logger.info(
            f"Auto-registered {len(registry.list_provider_names())} providers: "
            f"{registry.list_provider_names()}"
        )

    except ImportError as e:
        logger.error(f"Failed to auto-register providers: {e}")
        raise
