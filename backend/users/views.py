"""
Vistas (ViewSets) de la aplicación de usuarios.

Define los endpoints REST API para:
- Gestión de usuarios (CRUD, perfil, asignación de roles)
- Gestión de roles (lectura y escritura)
- Gestión de permisos (solo lectura)
- Cambio de contraseña
- Recuperación de contraseña
- Verificación de email

Incluye control de acceso basado en roles y permisos personalizados.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Permission, Role, UserToken
from .permissions import HasAppPermission
from .serializers import (
    AdminUpdateUserSerializer,
    ChangePasswordSerializer,
    EmailVerificationSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PermissionSerializer,
    RoleSerializer,
    UpdateUserSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description="Obtiene todos los usuarios del sistema. Requiere permisos administrativos "
        "(users:read) para ver usuarios distintos al propio.",
        tags=["Users"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de usuario",
        description="Recupera información completa de un usuario específico, incluyendo sus "
        "roles asignados y universidad asociada.",
        tags=["Users"],
    ),
    create=extend_schema(
        summary="Crear nuevo usuario",
        description="Registra un nuevo usuario en el sistema. Solo administradores con "
        "permisos users:write pueden crear usuarios. Se requiere username y password.",
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Actualizar usuario completo",
        description="Actualiza todos los campos de un usuario existente. Requiere permisos "
        "users:write.",
        tags=["Users"],
    ),
    partial_update=extend_schema(
        summary="Actualizar usuario parcialmente",
        description="Actualiza campos específicos de un usuario. Requiere permisos users:write.",
        tags=["Users"],
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        description="Elimina un usuario del sistema. Requiere permisos users:write. "
        "Cuidado: esto puede afectar integridad referencial con flujos y moléculas.",
        tags=["Users"],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios con RBAC (control de acceso basado en roles)."""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "users"
    permission_required = {
        # 'me' debe estar accesible para cualquier usuario autenticado;
        # no lo mapeamos a users:read para evitar requerir permisos administrativos.
        "permissions": ("users", "read"),
        "create": ("users", "write"),
        "update": ("users", "write"),
        "partial_update": ("users", "write"),
        "destroy": ("users", "write"),
    }

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=["get"])
    @extend_schema(
        summary="Listar permisos de usuario",
        description="Obtiene todos los permisos efectivos de un usuario, agregados a través "
        "de todos sus roles asignados. Útil para depuración y auditoría de permisos.",
        tags=["Users", "Permissions"],
    )
    def permissions(self, request, pk=None):
        """Obtiene todos los permisos de un usuario a través de sus roles."""
        user = self.get_object()
        permissions_qs = user.get_all_permissions()
        serializer = PermissionSerializer(permissions_qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    @extend_schema(
        summary="Obtener perfil del usuario actual",
        description="Recupera la información completa del usuario autenticado (yo). "
        "No requiere permisos administrativos. Útil para inicializar perfil en frontend.",
        tags=["Users"],
    )
    def me(self, request):
        """Obtiene información del usuario autenticado."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="me/update")
    @extend_schema(
        summary="Actualizar perfil propio",
        description="Permite al usuario actualizar su propia información"
        " (nombre, email, universidad). "
        "No permite cambiar contraseña (usar endpoint change-password) ni roles.",
        tags=["Users"],
        request=UpdateUserSerializer,
        responses={200: UserSerializer},
    )
    def update_me(self, request):
        """Actualiza el perfil del usuario autenticado."""
        serializer = UpdateUserSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Retornar datos completos del usuario
        return Response(UserSerializer(request.user).data)

    @action(detail=True, methods=["patch"], url_path="admin-update")
    @extend_schema(
        summary="Actualizar usuario (Admin)",
        description="Permite a administradores actualizar cualquier usuario, incluyendo roles, "
        "estado activo y permisos de staff. Requiere permisos users:write.",
        tags=["Users", "Admin"],
        request=AdminUpdateUserSerializer,
        responses={200: UserSerializer},
    )
    def admin_update(self, request, pk=None):
        """Permite a administradores actualizar usuarios completamente."""
        if not (
            request.user.is_superuser or request.user.has_permission("users", "write")
        ):
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        serializer = AdminUpdateUserSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(UserSerializer(user).data)

    @action(detail=False, methods=["post"], url_path="change-password")
    @extend_schema(
        summary="Cambiar contraseña propia",
        description="Permite al usuario cambiar su propia "
        "contraseña proporcionando la actual y la nueva.",
        tags=["Users", "Authentication"],
        request=ChangePasswordSerializer,
        responses={
            200: {"description": "Contraseña cambiada exitosamente"},
            400: {"description": "Datos inválidos o contraseña actual incorrecta"},
        },
    )
    def change_password(self, request):
        """Cambia la contraseña del usuario autenticado."""
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # Verificar contraseña actual
        if not request.user.check_password(
            serializer.validated_data.get("old_password", "")
        ):
            return Response(
                {"old_password": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cambiar contraseña
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()

        return Response({"detail": "Contraseña cambiada exitosamente."})

    @action(detail=True, methods=["post"], url_path="admin-change-password")
    @extend_schema(
        summary="Cambiar contraseña de usuario (Admin)",
        description="Permite a administradores cambiar la contraseña de cualquier usuario "
        "sin necesidad de conocer la contraseña actual. Requiere permisos users:write.",
        tags=["Users", "Admin"],
        request=ChangePasswordSerializer,
        responses={
            200: {"description": "Contraseña cambiada exitosamente"},
            403: {"description": "Sin permisos"},
        },
    )
    def admin_change_password(self, request, pk=None):
        """Permite a administradores cambiar contraseñas de usuarios."""
        if not (
            request.user.is_superuser or request.user.has_permission("users", "write")
        ):
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # Cambiar contraseña sin verificar la actual
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": f"Contraseña de {user.username} cambiada exitosamente."}
        )

    @action(detail=True, methods=["post"], url_path="activate")
    @extend_schema(
        summary="Activar usuario",
        description="Activa un usuario desactivado. Solo administradores."
        " Requiere permisos users:write.",
        tags=["Users", "Admin"],
        responses={200: UserSerializer},
    )
    def activate(self, request, pk=None):
        """Activa un usuario desactivado."""
        if not (
            request.user.is_superuser or request.user.has_permission("users", "write")
        ):
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        user.is_active = True
        user.save()

        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="deactivate")
    @extend_schema(
        summary="Desactivar usuario",
        description="Desactiva un usuario. El usuario no podrá iniciar sesión hasta que sea "
        "reactivado. Solo administradores. Requiere permisos users:write.",
        tags=["Users", "Admin"],
        responses={200: UserSerializer},
    )
    def deactivate(self, request, pk=None):
        """Desactiva un usuario."""
        if not (
            request.user.is_superuser or request.user.has_permission("users", "write")
        ):
            return Response(
                {"detail": "No tienes permisos para realizar esta acción."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()

        # No permitir desactivarse a sí mismo
        if user.id == request.user.id:
            return Response(
                {"detail": "No puedes desactivarte a ti mismo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = False
        user.save()

        return Response(UserSerializer(user).data)

    @action(detail=False, methods=["post"], url_path="request-password-reset")
    @extend_schema(
        summary="Solicitar recuperación de contraseña",
        description="Envía un email con un enlace para recuperar la contraseña. "
        "No requiere autenticación.",
        tags=["Authentication"],
        request=PasswordResetRequestSerializer,
        responses={
            200: {
                "description": "Si el email existe, se envió el enlace de recuperación"
            },
        },
    )
    def request_password_reset(self, request):
        """Solicita recuperación de contraseña vía email."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email, is_active=True)

            # Generar token de recuperación
            token = UserToken.generate_token(
                user=user, token_type="password_reset", expiry_hours=24
            )

            # Construir enlace de recuperación
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"

            # Enviar email
            subject = "Recuperación de Contraseña - ChemFlow"
            message = f"""
Hola {user.first_name or user.username},

Recibimos una solicitud para restablecer la contraseña de tu cuenta en ChemFlow.

Para crear una nueva contraseña, haz clic en el siguiente enlace:
{reset_url}

Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo.

Saludos,
El equipo de ChemFlow
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe o no
            pass

        return Response(
            {
                "detail": "Si el email está registrado, "
                "recibirás instrucciones para recuperar tu contraseña."
            }
        )

    @action(detail=False, methods=["post"], url_path="reset-password")
    @extend_schema(
        summary="Confirmar recuperación de contraseña",
        description="Usa el token recibido por email para establecer una nueva contraseña. "
        "No requiere autenticación.",
        tags=["Authentication"],
        request=PasswordResetConfirmSerializer,
        responses={
            200: {"description": "Contraseña restablecida exitosamente"},
            400: {"description": "Token inválido o expirado"},
        },
    )
    def reset_password(self, request):
        """Confirma la recuperación de contraseña con token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_value = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            token = UserToken.objects.get(
                token=token_value, token_type="password_reset"
            )

            if not token.is_valid():
                return Response(
                    {"detail": "El token es inválido o ha expirado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Cambiar contraseña
            user = token.user
            user.set_password(new_password)
            user.save()

            # Marcar token como usado
            token.mark_as_used()

            return Response(
                {
                    "detail": "Contraseña restablecida exitosamente. Ya puedes iniciar sesión."
                }
            )

        except UserToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"], url_path="send-verification-email")
    @extend_schema(
        summary="Enviar email de verificación",
        description="Envía un email de verificación al usuario autenticado. "
        "Útil si el usuario perdió el email original.",
        tags=["Authentication"],
        responses={200: {"description": "Email de verificación enviado"}},
    )
    def send_verification_email(self, request):
        """Envía email de verificación al usuario autenticado."""
        user = request.user

        # Generar token de verificación
        token = UserToken.generate_token(
            user=user,
            token_type="email_verification",
            expiry_hours=48,  # 2 días
        )

        # Construir enlace de verificación
        verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"

        # Enviar email
        subject = "Verifica tu email - ChemFlow"
        message = f"""
Hola {user.first_name or user.username},

¡Bienvenido a ChemFlow!

Para completar tu registro, por favor"
" verifica tu dirección de email haciendo clic en el siguiente enlace:
{verify_url}

Este enlace expirará en 48 horas.

Saludos,
El equipo de ChemFlow
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response({"detail": f"Email de verificación enviado a {user.email}"})

    @action(detail=False, methods=["post"], url_path="verify-email")
    @extend_schema(
        summary="Verificar email con token",
        description="Verifica el email del usuario usando el token recibido por correo. "
        "No requiere autenticación.",
        tags=["Authentication"],
        request=EmailVerificationSerializer,
        responses={
            200: {"description": "Email verificado exitosamente"},
            400: {"description": "Token inválido o expirado"},
        },
    )
    def verify_email(self, request):
        """Verifica el email del usuario con el token."""
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_value = serializer.validated_data["token"]

        try:
            token = UserToken.objects.get(
                token=token_value, token_type="email_verification"
            )

            if not token.is_valid():
                return Response(
                    {"detail": "El token es inválido o ha expirado."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Marcar email como verificado (puedes agregar un campo email_verified al User)
            user = token.user
            user.is_active = True  # o usar un campo email_verified personalizado
            user.save()

            # Marcar token como usado
            token.mark_as_used()

            return Response(
                {"detail": "Email verificado exitosamente. Tu cuenta está activa."}
            )

        except UserToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    list=extend_schema(
        summary="Listar roles",
        description="Obtiene todos los roles del sistema RBAC. Los roles agrupan permisos "
        "y se asignan a usuarios (ej: admin, scientist, viewer).",
        tags=["Roles"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de rol",
        description="Recupera información completa de un rol, incluyendo todos los permisos "
        "asociados.",
        tags=["Roles"],
    ),
    create=extend_schema(
        summary="Crear nuevo rol",
        description="Crea un nuevo rol en el sistema. Se pueden asignar permisos específicos "
        "al momento de creación o posteriormente.",
        tags=["Roles"],
    ),
    update=extend_schema(
        summary="Actualizar rol completo",
        description="Actualiza todos los campos de un rol, incluyendo su lista de permisos.",
        tags=["Roles"],
    ),
    partial_update=extend_schema(
        summary="Actualizar rol parcialmente",
        description="Actualiza campos específicos de un rol.",
        tags=["Roles"],
    ),
    destroy=extend_schema(
        summary="Eliminar rol",
        description="Elimina un rol del sistema. Los usuarios que tenían este rol perderán "
        "los permisos asociados.",
        tags=["Roles"],
    ),
)
class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de roles del sistema RBAC."""

    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "users"


@extend_schema_view(
    list=extend_schema(
        summary="Listar permisos disponibles",
        description="Obtiene todos los permisos definidos en el sistema (resource:action). "
        "Solo lectura. Los permisos se crean típicamente via seed o migraciones.",
        tags=["Permissions"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de permiso",
        description="Recupera información de un permiso específico, incluyendo su recurso, "
        "acción, codename y descripción.",
        tags=["Permissions"],
    ),
)
class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listado de permisos del sistema (solo lectura)."""

    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "users"
