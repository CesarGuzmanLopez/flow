"""
Register a predefined CADMA flow definition using the generic definitions.

CADMA (example) includes the following steps:
1) create_reference_family (o crear desde molécula)
2) generate_admetsa
3) create_reference_molecule_family (si aplica)
4) generate_substitution_family
5) generate_admetsa_family_aggregates

Note: The exact composition can be adjusted; definition is step-agnostic and
users can override configs at instantiation.
"""

from __future__ import annotations

from .definitions import FlowDefinition, FlowStepDef, register_definition


def _register():
    steps = [
        FlowStepDef(
            name="Crear familia de referencia",
            step_type="create_reference_family",
            description="Crea o selecciona una familia base",
            config={},
        ),
        FlowStepDef(
            name="Generar ADMETSA base",
            step_type="generate_admetsa",
            description="Calcula ADMETSA para la familia base",
            config={},
            requires=[0],
        ),
        FlowStepDef(
            name="Crear familia de molécula de referencia",
            step_type="create_reference_molecule_family",
            description="Crea familia con una única molécula de referencia",
            config={},
        ),
        FlowStepDef(
            name="Generar ADMETSA de molécula de referencia",
            step_type="generate_admetsa",
            description="Calcula ADMETSA para la familia de molécula de referencia",
            config={},
            requires=[2],
        ),
        FlowStepDef(
            name="Generar permutaciones por sustitución",
            step_type="generate_substitution_family",
            description="Genera familia por sustituciones (permutaciones)",
            config={},
            requires=[2],
        ),
        FlowStepDef(
            name="Agregados ADMETSA a nivel familia",
            step_type="generate_admetsa_family_aggregates",
            description="Calcula promedios ADMETSA de la familia generada",
            config={},
            requires=[4],
        ),
    ]
    defn = FlowDefinition(
        key="cadma",
        name="CADMA",
        description="Flujo CADMA predefinido",
        steps=steps,
        version=1,
        metadata={"category": "predefined"},
    )
    register_definition(defn)


# Perform registration on import
_register()

__all__ = []
