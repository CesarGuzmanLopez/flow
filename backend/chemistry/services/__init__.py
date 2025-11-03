"""Public exports for chemistry services package.

This package re-exports the split, responsibility-oriented modules. At this
point the legacy monolith has been migrated and can be removed; the package
exposes explicit module exports to be the single source of truth.
"""

# Family services
from .family import (
    FamilyFrozenError,
    add_members_to_family,
    create_family_from_smiles,
    create_single_molecule_family,
    generate_substituted_family,
    rehydrate_family_properties,
    remove_members_from_family,
)

# Molecule services
from .molecule import (
    create_molecule_from_smiles,
    create_or_get_molecule,
    get_molecule_structure_info,
    rehydrate_molecule_properties,
    update_molecule,
)

# Property services
from .properties import (
    InvariantPropertyError,
    PropertyAlreadyExistsError,
    create_or_update_family_property,
    create_or_update_molecular_property,
    validate_property_uniqueness,
)

# Property generator services
from .property_generator import (
    ADMETSA_PROPERTIES,
    compute_family_admetsa_aggregates,
    generate_admetsa_for_family,
    generate_admetsa_properties_for_family,
    generate_properties_for_family,
    preview_properties_for_family,
)

# Synthetic accessibility services
from .synthetic_accessibility import (
    ProviderType,
    SAProviderUnion,
    SyntheticAccessibilityService,
    get_sa_service,
)

# Utility services
from .utils import filter_molecules_for_user

__all__ = [
    # Family services
    "FamilyFrozenError",
    "add_members_to_family",
    "create_family_from_smiles",
    "create_single_molecule_family",
    "generate_substituted_family",
    "rehydrate_family_properties",
    "remove_members_from_family",
    # Molecule services
    "create_molecule_from_smiles",
    "create_or_get_molecule",
    "get_molecule_structure_info",
    "rehydrate_molecule_properties",
    "update_molecule",
    # Property services
    "InvariantPropertyError",
    "PropertyAlreadyExistsError",
    "create_or_update_family_property",
    "create_or_update_molecular_property",
    "validate_property_uniqueness",
    # Property generator services
    "ADMETSA_PROPERTIES",
    "compute_family_admetsa_aggregates",
    "generate_admetsa_for_family",
    "generate_admetsa_properties_for_family",
    "generate_properties_for_family",
    "preview_properties_for_family",
    # Synthetic accessibility services
    "ProviderType",
    "SAProviderUnion",
    "SyntheticAccessibilityService",
    "get_sa_service",
    # Utility services
    "filter_molecules_for_user",
]
