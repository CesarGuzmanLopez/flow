"""
Modelos de dominio para la aplicación de flujos de trabajo.

Define las entidades del sistema de workflows con arquitectura de árbol sin merges:
- Flow: Flujo de trabajo principal (workflow) con propietario
- FlowVersion: Versiones congeladas de flujos para reproducibilidad
- Step: Pasos individuales de un flujo con configuración
- StepDependency: Dependencias entre pasos
- Artifact: Artefactos content-addressable asociados a pasos
- ExecutionSnapshot: Instantáneas de ejecución de flujos
- StepExecution: Ejecución individual de pasos
- StepExecutionArtifact: Artefactos generados en ejecuciones
- FlowNode: Nodos del árbol de flujo (sin ciclos, sin duplicación)
- FlowBranch: Ramas del árbol de flujo con head móvil
"""

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

if TYPE_CHECKING:  # Solo para chequeo de tipos (evita import circular en runtime)
    pass


class Flow(models.Model):
    """Entidad principal de flujo de trabajo (workflow)."""

    name: models.CharField = models.CharField(max_length=200)
    description: models.TextField = models.TextField(blank=True)
    owner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flows"
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        """Compatibility: allow created_by alias for owner on creation.

        Tests may pass created_by=<user>; map it to owner if provided.
        """
        created_by = kwargs.pop("created_by", None)
        if created_by is not None and "owner" not in kwargs:
            kwargs["owner"] = created_by
        super().__init__(*args, **kwargs)


class FlowVersion(models.Model):
    """Version control for flows - allows branching without merging"""

    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name="versions")
    version_number = models.IntegerField()
    parent_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_versions",
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_frozen = models.BooleanField(default=False)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ["flow", "version_number"]

    def __str__(self):
        return f"{self.flow.name} v{self.version_number}"


class Step(models.Model):
    """Individual step in a flow version"""

    flow_version = models.ForeignKey(
        FlowVersion, on_delete=models.CASCADE, related_name="steps"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    step_type = models.CharField(max_length=100)
    order = models.IntegerField()
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        unique_together = ["flow_version", "order"]

    def __str__(self):
        return f"{self.flow_version} - {self.name}"


class StepDependency(models.Model):
    """Defines dependencies between steps"""

    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name="depends_on")
    depends_on_step = models.ForeignKey(
        Step, on_delete=models.CASCADE, related_name="required_by"
    )

    class Meta:
        unique_together = ["step", "depends_on_step"]

    def __str__(self):
        return f"{self.step.name} depends on {self.depends_on_step.name}"


class Artifact(models.Model):
    """Content-addressable artifacts (files, data) with SHA256 hash"""

    sha256 = models.CharField(max_length=64, unique=True, db_index=True)
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.BigIntegerField()
    storage_path = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="artifacts"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.sha256[:8]})"


class ExecutionSnapshot(models.Model):
    """Immutable snapshot of a flow execution"""

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("partial", "Partial"),
    ]

    flow_version = models.ForeignKey(
        FlowVersion, on_delete=models.CASCADE, related_name="executions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triggered_executions",
    )
    metadata = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Execution of {self.flow_version} at {self.created_at}"


class StepExecution(models.Model):
    """Execution record for a single step"""

    STATUS_CHOICES: list[tuple[str, str]] = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    step = models.ForeignKey(Step, on_delete=models.CASCADE, related_name="executions")
    execution_snapshot = models.ForeignKey(
        ExecutionSnapshot, on_delete=models.CASCADE, related_name="step_executions"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    inputs = models.JSONField(default=dict, blank=True)
    outputs = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["started_at"]

    def __str__(self):
        return f"{self.step.name} execution ({self.status})"


class StepExecutionArtifact(models.Model):
    """Links artifacts produced during step execution"""

    step_execution = models.ForeignKey(
        StepExecution, on_delete=models.CASCADE, related_name="execution_artifacts"
    )
    artifact = models.ForeignKey(
        Artifact, on_delete=models.CASCADE, related_name="produced_by_executions"
    )
    artifact_type = models.CharField(max_length=100)

    class Meta:
        unique_together = ["step_execution", "artifact"]

    def __str__(self):
        return f"{self.artifact.filename} from {self.step_execution}"


# ========================================================================
# Árbol de nodos para flujos (algoritmo sin merges, sin ciclos)
# ========================================================================


class FlowNode(models.Model):
    """Nodo en el árbol de flujo. Cada nodo tiene exactamente un padre (excepto raíz).

    Los nodos se comparten entre ramas hasta el punto de ramificación. Esto
    permite un árbol de flujo con ramas sin merges y sin duplicación de contenido.
    """

    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name="nodes")
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children_nodes",
    )
    content = models.JSONField()  # Configuración del paso
    content_hash = models.CharField(max_length=64, db_index=True)  # SHA256 del content
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_flow_nodes",
    )

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["flow", "content_hash"]),
        ]

    def __str__(self):
        return f"Node {self.id} in {self.flow.name}"


class FlowBranch(models.Model):
    """Rama nombrada en un flujo. Apunta al head (nodo final) y start_node (raíz de la rama).

    Las ramas permiten versionar y explorar alternativas sin merges. Cada rama
    es una vista lineal del árbol desde la raíz hasta el head.
    """

    flow = models.ForeignKey(Flow, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=200)
    head = models.ForeignKey(
        FlowNode, on_delete=models.CASCADE, related_name="branch_heads"
    )
    start_node = models.ForeignKey(
        FlowNode, on_delete=models.CASCADE, related_name="branch_starts"
    )
    parent_branch = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="child_branches",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_branches",
    )

    class Meta:
        unique_together = ["flow", "name"]
        ordering = ["created_at"]

    def __str__(self):
        return f"Branch '{self.name}' in {self.flow.name}"
