"""
Modelos de dominio para la app Users.

Define las entidades del sistema de autenticación y RBAC:
- User: usuario extendido con roles y campo universidad
- Role: rol para control de acceso basado en roles
- Permission: permiso granular (resource:action)
- RolePermission: relación many-to-many entre roles y permisos
- UserToken: tokens para verificación de email y recuperación de contraseña
"""

import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Role(models.Model):
    """Rol para control de acceso basado en roles (RBAC)."""

    # Campos tipados con django-stubs
    name: models.CharField = models.CharField(max_length=100, unique=True)
    description: models.TextField = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(models.Model):
    """Permiso para control de acceso granular (resource:action)."""

    name: models.CharField = models.CharField(max_length=100)
    codename: models.CharField = models.CharField(max_length=100, unique=True)
    resource: models.CharField = models.CharField(max_length=100)
    action: models.CharField = models.CharField(max_length=50)
    description: models.TextField = models.TextField(blank=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["resource", "action"]
        unique_together = ["resource", "action"]

    def __str__(self):
        return f"{self.resource}:{self.action}"


class RolePermission(models.Model):
    """Relación many-to-many entre roles y permisos."""

    role: models.ForeignKey = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="role_permissions"
    )
    permission: models.ForeignKey = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )
    granted_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["role", "permission"]

    def __str__(self):
        return f"{self.role.name} -> {self.permission.codename}"


class User(AbstractUser):
    """Modelo de usuario extendido con roles y campos adicionales."""

    roles: models.ManyToManyField = models.ManyToManyField(
        Role, related_name="users", blank=True
    )
    university: models.CharField = models.CharField(
        max_length=255, blank=True, default=""
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Verifica si el usuario tiene un permiso específico a través de sus roles.

        Args:
            resource: Nombre del recurso (ej: 'flows', 'chemistry', 'users')
            action: Acción del permiso (ej: 'read', 'write', 'execute')

        Returns:
            bool: True si el usuario tiene el permiso, False en caso contrario
        """
        return Permission.objects.filter(
            role_permissions__role__in=self.roles.all(),
            resource=resource,
            action=action,
        ).exists()

    def get_all_permissions(self):
        """
        Obtiene todos los permisos del usuario a través de sus roles.

        Returns:
            QuerySet de Permission: Permisos únicos del usuario
        """
        return Permission.objects.filter(
            role_permissions__role__in=self.roles.all()
        ).distinct()

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.username


class UserToken(models.Model):
    """
    Tokens para verificación de email y recuperación de contraseña.

    Tipos de token:
    - email_verification: Para verificar el email del usuario
    - password_reset: Para recuperación de contraseña olvidada
    """

    TOKEN_TYPE_CHOICES: list[tuple[str, str]] = [
        ("email_verification", "Verificación de Email"),
        ("password_reset", "Recuperación de Contraseña"),
    ]

    user: models.ForeignKey = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tokens"
    )
    token: models.CharField = models.CharField(
        max_length=100, unique=True, db_index=True
    )
    token_type: models.CharField = models.CharField(
        max_length=20, choices=TOKEN_TYPE_CHOICES
    )
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    expires_at: models.DateTimeField = models.DateTimeField()
    used_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token", "token_type"]),
            models.Index(fields=["user", "token_type"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.token_type} - {self.token[:8]}..."

    @classmethod
    def generate_token(
        cls, user: "User", token_type: str, expiry_hours: int = 24
    ) -> "UserToken":
        """
        Genera un nuevo token para el usuario.

        Args:
            user: Usuario para el que se genera el token
            token_type: Tipo de token ('email_verification' o 'password_reset')
            expiry_hours: Horas de validez del token (default: 24)

        Returns:
            UserToken: Token generado
        """
        # Generar token aleatorio seguro
        token_value = secrets.token_urlsafe(32)

        # Calcular fecha de expiración
        expires_at = timezone.now() + timedelta(hours=expiry_hours)

        # Crear y guardar el token
        token = cls.objects.create(
            user=user, token=token_value, token_type=token_type, expires_at=expires_at
        )

        return token

    def is_valid(self) -> bool:
        """Verifica si el token es válido (no usado y no expirado)."""
        if self.used_at is not None:
            return False
        if timezone.now() > self.expires_at:
            return False
        return True

    def mark_as_used(self) -> None:
        """Marca el token como usado."""
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])
