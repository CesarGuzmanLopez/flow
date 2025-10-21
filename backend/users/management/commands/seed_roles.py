"""
Comando de Django para poblar roles y permisos por defecto en ChemFlow.

Crea los roles básicos (admin, editor, viewer, moderator) y sus permisos
asociados (users.read/write, flows.read/write/execute, chemistry.read/write).
"""

from django.core.management.base import BaseCommand
from users.models import Permission, Role, RolePermission


class Command(BaseCommand):
    """Comando para crear roles y permisos por defecto del sistema."""

    help = "Crea roles y permisos por defecto para ChemFlow"

    def handle(self, *args, **options):
        """
        Ejecuta el comando de creación de roles y permisos.

        Crea los permisos base para users, flows y chemistry, y luego
        asigna los permisos correspondientes a cada rol.
        """
        # Define default permissions
        default_perms = [
            ("users", "read", "Users: Read", "users_read"),
            ("users", "write", "Users: Write", "users_write"),
            ("flows", "read", "Flows: Read", "flows_read"),
            ("flows", "write", "Flows: Write", "flows_write"),
            ("flows", "execute", "Flows: Execute", "flows_execute"),
            ("chemistry", "read", "Chemistry: Read", "chem_read"),
            ("chemistry", "write", "Chemistry: Write", "chem_write"),
        ]

        perm_objs = {}
        for resource, action, name, code in default_perms:
            perm, _ = Permission.objects.get_or_create(
                resource=resource,
                action=action,
                defaults={"name": name, "codename": code},
            )
            perm_objs[(resource, action)] = perm

        # Define roles
        roles = {
            "admin": [
                ("users", "read"),
                ("users", "write"),
                ("flows", "read"),
                ("flows", "write"),
                ("flows", "execute"),
                ("chemistry", "read"),
                ("chemistry", "write"),
            ],
            "editor": [
                ("flows", "read"),
                ("flows", "write"),
                ("flows", "execute"),
                ("chemistry", "read"),
                ("chemistry", "write"),
            ],
            "viewer": [
                ("flows", "read"),
                ("chemistry", "read"),
            ],
            "moderator": [
                ("users", "read"),
                ("flows", "read"),
                ("chemistry", "read"),
            ],
        }

        for role_name, grants in roles.items():
            role, _ = Role.objects.get_or_create(name=role_name)
            # Clear existing grants
            role.role_permissions.all().delete()
            for key in grants:
                perm = perm_objs[key]
                RolePermission.objects.create(role=role, permission=perm)

        self.stdout.write(self.style.SUCCESS("Seeded default roles and permissions."))
