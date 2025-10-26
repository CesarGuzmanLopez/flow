"""
Configuración del panel de administración de Django para la app Chemistry.

Este archivo registra todos los modelos de química en el admin de Django,
configurando las vistas de lista, filtros y búsqueda para facilitar la
gestión de moléculas, propiedades, familias y sus relaciones.
"""

from django.contrib import admin

from .models import (
    Family,
    FamilyMember,
    FamilyProperty,
    MolecularProperty,
    Molecule,
    MoleculeFlow,
)


@admin.register(Molecule)
class MoleculeAdmin(admin.ModelAdmin):
    """Configuración del admin para moléculas."""

    list_display = ("id", "name", "inchikey", "created_at", "frozen")
    list_filter = ("frozen",)
    search_fields = ("name", "inchikey", "smiles", "inchi")


@admin.register(MolecularProperty)
class MolecularPropertyAdmin(admin.ModelAdmin):
    """Configuración del admin para propiedades moleculares (EAV)."""

    list_display = (
        "id",
        "molecule_id",
        "property_type",
        "value",
        "units",
        "method",
        "relation",
        "source_id",
        "created_at",
    )
    list_filter = ("property_type", "units", "method")
    search_fields = ("property_type", "value", "source_id")


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    """Configuración del admin para familias de moléculas."""

    list_display = ("id", "name", "provenance", "frozen", "created_at")
    list_filter = ("frozen",)
    search_fields = ("name", "provenance")


@admin.register(FamilyProperty)
class FamilyPropertyAdmin(admin.ModelAdmin):
    """Configuración del admin para propiedades de familias (EAV)."""

    list_display = (
        "id",
        "family_id",
        "property_type",
        "value",
        "units",
        "method",
        "relation",
        "source_id",
        "created_at",
    )
    list_filter = ("property_type", "units", "method")
    search_fields = ("property_type", "value", "source_id")


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    """Configuración del admin para membresía molécula-familia."""

    list_display = ("id", "family_id", "molecule_id")
    search_fields = ("family__name", "molecule__name", "molecule__inchikey")


@admin.register(MoleculeFlow)
class MoleculeFlowAdmin(admin.ModelAdmin):
    """Configuración del admin para la relación molécula-flujo."""

    list_display = ("id", "molecule_id", "flow_id", "role", "step_number", "created_at")
    search_fields = ("molecule__name", "molecule__inchikey", "flow__name")
