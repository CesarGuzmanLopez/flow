"""
Serializadores de Django REST Framework para la app Chemistry.

Define serializadores para convertir modelos de química a JSON y viceversa,
incluyendo relaciones anidadas (propiedades dentro de moléculas/familias).
"""

from rest_framework import serializers

from .models import (
    Family,
    FamilyMember,
    FamilyProperty,
    MolecularProperty,
    Molecule,
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
        ]
        read_only_fields = ["id", "created_at"]


class MoleculeSerializer(serializers.ModelSerializer):
    """Serializador para moléculas con propiedades anidadas."""

    properties = MolecularPropertySerializer(many=True, read_only=True)

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
            "created_by",
            "properties",
        ]
        read_only_fields = ["id", "created_at", "created_by", "frozen"]


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
        ]
        read_only_fields = ["id", "created_at"]


class FamilySerializer(serializers.ModelSerializer):
    """Serializador para familias con propiedades anidadas."""

    properties = FamilyPropertySerializer(many=True, read_only=True)

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
            "properties",
        ]
        read_only_fields = ["id", "created_at"]


class FamilyMemberSerializer(serializers.ModelSerializer):
    """Serializador para membresía molécula-familia."""

    class Meta:
        model = FamilyMember
        fields = ["id", "family", "molecule"]
