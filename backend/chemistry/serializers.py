"""
Serializadores de Django REST Framework para la app Chemistry.

Define serializadores para convertir modelos de química a JSON y viceversa,
incluyendo relaciones anidadas (propiedades dentro de moléculas/familias)
con tipado fuerte para garantizar consistencia de datos.
"""

from typing import Any, Dict

from rest_framework import serializers

from .models import (
    Family,
    FamilyMember,
    FamilyProperty,
    MolecularProperty,
    Molecule,
)
from .services import (
    get_molecule_structure_info,
    rehydrate_family_properties,
    rehydrate_molecule_properties,
)
from .services.properties import (
    PropertyAlreadyExistsError,
    validate_property_uniqueness,
)


class MolecularPropertySerializer(serializers.ModelSerializer):
    """Serializador para propiedades moleculares EAV."""

    class Meta:
        model = MolecularProperty
        fields = [
            "id",
            "molecule",
            "property_type",
            "value",
            "is_invariant",
            "method",
            "units",
            "relation",
            "source_id",
            "metadata",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        extra_kwargs = {
            "method": {"required": False, "allow_blank": True},
            "units": {"required": False, "allow_blank": True},
            "relation": {"required": False, "allow_blank": True},
            "source_id": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        """Override to provide defaults for optional context fields."""
        # Ensure optional fields have defaults before validation
        data = data.copy() if hasattr(data, "copy") else dict(data)
        data.setdefault("method", "")
        data.setdefault("units", "")
        data.setdefault("relation", "")
        data.setdefault("source_id", "")
        return super().to_internal_value(data)

    def create(self, validated_data):
        """Crear propiedad molecular con validación de unicidad."""
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Defaults for optional context fields
        validated_data.setdefault("method", "")
        validated_data.setdefault("units", "")
        validated_data.setdefault("relation", "")
        validated_data.setdefault("source_id", "")

        # Check for duplicate using composite key
        existing = validate_property_uniqueness(
            model_class=MolecularProperty,
            entity_field="molecule",
            entity_id=validated_data["molecule"].id,
            property_type=validated_data["property_type"],
            method=validated_data["method"],
            relation=validated_data["relation"],
            source_id=validated_data["source_id"],
        )

        if existing:
            raise PropertyAlreadyExistsError(
                property_type=validated_data["property_type"],
                method=validated_data["method"],
                relation=validated_data["relation"],
                source_id=validated_data["source_id"],
            )

        if user and user.is_authenticated:
            validated_data.setdefault("created_by", user)

        return MolecularProperty.objects.create(**validated_data)


class MoleculeSerializer(serializers.ModelSerializer):
    """Serializador para moléculas con propiedades anidadas y tipado fuerte."""

    properties = MolecularPropertySerializer(many=True, read_only=True)

    # Add computed fields for type-safe data access
    structure_identifiers = serializers.SerializerMethodField()
    computed_properties = serializers.SerializerMethodField()

    class Meta:
        model = Molecule
        fields = [
            "id",
            "name",
            "inchikey",
            "smiles",
            "inchi",
            "canonical_smiles",
            "molecular_formula",
            "metadata",
            "frozen",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "properties",
            "structure_identifiers",
            "computed_properties",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "frozen",
            "structure_identifiers",
            "computed_properties",
        ]

    def get_structure_identifiers(self, obj: Molecule) -> Dict[str, Any]:
        """Get structure identifiers using type-safe interface."""
        try:
            identifiers = get_molecule_structure_info(obj)
            return identifiers.to_dict()
        except Exception:
            # Fallback to direct field access
            return {
                "inchi": obj.inchi or "",
                "inchikey": obj.inchikey or "",
                "canonical_smiles": obj.canonical_smiles or obj.smiles or "",
                "molecular_formula": obj.molecular_formula or None,
            }

    def get_computed_properties(self, obj: Molecule) -> Dict[str, Any]:
        """Get computed properties using type-safe interface."""
        try:
            properties = rehydrate_molecule_properties(obj)
            return properties.to_dict()
        except Exception:
            # Fallback to empty dict
            return {}


class FamilyPropertySerializer(serializers.ModelSerializer):
    """Serializador para propiedades de familias EAV."""

    class Meta:
        model = FamilyProperty
        fields = [
            "id",
            "family",
            "property_type",
            "value",
            "is_invariant",
            "method",
            "units",
            "relation",
            "source_id",
            "metadata",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        extra_kwargs = {
            "method": {"required": False, "allow_blank": True},
            "units": {"required": False, "allow_blank": True},
            "relation": {"required": False, "allow_blank": True},
            "source_id": {"required": False, "allow_blank": True},
        }

    def to_internal_value(self, data):
        """Override to provide defaults for optional context fields."""
        # Ensure optional fields have defaults before validation
        data = data.copy() if hasattr(data, "copy") else dict(data)
        data.setdefault("method", "")
        data.setdefault("units", "")
        data.setdefault("relation", "")
        data.setdefault("source_id", "")
        return super().to_internal_value(data)

    def create(self, validated_data):
        """Crear propiedad de familia con validación de unicidad."""
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # Defaults for optional context fields
        validated_data.setdefault("method", "")
        validated_data.setdefault("units", "")
        validated_data.setdefault("relation", "")
        validated_data.setdefault("source_id", "")

        # Check for duplicate using composite key
        existing = validate_property_uniqueness(
            model_class=FamilyProperty,
            entity_field="family",
            entity_id=validated_data["family"].id,
            property_type=validated_data["property_type"],
            method=validated_data["method"],
            relation=validated_data["relation"],
            source_id=validated_data["source_id"],
        )

        if existing:
            raise PropertyAlreadyExistsError(
                property_type=validated_data["property_type"],
                method=validated_data["method"],
                relation=validated_data["relation"],
                source_id=validated_data["source_id"],
            )

        if user and user.is_authenticated:
            validated_data.setdefault("created_by", user)

        return FamilyProperty.objects.create(**validated_data)


class FamilySerializer(serializers.ModelSerializer):
    """Serializador para familias con propiedades anidadas y tipado fuerte."""

    properties = FamilyPropertySerializer(many=True, read_only=True)

    # Add computed fields for type-safe data access
    aggregated_properties = serializers.SerializerMethodField()
    member_statistics = serializers.SerializerMethodField()

    class Meta:
        model = Family
        fields = [
            "id",
            "name",
            "description",
            "family_hash",
            "provenance",
            "frozen",
            "metadata",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "properties",
            "aggregated_properties",
            "member_statistics",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "aggregated_properties",
            "member_statistics",
        ]

    def get_aggregated_properties(self, obj: Family) -> Dict[str, Any]:
        """Get family aggregated properties using type-safe interface."""
        try:
            family_data = rehydrate_family_properties(obj)
            return family_data.get("family_properties", {})
        except Exception:
            # Fallback to empty dict
            return {}

    def get_member_statistics(self, obj: Family) -> Dict[str, Any]:
        """Get member property statistics using type-safe interface."""
        try:
            family_data = rehydrate_family_properties(obj)
            return {
                "member_count": family_data.get("member_count", 0),
                "property_stats": family_data.get("aggregated_stats", {}),
            }
        except Exception:
            # Fallback to basic count
            return {
                "member_count": obj.members.count(),
                "property_stats": {},
            }


class FamilyMemberSerializer(serializers.ModelSerializer):
    """Serializador para membresía molécula-familia."""

    class Meta:
        model = FamilyMember
        fields = ["id", "family", "molecule"]


class CreateMoleculeFromSmilesSerializer(serializers.Serializer):
    """Serializador para crear molécula desde SMILES."""

    smiles = serializers.CharField(
        max_length=1000, help_text="Notación SMILES de la molécula"
    )
    name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Nombre opcional de la molécula",
    )
    extra_metadata = serializers.JSONField(
        required=False, default=dict, help_text="Metadatos adicionales"
    )
    compute_descriptors = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si es true, el backend calculará y guardará descriptores en metadata",
    )


class CreateMoleculeSerializer(serializers.Serializer):
    """Serializer used by the openapi schema for creating or looking up molecules.

    Supports multiple payload shapes accepted by the service:
    - `smiles` (preferred): create or deduplicate by provider InChIKey
    - `inchikey` (lookup-only when provided without `smiles`)
    - Optional `name` and `extra_metadata` fields
    """

    smiles = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Notación SMILES de la molécula (preferida para creación)",
    )
    inchikey = serializers.CharField(
        max_length=27,
        required=False,
        allow_blank=True,
        help_text="InChIKey (busqueda; el backend no confía en inchikeys enviados para creación)",
    )
    name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Nombre opcional de la molécula",
    )
    extra_metadata = serializers.JSONField(
        required=False, default=dict, help_text="Metadatos adicionales"
    )
    compute_descriptors = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si es true, el backend calculará y guardará descriptores en metadata",
    )


class MoleculeUpdateSerializer(serializers.Serializer):
    """Serializer for validating update/patch payloads for Molecule endpoints.

    Admins may include structural fields; regular users must not include them.
    """

    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    smiles = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    inchi = serializers.CharField(required=False, allow_blank=True)
    inchikey = serializers.CharField(max_length=27, required=False, allow_blank=True)
    canonical_smiles = serializers.CharField(
        max_length=1000, required=False, allow_blank=True
    )
    molecular_formula = serializers.CharField(
        max_length=200, required=False, allow_blank=True
    )
    metadata = serializers.JSONField(required=False, default=dict)
    frozen = serializers.BooleanField(required=False)


class CreateFamilyFromSmilesSerializer(serializers.Serializer):
    """Serializador para crear familia desde lista de SMILES."""

    name = serializers.CharField(max_length=200, help_text="Nombre de la familia")
    smiles_list = serializers.ListField(
        child=serializers.CharField(max_length=1000),
        min_length=1,
        help_text="Lista de notaciones SMILES",
    )
    provenance = serializers.CharField(
        max_length=200, default="user", help_text="Origen de la familia"
    )


class GenerateADMETSASerializer(serializers.Serializer):
    """Serializador para generar propiedades ADMETSA de una familia."""

    family_id = serializers.IntegerField(help_text="ID de la familia")


class AddPropertySerializer(serializers.Serializer):
    """Serializador para agregar propiedades a moléculas o familias."""

    property_type = serializers.CharField(max_length=200, help_text="Tipo de propiedad")
    value = serializers.CharField(max_length=500, help_text="Valor de la propiedad")
    method = serializers.CharField(
        max_length=100, required=False, allow_blank=True, help_text="Método de cálculo"
    )
    units = serializers.CharField(
        max_length=50, required=False, allow_blank=True, help_text="Unidades"
    )
    source_id = serializers.CharField(
        max_length=100, required=False, allow_blank=True, help_text="ID de fuente"
    )
    metadata = serializers.JSONField(
        required=False, default=dict, help_text="Metadatos adicionales"
    )


class PropertyGenerationRequestSerializer(serializers.Serializer):
    """Serializer for property generation requests.

    This serializer validates requests for the unified property generation
    system, supporting both persistent and preview modes with metadata.

    Fields:
        metadata: Global metadata applied to all molecules (optional)
        per_molecule_metadata: Metadata per molecule {mol_id: {key: value}} (optional)
        properties_data: Pre-calculated properties for manual provider (optional)

    Examples:
        # RDKit with global metadata
        {
            "metadata": {"experiment_id": "EXP-001", "batch": "batch-42"}
        }

        # Manual provider with per-molecule data
        {
            "properties_data": {
                "8": {"MolWt": "180.16", "LogP": "2.45"},
                "9": {"MolWt": "194.19"}
            },
            "per_molecule_metadata": {
                "8": {"technician": "John"},
                "9": {"technician": "Jane"}
            }
        }

        # Combined metadata
        {
            "metadata": {"experiment_id": "EXP-001"},
            "per_molecule_metadata": {
                "8": {"replicate": 1}
            }
        }
    """

    metadata = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Global metadata applied to all molecules",
    )
    per_molecule_metadata = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Metadata per molecule: {molecule_id: {key: value}}",
    )
    properties_data = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Pre-calculated properties for manual provider: {molecule_id: {prop: value}}",
    )

    def validate_per_molecule_metadata(self, value):
        """Validate per_molecule_metadata structure.

        Must be a dictionary mapping molecule IDs (as strings or ints) to
        metadata dictionaries.
        """
        if value is None:
            return None

        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "per_molecule_metadata must be a dictionary"
            )

        # Convert string keys to integers and validate structure
        converted = {}
        for mol_id, metadata in value.items():
            try:
                mol_id_int = int(mol_id)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Invalid molecule ID: {mol_id}. Must be an integer."
                )

            if not isinstance(metadata, dict):
                raise serializers.ValidationError(
                    f"Metadata for molecule {mol_id} must be a dictionary"
                )

            converted[mol_id_int] = metadata

        return converted

    def validate_properties_data(self, value):
        """Validate properties_data structure.

        Must be a dictionary mapping molecule IDs to property dictionaries.
        """
        if value is None:
            return None

        if not isinstance(value, dict):
            raise serializers.ValidationError("properties_data must be a dictionary")

        # Convert string keys to integers and validate structure
        converted = {}
        for mol_id, properties in value.items():
            try:
                mol_id_int = int(mol_id)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Invalid molecule ID: {mol_id}. Must be an integer."
                )

            if not isinstance(properties, dict):
                raise serializers.ValidationError(
                    f"Properties for molecule {mol_id} must be a dictionary"
                )

            # Validate all property values are strings
            for prop_key, prop_value in properties.items():
                if not isinstance(prop_value, str):
                    raise serializers.ValidationError(
                        f"Property value for {prop_key} in molecule {mol_id} "
                        f"must be a string, got {type(prop_value).__name__}"
                    )

            converted[mol_id_int] = properties

        return converted

    def validate(self, data):
        """Cross-field validation."""
        # If properties_data is provided, ensure it's consistent with metadata
        properties_data = data.get("properties_data")
        per_molecule_metadata = data.get("per_molecule_metadata")

        if properties_data and per_molecule_metadata:
            # Check that molecule IDs match
            props_mol_ids = set(properties_data.keys())
            metadata_mol_ids = set(per_molecule_metadata.keys())

            # It's OK if metadata has fewer molecules than properties_data,
            # but warn if metadata has molecules not in properties_data
            extra_metadata_mols = metadata_mol_ids - props_mol_ids
            if extra_metadata_mols:
                raise serializers.ValidationError(
                    f"per_molecule_metadata contains molecule IDs not in properties_data: "
                    f"{extra_metadata_mols}"
                )

        return data
