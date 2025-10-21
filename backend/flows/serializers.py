"""
Serializadores de Django REST Framework para la aplicación de flujos.

Define serializadores para convertir modelos de flujos de trabajo a JSON y viceversa.
Incluye:
- FlowSerializer: Flujos con versiones y propietario
- FlowVersionSerializer: Versiones de flujos con pasos
- StepSerializer: Pasos con dependencias y artefactos
- ArtifactSerializer: Artefactos asociados a pasos
- ExecutionSnapshotSerializer: Instantáneas de ejecución
- StepExecutionSerializer: Ejecuciones individuales de pasos
- FlowBranchSerializer: Ramas de flujos (sistema de árbol)
- FlowNodeSerializer: Nodos del árbol de flujo
- AddStepSerializer: Para agregar pasos a ramas
- CreateBranchSerializer: Para crear nuevas ramas
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Artifact,
    ExecutionSnapshot,
    Flow,
    FlowBranch,
    FlowNode,
    FlowVersion,
    Step,
    StepDependency,
    StepExecution,
    StepExecutionArtifact,
)

User = get_user_model()


class ArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artifact
        fields = [
            "id",
            "sha256",
            "filename",
            "content_type",
            "size",
            "storage_path",
            "metadata",
            "created_at",
            "created_by",
        ]
        read_only_fields = ["id", "created_at", "created_by"]


class StepDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = StepDependency
        fields = ["id", "step", "depends_on_step"]


class StepSerializer(serializers.ModelSerializer):
    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Step.objects.all(),
        required=False,
        source="depends_on.depends_on_step",
    )

    class Meta:
        model = Step
        fields = [
            "id",
            "flow_version",
            "name",
            "description",
            "step_type",
            "order",
            "config",
            "dependencies",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FlowVersionSerializer(serializers.ModelSerializer):
    steps = StepSerializer(many=True, read_only=True)

    class Meta:
        model = FlowVersion
        fields = [
            "id",
            "flow",
            "version_number",
            "parent_version",
            "created_at",
            "created_by",
            "metadata",
            "is_frozen",
            "steps",
        ]
        read_only_fields = ["id", "created_at", "created_by"]


class FlowSerializer(serializers.ModelSerializer):
    current_version = FlowVersionSerializer(read_only=True)
    versions = FlowVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Flow
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "created_at",
            "updated_at",
            "current_version",
            "versions",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class StepExecutionArtifactSerializer(serializers.ModelSerializer):
    artifact = ArtifactSerializer(read_only=True)

    class Meta:
        model = StepExecutionArtifact
        fields = ["id", "step_execution", "artifact", "artifact_type"]


class StepExecutionSerializer(serializers.ModelSerializer):
    execution_artifacts = StepExecutionArtifactSerializer(many=True, read_only=True)

    class Meta:
        model = StepExecution
        fields = [
            "id",
            "step",
            "execution_snapshot",
            "started_at",
            "completed_at",
            "status",
            "inputs",
            "outputs",
            "error_message",
            "execution_artifacts",
        ]
        read_only_fields = ["id", "started_at"]


class ExecutionSnapshotSerializer(serializers.ModelSerializer):
    step_executions = StepExecutionSerializer(many=True, read_only=True)

    class Meta:
        model = ExecutionSnapshot
        fields = [
            "id",
            "flow_version",
            "created_at",
            "triggered_by",
            "metadata",
            "status",
            "step_executions",
        ]
        read_only_fields = ["id", "created_at", "triggered_by"]


# ========================================================================
# Serializers para árbol de nodos
# ========================================================================


class FlowNodeSerializer(serializers.ModelSerializer):
    """Serializer para nodos del árbol de flujo."""

    class Meta:
        model = FlowNode
        fields = [
            "id",
            "flow",
            "parent",
            "content",
            "content_hash",
            "created_at",
            "created_by",
        ]
        read_only_fields = ["id", "content_hash", "created_at", "created_by"]


class FlowBranchSerializer(serializers.ModelSerializer):
    """Serializer para ramas del flujo."""

    path_length = serializers.SerializerMethodField()

    class Meta:
        model = FlowBranch
        fields = [
            "id",
            "flow",
            "name",
            "head",
            "start_node",
            "parent_branch",
            "created_at",
            "created_by",
            "path_length",
        ]
        read_only_fields = ["id", "head", "start_node", "created_at", "created_by"]

    def get_path_length(self, obj) -> int:
        """Calcula el número de pasos en la rama."""
        from . import services as flow_services

        try:
            path = flow_services.get_path(obj.name, obj.flow)
            return len(path)
        except ValueError:
            return 0


class AddStepSerializer(serializers.Serializer):
    """Serializer para añadir un paso a una rama."""

    content = serializers.JSONField(required=True, help_text="Contenido del paso")


class CreateBranchSerializer(serializers.Serializer):
    """Serializer para crear una nueva rama."""

    name = serializers.CharField(
        max_length=200, required=True, help_text="Nombre de la nueva rama"
    )
    from_branch = serializers.CharField(
        max_length=200, required=True, help_text="Rama padre desde la cual ramificar"
    )
    at_step = serializers.IntegerField(
        min_value=1,
        required=True,
        help_text="Número de paso (1-indexed) donde iniciar la nueva rama",
    )
