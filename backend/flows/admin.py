"""
Configuración del panel de administración de Django para la app Flows.

Registra los modelos principales para facilitar la gestión administrativa
de flujos, versiones, pasos, artefactos y ejecuciones. Mantiene una
configuración sencilla y legible, alineada con SOLID (SRP: un admin por
modelo) y arquitectura hexagonal (adaptador de infraestructura/UI).
"""

from django.contrib import admin

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


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "updated_at", "created_at")
    list_filter = ("owner",)
    search_fields = ("name", "description", "owner__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(FlowVersion)
class FlowVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flow",
        "version_number",
        "parent_version",
        "created_by",
        "is_frozen",
        "created_at",
    )
    list_filter = ("flow", "is_frozen")
    search_fields = ("flow__name",)
    readonly_fields = ("created_at",)


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ("id", "flow_version", "order", "name", "step_type")
    list_filter = ("flow_version", "step_type")
    search_fields = ("name", "flow_version__flow__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(StepDependency)
class StepDependencyAdmin(admin.ModelAdmin):
    list_display = ("id", "step", "depends_on_step")
    list_filter = ("step",)
    search_fields = ("step__name", "depends_on_step__name")


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    list_display = ("id", "filename", "content_type", "size", "created_by")
    list_filter = ("content_type",)
    search_fields = ("filename", "sha256")
    readonly_fields = ("created_at",)


@admin.register(ExecutionSnapshot)
class ExecutionSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "flow_version",
        "triggered_by",
        "status",
        "created_at",
    )
    list_filter = ("status",)
    readonly_fields = ("created_at",)


@admin.register(StepExecution)
class StepExecutionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "step",
        "execution_snapshot",
        "status",
        "started_at",
        "completed_at",
    )
    list_filter = ("status",)
    readonly_fields = ("started_at", "completed_at")


@admin.register(StepExecutionArtifact)
class StepExecutionArtifactAdmin(admin.ModelAdmin):
    list_display = ("id", "step_execution", "artifact", "artifact_type")
    list_filter = ("artifact_type",)
    search_fields = ("artifact__filename", "artifact__sha256")


@admin.register(FlowNode)
class FlowNodeAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "parent", "content_hash", "created_at")
    list_filter = ("flow",)
    search_fields = ("content_hash", "flow__name")
    readonly_fields = ("created_at",)


@admin.register(FlowBranch)
class FlowBranchAdmin(admin.ModelAdmin):
    list_display = ("id", "flow", "name", "head", "start_node", "created_at")
    list_filter = ("flow",)
    search_fields = ("name", "flow__name")
    readonly_fields = ("created_at",)
