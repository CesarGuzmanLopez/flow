"""
Servicios para gestión de propiedades moleculares y de familia.

Implementa reglas de negocio para:
- Unicidad compuesta (entity, property_type, method, relation, source_id)
- Protección de propiedades invariantes (is_invariant=True)
- Validación y actualización controlada
"""

import logging
from typing import Any, Dict, Optional, Tuple

from django.core.exceptions import ValidationError

from ..models import Family, FamilyProperty, MolecularProperty, Molecule

logger = logging.getLogger(__name__)


class PropertyAlreadyExistsError(ValidationError):
    """Raised when attempting to create a property that already exists with same key."""

    def __init__(self, property_type: str, method: str, relation: str, source_id: str):
        message = (
            f"Property already exists: property_type='{property_type}', "
            f"method='{method}', relation='{relation}', source_id='{source_id}'. "
            "Use PATCH or PUT to update existing properties."
        )
        super().__init__(message)
        self.property_type = property_type
        self.method = method
        self.relation = relation
        self.source_id = source_id


class InvariantPropertyError(ValidationError):
    """Raised when attempting to modify the value of an invariant property."""

    def __init__(self, property_id: int):
        message = (
            f"Cannot modify value of invariant property (id={property_id}). "
            "Invariant properties can only have their metadata updated."
        )
        super().__init__(message)
        self.property_id = property_id


def create_or_update_molecular_property(
    *,
    molecule: Molecule,
    property_type: str,
    value: str,
    method: str = "",
    relation: str = "",
    source_id: str = "",
    units: str = "",
    is_invariant: bool = False,
    metadata: Dict[str, Any] = None,
    created_by: Any = None,
    force_create: bool = False,
) -> Tuple[MolecularProperty, bool]:
    """
    Create or update molecular property with uniqueness validation.

    Args:
        molecule: Target molecule
        property_type: Type of property
        value: Property value
        method: Method used to obtain/calculate the property
        relation: Relation/context (e.g., "atom:12", "conformer:3")
        source_id: Source identifier for provenance
        units: Units of measurement
        is_invariant: If True, value cannot be modified later
        metadata: Additional metadata (always updatable)
        created_by: User creating the property
        force_create: If True, raise error on duplicate instead of updating

    Returns:
        Tuple of (MolecularProperty, created: bool)

    Raises:
        PropertyAlreadyExistsError: If force_create=True and property exists
        InvariantPropertyError: If trying to modify value of invariant property
    """
    lookup = {
        "molecule": molecule,
        "property_type": property_type,
        "method": method or "",
        "relation": relation or "",
        "source_id": source_id or "",
    }

    try:
        existing = MolecularProperty.objects.get(**lookup)

        if force_create:
            raise PropertyAlreadyExistsError(
                property_type=property_type,
                method=method or "",
                relation=relation or "",
                source_id=source_id or "",
            )

        # Check if trying to modify invariant property value
        if existing.is_invariant and existing.value != value:
            raise InvariantPropertyError(property_id=existing.id)

        # Update allowed fields
        if not existing.is_invariant:
            existing.value = value
            existing.units = units or ""
            existing.is_invariant = is_invariant

        # Metadata can always be updated
        if metadata is not None:
            existing.metadata = metadata

        existing.save()
        logger.info(
            f"Updated MolecularProperty {existing.id} for molecule {molecule.id}"
        )
        return existing, False

    except MolecularProperty.DoesNotExist:
        # Create new property
        prop = MolecularProperty.objects.create(
            molecule=molecule,
            property_type=property_type,
            value=value,
            method=method or "",
            relation=relation or "",
            source_id=source_id or "",
            units=units or "",
            is_invariant=is_invariant,
            metadata=metadata or {},
            created_by=created_by,
        )
        logger.info(f"Created MolecularProperty {prop.id} for molecule {molecule.id}")
        return prop, True


def create_or_update_family_property(
    *,
    family: Family,
    property_type: str,
    value: str,
    method: str = "",
    relation: str = "",
    source_id: str = "",
    units: str = "",
    is_invariant: bool = False,
    metadata: Dict[str, Any] = None,
    created_by: Any = None,
    force_create: bool = False,
) -> Tuple[FamilyProperty, bool]:
    """
    Create or update family property with uniqueness validation.

    Args:
        family: Target family
        property_type: Type of property
        value: Property value
        method: Method used to obtain/calculate the property
        relation: Relation/context (e.g., "aggregated:mean")
        source_id: Source identifier for provenance
        units: Units of measurement
        is_invariant: If True, value cannot be modified later
        metadata: Additional metadata (always updatable)
        created_by: User creating the property
        force_create: If True, raise error on duplicate instead of updating

    Returns:
        Tuple of (FamilyProperty, created: bool)

    Raises:
        PropertyAlreadyExistsError: If force_create=True and property exists
        InvariantPropertyError: If trying to modify value of invariant property
    """
    lookup = {
        "family": family,
        "property_type": property_type,
        "method": method or "",
        "relation": relation or "",
        "source_id": source_id or "",
    }

    try:
        existing = FamilyProperty.objects.get(**lookup)

        if force_create:
            raise PropertyAlreadyExistsError(
                property_type=property_type,
                method=method or "",
                relation=relation or "",
                source_id=source_id or "",
            )

        # Check if trying to modify invariant property value
        if existing.is_invariant and existing.value != value:
            raise InvariantPropertyError(property_id=existing.id)

        # Update allowed fields
        if not existing.is_invariant:
            existing.value = value
            existing.units = units or ""
            existing.is_invariant = is_invariant

        # Metadata can always be updated
        if metadata is not None:
            existing.metadata = metadata

        existing.save()
        logger.info(f"Updated FamilyProperty {existing.id} for family {family.id}")
        return existing, False

    except FamilyProperty.DoesNotExist:
        # Create new property
        prop = FamilyProperty.objects.create(
            family=family,
            property_type=property_type,
            value=value,
            method=method or "",
            relation=relation or "",
            source_id=source_id or "",
            units=units or "",
            is_invariant=is_invariant,
            metadata=metadata or {},
            created_by=created_by,
        )
        logger.info(f"Created FamilyProperty {prop.id} for family {family.id}")
        return prop, True


def validate_property_uniqueness(
    *,
    model_class,
    entity_field: str,
    entity_id: int,
    property_type: str,
    method: str = "",
    relation: str = "",
    source_id: str = "",
) -> Optional[Any]:
    """
    Check if a property with the given composite key already exists.

    Args:
        model_class: MolecularProperty or FamilyProperty class
        entity_field: 'molecule' or 'family'
        entity_id: ID of the molecule or family
        property_type: Type of property
        method: Method identifier
        relation: Relation identifier
        source_id: Source identifier

    Returns:
        Existing property instance or None
    """
    lookup = {
        entity_field: entity_id,
        "property_type": property_type,
        "method": method or "",
        "relation": relation or "",
        "source_id": source_id or "",
    }

    try:
        return model_class.objects.get(**lookup)
    except model_class.DoesNotExist:
        return None
