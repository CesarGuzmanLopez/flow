"""
Serializadores de Django REST Framework para la aplicación de usuarios.

Define serializadores para convertir modelos de usuarios, roles y permisos a JSON
y viceversa. Incluye:
- PermissionSerializer: Para permisos individuales
- RoleSerializer: Para roles con sus permisos anidados
- UserSerializer: Para usuarios con roles y universidad
- UserCreateSerializer: Para creación de usuarios con validación de contraseña
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .domain.services import UserAuthenticationService
from .models import Permission, Role, RolePermission

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "codename",
            "resource",
            "action",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(
        source="role_permissions.permission", many=True, read_only=True
    )
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Permission.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
            "permissions",
            "permission_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", [])
        role = Role.objects.create(**validated_data)
        for permission in permission_ids:
            RolePermission.objects.create(role=role, permission=permission)
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        instance = super().update(instance, validated_data)

        if permission_ids is not None:
            instance.role_permissions.all().delete()
            for permission in permission_ids:
                RolePermission.objects.create(role=instance, permission=permission)

        return instance


class UserSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        write_only=True,
        required=False,
        source="roles",
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "university",
            "is_active",
            "roles",
            "role_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"password": {"write_only": True}}


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )
    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        write_only=True,
        required=False,
        source="roles",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "university",
            "password",
            "password2",
            "role_ids",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        roles = validated_data.pop("roles", [])
        # Usar el servicio para crear el usuario
        user, is_new = UserAuthenticationService.create_user(**validated_data)
        if not is_new:
            raise serializers.ValidationError({"username": "El usuario ya existe."})
        user.roles.set(roles)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializador para cambio de contraseña.

    Permite a un usuario cambiar su contraseña proporcionando la actual y la nueva.
    Los administradores pueden cambiar contraseñas sin conocer la actual.
    """

    old_password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="Contraseña actual (requerida para usuarios no admin)",
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        min_length=8,
        help_text="Nueva contraseña (mínimo 8 caracteres)",
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Confirmación de nueva contraseña",
    )

    def validate(self, attrs):
        """Valida que las contraseñas coincidan."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."}
            )
        return attrs

    def validate_old_password(self, value):
        """Valida que la contraseña actual sea correcta (si se proporciona)."""
        user = self.context["request"].user
        if value and not UserAuthenticationService.verify_password(user, value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value


class UpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializador para actualización de perfil de usuario.

    Permite actualizar datos básicos del usuario sin modificar contraseña ni roles.
    """

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "university",
        ]

    def validate_email(self, value):
        """Verifica que el email no esté en uso por otro usuario."""
        user = self.context["request"].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está en uso.")
        return value


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    """
    Serializador para que administradores actualicen usuarios.

    Permite modificar roles, estado activo y toda la información del usuario.
    """

    role_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Role.objects.all(),
        write_only=True,
        required=False,
        source="roles",
    )
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "university",
            "is_active",
            "is_staff",
            "role_ids",
            "roles",
        ]
        read_only_fields = ["roles"]

    def update(self, instance, validated_data):
        """Actualiza el usuario y sus roles si se proporcionan."""
        roles = validated_data.pop("roles", None)
        instance = super().update(instance, validated_data)

        if roles is not None:
            instance.roles.set(roles)

        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializador para solicitar recuperación de contraseña.

    Permite a usuarios solicitar un enlace de recuperación vía email.
    """

    email = serializers.EmailField(
        required=True,
        help_text="Email del usuario que solicita recuperación de contraseña",
    )

    def validate_email(self, value):
        """Verifica que exista un usuario con ese email."""
        if not User.objects.filter(email=value, is_active=True).exists():
            # Por seguridad, no revelamos si el email existe o no
            # pero internamente verificamos
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializador para confirmar recuperación de contraseña con token.
    """

    token = serializers.CharField(
        required=True, help_text="Token de recuperación recibido por email"
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        min_length=8,
        help_text="Nueva contraseña (mínimo 8 caracteres)",
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Confirmación de nueva contraseña",
    )

    def validate(self, attrs):
        """Valida que las contraseñas coincidan."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."}
            )
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializador para verificación de email con token.
    """

    token = serializers.CharField(
        required=True, help_text="Token de verificación recibido por email"
    )
