"""
Tests de Extensión de Providers del módulo Chemistry.

Validaciones probadas:
- Cómo crear un provider custom
- Registro en Factory
- Invocación desde API
- Manejo de errores
- Patrón Template Method
"""

from dataclasses import dataclass
from typing import Any, Dict

import pytest

from chemistry.providers.factory import (
    PropertyProviderFactory,
    PropertyProviderRegistry,
)
from chemistry.providers.interfaces import (
    AbstractPropertyProvider,
    PropertyInfo,
    PropertyProviderInfo,
)

# ============================================================================
# CUSTOM PROVIDER EXAMPLE
# ============================================================================


@dataclass
class ExperimentalMoleculeData:
    """Data structure for experimental provider results."""

    mw: float
    logp: float
    hbd: int


class ExperimentalPropertyProvider(AbstractPropertyProvider):
    """
    Custom property provider: User-provided experimental data.

    Propósito:
    - Permitir usuarios ingresar datos experimentales manualmente
    - No requiere cálculos computacionales
    - Source es "experimental", no "rdkit"

    Ejemplo de uso:

    >>> provider = ExperimentalPropertyProvider()
    >>> provider.calculate_properties(
    ...     smiles="CCO",
    ...     properties_data={
    ...         "MolWt": {"value": 46.07, "units": "g/mol"},
    ...         "LogP": {"value": -0.31, "units": ""},
    ...     }
    ... )
    >>> # Retorna properties guardadas
    """

    def _initialize_metadata(self) -> PropertyProviderInfo:
        """Define metadata del provider."""
        return PropertyProviderInfo(
            name="experimental",
            display_name="Experimental Data",
            is_computational=False,
            requires_external_data=True,
            supported_categories=["manual", "experimental"],
            description="User-provided experimental measurements",
        )

    def _initialize_properties(self) -> Dict[str, PropertyInfo]:
        """Define qué propiedades puede calcular."""
        return {
            "MolWt": PropertyInfo(
                name="MolWt",
                description="Molecular weight (experimental)",
                units="g/mol",
                value_type="float",
                range_min=0,
                range_max=1000,
            ),
            "LogP": PropertyInfo(
                name="LogP",
                description="Lipophilicity (experimental)",
                units="",
                value_type="float",
                range_min=-10,
                range_max=10,
            ),
            "HBD": PropertyInfo(
                name="HBD",
                description="H-bond donors (experimental)",
                units="count",
                value_type="int",
                range_min=0,
                range_max=20,
            ),
        }

    def _calculate_properties_impl(
        self, smiles: str, properties_data: Dict[str, Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Implementación: Validar y guardar datos.

        Override del Template Method en AbstractPropertyProvider.

        Parámetros:
        - smiles: SMILES (validación básica)
        - properties_data: Dict con valores ingresados por usuario

        >>> provider = ExperimentalPropertyProvider()
        >>> result = provider._calculate_properties_impl(
        ...     smiles="CCO",
        ...     properties_data={
        ...         "MolWt": {"value": 46.07, "units": "g/mol"},
        ...         "LogP": {"value": -0.31, "units": ""},
        ...         "HBD": {"value": 1, "units": "count"}
        ...     }
        ... )
        >>> print(result)
        {
            "MolWt": {"value": 46.07, "units": "g/mol", "source": "experimental"},
            "LogP": {"value": -0.31, "units": "", "source": "experimental"},
            "HBD": {"value": 1, "units": "count", "source": "experimental"}
        }
        """
        if not properties_data:
            return {}

        validated = {}

        for prop_name, prop_data in properties_data.items():
            if prop_name not in self._properties:
                continue  # Skip unknown properties

            prop_info = self._properties[prop_name]
            value = prop_data.get("value")

            # Validar rango
            if prop_info.range_min is not None:
                if value < prop_info.range_min:
                    raise ValueError(
                        f"{prop_name}: value {value} < min {prop_info.range_min}"
                    )

            if prop_info.range_max is not None:
                if value > prop_info.range_max:
                    raise ValueError(
                        f"{prop_name}: value {value} > max {prop_info.range_max}"
                    )

            # Guardar con source
            validated[prop_name] = {
                "value": value,
                "units": prop_data.get("units", ""),
                "source": "experimental",
                "method": "user_input",
            }

        return validated


# ============================================================================
# TESTS: Custom Provider
# ============================================================================


class TestCustomProvider:
    """Test creación e uso de custom provider."""

    @pytest.fixture
    def experimental_provider(self):
        """Create instance of custom provider."""
        return ExperimentalPropertyProvider()

    def test_provider_metadata(self, experimental_provider):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>> info = provider.get_metadata()
        >>>
        >>> assert info.name == "experimental"
        >>> assert not info.is_computational
        >>> assert info.requires_external_data
        """
        info = experimental_provider.get_metadata()

        assert info.name == "experimental"
        assert info.display_name == "Experimental Data"
        assert not info.is_computational
        assert info.requires_external_data

    def test_provider_properties(self, experimental_provider):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> props = provider.get_properties()
        >>> assert "MolWt" in props
        >>> assert "LogP" in props
        >>> assert "HBD" in props
        """
        props = experimental_provider.get_properties()

        assert "MolWt" in props
        assert "LogP" in props
        assert "HBD" in props

        # Check property info
        mw_info = props["MolWt"]
        assert mw_info.name == "MolWt"
        assert mw_info.units == "g/mol"

    def test_calculate_properties_with_valid_data(self, experimental_provider):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     properties_data={
        ...         "MolWt": {"value": 46.07, "units": "g/mol"},
        ...         "LogP": {"value": -0.31, "units": ""}
        ...     }
        ... )
        >>>
        >>> assert result["MolWt"]["value"] == 46.07
        >>> assert result["LogP"]["value"] == -0.31
        """
        result = experimental_provider.calculate_properties(
            smiles="CCO",
            properties_data={
                "MolWt": {"value": 46.07, "units": "g/mol"},
                "LogP": {"value": -0.31, "units": ""},
                "HBD": {"value": 1, "units": "count"},
            },
        )

        assert result["MolWt"]["value"] == 46.07
        assert result["LogP"]["value"] == -0.31
        assert result["HBD"]["value"] == 1
        assert result["MolWt"]["source"] == "experimental"

    def test_calculate_properties_with_out_of_range_value(self, experimental_provider):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> # LogP > 10 es fuera de rango
        >>> with pytest.raises(ValueError):
        ...     provider.calculate_properties(
        ...         smiles="CCO",
        ...         properties_data={
        ...             "LogP": {"value": 50, "units": ""}  # OUT OF RANGE
        ...         }
        ...     )
        """
        with pytest.raises(ValueError):
            experimental_provider.calculate_properties(
                smiles="CCO",
                properties_data={
                    "LogP": {"value": 50, "units": ""}  # OUT OF RANGE
                },
            )

    def test_calculate_properties_with_empty_data(self, experimental_provider):
        """
        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     properties_data={}
        ... )
        >>> assert result == {}
        """
        result = experimental_provider.calculate_properties(
            smiles="CCO", properties_data={}
        )

        assert result == {}


# ============================================================================
# PROVIDER REGISTRY TESTS
# ============================================================================


class TestProviderRegistry:
    """Test registro de providers en Factory."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry for testing."""
        return PropertyProviderRegistry()

    def test_register_custom_provider(self, registry):
        """
        >>> registry = PropertyProviderRegistry()
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> # Registrar provider
        >>> registry.register("experimental", provider)
        >>>
        >>> # Verificar que está registrado
        >>> assert registry.get_provider("experimental") is provider
        """
        provider = ExperimentalPropertyProvider()

        registry.register("experimental", provider)

        retrieved = registry.get_provider("experimental")
        assert retrieved is provider

    def test_list_registered_providers(self, registry):
        """
        >>> registry.register("experimental", ExperimentalPropertyProvider())
        >>> registry.register("rdkit", RDKitProvider())
        >>>
        >>> providers = registry.list_providers()
        >>> assert "experimental" in providers
        >>> assert "rdkit" in providers
        """
        exp_provider = ExperimentalPropertyProvider()
        registry.register("experimental", exp_provider)

        providers = registry.list_providers()
        assert "experimental" in providers

    def test_get_providers_for_category(self, registry):
        """
        >>> registry.register("experimental", ExperimentalPropertyProvider())
        >>>
        >>> # Get providers que soportan categoría "manual"
        >>> providers = registry.get_providers_for_category("experimental")
        >>>
        >>> assert "experimental" in providers
        """
        exp_provider = ExperimentalPropertyProvider()
        registry.register("experimental", exp_provider)

        # Custom provider soporta ["manual", "experimental"]
        providers = registry.get_providers_for_category("experimental")

        assert "experimental" in providers

    def test_duplicate_registration_overrides(self, registry):
        """
        >>> provider1 = ExperimentalPropertyProvider()
        >>> provider2 = ExperimentalPropertyProvider()
        >>>
        >>> registry.register("exp", provider1)
        >>> registry.register("exp", provider2)  # Overrides
        >>>
        >>> assert registry.get_provider("exp") is provider2
        """
        provider1 = ExperimentalPropertyProvider()
        provider2 = ExperimentalPropertyProvider()

        registry.register("exp", provider1)
        registry.register("exp", provider2)

        retrieved = registry.get_provider("exp")
        assert retrieved is provider2


# ============================================================================
# PROVIDER FACTORY TESTS
# ============================================================================


class TestProviderFactory:
    """Test Factory para obtener providers."""

    @pytest.fixture
    def factory(self):
        """Create factory with test registry."""
        factory = PropertyProviderFactory()
        factory._registry = PropertyProviderRegistry()
        return factory

    def test_get_provider_from_factory(self, factory):
        """
        >>> factory = PropertyProviderFactory()
        >>> factory._registry.register(
        ...     "experimental",
        ...     ExperimentalPropertyProvider()
        ... )
        >>>
        >>> provider = factory.get_provider("experimental")
        >>> assert isinstance(provider, ExperimentalPropertyProvider)
        """
        exp_provider = ExperimentalPropertyProvider()
        factory._registry.register("experimental", exp_provider)

        retrieved = factory.get_provider("experimental")
        assert retrieved is exp_provider

    def test_get_provider_not_found(self, factory):
        """
        >>> with pytest.raises(ValueError):
        ...     factory.get_provider("nonexistent")
        """
        with pytest.raises(ValueError):
            factory.get_provider("nonexistent")


# ============================================================================
# EXTENSION PATTERN TESTS
# ============================================================================


class TestExtensionPatterns:
    """Test patrones recomendados para extender."""

    def test_template_method_pattern(self):
        """
        >>> # AbstractPropertyProvider usa Template Method
        >>> # Subclases solo implementan _calculate_properties_impl
        >>>
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> # calculate_properties (Template Method) llama a:
        >>> # 1. _initialize_metadata
        >>> # 2. _initialize_properties
        >>> # 3. _calculate_properties_impl
        >>>
        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     properties_data={"MolWt": {"value": 46.07}}
        ... )
        """
        provider = ExperimentalPropertyProvider()

        result = provider.calculate_properties(
            smiles="CCO", properties_data={"MolWt": {"value": 46.07, "units": "g/mol"}}
        )

        assert "MolWt" in result
        assert result["MolWt"]["value"] == 46.07

    def test_adapter_pattern(self):
        """
        >>> # Custom provider adapta datos arbitrarios al interfaz estándar
        >>>
        >>> provider = ExperimentalPropertyProvider()
        >>> provider.get_metadata()  # Interfaz estándar
        >>> provider.get_properties()  # Interfaz estándar
        >>> provider.calculate_properties(...)  # Interfaz estándar
        >>>
        >>> # Pero internamente adapta datos experimentales
        """
        provider = ExperimentalPropertyProvider()

        # Interfaz uniforme
        info = provider.get_metadata()
        props = provider.get_properties()

        assert info.name == "experimental"
        assert "MolWt" in props

    def test_dependency_injection_in_factory(self):
        """
        >>> # Factory usa dependency injection para providers
        >>>
        >>> registry = PropertyProviderRegistry()
        >>> registry.register("experimental", ExperimentalPropertyProvider())
        >>>
        >>> factory = PropertyProviderFactory(registry=registry)
        >>>
        >>> provider = factory.get_provider("experimental")
        >>> # Provider viene de registry inyectado
        """
        registry = PropertyProviderRegistry()
        registry.register("experimental", ExperimentalPropertyProvider())

        factory = PropertyProviderFactory(registry=registry)

        provider = factory.get_provider("experimental")
        assert isinstance(provider, ExperimentalPropertyProvider)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test manejo de errores en providers."""

    def test_provider_validation_error(self):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> # Valor fuera de rango
        >>> with pytest.raises(ValueError):
        ...     provider.calculate_properties(
        ...         smiles="CCO",
        ...         properties_data={
        ...             "MolWt": {"value": -10, "units": "g/mol"}
        ...         }
        ...     )
        """
        provider = ExperimentalPropertyProvider()

        # MolWt tiene range_min=0
        with pytest.raises(ValueError):
            provider.calculate_properties(
                smiles="CCO",
                properties_data={"MolWt": {"value": -10, "units": "g/mol"}},
            )

    def test_provider_with_unknown_property(self):
        """
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     properties_data={
        ...         "UnknownProperty": {"value": 123}
        ...     }
        ... )
        >>>
        >>> # Unknown properties se ignoran
        >>> assert "UnknownProperty" not in result
        """
        provider = ExperimentalPropertyProvider()

        result = provider.calculate_properties(
            smiles="CCO", properties_data={"UnknownProperty": {"value": 123}}
        )

        # Unknown property ignored
        assert "UnknownProperty" not in result
        assert result == {}


# ============================================================================
# INTEGRATION WITH MODELS/SERVICES TESTS
# ============================================================================


class TestProviderIntegrationWithServices:
    """Test integración de custom provider con servicios."""

    def test_custom_provider_with_molecule_model(self):
        """
        >>> # Custom provider trabaja con Molecule model
        >>> # (en un test real, usaría DB)
        >>>
        >>> from chemistry.models import Molecule, MolecularProperty
        >>>
        >>> provider = ExperimentalPropertyProvider()
        >>>
        >>> # Simulado (sin DB):
        >>> result = provider.calculate_properties(
        ...     smiles="CCO",
        ...     properties_data={
        ...         "MolWt": {"value": 46.07, "units": "g/mol"}
        ...     }
        ... )
        >>>
        >>> # Estos datos se guardarían en MolecularProperty
        >>> # con source="experimental", method="user_input"
        """
        provider = ExperimentalPropertyProvider()

        result = provider.calculate_properties(
            smiles="CCO", properties_data={"MolWt": {"value": 46.07, "units": "g/mol"}}
        )

        # Data structure is correct for saving to MolecularProperty
        assert result["MolWt"]["source"] == "experimental"
        assert result["MolWt"]["method"] == "user_input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
