"""
Servicios de aplicación para gestión de flujos.

Orquestación entre controladores (views) y dominio.
Responsabilidades extraídas de FlowViewSet.
"""

from typing import Any, Dict, Optional

from flows.domain.flujo.builder import create_flow_from_definition
from flows.domain.flujo.definitions import get_definition
from flows.models import Flow, FlowVersion


class FlowApplicationService:
    """
    Servicio de aplicación para operaciones de flujos.

    Responsabilidades:
    - Crear flujos desde definiciones
    - Versioning de flujos
    - Delegación a servicios de dominio
    """

    def __init__(self, chemistry_port: Any):
        """
        Inicializa con inyección de dependencias.

        Args:
            chemistry_port: Implementación de IChemistryPort
        """
        self.chemistry_port = chemistry_port

    def create_flow_from_definition(
        self,
        owner: Any,
        definition_key: str,
        name: Optional[str] = None,
        params_override: Optional[Dict[int, Dict]] = None,
    ) -> Flow:
        """
        Crea un flujo a partir de definición registrada.

        Args:
            owner: Usuario propietario
            definition_key: Clave de definición (e.g., 'cadma')
            name: Nombre opcional del flujo
            params_override: Parámetros para pasos

        Returns:
            Flow creado
        """
        defn = get_definition(definition_key)
        return create_flow_from_definition(
            owner=owner,
            defn=defn,
            name=name,
            params_override=params_override,
        )

    def create_flow_version(self, flow: Flow, created_by: Any) -> FlowVersion:
        """Crea nueva versión de flujo."""
        latest_version = flow.flowversion_set.order_by("-version_number").first()
        next_version_number = latest_version.version_number + 1 if latest_version else 1

        return FlowVersion.objects.create(
            flow=flow,
            version_number=next_version_number,
            parent_version=latest_version,
            created_by=created_by,
            is_frozen=False,
        )

    def freeze_flow_version(self, version: FlowVersion) -> FlowVersion:
        """Congela una versión (la hace inmutable)."""
        if version.is_frozen:
            raise ValueError("Version is already frozen")
        version.is_frozen = True
        version.save()
        return version
