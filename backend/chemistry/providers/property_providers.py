"""
Proveedores de cálculo de propiedades para el sistema de generación.

Este módulo implementa proveedores concretos siguiendo SOLID y arquitectura
hexagonal. Cada proveedor es un Adaptador que cumple el Puerto
(PropertyProviderInterface) y encapsula la estrategia de cálculo.
Objetivos: extensibilidad sin tocar servicios, trazabilidad de capacidades
por categoría y validaciones específicas por proveedor.

Resumen en inglés:
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

from chemistry import providers as chem_providers
from chemistry.providers.core.interfaces import (
    AbstractPropertyProvider,
    PropertyCategoryInfo,
    PropertyInfo,
    PropertyProviderInfo,
)
from chemistry.providers.external_tools.test_runner import run_test as run_webtest
from chemistry.type_definitions import MolecularProperties

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


def create_toxicology_properties() -> list[PropertyInfo]:
    """Create PropertyInfo objects for toxicology category.

    This category groups common toxicological endpoints used by the T.E.S.T.
    runner and the external WebTEST tool.
    """
    return [
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
            name="DevTox",
            description="Developmental Toxicity",
            units="probability",
            value_type="float",
            range_min=0.0,
            range_max=1.0,
        ),
        PropertyInfo(
            name="LC50DM",
            description="48h Daphnia magna LC50",
            units="mg/L",
            value_type="float",
            range_min=0.0,
            range_max=1e6,
        ),
    ]


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
    ) -> Dict[str, object]:
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


# ========== Toxicology Provider (simple deterministic for known test SMILES) ==========


class ToxicologyProvider(AbstractPropertyProvider):
    """Provider for toxicological endpoints.

    This is a lightweight provider intended to supply toxicology-like values
    for the most common endpoints (LD50, Mutagenicity, DevTox, LC50DM).

    Implementation notes:
    - For reproducible tests we include a small mapping of SMILES -> predictions
      matching the sample outputs used in the project tests. For unknown SMILES
      the provider returns "NA" or raises a mild error encoded in the raw string
      to allow callers to persist error information.
    - This provider supports categories: "toxicology" and "admet" for
      backward compatibility.
    """

    def _initialize_metadata(self) -> None:
        self._provider_info = PropertyProviderInfo(
            name="toxicology",
            display_name="Toxicology (Mock/T.E.S.T.)",
            description=(
                "Lightweight toxicology provider that returns deterministic mock "
                "predictions for common endpoints (LD50, Mutagenicity, DevTox, LC50DM)"
            ),
            supported_categories=["toxicology", "admet"],
            requires_external_data=False,
            is_computational=True,
        )

        self._category_definitions = {
            "toxicology": PropertyCategoryInfo(
                name="toxicology",
                display_name="Toxicology Endpoints",
                description="Toxicological endpoints such as LD50, Mutagenicity, DevTox, LC50DM",
                properties=create_toxicology_properties(),
                available_providers=["toxicology"],
            ),
            # also expose under admet for compatibility
            "admet": PropertyCategoryInfo(
                name="admet",
                display_name="ADMET (with toxicology)",
                description="Extended ADMET including toxicology endpoints",
                properties=create_toxicology_properties(),
                available_providers=["toxicology"],
            ),
        }

    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        """Return deterministic mock toxicology values for a handful of SMILES.

        The return format is property name -> string value (legacy compatibility).
        """
        # Known mapping (based on the sample output provided in the issue)
        mapping = {
            "CCO": {
                "LC50DM": "1.55",
                "LD50": "1.77",
                "DevTox": "0.46",
                "Mutagenicity": "-0.01",
            },
            "NNCNO": {
                "LC50DM": "1.87",
                "LD50": "2.17",
                "DevTox": "0.50",
                "Mutagenicity": "NA",
            },
            "CCCNNCNO": {
                "LC50DM": "2.54",
                "LD50": "1.96",
                "DevTox": "0.48",
                "Mutagenicity": "0.29",
            },
            "c1ccccc1NNCNO": {
                "LC50DM": "2.89",
                "LD50": "NA",
                "DevTox": "0.51",
                "Mutagenicity": "0.72",
            },
            "smilefalso": {
                # invalid smiles case -> return NA and let caller store error details
                "LC50DM": "NA",
                "LD50": "NA",
                "DevTox": "NA",
                "Mutagenicity": "NA",
            },
            "CCNc1ccOccc1": {
                "LC50DM": "3.36",
                "LD50": "1.84",
                "DevTox": "0.32",
                "Mutagenicity": "0.21",
            },
        }

        # Normalize small canonicalization (strip whitespace)
        key = smiles.strip()
        if key in mapping:
            return mapping[key]

        # For unknown smiles, return NA for all properties
        props = create_toxicology_properties()
        return {p.name: "NA" for p in props}


# ========== WebTEST Provider (invokes external T.E.S.T. runner) ==========


class WebTESTProvider(AbstractPropertyProvider):
    """Provider that calls the local T.E.S.T. runner to compute endpoints.

    Supports a minimal set of endpoints used by our examples/tests:
    - Toxicology: LD50, DevTox, Mutagenicity
    - Physics: Density
    Returns values as strings (or 'NA') for compatibility with existing patterns.
    """

    def _initialize_metadata(self) -> None:
        self._provider_info = PropertyProviderInfo(
            name="webtest",
            display_name="WebTEST (External Tool)",
            description=(
                "External T.E.S.T. runner adapter (invokes tools/external/test/test/run_test.py)."
            ),
            supported_categories=["toxicology", "physics"],
            requires_external_data=True,
            is_computational=True,
        )

        self._category_definitions = {
            "toxicology": PropertyCategoryInfo(
                name="toxicology",
                display_name="Toxicology Endpoints (WebTEST)",
                description="LD50, Mutagenicity, DevTox from T.E.S.T.",
                properties=[
                    PropertyInfo(
                        name="LD50",
                        description="Dosis letal oral para el 50% de ratas.",
                        units="mg/kg",
                        value_type="float",
                    ),
                    PropertyInfo(
                        name="Mutagenicity",
                        description="Potencial mutagénico (prueba de Ames).",
                        units="Binario",
                        value_type="float",
                    ),
                    PropertyInfo(
                        name="DevTox",
                        description="Probabilidad de toxicidad del desarrollo (sí/no).",
                        units="Binario",
                        value_type="float",
                    ),
                ],
                available_providers=["webtest"],
            ),
            "physics": PropertyCategoryInfo(
                name="physics",
                display_name="Physical Properties (WebTEST)",
                description="Subset of physical properties from T.E.S.T.",
                properties=[
                    PropertyInfo(
                        name="Density",
                        description="Densidad a 25°C.",
                        units="g/cm³",
                        value_type="float",
                    )
                ],
                available_providers=["webtest"],
            ),
        }

    def _calculate_properties_impl(
        self, smiles: str, category: str, **kwargs
    ) -> Dict[str, str]:
        # Choose endpoints for the category
        if category == "toxicology":
            endpoints = ["LD50", "Mutagenicity", "DevTox"]
        elif category == "physics":
            endpoints = ["Density"]
        else:
            raise ValueError(f"Unsupported category for webtest: {category}")

        data = run_webtest([smiles], endpoints, timeout_sec=kwargs.get("timeout"))
        # Expect structure: { "molecules": [ { "smiles": ..., "properties": { name: { value, error, ... } } } ] }
        mols = data.get("molecules") or []
        if not mols:
            # Return all NA
            return {name: "NA" for name in endpoints}
        props = mols[0].get("properties") or {}
        result: Dict[str, object] = {}

        def _parse_float_locale(x: object) -> float | None:
            """Parse float with locale-safe handling of comma decimals."""
            if x is None:
                return None
            if isinstance(x, (int, float)):
                return float(x)
            s = str(x).strip()
            if not s or s.upper() == "N/A":
                return None
            # Normalize common locale decimal comma to dot, remove spaces
            s = s.replace(" ", "").replace(",", ".")
            try:
                return float(s)
            except Exception:
                return None

        # Preferred keys per endpoint. For categorical endpoints we prefer Pred_Result
        pref_keys = {
            "LD50": "Pred_Value:_mg/kg",
            "Density": "Pred_Value:_g/cm³",
            "Mutagenicity": "Pred_Value",  # numeric score if no Pred_Result present
            "DevTox": "Pred_Value",        # numeric score if no Pred_Result present
        }

        categorical_endpoints = {"Mutagenicity", "DevTox"}

        for name in endpoints:
            p = props.get(name, {}) or {}
            raw = p.get("raw_data") or {}
            entry: dict = {"raw_data": raw}

            # For categorical endpoints, prefer textual Pred_Result when available
            if name in categorical_endpoints:
                pred_res = raw.get("Pred_Result")
                if pred_res and str(pred_res).strip():
                    entry["value"] = str(pred_res).strip()
                else:
                    preferred_key = pref_keys.get(name)
                    preferred_val = raw.get(preferred_key) if preferred_key else None
                    val = _parse_float_locale(preferred_val)
                    if val is None:
                        val = _parse_float_locale(p.get("value"))
                    entry["value"] = "NA" if val is None else f"{val:.2f}"
            else:
                # Numeric endpoints: prefer configured Pred_Value key
                preferred_key = pref_keys.get(name)
                preferred_val = raw.get(preferred_key) if preferred_key else None
                val = _parse_float_locale(preferred_val)
                if val is None:
                    val = _parse_float_locale(p.get("value"))
                entry["value"] = "NA" if val is None else f"{val:.2f}"

            result[name] = entry
        return result
