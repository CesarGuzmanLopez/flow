"""
Configuración de la aplicación Chemistry para Django.

Esta app gestiona el dominio de química: moléculas, familias de moléculas,
propiedades moleculares y de familia (modelo EAV), y relaciones con flujos.
"""

from django.apps import AppConfig


class ChemistryConfig(AppConfig):
    """Configuración de la app Chemistry."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "chemistry"

    def ready(self):
        """Initialize app - register property providers."""
        # Import from package root (re-exported by providers/__init__.py)
        from .providers import auto_register_providers

        # Auto-register all built-in providers (RDKit, Manual, Random)
        auto_register_providers()
