"""
Configuración del panel de administración para notificaciones.

Registra modelos de notificaciones y suscripciones webhook.
"""

from django.contrib import admin

from .models import NotificationLog, WebhookSubscription


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Configuración del admin para logs de notificaciones."""

    list_display = (
        "notification_id",
        "notification_type",
        "recipient",
        "status",
        "priority",
        "created_at",
        "sent_at",
    )
    list_filter = ("notification_type", "status", "priority", "created_at")
    search_fields = ("recipient", "subject", "notification_id")
    readonly_fields = ("notification_id", "created_at", "sent_at", "failed_at")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Identificación",
            {"fields": ("notification_id", "notification_type", "recipient")},
        ),
        (
            "Contenido",
            {"fields": ("subject", "message", "template_name")},
        ),
        (
            "Estado",
            {
                "fields": (
                    "status",
                    "priority",
                    "created_at",
                    "sent_at",
                    "failed_at",
                )
            },
        ),
        (
            "Errores",
            {"fields": ("error_message", "retry_count", "max_retries")},
        ),
        (
            "Metadata",
            {"fields": ("metadata",)},
        ),
    )


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):
    """Configuración del admin para suscripciones webhook."""

    list_display = (
        "name",
        "user",
        "event_type",
        "is_active",
        "total_sent",
        "total_failed",
        "created_at",
    )
    list_filter = ("event_type", "is_active", "created_at")
    search_fields = ("name", "webhook_url", "user__username")
    readonly_fields = ("created_at", "updated_at", "last_sent_at")
    ordering = ("-created_at",)

    fieldsets = (
        (
            "Información",
            {"fields": ("user", "name", "event_type", "is_active")},
        ),
        (
            "Configuración",
            {"fields": ("webhook_url", "secret")},
        ),
        (
            "Estadísticas",
            {"fields": ("total_sent", "total_failed", "last_sent_at")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
