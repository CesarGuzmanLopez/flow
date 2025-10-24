"""
Modelos de dominio para la app Chemistry.

Define las entidades del dominio químico alineadas con estándares ChEMBL/PubChem:
- Molecule: entidad molecular con invariantes (InChIKey, SMILES, fórmula)
- Family: agregación de moléculas relacionadas
- MolecularProperty/FamilyProperty: modelo EAV para propiedades flexibles
- FamilyMember: relación many-to-many entre moléculas y familias
- MoleculeFlow: relación many-to-many entre moléculas y flujos
"""

from django.conf import settings
from django.db import models


class Molecule(models.Model):
    """Entidad molecular alineada con estándares ChEMBL/PubChem.

    Notes:
    - Keep `name` for UI/tests convenience (not strictly part of invariants).
    - Prefer uniqueness via `inchikey` when available.
    - Store invariant structure fields and flexible metadata.
    - Link to users (created_by) and flows (many-to-many via MoleculeFlow).
    """

    # Convenience display name (optional)
    name = models.CharField(max_length=200, blank=True)

    # Invariant identifiers/structures
    inchikey = models.CharField(
        max_length=27, blank=True, null=True, unique=True, db_index=True
    )
    smiles = models.TextField(blank=True)
    inchi = models.TextField(blank=True)
    canonical_smiles = models.TextField(blank=True)
    molecular_formula = models.CharField(max_length=200, blank=True)

    # Flexible metadata and lifecycle
    metadata = models.JSONField(default=dict, blank=True)
    frozen = models.BooleanField(default=False)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_molecules",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_molecules",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "inchikey"]

    def __str__(self):
        return self.name or self.inchikey or f"Molecule {self.pk}"


class Family(models.Model):
    """Familia de moléculas relacionadas (agregados)."""

    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    family_hash = models.CharField(max_length=128)
    provenance = models.CharField(max_length=200)
    frozen = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_families",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_families",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "created_at"]

    def __str__(self):
        return self.name or f"Family {self.pk}"


class FamilyProperty(models.Model):
    """Propiedades EAV para familias con campos contextuales (método, unidades, fuente)."""

    family = models.ForeignKey(
        Family, on_delete=models.CASCADE, related_name="properties"
    )
    property_type = models.CharField(max_length=200)
    value = models.TextField()
    is_invariant = models.BooleanField(default=False)
    method = models.CharField(max_length=100, blank=True)
    units = models.CharField(max_length=50, blank=True)
    relation = models.CharField(max_length=10, blank=True)
    source_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_family_properties",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_family_properties",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["family", "property_type", "method", "relation", "source_id"],
                name="unique_family_property_key",
            )
        ]
        ordering = ["property_type", "created_at"]

    def __str__(self):
        return f"{self.property_type}={self.value} ({self.units})"


class MolecularProperty(models.Model):
    """Propiedades EAV para moléculas con campos contextuales (método, unidades, fuente)."""

    molecule = models.ForeignKey(
        Molecule, on_delete=models.CASCADE, related_name="properties"
    )
    property_type = models.CharField(max_length=200)
    value = models.TextField()
    is_invariant = models.BooleanField(default=False)
    method = models.CharField(max_length=100, blank=True)
    units = models.CharField(max_length=50, blank=True)
    relation = models.CharField(max_length=10, blank=True)
    source_id = models.CharField(
        max_length=100, blank=True
    )  # ID de la fuente o referencias
    metadata = models.JSONField(default=dict, blank=True)

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_molecular_properties",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_molecular_properties",
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["molecule", "property_type", "method", "relation", "source_id"],
                name="unique_molecular_property_key",
            )
        ]
        ordering = ["property_type", "created_at"]

    def __str__(self):
        return f"{self.property_type}={self.value} ({self.units})"


class FamilyMember(models.Model):
    """Membresía que vincula moléculas con familias (relación many-to-many)."""

    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name="members")
    molecule = models.ForeignKey(
        Molecule, on_delete=models.CASCADE, related_name="families"
    )

    class Meta:
        unique_together = ["family", "molecule"]

    def __str__(self):
        return f"{self.molecule} in {self.family}"


class MoleculeFlow(models.Model):
    """Relación entre moléculas y flujos para asociación en workflows."""

    # reference Flow model from flows app by label to avoid circular import
    flow = models.ForeignKey(
        "flows.Flow", on_delete=models.CASCADE, related_name="flow_molecules"
    )
    molecule = models.ForeignKey(
        Molecule, on_delete=models.CASCADE, related_name="flow_links"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["flow", "molecule"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.molecule} -> {self.flow}"
