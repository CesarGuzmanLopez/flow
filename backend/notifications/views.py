"""
Views para la API REST de notificaciones.

Implementa los endpoints para gestionar notificaciones de usuario.
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserNotification
from .serializers import UserNotificationSerializer


class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificaciones de usuario.

    Proporciona operaciones CRUD para notificaciones visibles al usuario.
    """

    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retorna solo las notificaciones del usuario autenticado."""
        return UserNotification.objects.filter(user=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ]
    )
    def mark_as_read(self, request, pk=None):
        """Marca una notificación específica como leída."""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def mark_all_as_read(self, request):
        """Marca todas las notificaciones del usuario como leídas."""
        from django.utils import timezone

        self.get_queryset().filter(read=False).update(read=True, read_at=timezone.now())
        return Response({"message": "All notifications marked as read"})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Retorna el conteo de notificaciones no leídas."""
        count = self.get_queryset().filter(read=False).count()
        return Response({"unread_count": count})
