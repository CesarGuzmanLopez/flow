"""
Paquete Chemistry: APIs públicas para extensión y uso externo.

Objetivos:
- Exponer interfaces y registros para crear proveedores de propiedades.
- Exponer servicios de dominio (moléculas, familias, propiedades) con contratos estables.
- Facilitar importación desde otros módulos o desde la propia API.

Nota sobre Flows:
Actualmente las propiedades pueden asociarse a un flujo a través de `metadata["flow_id"]`.
En una iteración futura se evaluará añadir una FK opcional en propiedades hacia Flow.
"""

# El paquete chemistry expone sus submódulos directamente
# Los imports se hacen donde se necesiten para evitar circular imports
__all__ = []
