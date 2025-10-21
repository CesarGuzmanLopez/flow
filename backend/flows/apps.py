"""
Configuración de la aplicación Flows para Django.

Esta app gestiona el dominio de flujos de trabajo (workflows): flujos, versiones,
pasos, artefactos, ejecuciones y el árbol de nodos/ramas (algoritmo step-first
sin merges ni ciclos).
"""

from django.apps import AppConfig


class FlowsConfig(AppConfig):
    """Configuración de la app Flows."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "flows"
