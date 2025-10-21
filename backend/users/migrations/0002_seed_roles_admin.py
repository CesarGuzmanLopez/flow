"""
Migración de datos para poblar roles, permisos y usuario admin.

Esta migración crea:
- Roles por defecto: admin, moderator, editor, viewer, scientist
- Permisos base: users.read/write, flows.read/write/execute, chemistry.read/write
- Usuario admin por defecto con contraseña 'admin123'
- Asignación de permisos a roles según su nivel de acceso
"""

from django.conf import settings
from django.db import migrations


def seed_roles_and_admin(apps, _schema_editor):
    """
    Crea roles, permisos y usuario administrador por defecto.

    Args:
        apps: Registro de aplicaciones de Django
        _schema_editor: Editor de esquema (no usado)
    """
    Role = apps.get_model("users", "Role")
    Permission = apps.get_model("users", "Permission")
    RolePermission = apps.get_model("users", "RolePermission")
    User = apps.get_model("users", "User")

    # Ensure 5 roles exist
    role_names = [
        "admin",
        "moderator",
        "editor",
        "viewer",
        "scientist",
    ]
    roles = {}
    for name in role_names:
        role, _ = Role.objects.get_or_create(name=name)
        roles[name] = role

    # Create some default permissions
    perms = [
        ("users", "read", "users_read"),
        ("users", "write", "users_write"),
        ("flows", "read", "flows_read"),
        ("flows", "write", "flows_write"),
        ("flows", "execute", "flows_execute"),
        ("chemistry", "read", "chem_read"),
        ("chemistry", "write", "chem_write"),
    ]
    perm_objs = {}
    for res, act, code in perms:
        perm, _ = Permission.objects.get_or_create(
            resource=res,
            action=act,
            defaults={"name": f"{res}:{act}", "codename": code},
        )
        perm_objs[(res, act)] = perm

    # Grant permissions to roles (admin gets all)
    for perm in perm_objs.values():
        RolePermission.objects.get_or_create(role=roles["admin"], permission=perm)

    for key in [("flows", "read"), ("chemistry", "read")]:
        RolePermission.objects.get_or_create(
            role=roles["viewer"], permission=perm_objs[key]
        )

    for key in [
        ("flows", "read"),
        ("flows", "write"),
        ("flows", "execute"),
        ("chemistry", "read"),
        ("chemistry", "write"),
    ]:
        RolePermission.objects.get_or_create(
            role=roles["editor"], permission=perm_objs[key]
        )

    for key in [("users", "read"), ("flows", "read"), ("chemistry", "read")]:
        RolePermission.objects.get_or_create(
            role=roles["moderator"], permission=perm_objs[key]
        )

    for key in [("chemistry", "read"), ("chemistry", "write")]:
        RolePermission.objects.get_or_create(
            role=roles["scientist"], permission=perm_objs[key]
        )

    # Create an admin user if not exists; use env vars when available
    admin_username = getattr(settings, "ADMIN_USERNAME", None) or "admin"
    admin_email = getattr(settings, "ADMIN_EMAIL", None) or "admin@example.com"
    admin_password = getattr(settings, "ADMIN_PASSWORD", None) or "admin1234"

    if not User.objects.filter(username=admin_username).exists():
        admin = User.objects.create_superuser(
            username=admin_username, email=admin_email, password=admin_password
        )
        admin.roles.add(roles["admin"])


def unseed_roles_and_admin(apps, _schema_editor):
    """
    Revierte la migración eliminando roles, permisos y usuario admin.

    Args:
        apps: Registro de aplicaciones de Django
        _schema_editor: Editor de esquema (no usado)
    """
    Role = apps.get_model("users", "Role")
    # Don't delete users on reverse; only remove the roles created
    Role.objects.filter(
        name__in=[
            "admin",
            "moderator",
            "editor",
            "viewer",
            "scientist",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_admin, unseed_roles_and_admin),
    ]
