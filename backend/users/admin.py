"""
Configuración del panel de administración de Django para la app Users.

Registra modelos de usuarios, roles, permisos y sus relaciones,
extendiendo el UserAdmin de Django para incluir campos personalizados.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Permission, Role, RolePermission, User, UserToken
from django.utils.translation import gettext_lazy as _


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Configuración del admin para roles."""

    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Configuración del admin para permisos."""

    list_display = ("codename", "resource", "action", "name")
    list_filter = ("resource", "action")
    search_fields = ("codename", "name")


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    """Configuración del admin para relaciones rol-permiso."""

    list_display = ("role", "permission", "granted_at")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Configuración del admin para usuarios, extendiendo UserAdmin de Django."""

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "email", "university")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    """Configuración del admin para tokens de usuario."""

    list_display = (
        "user",
        "token_type",
        "created_at",
        "expires_at",
        "is_valid",
        "used_at",
    )
    list_filter = ("token_type", "created_at", "expires_at")
    search_fields = ("user__username", "user__email", "token")
    readonly_fields = ("token", "created_at", "used_at")
    ordering = ("-created_at",)

    def is_valid(self, obj):
        """Muestra si el token es válido."""
        return obj.is_valid()

    is_valid.boolean = True
    is_valid.short_description = "Válido"
