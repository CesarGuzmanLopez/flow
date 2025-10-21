"""
Comando maestro para poblar toda la base de datos con datos de ejemplo.

Ejecuta todos los comandos de seed en el orden correcto:
1. Roles y permisos
2. Usuarios de ejemplo
3. Moléculas de ejemplo
4. Flujos de ejemplo
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Comando maestro para ejecutar todos los seeds en orden."""

    help = "Ejecuta todos los comandos de seed para poblar la base de datos completa"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Elimina datos existentes antes de crear nuevos",
        )

    def handle(self, *args, **options):
        """Ejecuta todos los comandos de seed en orden."""
        delete_flag = options.get("delete", False)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(
            self.style.SUCCESS(
                "    POBLANDO BASE DE DATOS DE CHEMFLOW CON DATOS DE EJEMPLO"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        commands = [
            ("seed_roles", "Roles y Permisos"),
            ("seed_users", "Usuarios de Ejemplo"),
            ("seed_molecules", "Moléculas de Ejemplo"),
            ("seed_flows", "Flujos de Trabajo de Ejemplo"),
        ]

        for cmd, description in commands:
            self.stdout.write("")
            self.stdout.write(self.style.HTTP_INFO(f"► {description}..."))
            self.stdout.write("-" * 70)

            try:
                if delete_flag and cmd != "seed_roles":
                    call_command(cmd, delete=True)
                else:
                    call_command(cmd)
                self.stdout.write(self.style.SUCCESS(f"✓ {description} completado"))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error en {description}: {str(e)}")
                )
                return

        # Resumen final
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(
            self.style.SUCCESS("    ✓ BASE DE DATOS POBLADA EXITOSAMENTE")
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("📋 Resumen de datos creados:"))
        self.stdout.write("")
        self.stdout.write("  Usuarios creados:")
        self.stdout.write(
            "    • admin       - Administrador del sistema (superusuario)"
        )
        self.stdout.write("    • moderator   - Moderador con permisos de lectura")
        self.stdout.write("    • editor      - Editor de flujos y química")
        self.stdout.write("    • viewer      - Observador con solo lectura")
        self.stdout.write("    • scientist   - Científico con múltiples roles")
        self.stdout.write("")
        self.stdout.write("  Moléculas creadas:")
        self.stdout.write("    • Agua, Etanol, Ácido Acético")
        self.stdout.write("    • Aspirina, Cafeína")
        self.stdout.write("    • Familia: Compuestos Orgánicos Simples")
        self.stdout.write("")
        self.stdout.write("  Flujos creados:")
        self.stdout.write("    • Síntesis de Aspirina")
        self.stdout.write("    • Análisis de Pureza")
        self.stdout.write("    • Caracterización Molecular")
        self.stdout.write("")
        self.stdout.write(self.style.WARNING("⚠️  Credenciales de acceso:"))
        self.stdout.write("-" * 70)
        self.stdout.write("  Usuario         | Contraseña      | Rol")
        self.stdout.write("-" * 70)
        self.stdout.write("  admin           | admin123        | Administrador")
        self.stdout.write("  moderator       | moderator123    | Moderador")
        self.stdout.write("  editor          | editor123       | Editor")
        self.stdout.write("  viewer          | viewer123       | Observador")
        self.stdout.write("  scientist       | scientist123    | Científico")
        self.stdout.write("-" * 70)
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "⚠️  Estos son datos de DESARROLLO. NO usar en producción."
            )
        )
        self.stdout.write("")
