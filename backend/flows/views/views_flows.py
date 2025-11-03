"""
Vistas de gestión de flujos y versiones.
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
from ..domain.flujo.builder import create_flow_from_definition
from ..domain.flujo.definitions import get_definition, list_definitions
from ..domain.steps.interface import (
    DataStack,
    StepContext,
    execute_step,
)
from ..models import ExecutionSnapshot, Flow, FlowVersion, Step
from ..serializers import (
    CreateBranchSerializer,
    ExecutionSnapshotSerializer,
    FlowBranchSerializer,
    FlowSerializer,
    FlowVersionSerializer,
    StepSerializer,
)


class BaseFlowViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar flujos de trabajo",
        description=(
            "Obtiene todos los flujos de trabajo (workflows) accesibles por el usuario. "
            "Los usuarios con permisos globales ven todos los flujos, mientras que los demás "
            "solo ven sus propios flujos. Usa ?mine=true para obtener solo los "
            "creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo los flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Flows"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de un flujo",
        description="Recupera la información completa de un flujo específico por su ID.",
        tags=["Flows"],
    ),
    create=extend_schema(
        summary="Crear un nuevo flujo",
        description="Crea un nuevo flujo de trabajo. Automáticamente inicializa una rama "
        "principal vacía para el flujo. El usuario autenticado se asigna como propietario.",
        tags=["Flows"],
    ),
    partial_update=extend_schema(
        summary="Actualizar flujo parcialmente",
        description="Actualiza campos específicos de un flujo existente (PATCH parcial).",
        tags=["Flows"],
    ),
    destroy=extend_schema(
        summary="Eliminar un flujo",
        description="Elimina permanentemente un flujo y todas sus versiones, ramas y "
        "nodos asociados.",
        tags=["Flows"],
    ),
)
class FlowViewSet(BaseFlowViewSet):
    """ViewSet para gestión de flujos de trabajo (workflows)."""

    queryset = Flow.objects.all()
    serializer_class = FlowSerializer
    search_fields = ["name", "description"]
    ordering_fields = ["id", "created_at", "name"]
    permission_required = {
        "versions": ("flows", "read"),
        "create_version": ("flows", "write"),
    }

    def perform_create(self, serializer):
        flow = serializer.save(owner=self.request.user)
        # Inicializar rama principal automáticamente
        try:
            flow_services.initialize_main_branch(flow, self.request.user)
        except ValueError:
            # Si ya existe, ignorar (no debería pasar en creación)
            pass

    def get_queryset(self):
        """Soporta filtrado por propiedad del usuario y query param ?mine=true.

        - Si ?mine=true, devuelve solo flows del usuario.
        - En caso contrario, filtra según permisos (todas vs. propias).
        """
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(owner=self.request.user)
        return flow_services.filter_flows_for_user(qs, self.request.user)

    def update(self, request, *args, **kwargs):
        """PUT method disabled for security reasons. Use PATCH instead."""
        from rest_framework import status
        from rest_framework.response import Response

        return Response(
            {
                "error": "Method PUT not allowed",
                "detail": "Use PATCH /api/flows/{id}/ para actualizaciones.",
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Listar versiones de un flujo",
        description="Obtiene todas las versiones (congeladas o no) de un flujo específico. "
        "Las versiones congeladas son instantáneas inmutables del flujo.",
        tags=["Flows"],
    )
    def versions(self, request, pk=None):
        """Obtiene todas las versiones de un flujo."""
        flow = cast(Flow, self.get_object())
        versions = flow.versions.all()
        serializer = FlowVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="create-branch")
    @extend_schema(
        summary="Crear rama en un flujo",
        description="Crea una nueva rama en el árbol del flujo a partir de un nodo específico "
        "de una rama existente. Permite experimentar con variaciones sin afectar otras ramas. "
        "No se permiten merges (arquitectura de árbol sin ciclos).",
        tags=["Flows", "Branches"],
    )
    def create_branch(self, request, pk=None):
        """Crea una nueva rama en el flujo."""
        flow = cast(Flow, self.get_object())
        serializer = CreateBranchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            branch = flow_services.create_branch(
                serializer.validated_data["name"],
                flow,
                serializer.validated_data["from_branch"],
                serializer.validated_data["at_step"],
                request.user,
            )
            return Response(
                FlowBranchSerializer(branch).data, status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_version(self, request, pk=None):
        """Create a new version for a flow"""
        flow = cast(Flow, self.get_object())
        data = request.data.copy()
        data["flow"] = flow.id
        data["created_by"] = request.user.id

        serializer = FlowVersionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="definitions")
    def list_definitions_action(self, request):
        """List available flow definitions (predefined templates)."""
        return Response({"definitions": list_definitions()})

    @action(detail=False, methods=["post"], url_path="create-from-definition")
    def create_from_definition(self, request):
        """Create a flow instance from a registered definition.

        Body: { key: str, name?: str, params_override?: { index: dict } }
        """
        key = request.data.get("key")
        if not key:
            return Response(
                {"detail": "'key' is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        defn = get_definition(key)
        flow_name = request.data.get("name")
        raw_override = request.data.get("params_override") or {}
        # Coerce string indices to integers for builder compatibility
        params_override = {}
        if isinstance(raw_override, dict):
            for k, v in raw_override.items():
                try:
                    idx = int(k)
                except (TypeError, ValueError):
                    continue
                params_override[idx] = v
        flow = create_flow_from_definition(
            owner=request.user,
            defn=defn,
            name=flow_name,
            params_override=params_override,
        )
        ser = FlowSerializer(flow)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="create-cadma1")
    @extend_schema(
        summary="Crear flujo CADMA 1 con paso inicial",
        description=(
            "Crea un flujo 'CADMA 1' con el primer paso 'crear familia de referencia'.\n"
            "Params del paso: { mode: 'existing'|'new', family_id?, name?, smiles_list? }"
        ),
        tags=["Flows"],
    )
    def create_cadma1(self, request):
        """Crea un flow con el primer paso 'create_reference_family' ejecutado."""
        user = request.user
        params = request.data or {}
        # Ejecutar el step lógicamente (agnóstico de flow) para producir outputs
        ctx = StepContext(user=user, data_stack=DataStack())
        result = execute_step("create_reference_family", ctx, params)

        # Crear Flow y primera versión + Step registro
        flow = Flow.objects.create(name="CADMA 1", description="", owner=user)
        flow_services.initialize_main_branch(flow, user)
        version = FlowVersion.objects.create(
            flow=flow, version_number=1, parent_version=None, created_by=user
        )
        step = Step.objects.create(
            flow_version=version,
            name="Crear familia de referencia",
            description="",
            step_type="create_reference_family",
            order=1,
            config={"params": params, "metadata": result.metadata},
        )

        ser = FlowSerializer(flow)
        return Response(
            {
                "flow": ser.data,
                "initial_step": step.id,
                "outputs": result.outputs,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def mine(self, request):
        """Devuelve los flows creados por el usuario autenticado.

        Endpoint de conveniencia usado por el frontend y tests: retorna únicamente
        los flujos cuyo `owner` es el usuario autenticado.
        """
        if not request.user or not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        qs = self.get_queryset().filter(owner=request.user)
        serializer = FlowSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listar versiones de flujos",
        description=(
            "Obtiene todas las versiones de flujos del sistema que el usuario puede ver. "
            "Usa ?mine=true para obtener solo las versiones de flujos "
            "creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo las versiones de"
                "flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Flow Versions"],
    ),
    retrieve=extend_schema(
        summary="Obtener versión de flujo",
        description="Recupera los detalles de una versión específica de un flujo.",
        tags=["Flow Versions"],
    ),
    create=extend_schema(
        summary="Crear versión de flujo",
        description="Crea una nueva versión (snapshot) de un flujo. Las versiones pueden ser "
        "congeladas para hacerlas inmutables.",
        tags=["Flow Versions"],
    ),
    partial_update=extend_schema(
        summary="Actualizar versión parcialmente",
        description="Actualiza campos específicos de una versión (solo si no está congelada).",
        tags=["Flow Versions"],
    ),
    destroy=extend_schema(
        summary="Eliminar versión de flujo",
        description="Elimina una versión de flujo (típicamente no permitido si está congelada).",
        tags=["Flow Versions"],
    ),
)
class FlowVersionViewSet(BaseFlowViewSet):
    """ViewSet para gestión de versiones de flujos (snapshots inmutables)."""

    queryset = FlowVersion.objects.all()
    serializer_class = FlowVersionSerializer
    search_fields = ["version_number"]
    ordering_fields = ["id", "created_at", "version_number"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(flow__owner=self.request.user)
        return flow_services.filter_versions_for_user(qs, self.request.user)

    def update(self, request, *args, **kwargs):
        """PUT method disabled for security reasons. Use PATCH instead."""
        from rest_framework import status
        from rest_framework.response import Response

        return Response(
            {
                "error": "Method PUT not allowed",
                "detail": "Use PATCH /api/flow-versions/{id}/ para actualizaciones.",
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Congelar versión de flujo",
        description="Congela una versión de flujo, haciéndola inmutable. Una vez congelada, "
        "no puede ser modificada ni descongelada. Útil para preservar estados específicos.",
        tags=["Flow Versions"],
    )
    def freeze(self, request, pk=None):
        """Congela una versión de flujo (la hace inmutable)."""
        version = cast(FlowVersion, self.get_object())
        if version.is_frozen:
            return Response(
                {"error": "Version is already frozen"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        version.is_frozen = True
        version.save()
        serializer = self.get_serializer(version)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Ejecutar versión de flujo",
        description="Crea un snapshot de ejecución para una versión de flujo. Registra inputs "
        "y metadata de la ejecución. Los resultados de cada paso se almacenan en step executions.",
        tags=["Executions"],
    )
    def execute(self, request, pk=None):
        """Ejecuta una versión de flujo creando un snapshot de ejecución."""
        version = cast(FlowVersion, self.get_object())
        inputs = request.data.get("inputs", {})

        snapshot = ExecutionSnapshot.objects.create(
            flow_version=version, triggered_by=request.user, metadata={"inputs": inputs}
        )

        serializer = ExecutionSnapshotSerializer(snapshot)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="append-step")
    @extend_schema(
        summary="Agregar paso a la versión",
        description=(
            "Agrega un paso (por step_type) a la versión. Params del paso van en 'params'.\n"
            "Si faltan datos, se pueden inferir de un contexto anterior (simplificado)."
        ),
        tags=["Flow Versions", "Steps"],
    )
    def append_step(self, request, pk=None):
        version = cast(FlowVersion, self.get_object())
        payload = request.data or {}
        step_type = payload.get("step_type")
        params = payload.get("params") or {}

        if not step_type:
            return Response(
                {"error": "step_type requerido"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Obtenemos el último orden
        last_step = version.steps.order_by("-order").first()
        next_order = (last_step.order + 1) if last_step else 1

        step = Step.objects.create(
            flow_version=version,
            step_type=step_type,
            config=params,
            order=next_order,
        )
        return Response(StepSerializer(step).data, status=status.HTTP_201_CREATED)
