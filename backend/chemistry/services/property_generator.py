"""
Servicio unificado de generación de propiedades para familias moleculares.

Este módulo proporciona un sistema flexible y agnóstico al proveedor para generar
propiedades moleculares siguiendo arquitectura hexagonal e inyección de dependencias.

Motivación y objetivos:
- Aislar la lógica de negocio (servicio) de los adaptadores (proveedores) para permitir sustitución segura.
- Facilitar pruebas con inyección de dependencias (inyectar registry/proveedores falsos).
- Garantizar consistencia en la persistencia (modelo EAV) y trazabilidad vía metadata.
- Preparar integración con flujos (Flow): opcionalmente incluir `flow_id` en metadata para acoplar resultados.

English summary:
Unified property generation service for molecular families.

This module provides a flexible, provider-agnostic system for generating
molecular properties following hexagonal architecture and dependency injection.

Architecture (Hexagonal/Ports & Adapters):
- Port (Interface): PropertyProviderInterface defines the contract
- Adapters: RDKitProvider, ManualProvider, RandomProvider implement the interface
- Core Service: generate_properties_for_family (this module) orchestrates the flow
- Registry: Provides DI for provider instances

Key Features:
- Multiple property categories (ADMETSA, physics, pharmacodynamic, etc.)
- Multiple providers (RDKit, manual, external sources)
- Metadata support (global and per-molecule)
- Preview mode (calculate without saving)
- Dependency Injection via registry parameter

SOLID Principles Applied:
- SRP: Service only orchestrates, providers handle calculation
- OCP: New providers can be added without modifying this service
- LSP: All providers are interchangeable through interface
- ISP: Minimal interface with only required methods
- DIP: Depends on PropertyProviderInterface abstraction

Examples:
    >>> # Using default registry
    >>> result = generate_properties_for_family(
    ...     family_id=5,
    ...     category="admetsa",
    ...     provider="rdkit",
    ...     persist=True,
    ...     metadata={"experiment_id": "EXP-001"},
    ...     created_by=user
    ... )

    >>> # With custom registry (DI for testing)
    >>> from chemistry.providers import PropertyProviderRegistry
    >>> custom_registry = PropertyProviderRegistry()
    >>> result = generate_properties_for_family(
    ...     family_id=5,
    ...     category="admetsa",
    ...     provider="rdkit",
    ...     provider_registry=custom_registry,
    ...     created_by=user
    ... )
"""

# mypy: disable-error-code="attr-defined"

import logging
from typing import Any, Dict, List, Optional

from ..models import Family, FamilyMember, FamilyProperty, MolecularProperty
from ..providers import registry as default_registry
from ..providers.interfaces import PropertyProviderInterface
from ..types import PropertyGenerationResult

logger = logging.getLogger(__name__)


# Common, public list of ADMETSA property names used across services/flows
ADMETSA_PROPERTIES: List[str] = ["MolWt", "LogP", "TPSA", "HBA", "HBD", "RB"]


def generate_properties_for_family(
    *,
    family_id: int,
    category: str,
    provider: str,
    persist: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
    per_molecule_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
    properties_data: Optional[Dict[int, Dict[str, str]]] = None,
    created_by: Any = None,
    provider_registry: Any = None,
) -> PropertyGenerationResult:
    """Generate properties for all molecules in a family.

    This is the main entry point for the property generation system following
    hexagonal architecture with dependency injection.

    Architecture Flow:
        1. Validate inputs
        2. Retrieve provider from registry (Port/Adapter pattern)
        3. For each molecule: calculate properties via provider interface
        4. Optionally persist to database
        5. Return structured result

    Args:
        family_id: ID of the family to generate properties for
        category: Property category (admetsa, physics, pharmacodynamic, etc.)
        provider: Provider name (rdkit, manual, random, etc.)
        persist: If True, save properties to database. If False, return preview only
        metadata: Global metadata applied to all molecules (optional)
        per_molecule_metadata: Metadata specific to each molecule {mol_id: {key: value}} (optional)
        properties_data: Pre-calculated properties (required for provider="manual")
        created_by: User initiating the generation (required if persist=True)
        provider_registry: Provider registry instance (DI for testing, uses default if None)

    Returns:
        Dictionary containing:
        - family_id: ID of the family
        - category: Property category used
        - provider: Provider used
        - persisted: Whether properties were saved
        - properties_created: Number of properties created (if persisted)
        - molecules: List of molecule results with properties

    Raises:
        ValueError: If invalid category/provider or missing required data
        KeyError: If provider not found in registry
        Exception: If property calculation fails

    Examples:
        >>> # Standard usage with default registry
        >>> result = generate_properties_for_family(
        ...     family_id=5,
        ...     category="admetsa",
        ...     provider="rdkit",
        ...     metadata={"experiment": "screening-2025"},
        ...     created_by=user
        ... )
        >>> print(result["properties_created"])
        42

        >>> # Dependency Injection for testing
        >>> mock_registry = PropertyProviderRegistry()
        >>> mock_registry.register("test", MockProvider())
        >>> result = generate_properties_for_family(
        ...     family_id=5,
        ...     category="admetsa",
        ...     provider="test",
        ...     provider_registry=mock_registry,
        ...     created_by=user
        ... )
    """
    # Use default registry if not provided (DI)
    if provider_registry is None:
        provider_registry = default_registry

    # Validate inputs
    if persist and created_by is None:
        raise ValueError("created_by is required when persist=True")

    # Get family and members
    try:
        family = Family.objects.get(pk=family_id)
    except Family.DoesNotExist:
        raise ValueError(f"Family with ID {family_id} does not exist")

    members = FamilyMember.objects.select_related("molecule").filter(family=family)

    if not members.exists():
        logger.warning(f"Family {family_id} has no molecules")
        return PropertyGenerationResult(
            family_id=family_id,
            category=category,
            provider=provider,
            persisted=persist,
            molecules=[],
            properties_created=0 if persist else None,
        )

    # Get provider instance from registry (Port/Adapter pattern)
    provider_instance: PropertyProviderInterface = provider_registry.get_provider(
        provider
    )

    # Validate provider supports category
    try:
        provider_instance.get_category_info(category)
    except ValueError as e:
        raise ValueError(
            f"Provider '{provider}' does not support category '{category}'. {e}"
        )

    # Early validation for providers that require external data (e.g., manual)
    provider_info = provider_instance.get_info()
    if provider_info.requires_external_data and properties_data is None:
        raise ValueError(
            f"properties_data is required for provider '{provider_info.name}'"
        )

    # Initialize metadata defaults
    metadata = metadata or {}
    per_molecule_metadata = per_molecule_metadata or {}

    # Generate properties for each molecule
    results: List[Dict[str, Any]] = []
    properties_created = 0

    for member in members:
        molecule = member.molecule
        smiles = molecule.canonical_smiles or molecule.smiles

        try:
            # Calculate or retrieve properties based on provider
            if provider_info.requires_external_data:
                # Manual-like providers use pre-calculated data supplied by caller
                props_dict = provider_instance.calculate_properties(
                    smiles,
                    category,
                    properties_data=properties_data,
                    molecule_id=molecule.id,
                )
            else:
                # Computational providers calculate from SMILES
                props_dict = provider_instance.calculate_properties(smiles, category)

            # Merge metadata: global + per-molecule
            molecule_metadata = dict(metadata)
            if molecule.id in per_molecule_metadata:
                molecule_metadata.update(per_molecule_metadata[molecule.id])

            # Add category to metadata for tracking
            molecule_metadata["category"] = category

            # Save to database if persist=True
            if persist:
                for prop_key, prop_value in props_dict.items():
                    # Extraer valor y metadatos estandarizados si el provider devuelve estructura enriquecida
                    if isinstance(prop_value, dict) and "value" in prop_value:
                        _val = prop_value.get("value")
                        _units = str(prop_value.get("units", ""))
                        _method = str(prop_value.get("method", provider.lower()))
                        _source = str(prop_value.get("source", f"provider:{provider}"))
                    else:
                        _val = prop_value
                        _units = ""
                        _method = provider.lower()
                        _source = f"provider:{provider}"

                    MolecularProperty.objects.update_or_create(
                        molecule=molecule,
                        property_type=prop_key,
                        method=_method,
                        relation=f"endpoint /generate-properties/{category}/{provider}",
                        source_id=_source,
                        defaults={
                            "value": str(_val),
                            "is_invariant": False,
                            "units": _units,
                            "metadata": molecule_metadata,
                            "created_by": created_by,
                        },
                    )
                    properties_created += 1

            # Build result for this molecule
            molecule_result = {
                "molecule_id": molecule.id,
                "properties": props_dict,
            }

            # Include metadata in response if provided
            if molecule_metadata:
                molecule_result["metadata"] = molecule_metadata

            results.append(molecule_result)

        except Exception as e:
            logger.error(
                f"Failed to generate properties for molecule {molecule.id}: {e}"
            )
            results.append(
                {
                    "molecule_id": molecule.id,
                    "properties": {},
                    "error": str(e),
                }
            )

    # Build final result
    return PropertyGenerationResult(
        family_id=family.id,
        category=category,
        provider=provider,
        persisted=persist,
        molecules=results,
        properties_created=properties_created if persist else None,
    )


def preview_properties_for_family(
    *,
    family_id: int,
    category: str,
    provider: str,
    metadata: Optional[Dict[str, Any]] = None,
    per_molecule_metadata: Optional[Dict[int, Dict[str, Any]]] = None,
    properties_data: Optional[Dict[int, Dict[str, str]]] = None,
) -> PropertyGenerationResult:
    """Preview property generation without persisting to database.

        This is a convenience wrapper around generate_properties_for_family()
        that always operates in preview mode (persist=False). Useful for:
        - Validating input data before saving
        - Testing different providers/categories
        - Exploring property values without committing

        Args:
            family_id: ID of the family
            category: Property category
            provider: Provider name
            metadata: Global metadata (optional)
            per_molecule_metadata: Per-molecule metadata (optional)
            properties_data: Pre-calculated properties for manual provider (optional)
        Returns:
            Dictionary with preview results (persisted=False)

    Examples:
            >>> # Preview RDKit calculations
            >>> preview = preview_properties_for_family(
            ...     family_id=5,
            ...     category="admetsa",
            ...     provider="rdkit"
            ... )
            >>>
            >>> # Check results before deciding to persist
            >>> if all(m.get("properties") for m in preview["molecules"]):
            ...     # Looks good, now persist
            ...     result = generate_properties_for_family(
            ...         family_id=5,
            ...         category="admetsa",
            ...         provider="rdkit",
            ...         persist=True,
            ...         created_by=user
            ...     )
    """
    return generate_properties_for_family(
        family_id=family_id,
        category=category,
        provider=provider,
        persist=False,
        metadata=metadata,
        per_molecule_metadata=per_molecule_metadata,
        properties_data=properties_data,
        created_by=None,  # Not needed for preview
    )


def generate_admetsa_for_family(*, family_id: int, created_by: Any) -> Dict[str, Any]:
    """Ensure ADMETSA properties exist for all family molecules and return a summary.

    Returns a dict suitable for flows step consumption:
        {"family_id": int, "count": int, "molecules": [{molecule_id, properties}...]}
    """
    result = generate_properties_for_family(
        family_id=family_id,
        category="admetsa",
        provider="rdkit",
        persist=True,
        created_by=created_by,
    )
    # Normalize to dict for flow compatibility
    summary = {
        "family_id": result.family_id,
        "count": len(result.molecules),
        "molecules": result.molecules,
    }
    return summary


def generate_admetsa_properties_for_family(
    *, family_id: int, created_by: Any
) -> Dict[str, Any]:
    """Alias kept for backward compatibility used by flows ChemistryAdapter."""
    return generate_admetsa_for_family(family_id=family_id, created_by=created_by)


def compute_family_admetsa_aggregates(
    *, family_id: int, created_by: Any, method: str | None = None
) -> Dict[str, Any]:
    """Compute and persist ADMETSA aggregates (mean) at family level.

    - Aggregates are stored as FamilyProperty with property_type 'ADMETSA.avg.<Prop>'.
    - Returns a dict with {family_id, count, aggregates}.
    """
    if not created_by:
        raise ValueError("created_by is required")

    try:
        family = Family.objects.get(pk=family_id)
    except Family.DoesNotExist:
        raise ValueError(f"Family with ID {family_id} does not exist")

    member_ids = list(
        FamilyMember.objects.filter(family=family).values_list("molecule_id", flat=True)
    )
    # Collect values per property
    values: Dict[str, List[float]] = {k: [] for k in ADMETSA_PROPERTIES}
    if member_ids:
        for mp in MolecularProperty.objects.filter(
            molecule_id__in=member_ids, property_type__in=ADMETSA_PROPERTIES
        ):
            try:
                v = float(mp.value)
            except (ValueError, TypeError):
                continue
            values.get(mp.property_type, []).append(v)

    from statistics import mean

    aggregates: Dict[str, float] = {}
    for prop_name, arr in values.items():
        if arr:
            aggregates[prop_name] = float(mean(arr))

    # Persist as FamilyProperty records
    saved = 0
    store_method = method or "flows.family_aggregates"
    for prop, val in aggregates.items():
        _, created = FamilyProperty.objects.update_or_create(
            family=family,
            property_type=f"ADMETSA.avg.{prop}",
            method=store_method,
            relation="endpoint",
            source_id="aggregate:mean",
            defaults={
                "value": f"{val}",
                "is_invariant": False,
                "units": "",
                "metadata": {"category": "admetsa"},
                "created_by": created_by,
            },
        )
        if created:
            saved += 1

    return {"family_id": family.id, "count": saved, "aggregates": aggregates}
