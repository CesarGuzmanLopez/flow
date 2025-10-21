"""
Configuración de URLs para la app Flows.

Registra todos los endpoints REST de la app usando el router de DRF:
- /api/flows/flows/ - Gestión de flujos (workflows)
- /api/flows/versions/ - Versiones de flujos (congeladas)
- /api/flows/steps/ - Pasos/tareas de flujos
- /api/flows/artifacts/ - Artefactos content-addressable
- /api/flows/executions/ - Snapshots de ejecución
- /api/flows/step-executions/ - Ejecución de pasos individuales
- /api/flows/branches/ - Ramas del árbol de flujo
- /api/flows/nodes/ - Nodos del árbol (compartidos entre ramas)
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArtifactViewSet,
    ExecutionSnapshotViewSet,
    FlowBranchViewSet,
    FlowNodeViewSet,
    FlowVersionViewSet,
    FlowViewSet,
    StepExecutionViewSet,
    StepViewSet,
    step_execution_logs_append,
    step_execution_logs_stream,
)

router = DefaultRouter()
router.register(r"flows", FlowViewSet, basename="flow")
router.register(r"versions", FlowVersionViewSet, basename="flowversion")
router.register(r"steps", StepViewSet, basename="step")
router.register(r"artifacts", ArtifactViewSet, basename="artifact")
router.register(r"executions", ExecutionSnapshotViewSet, basename="execution")
router.register(r"step-executions", StepExecutionViewSet, basename="stepexecution")
# Árbol de nodos
router.register(r"branches", FlowBranchViewSet, basename="branch")
router.register(r"nodes", FlowNodeViewSet, basename="node")

urlpatterns = [
    path("", include(router.urls)),
    # SSE stream y append de logs de StepExecution
    path(
        "step-executions/<uuid:pk>/logs/stream/",
        step_execution_logs_stream,
        name="step-execution-logs-stream",
    ),
    path(
        "step-executions/<uuid:pk>/logs/append/",
        step_execution_logs_append,
        name="step-execution-logs-append",
    ),
]
