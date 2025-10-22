"""
Serializers para la API REST de notificaciones.

Convierte modelos Django a JSON y viceversa para la API.
"""

from rest_framework import serializers

from .models import UserNotification


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones de usuario."""

    class Meta:
        model = UserNotification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "priority",
            "read",
            "created_at",
            "read_at",
            "metadata",
        ]
        read_only_fields = ["id", "created_at", "read_at"]

    def to_representation(self, instance):
        """Personaliza la representación para incluir campos calculados."""
        data = super().to_representation(instance)
        # Asegurar que created_at sea serializable
        if hasattr(data["created_at"], "isoformat"):
            data["created_at"] = data["created_at"].isoformat()
        if data.get("read_at") and hasattr(data["read_at"], "isoformat"):
            data["read_at"] = data["read_at"].isoformat()
        return data
