"""
Property calculation providers for the property generation system.

This module implements concrete property providers following SOLID principles
and hexagonal architecture.

All providers inherit from AbstractPropertyProvider and implement the required
interface contract defined in interfaces.py.

Architecture:
- Each provider is an Adapter in the hexagonal architecture
- PropertyProviderInterface is the Port (interface)
- AbstractPropertyProvider provides Template Method pattern

Design Patterns:
- Template Method: AbstractPropertyProvider defines algorithm structure
- Strategy: Different providers = different calculation strategies
- Factory: Created and managed by PropertyProviderFactory
"""

import logging
import random
from typing import Dict

from .. import providers as chem_providers
from ..types import MolecularProperties
from .interfaces import (
    AbstractPropertyProvider,
    PropertyCategoryInfo,
    PropertyInfo,
    PropertyProviderInfo,
)

logger = logging.getLogger(__name__)


# ========== Property Definitions by Category ==========


def create_admetsa_properties() -> list[PropertyInfo]:
    """Create PropertyInfo objects for ADMETSA category."""
    return [
        PropertyInfo(
            name="MolWt",
            description="Molecular Weight",
            units="g/mol",
            value_type="float",
            range_min=0.0,
            range_max=2000.0,
        ),
        PropertyInfo(
            name="LogP",
            description="Partition Coefficient (octanol-water)",
            units="dimensionless",
            value_type="float",
            range_min=-5.0,
            range_max=10.0,
        ),
        PropertyInfo(
            name="TPSA",
            description="Topological Polar Surface Area",
            units="Ų",
            value_type="float",
            range_min=0.0,
            range_max=300.0,
        ),
        PropertyInfo(
            name="HBA",
            description="Hydrogen Bond Acceptors",
            units="count",
            value_type="int",
            range_min=0.0,
            range_max=30.0,
        ),
        PropertyInfo(
            name="HBD",
            description="Hydrogen Bond Donors",
            units="count",
            value_type="int",
            range_min=0.0,
            range_max=20.0,
        ),
        PropertyInfo(
            name="RB",
            description="Rotatable Bonds",
            units="count",
            value_type="int",
            range_min=0.0,
            range_max=50.0,
        ),
    ]


def create_admet_properties() -> list[PropertyInfo]:
    """Create PropertyInfo objects for ADMET category (extended)."""
    props = create_admetsa_properties()
    props.extend(
        [
            PropertyInfo(
                name="LD50",
                description="Median Lethal Dose",
                units="mg/kg",
                value_type="float",
                range_min=0.0,
                range_max=10000.0,
            ),
            PropertyInfo(
                name="Mutagenicity",
                description="Mutagenicity Score",
                units="probability",
                value_type="float",
                range_min=0.0,
                range_max=1.0,
            ),
            PropertyInfo(
                name="DevelopmentalToxicity",
                description="Developmental Toxicity Score",
                units="probability",
                value_type="float",
                range_min=0.0,
                range_max=1.0,
            ),
            PropertyInfo(
                name="SyntheticAccessibility",
                description="Synthetic Accessibility Score",
                units="score",
                value_type="float",
                range_min=1.0,
                range_max=10.0,
            ),
        ]
    )
    return props


def create_physics_properties() -> list[PropertyInfo]:
    """Create PropertyInfo objects for physics category."""
    return [
        PropertyInfo(
            name="MolWt",
            description="Molecular Weight",
            units="g/mol",
            value_type="float",
            range_min=0.0,
            range_max=2000.0,
        ),
        PropertyInfo(
            name="LogP",
            description="Partition Coefficient",
            units="dimensionless",
            value_type="float",
            range_min=-5.0,
            range_max=10.0,
        ),
        PropertyInfo(
            name="TPSA",
            description="Topological Polar Surface Area",
            units="Ų",
            value_type="float",
            range_min=0.0,
            range_max=300.0,
        ),
        PropertyInfo(
            name="MR",
            description="Molar Refractivity",
            units="cm³/mol",
            value_type="float",
            range_min=0.0,
            range_max=300.0,
        ),
        PropertyInfo(
            name="AtX",
            description="Atom Count",
            units="count",
            value_type="int",
            range_min=1.0,
            range_max=200.0,
        ),
    ]


def create_pharmacodynamic_properties() -> list[PropertyInfo]:
    """Create PropertyInfo objects for pharmacodynamic category."""
    return [
        PropertyInfo(
            name="LogP",
            description="Partition Coefficient",
            units="dimensionless",
            value_type="float",
            range_min=-5.0,
            range_max=10.0,
        ),
        PropertyInfo(
            name="HBA",
            description="Hydrogen Bond Acceptors",
            units="count",
            value_type="int",
            range_min=0.0,
            range_max=30.0,
        ),
        PropertyInfo(
            name="HBD",
            description="Hydrogen Bond Donors",
            units="count",
            value_type="int",
            range_min=0.0,
            range_max=20.0,
        ),
        PropertyInfo(
            name="TPSA",
            description="Topological Polar Surface Area",
            units="Ų",
            value_type="float",
            range_min=0.0,
            range_max=300.0,
        ),
        PropertyInfo(
            name="SyntheticAccessibility",
            description="Synthetic Accessibility Score",
            units="score",
            value_type="float",
            range_min=1.0,
            range_max=10.0,
        ),
    ]


# ========== RDKit Provider ==========


class RDKitProvider(AbstractPropertyProvider):
    """Calculate molecular properties using RDKit.

    This provider uses the RDKit chemistry engine to compute properties
    from SMILES strings. It's a computational provider that doesn't require
    external data.

    Adapter Pattern: Adapts RDKit engine to PropertyProviderInterface

    Supported Categories:
        - admetsa: Basic ADMET properties
        - admet: Extended ADMET properties
        - physics: Physical properties
        - pharmacodynamic: Pharmacodynamic properties

    Examples:
        >>> provider = RDKitProvider()
        >>> info = provider.get_info()
        >>> print(info.display_name)
        'RDKit Computational'
        >>>
        >>> props = provider.calculate_properties("CCO", "admetsa")
        >>> print(props["MolWt"])
        '46.07'
    """

    def _initialize_metadata(self) -> None:
        """Initialize RDKit provider metadata."""
        # Provider info
        self._provider_info = PropertyProviderInfo(
            name="rdkit",
            display_name="RDKit Computational",
            description="Calculate properties computationally using RDKit chemistry library",
            supported_categories=["admetsa", "admet", "physics", "pharmacodynamic"],
            requires_external_data=False,
            is_computational=True,
        )

        # Category definitions
        self._category_definitions = {
            "admetsa": PropertyCategoryInfo(
                name="admetsa",
                display_name="ADMET-SA (Basic)",
                description="Basic ADMET properties: MolWt, LogP, TPSA, HBA, HBD, RB",
                properties=create_admetsa_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "admet": PropertyCategoryInfo(
                name="admet",
                display_name="ADMET (Extended)",
                description="Extended ADMET properties including toxicity predictions",
                properties=create_admet_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "physics": PropertyCategoryInfo(
                name="physics",
                display_name="Physical Properties",
                description="Physical and chemical properties: MolWt, LogP, TPSA, MR, AtX",
                properties=create_physics_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "pharmacodynamic": PropertyCategoryInfo(
                name="pharmacodynamic",
                display_name="Pharmacodynamic Properties",
                description="Properties relevant to drug-target interactions",
                properties=create_pharmacodynamic_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
        }

    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Calculate properties using RDKit engine.

        Args:
            smiles: SMILES string
            category: Property category
            **kwargs: Additional arguments (unused)

        Returns:
            Dictionary of property name -> string value

        Raises:
            Exception: If RDKit calculation fails
        """
        # Get property names for this category
        category_info = self.get_category_info(category)
        property_names = [prop.name for prop in category_info.properties]

        # Use strongly typed RDKit provider
        properties: MolecularProperties = chem_providers.engine.calculate_properties(
            smiles, return_dataclass=True
        )
        props_dict = properties.to_dict()

        # Filter to only properties defined for this category
        result = {}
        for prop_key in property_names:
            prop_value = props_dict.get(prop_key)
            if prop_value is not None:
                result[prop_key] = str(prop_value)

        return result


# ========== Manual Provider ==========


class ManualProvider(AbstractPropertyProvider):
    """Use user-provided property values.

    This provider retrieves pre-calculated properties from a data dictionary
    provided by the user. It's NOT computational - values must be supplied.

    Use Cases:
        - Importing external lab data
        - Manual measurements
        - Migrating data from other systems

    Required kwargs:
        - properties_data: Dict[int, Dict[str, str]] mapping molecule_id to properties
        - molecule_id: int identifying which molecule to get properties for

    Examples:
        >>> provider = ManualProvider()
        >>> data = {8: {"MolWt": "180.16", "LogP": "2.45"}}
        >>> props = provider.calculate_properties(
        ...     smiles="unused",
        ...     category="admetsa",
        ...     properties_data=data,
        ...     molecule_id=8
        ... )
        >>> print(props["MolWt"])
        '180.16'
    """

    def _initialize_metadata(self) -> None:
        """Initialize Manual provider metadata."""
        self._provider_info = PropertyProviderInfo(
            name="manual",
            display_name="Manual Input",
            description="User-provided property values from external sources",
            supported_categories=["admetsa", "admet", "physics", "pharmacodynamic"],
            requires_external_data=True,
            is_computational=False,
        )

        # Use same category definitions as RDKit
        self._category_definitions = {
            "admetsa": PropertyCategoryInfo(
                name="admetsa",
                display_name="ADMET-SA (Basic)",
                description="Basic ADMET properties provided by user",
                properties=create_admetsa_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "admet": PropertyCategoryInfo(
                name="admet",
                display_name="ADMET (Extended)",
                description="Extended ADMET properties provided by user",
                properties=create_admet_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "physics": PropertyCategoryInfo(
                name="physics",
                display_name="Physical Properties",
                description="Physical properties provided by user",
                properties=create_physics_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "pharmacodynamic": PropertyCategoryInfo(
                name="pharmacodynamic",
                display_name="Pharmacodynamic Properties",
                description="Pharmacodynamic properties provided by user",
                properties=create_pharmacodynamic_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
        }

    def validate_input(self, category: str, **kwargs) -> None:
        """Validate manual provider requires properties_data and molecule_id."""
        super().validate_input(category, **kwargs)

        if "properties_data" not in kwargs:
            raise ValueError(
                "Manual provider requires 'properties_data' parameter: "
                "Dict[int, Dict[str, str]] mapping molecule IDs to properties"
            )

        if "molecule_id" not in kwargs:
            raise ValueError(
                "Manual provider requires 'molecule_id' parameter: "
                "int identifying which molecule to retrieve"
            )

        properties_data = kwargs["properties_data"]
        molecule_id = kwargs["molecule_id"]

        if not isinstance(properties_data, dict):
            raise ValueError("properties_data must be a dictionary")

        if molecule_id not in properties_data:
            raise KeyError(
                f"No property data provided for molecule {molecule_id}. "
                f"Available molecules: {list(properties_data.keys())}"
            )

    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Retrieve pre-calculated properties.

        Note: SMILES is ignored for manual provider since values are pre-calculated.

        Args:
            smiles: SMILES string (not used)
            category: Property category
            **kwargs: Must include 'properties_data' and 'molecule_id'

        Returns:
            Dictionary of property name -> string value
        """
        properties_data = kwargs["properties_data"]
        molecule_id = kwargs["molecule_id"]

        return properties_data[molecule_id]


# ========== Random Provider ==========


class RandomProvider(AbstractPropertyProvider):
    """Generate random property values for testing.

    This provider generates randomized but realistic-looking values within
    appropriate ranges for each property. Useful for:
    - Development and testing
    - Generating mock data
    - Demonstrating the system

    ⚠️ WARNING: Values are RANDOM and should NOT be used for real chemistry work!

    Optional kwargs:
        - seed: int for reproducible random values

    Examples:
        >>> provider = RandomProvider()
        >>> props = provider.calculate_properties("CCO", "admetsa", seed=42)
        >>> # Returns consistent random values due to seed
    """

    def _initialize_metadata(self) -> None:
        """Initialize Random provider metadata."""
        self._provider_info = PropertyProviderInfo(
            name="random",
            display_name="Random Generator (Testing)",
            description="Generate random property values for testing and development",
            supported_categories=["admetsa", "admet", "physics", "pharmacodynamic"],
            requires_external_data=False,
            is_computational=True,
        )

        # Use same category definitions
        self._category_definitions = {
            "admetsa": PropertyCategoryInfo(
                name="admetsa",
                display_name="ADMET-SA (Random)",
                description="Randomly generated ADMET properties for testing",
                properties=create_admetsa_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "admet": PropertyCategoryInfo(
                name="admet",
                display_name="ADMET (Random)",
                description="Randomly generated extended ADMET properties",
                properties=create_admet_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "physics": PropertyCategoryInfo(
                name="physics",
                display_name="Physical Properties (Random)",
                description="Randomly generated physical properties",
                properties=create_physics_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
            "pharmacodynamic": PropertyCategoryInfo(
                name="pharmacodynamic",
                display_name="Pharmacodynamic (Random)",
                description="Randomly generated pharmacodynamic properties",
                properties=create_pharmacodynamic_properties(),
                available_providers=["rdkit", "manual", "random"],
            ),
        }

    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Generate random property values.

        Args:
            smiles: SMILES string (used for logging only)
            category: Property category
            **kwargs: Optional 'seed' for reproducible random

        Returns:
            Dictionary of property name -> random string value
        """
        # Get seed if provided
        seed = kwargs.get("seed")
        rng = random.Random(seed)

        # Get properties for this category
        category_info = self.get_category_info(category)

        result = {}
        for prop_info in category_info.properties:
            min_val = prop_info.range_min or 0.0
            max_val = prop_info.range_max or 100.0

            value = rng.uniform(min_val, max_val)

            # Format based on value type
            if prop_info.value_type == "int":
                result[prop_info.name] = str(int(value))
            else:
                result[prop_info.name] = f"{value:.2f}"

        return result
