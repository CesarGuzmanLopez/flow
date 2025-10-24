"""
Views package for flows app.

Organiza las vistas en módulos específicos por funcionalidad:
- views_flows.py: FlowViewSet, FlowVersionViewSet
- views_steps.py: StepViewSet
- views_artifacts.py: ArtifactViewSet
- views_executions.py: ExecutionSnapshotViewSet, StepExecutionViewSet, funciones SSE
- views_branches.py: FlowBranchViewSet, FlowNodeViewSet
"""

from .views_artifacts import ArtifactViewSet
from .views_branches import FlowBranchViewSet, FlowNodeViewSet
from .views_executions import (
    ExecutionSnapshotViewSet,
    StepExecutionViewSet,
    step_execution_logs_append,
    step_execution_logs_stream,
)
from .views_flows import FlowVersionViewSet, FlowViewSet
from .views_steps import StepViewSet

__all__ = [
    "FlowViewSet",
    "FlowVersionViewSet",
    "StepViewSet",
    "ArtifactViewSet",
    "ExecutionSnapshotViewSet",
    "StepExecutionViewSet",
    "FlowBranchViewSet",
    "FlowNodeViewSet",
    "step_execution_logs_stream",
    "step_execution_logs_append",
]
