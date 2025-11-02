"""
Views para la API REST de notificaciones.

Implementa los endpoints para gestionar notificaciones de usuario.
"""

from typing import cast

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import UserNotification
from .serializers import UserNotificationSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Listar notificaciones del usuario",
        description="Retorna todas las notificaciones del usuario autenticado.",
    ),
    create=extend_schema(
        summary="Crear notificación",
        description="Crea una nueva notificación para el usuario.",
    ),
    retrieve=extend_schema(
        summary="Obtener notificación",
        description="Retorna una notificación específica por ID.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente notificación",
        description="Actualiza parcialmente una notificación.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ],
    ),
    destroy=extend_schema(
        summary="Eliminar notificación",
        description="Elimina una notificación.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ],
    ),
)
class UserNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificaciones de usuario.

    Proporciona operaciones CRUD para notificaciones visibles al usuario.
    """

    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    # Expose a base queryset so schema generation can infer model/field types
    queryset = UserNotification.objects.all()
    # Use explicit 'id' as lookup to align URL kwarg and schema parameter name
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        """Retorna solo las notificaciones del usuario autenticado."""
        user = self.request.user
        if user.is_authenticated:
            # Cast to int to satisfy type checker - pk is always an int for authenticated users
            user_id = int(user.pk) if user.pk is not None else None
            if user_id is not None:
                return UserNotification.objects.filter(user=user_id)
        return UserNotification.objects.none()

    def update(self, request, *args, **kwargs):
        """PUT method disabled for security reasons. Use PATCH instead."""
        from rest_framework import status

        return Response(
            {
                "error": "Method PUT not allowed",
                "detail": "Use PATCH /api/notifications/{id}/ para actualizaciones.",
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @extend_schema(
        summary="Marcar notificación como leída",
        description="Marca una notificación específica como leída.",
        parameters=[
            OpenApiParameter(
                name="id",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID de la notificación",
            )
        ],
    )
    @action(detail=True, methods=["post"])
    def mark_as_read(self, request, id=None):
        """Marca una notificación específica como leída."""
        notification_obj = self.get_object()
        notification = cast(UserNotification, notification_obj)
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @extend_schema(
        summary="Marcar todas como leídas",
        description="Marca todas las notificaciones del usuario como leídas.",
    )
    @action(detail=False, methods=["post"])
    def mark_all_as_read(self, request):
        """Marca todas las notificaciones del usuario como leídas."""
        from django.utils import timezone

        self.get_queryset().filter(read=False).update(read=True, read_at=timezone.now())
        return Response({"message": "All notifications marked as read"})

    @extend_schema(
        summary="Contar notificaciones no leídas",
        description="Retorna el conteo de notificaciones no leídas del usuario.",
    )
    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        """Retorna el conteo de notificaciones no leídas."""
        count = self.get_queryset().filter(read=False).count()
        return Response({"unread_count": count})
