"""
Comando de Django para poblar usuarios de ejemplo en el sistema.

Crea un usuario de cada tipo (admin, moderator, editor, viewer, scientist)
con sus respectivos roles, permisos y propiedades configuradas.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from users.models import Role

User = get_user_model()


class Command(BaseCommand):
    """Comando para crear usuarios de ejemplo de cada tipo en el sistema."""

    help = "Crea usuarios de ejemplo de cada tipo con sus roles y propiedades"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Elimina usuarios de ejemplo existentes antes de crear nuevos",
        )

    def handle(self, *args, **options):
        """Ejecuta el comando de creación de usuarios."""
        # Lista de usuarios a crear
        users_data = [
            {
                "username": "admin",
                "email": "admin@chemflow.com",
                "password": "admin123",
                "first_name": "Carlos",
                "last_name": "Administrador",
                "university": "Universidad Nacional",
                "is_superuser": True,
                "is_staff": True,
                "roles": ["admin"],
            },
            {
                "username": "moderator",
                "email": "moderator@chemflow.com",
                "password": "moderator123",
                "first_name": "María",
                "last_name": "Moderadora",
                "university": "Universidad de los Andes",
                "is_staff": True,
                "roles": ["moderator"],
            },
            {
                "username": "editor",
                "email": "editor@chemflow.com",
                "password": "editor123",
                "first_name": "Juan",
                "last_name": "Editor",
                "university": "Universidad del Valle",
                "roles": ["editor"],
            },
            {
                "username": "viewer",
                "email": "viewer@chemflow.com",
                "password": "viewer123",
                "first_name": "Ana",
                "last_name": "Observadora",
                "university": "Universidad de Antioquia",
                "roles": ["viewer"],
            },
            {
                "username": "scientist",
                "email": "scientist@chemflow.com",
                "password": "scientist123",
                "first_name": "Pedro",
                "last_name": "Científico",
                "university": "Universidad Javeriana",
                "roles": ["editor", "viewer"],
            },
        ]

        # Eliminar usuarios existentes si se solicita
        if options["delete"]:
            usernames = [u["username"] for u in users_data]
            deleted_count = User.objects.filter(username__in=usernames).delete()[0]
            if deleted_count > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Eliminados {deleted_count} usuarios existentes"
                    )
                )

        # Crear usuarios
        created_count = 0
        updated_count = 0

        for user_data in users_data:
            username = user_data["username"]
            roles_names = user_data.pop("roles", [])
            password = user_data.pop("password")

            # Verificar si el usuario ya existe
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": user_data["email"],
                    "first_name": user_data.get("first_name", ""),
                    "last_name": user_data.get("last_name", ""),
                    "university": user_data.get("university", ""),
                    "is_superuser": user_data.get("is_superuser", False),
                    "is_staff": user_data.get("is_staff", False),
                },
            )

            if created:
                # Configurar password para usuario nuevo
                user.set_password(password)
                user.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Creado usuario: {username}"))
            else:
                # Actualizar datos de usuario existente
                user.email = user_data["email"]
                user.first_name = user_data.get("first_name", "")
                user.last_name = user_data.get("last_name", "")
                user.university = user_data.get("university", "")
                user.is_superuser = user_data.get("is_superuser", False)
                user.is_staff = user_data.get("is_staff", False)
                user.set_password(password)
                user.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⟳ Actualizado usuario: {username}")
                )

            # Asignar roles
            user.roles.clear()
            for role_name in roles_names:
                try:
                    role = Role.objects.get(name=role_name)
                    user.roles.add(role)
                    self.stdout.write(f"  → Rol asignado: {role_name}")
                except Role.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ Rol no encontrado: {role_name}. "
                            f"Ejecuta primero: python manage.py seed_roles"
                        )
                    )

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuarios creados: {created_count} | Actualizados: {updated_count}"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("Credenciales de acceso:")
        self.stdout.write("-" * 60)

        for user_data in users_data:
            username = user_data["username"]
            password = "***123"  # Mostrar patrón sin revelar completo
            self.stdout.write(f"  {username:15} / {username}{password}")

        self.stdout.write("-" * 60)
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "⚠️  Estos son usuarios de DESARROLLO. NO usar en producción."
            )
        )
