"""
Vistas de gestión de pasos (steps) en flujos.
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
from ..domain.services import FlowExecutionService, FlowPermissionService
from ..domain.steps.interface import (
    DataStack,
    StepContext,
    execute_step,
    list_step_specs,
)
from ..models import ExecutionSnapshot, Step
from ..serializers import (
    StepExecutionSerializer,
    StepSerializer,
)


class BaseFlowViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar pasos de flujos",
        description=(
            "Obtiene todos los pasos (tareas) definidos en los flujos del sistema. "
            "Usa ?mine=true para obtener solo los pasos de "
            "flujos creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo los pasos de flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Steps"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de un paso",
        description="Recupera la información completa de un paso específico de un flujo.",
        tags=["Steps"],
    ),
    create=extend_schema(
        summary="Crear un paso",
        description="Crea un nuevo paso (tarea) en un flujo, definiendo su configuración, "
        "inputs esperados y outputs generados.",
        tags=["Steps"],
    ),
    partial_update=extend_schema(
        summary="Actualizar paso parcialmente",
        description="Actualiza campos específicos de un paso existente.",
        tags=["Steps"],
    ),
    destroy=extend_schema(
        summary="Eliminar un paso",
        description="Elimina un paso de un flujo.",
        tags=["Steps"],
    ),
)
class StepViewSet(BaseFlowViewSet):
    """ViewSet para gestión de pasos (tareas) en flujos de trabajo."""

    queryset = Step.objects.all()
    serializer_class = StepSerializer
    search_fields = ["name", "step_type", "description"]
    ordering_fields = ["id", "order", "flow_version__id"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(flow_version__flow__owner=self.request.user)
        return flow_services.filter_steps_for_user(qs, self.request.user)

    def update(self, request, *args, **kwargs):
        """PUT method disabled for security reasons. Use PATCH instead."""
        from rest_framework import status
        from rest_framework.response import Response

        return Response(
            {
                "error": "Method PUT not allowed",
                "detail": "Use PATCH /api/steps/{id}/ para actualizaciones.",
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["get"], url_path="catalog")
    @extend_schema(
        summary="Catálogo de pasos disponibles",
        description="Lista los step types registrados con sus esquemas de entrada/salida",
        tags=["Steps"],
    )
    def catalog(self, request):
        return Response({"steps": list_step_specs()})

    @action(detail=False, methods=["post"], url_path="execute")
    @extend_schema(
        summary="Ejecutar step agnóstico",
        description=(
            "Ejecuta un step reutilizable sin pertenecer a un flujo.\n"
            "Body: { step_type: string, params: object }"
        ),
        tags=["Steps"],
    )
    def execute(self, request):
        payload = request.data or {}
        step_type = payload.get("step_type")
        params = payload.get("params") or {}
        if not step_type:
            return Response(
                {"error": "step_type is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        ctx = StepContext(user=request.user, data_stack=DataStack())
        result = execute_step(step_type, ctx, params)
        return Response(
            {"outputs": result.outputs, "metadata": result.metadata},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="run")
    @extend_schema(
        summary="Ejecutar un Step dentro de un snapshot",
        description=(
            "Ejecuta el Step seleccionado creando (o usando) un ExecutionSnapshot y "
            "registrando una StepExecution con logs SSE.\n"
            "Body opcional: { snapshot_id?: number, send_email?: boolean, webhook_url?: string }"
        ),
        tags=["Steps", "Executions"],
    )
    def run(self, request, pk=None):
        step_obj = self.get_object()
        step = cast(Step, step_obj)
        flow = step.flow_version.flow
        if not FlowPermissionService.can_user_execute_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)

        payload = request.data or {}
        snapshot_id = payload.get("snapshot_id")
        send_email = bool(payload.get("send_email", False))
        webhook_url = payload.get("webhook_url")
        override_params = payload.get("params")

        snapshot = None
        if snapshot_id:
            try:
                snapshot = ExecutionSnapshot.objects.get(
                    id=snapshot_id, flow_version=step.flow_version
                )
            except ExecutionSnapshot.DoesNotExist:
                return Response(
                    {"error": "snapshot_id inválido para este Step"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            snapshot = ExecutionSnapshot.objects.create(
                flow_version=step.flow_version,
                triggered_by=request.user,
                metadata={"inputs": step.config.get("params", {})},
            )

        # Iniciar ejecución
        step_exec = FlowExecutionService.start_step_execution(
            step, snapshot, send_email=send_email, webhook_url=webhook_url
        )
        # If runtime params are provided, store them in execution inputs
        if isinstance(override_params, dict):
            step_exec.inputs = override_params
            step_exec.save(update_fields=["inputs"])

        # Ejecutar lógica agnóstica del step
        try:
            FlowExecutionService.log_step_output(
                step_exec, f"Starting step '{step.step_type}'"
            )
            ctx = StepContext(user=request.user, data_stack=DataStack())
            effective_params = (
                override_params
                if isinstance(override_params, dict)
                else step.config.get("params", {})
            )
            result = execute_step(step.step_type, ctx, effective_params)
            # Persistir outputs del step
            step_exec.outputs = result.outputs or {}
            step_exec.save(update_fields=["outputs"])
            FlowExecutionService.complete_step_execution(
                step_exec, webhook_url=webhook_url
            )
            FlowExecutionService.complete_step_logs(step_exec)

            # Completar snapshot si no hay otras ejecuciones vinculadas
            other_exists = snapshot.step_executions.exclude(id=step_exec.id).exists()
            if not other_exists:
                FlowExecutionService.complete_flow_execution(
                    snapshot, webhook_url=webhook_url
                )

            return Response(
                StepExecutionSerializer(step_exec).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:  # noqa: BLE001 - registramos el error textual
            FlowExecutionService.fail_step_execution(
                step_exec, str(e), webhook_url=webhook_url
            )
            FlowExecutionService.complete_step_logs(step_exec)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
