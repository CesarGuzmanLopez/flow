"""
Vistas de gestión de ejecuciones (executions y SSE).
"""

from django.http import Http404, StreamingHttpResponse
from django.utils.timezone import now
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from .. import services as flow_services
from ..domain.services import FlowExecutionService, FlowPermissionService
from ..models import ExecutionSnapshot, StepExecution
from ..serializers import (
    ExecutionSnapshotSerializer,
    StepExecutionSerializer,
)
from ..sse import step_log_broker


class BaseFlowViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "flows"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Listar ejecuciones de flujos",
        description=(
            "Obtiene todos los snapshots de ejecución de flujos. Cada snapshot "
            "representa una ejecución completa de un flujo con sus inputs, outputs y metadata. "
            "Usa ?mine=true para obtener solo las ejecuciones de flujos creados por el "
            "usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo las ejecuciones de flujos creados por el usuario"
                " autenticado.",
            ),
        ],
        tags=["Executions"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de ejecución",
        description="Recupera información completa de un snapshot de ejecución, incluyendo "
        "la versión del flujo ejecutada, usuario que la disparó y timestamp.",
        tags=["Executions"],
    ),
    create=extend_schema(
        summary="Crear snapshot de ejecución",
        description="Crea un nuevo snapshot de ejecución para un flujo. Típicamente se usa "
        "a través del endpoint execute de FlowVersion.",
        tags=["Executions"],
    ),
)
class ExecutionSnapshotViewSet(BaseFlowViewSet):
    """ViewSet para gestión de snapshots de ejecución de flujos."""

    queryset = ExecutionSnapshot.objects.all()
    serializer_class = ExecutionSnapshotSerializer
    search_fields = ["metadata"]
    ordering_fields = ["id", "created_at"]

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(flow_version__flow__owner=self.request.user)
        return flow_services.filter_snapshots_for_user(qs, self.request.user)

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Listar ejecuciones de pasos",
        description="Obtiene todas las ejecuciones de pasos individuales dentro de un snapshot "
        "de ejecución, incluyendo inputs, outputs, estado y artefactos generados.",
        tags=["Executions"],
    )
    def steps(self, request, pk=None):
        """Obtiene las ejecuciones de pasos de un snapshot."""
        snapshot = self.get_object()
        executions = snapshot.step_executions.all()
        serializer = StepExecutionSerializer(executions, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listar todas las ejecuciones de pasos",
        description=(
            "Obtiene todas las ejecuciones individuales de pasos a través de todos "
            "los snapshots de ejecución. "
            "Usa ?mine=true para obtener solo las ejecuciones de pasos de "
            "flujos creados por el usuario autenticado."
        ),
        parameters=[
            OpenApiParameter(
                name="mine",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filtrar solo las ejecuciones de"
                " pasos de flujos creados por el usuario autenticado.",
            ),
        ],
        tags=["Step Executions"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de ejecución de paso",
        description="Recupera información detallada de la ejecución de un paso específico, "
        "incluyendo inputs, outputs, estado (success/failure), logs y artefactos producidos.",
        tags=["Step Executions"],
    ),
)
class StepExecutionViewSet(BaseFlowViewSet):
    """ViewSet para gestión de ejecuciones individuales de pasos."""

    queryset = StepExecution.objects.all()
    serializer_class = StepExecutionSerializer
    search_fields = ["status", "error_message"]
    ordering_fields = ["id", "started_at", "completed_at"]

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(
                execution_snapshot__flow_version__flow__owner=self.request.user
            )
        # Asumiendo que hay un filter_step_executions_for_user o similar; si no, ajustar
        return qs  # O implementar filtro similar

    @action(detail=True, methods=["get"], url_path="status")
    @extend_schema(
        summary="Consultar estado de ejecución de un Step",
        description="Retorna el estado actual, timestamps y salida de la ejecución.",
        tags=["Step Executions"],
    )
    def status(self, request, pk=None):  # type: ignore[override]
        step_exec = self.get_object()
        flow = step_exec.step.flow_version.flow
        if not FlowPermissionService.can_user_read_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = {
            "id": step_exec.id,
            "status": step_exec.status,
            "started_at": step_exec.started_at,
            "completed_at": step_exec.completed_at,
            "error_message": step_exec.error_message,
            "outputs": step_exec.outputs,
        }
        return Response(data)

    @action(detail=True, methods=["post"], url_path="cancel")
    @extend_schema(
        summary="Cancelar ejecución de Step",
        description=(
            "Marca la ejecución como cancelada si está en estado pending/running y "
            "cierra el stream de logs."
        ),
        tags=["Step Executions"],
    )
    def cancel(self, request, pk=None):  # type: ignore[override]
        step_exec = self.get_object()
        flow = step_exec.step.flow_version.flow
        if not FlowPermissionService.can_user_execute_flow(request.user, flow):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if step_exec.status in ("pending", "running"):
            step_exec.status = "cancelled"
            step_exec.completed_at = now()
            step_exec.save(update_fields=["status", "completed_at"])
            FlowExecutionService.log_step_output(
                step_exec, "Execution cancelled", event="cancel"
            )
            FlowExecutionService.complete_step_logs(step_exec)
            return Response({"ok": True})
        return Response(
            {"error": f"No se puede cancelar en estado {step_exec.status}"},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ========================================================================
# SSE: Streaming de logs de StepExecution
# ========================================================================


@extend_schema(
    summary="Stream SSE de logs de un StepExecution",
    description=(
        "Devuelve un stream Server-Sent Events (text/event-stream) con los logs de "
        "ejecución de un step. Úsalo desde el frontend con EventSource."
    ),
    tags=["Executions", "SSE"],
    parameters=[
        OpenApiParameter(
            name="pk",
            description="ID del StepExecution",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        )
    ],
)
def step_execution_logs_stream(request, pk: str):  # type: ignore[override]
    """Endpoint SSE para consumir logs en tiempo real de un StepExecution."""
    if not request.user or not request.user.is_authenticated:
        # Forzamos auth; si se requiere público, cambiar a AllowAny + tokens firmados
        raise Http404()

    try:
        step_execution = StepExecution.objects.select_related(
            "execution_snapshot__flow_version__flow__owner"
        ).get(pk=pk)
    except StepExecution.DoesNotExist:
        raise Http404()

    # Verificar permisos de lectura del flow
    flow = step_execution.step.flow_version.flow
    if not FlowPermissionService.can_user_read_flow(request.user, flow):
        raise Http404()

    def event_stream():
        # Comentario inicial para confirmar conexión
        yield ": connected\n\n"
        # Anunciar inicio
        step_log_broker.publish(
            step_execution.id,
            event="start",
            data={"at": now().isoformat()},
        )
        # Reenviar el stream del broker
        for chunk in step_log_broker.stream(step_execution.id):
            yield chunk

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    # Encabezados recomendados para SSE
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Nginx: deshabilita buffering
    response["Connection"] = "keep-alive"
    return response


@extend_schema(
    summary="Append de log a un StepExecution",
    description=(
        "Publica una línea de log (o JSON) hacia los suscriptores del stream SSE del "
        "StepExecution. Acepta { line: string, event?: string, end?: boolean }."
    ),
    tags=["Executions", "SSE"],
)
def step_execution_logs_append(request, pk: str):  # type: ignore[override]
    """Endpoint para publicar logs a un StepExecution (solo usuarios autorizados)."""
    if request.method != "POST":
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if not request.user or not request.user.is_authenticated:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    try:
        step_execution = StepExecution.objects.select_related(
            "execution_snapshot__flow_version__flow__owner", "step__flow"
        ).get(pk=pk)
    except StepExecution.DoesNotExist:
        raise Http404()

    # Verificar permiso de ejecución/escritura en el flujo
    flow = step_execution.step.flow_version.flow
    if not FlowPermissionService.can_user_execute_flow(request.user, flow):
        return Response(status=status.HTTP_403_FORBIDDEN)

    payload = request.data or {}
    line = payload.get("line", "")
    event_name = payload.get("event", "log")
    end_flag = bool(payload.get("end", False))

    if line:
        step_log_broker.publish(
            step_execution.id,
            event=event_name,
            data={"line": str(line), "at": now().isoformat()},
        )

    if end_flag:
        step_log_broker.complete(step_execution.id)

    return Response({"ok": True})
