"""
Vistas de gestión de ramas (branches) y nodos (nodes).
"""

from typing import cast

from back.envelope import StandardEnvelopeMixin
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from .. import services as flow_services
from ..models import FlowBranch, FlowNode
from ..serializers import (
    AddStepSerializer,
    CreateBranchSerializer,
    FlowBranchSerializer,
    FlowNodeSerializer,
)


class BaseFlowViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar ramas de flujos",
        description=(
            "Obtiene todas las ramas en la estructura de árbol de flujos. Cada rama "
            "representa una línea de desarrollo independiente sin posibilidad de merge. "
            "Usa ?mine=true para obtener solo las ramas de"
            " flujos creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo las ramas de flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Branches"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de una rama",
        description="Recupera información de una rama específica, incluyendo su nodo head "
        "(último paso) y nodo de inicio.",
        tags=["Branches"],
    ),
    create=extend_schema(
        summary="Crear nueva rama",
        description="Crea una rama bifurcando desde un nodo existente de otra rama. "
        "Implementa algoritmo de árbol sin merges ni ciclos.",
        tags=["Branches"],
    ),
    destroy=extend_schema(
        summary="Eliminar rama",
        description="Elimina una rama y todas sus sub-ramas recursivamente. Los nodos "
        "compartidos con otras ramas no se eliminan. No se puede eliminar la rama principal.",
        tags=["Branches"],
    ),
)
class FlowBranchViewSet(BaseFlowViewSet):
    """ViewSet para gestión de ramas en el árbol de flujos (sin merges)."""

    queryset = FlowBranch.objects.all()
    search_fields = ["name"]
    ordering_fields = ["id"]

    def get_serializer_class(self):
        if self.action == "add_step":
            return AddStepSerializer
        elif self.action == "create":
            return CreateBranchSerializer
        else:
            return FlowBranchSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(flow__owner=self.request.user)
        if not flow_services.user_can_read_all_flows(self.request.user):
            qs = qs.filter(flow__owner=self.request.user)
        return qs

    @action(detail=True, methods=["post"], url_path="add-step")
    @extend_schema(
        summary="Añadir paso a rama",
        description="Añade un nuevo nodo (paso) al final de una rama. Si el contenido "
        "(content hash) ya existe en el flujo, se reutiliza el nodo existente. "
        "Implementa deduplicación de nodos compartidos.",
        tags=["Branches"],
    )
    def add_step(self, request, pk=None):
        """Añade un paso a la rama."""
        branch = cast(FlowBranch, self.get_object())
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            node = flow_services.add_step(
                branch.name,
                branch.flow,
                serializer.validated_data["content"],
                request.user,
            )
            return Response(
                FlowNodeSerializer(node).data, status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"], url_path="path")
    @extend_schema(
        summary="Obtener camino completo de rama",
        description="Recupera la secuencia ordenada de nodos desde la raíz hasta el head "
        "de la rama. Útil para reconstruir el flujo lineal de una rama específica.",
        tags=["Branches"],
    )
    def path(self, request, pk=None):
        """Retorna el camino de nodos de la rama."""
        branch = cast(FlowBranch, self.get_object())
        try:
            path_nodes = flow_services.get_path(branch.name, branch.flow)
            return Response(FlowNodeSerializer(path_nodes, many=True).data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """DELETE /api/flows/branches/{id}/ - Elimina la rama y subramas recursivamente."""
        branch = cast(FlowBranch, self.get_object())
        if branch.name == "principal":
            return Response(
                {"error": "No se puede eliminar la rama principal"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            flow_services.delete_branch(branch.name, branch.flow)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        summary="Listar nodos de flujos",
        description=(
            "Obtiene todos los nodos (pasos) en el árbol de flujos. Los nodos "
            "pueden ser compartidos entre múltiples ramas (deduplicación por content_hash). "
            "Usa ?mine=true para obtener solo los nodos de "
            "flujos creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo los nodos de flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Nodes"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de nodo",
        description="Recupera información de un nodo específico, incluyendo su contenido, "
        "padre y hash de contenido. Solo lectura.",
        tags=["Nodes"],
    ),
)
class FlowNodeViewSet(StandardEnvelopeMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet para nodos del árbol de flujos (solo lectura, deduplicación por hash)."""

    queryset = FlowNode.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]
    search_fields = ["content_hash"]
    ordering_fields = ["id", "created_at"]

    def get_serializer_class(self):
        return FlowNodeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(flow__owner=self.request.user)
        if not flow_services.user_can_read_all_flows(self.request.user):
            qs = qs.filter(flow__owner=self.request.user)
        return qs
