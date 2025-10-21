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
