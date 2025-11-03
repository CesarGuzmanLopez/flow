
"""
Modelos Django para ejecuciones duraderas, checkpoints y transactional outbox.
Incluye Execution, Checkpoint, OutboxEntry.
"""

from __future__ import annotations

import uuid

# from typing import TYPE_CHECKING
from django.db import models
from django.utils import timezone


class ExecutionStatus(models.TextChoices):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_RETRY = "waiting_retry"
    WAITING_RESUME = "waiting_resume"
    BROKEN = "broken"


# (TYPE_CHECKING import moved inside class for mypy only)


class Execution(models.Model):
    # Explicitly declare the default manager for mypy
    objects: models.Manager["Execution"] = models.Manager()

    # For type checking: declare related manager for checkpoints
    # For type checking: declare related manager for checkpoints
    # (import TYPE_CHECKING at the top if not already present)
    try:
        from typing import TYPE_CHECKING
    except ImportError:
        TYPE_CHECKING = False
    if TYPE_CHECKING:
        from django.db.models import Manager

        checkpoints: "Manager[Checkpoint]"
        outbox_entries: "Manager[OutboxEntry]"
    execution_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    idempotency_key = models.CharField(max_length=128, db_index=True)
    provider_name = models.CharField(max_length=64)
    status = models.CharField(
        max_length=32, choices=ExecutionStatus.choices, default=ExecutionStatus.PENDING
    )
    payload = models.JSONField()
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=["idempotency_key"]),
            models.Index(fields=["provider_name", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider_name", "idempotency_key"],
                name="uq_provider_idempotency",
            )
        ]
        app_label = "chemistry"


class Checkpoint(models.Model):
    # Explicitly declare the default manager for mypy
    objects: models.Manager["Checkpoint"] = models.Manager()
    execution = models.ForeignKey(
        Execution, on_delete=models.CASCADE, related_name="checkpoints"
    )
    step = models.CharField(max_length=128)
    data = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("execution", "step", "version")
        ordering = ["-created_at"]
        app_label = "chemistry"


class OutboxEntry(models.Model):
    # Explicitly declare the default manager for mypy
    objects: models.Manager["OutboxEntry"] = models.Manager()
    execution = models.ForeignKey(
        Execution, on_delete=models.CASCADE, related_name="outbox_entries"
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    processed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["processed"]),
            models.Index(fields=["event_type"]),
        ]
        app_label = "chemistry"
