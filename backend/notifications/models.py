"""
Modelos Django para el sistema de notificaciones.

Persiste las notificaciones en la base de datos para auditoría y reintentos.
"""

from django.conf import settings
from django.db import models


class NotificationLog(models.Model):
    """
    Registro de notificaciones enviadas.

    Persiste información sobre notificaciones para auditoría y reintentos.
    """

    TYPE_CHOICES = [
        ("email", "Email"),
        ("webhook", "Webhook"),
        ("realtime", "Tiempo Real"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("sent", "Enviado"),
        ("failed", "Fallido"),
        ("retrying", "Reintentando"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Baja"),
        ("normal", "Normal"),
        ("high", "Alta"),
        ("urgent", "Urgente"),
    ]

    # Identificación
    notification_id = models.UUIDField(unique=True, db_index=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Contenido
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    template_name = models.CharField(max_length=100, blank=True)

    # Estado
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="normal", db_index=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "notification_logs"
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["notification_type", "status"]),
            models.Index(fields=["priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} - {self.recipient} - {self.status}"


class WebhookSubscription(models.Model):
    """
    Suscripción a webhooks para eventos del sistema.

    Permite configurar webhooks para recibir notificaciones de eventos.
    """

    EVENT_CHOICES = [
        ("flow.step.started", "Step Iniciado"),
        ("flow.step.completed", "Step Completado"),
        ("flow.step.failed", "Step Fallido"),
        ("flow.completed", "Flujo Completado"),
        ("user.registered", "Usuario Registrado"),
        ("user.password_reset", "Recuperación de Contraseña"),
    ]

    # Propietario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webhook_subscriptions",
    )

    # Configuración
    name = models.CharField(max_length=100)
    webhook_url = models.URLField()
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    is_active = models.BooleanField(default=True, db_index=True)

    # Seguridad
    secret = models.CharField(max_length=255, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Estadísticas
    total_sent = models.IntegerField(default=0)
    total_failed = models.IntegerField(default=0)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "webhook_subscriptions"
        verbose_name = "Suscripción Webhook"
        verbose_name_plural = "Suscripciones Webhook"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["event_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.event_type}"


class UserNotification(models.Model):
    """
    Notificaciones visibles para el usuario.

    Almacena notificaciones que los usuarios pueden ver en su panel,
    como actualizaciones de flujos, errores, etc.
    """

    TYPE_CHOICES = [
        ("info", "Información"),
        ("success", "Éxito"),
        ("warning", "Advertencia"),
        ("error", "Error"),
        ("flow_update", "Actualización de Flujo"),
        ("system", "Sistema"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Baja"),
        ("normal", "Normal"),
        ("high", "Alta"),
        ("urgent", "Urgente"),
    ]

    # Usuario destinatario
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )

    # Contenido
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info")
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="normal", db_index=True
    )

    # Estado
    read = models.BooleanField(default=False, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "user_notifications"
        verbose_name = "Notificación de Usuario"
        verbose_name_plural = "Notificaciones de Usuario"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "read", "created_at"]),
            models.Index(fields=["user", "priority", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """Marca la notificación como leída."""
        from django.utils import timezone

        if not self.read:
            self.read = True
            self.read_at = timezone.now()
            self.save(update_fields=["read", "read_at"])
