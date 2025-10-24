"""
Vistas de gestión de artefactos (artifacts).
"""

from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from .. import services as flow_services
from ..models import Artifact
from ..serializers import ArtifactSerializer


class BaseFlowViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar artefactos",
        description=(
            "Obtiene todos los artefactos (archivos, datos) generados por flujos. "
            "Los artefactos son content-addressable (identificados por hash SHA256). "
            "Usa ?mine=true para obtener solo los artefactos asociados a flujos creados por el "
            "usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo los artefactos asociados"
                " a flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Artifacts"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de artefacto",
        description="Recupera metadata de un artefacto específico, incluyendo hash, "
        "tipo de contenido y ubicación de almacenamiento.",
        tags=["Artifacts"],
    ),
    create=extend_schema(
        summary="Crear artefacto",
        description="Registra un nuevo artefacto en el sistema. El contenido debe ser "
        "almacenado en storage externo (S3/MinIO) y se registra el hash SHA256.",
        tags=["Artifacts"],
    ),
    update=extend_schema(
        summary="Actualizar artefacto completo",
        description="Actualiza metadata de un artefacto (no el contenido, que es inmutable).",
        tags=["Artifacts"],
    ),
    partial_update=extend_schema(
        summary="Actualizar artefacto parcialmente",
        description="Actualiza campos específicos de metadata de un artefacto.",
        tags=["Artifacts"],
    ),
    destroy=extend_schema(
        summary="Eliminar artefacto",
        description="Elimina el registro de un artefacto (no borra el contenido en storage).",
        tags=["Artifacts"],
    ),
)
class ArtifactViewSet(BaseFlowViewSet):
    """ViewSet para gestión de artefactos content-addressable (archivos y datos)."""

    queryset = Artifact.objects.all()
    serializer_class = ArtifactSerializer
    search_fields = ["hash", "filename", "content_type"]
    ordering_fields = ["id", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(
                step_execution__execution_snapshot__flow_version__flow__owner=self.request.user
            )
        return flow_services.filter_artifacts_for_user(qs, self.request.user)

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Obtener URL de descarga de artefacto",
        description="Genera o devuelve la URL de descarga para acceder al contenido del artefacto "
        "desde el almacenamiento externo (S3/MinIO). Actualmente retorna metadata.",
        tags=["Artifacts"],
    )
    def download(self, request, pk=None):
        """Obtiene la URL de descarga del archivo del artefacto."""
        artifact = self.get_object()
        return Response(
            {
                "download_url": f"/media/{artifact.storage_path}",
                "filename": artifact.filename,
            }
        )
