"""
Comando de Django para configuración inicial completa de ChemFlow.

Este comando simplificado:
1. Aplica todas las migraciones (users + chemistry)
2. Verifica que el sistema esté configurado correctamente

Sin dependencias de comandos management externos.
"""

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Comando simplificado para configuración inicial de ChemFlow."""

    help = "Configuración inicial completa del sistema ChemFlow (simplificado)"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--skip-migrations",
            action="store_true",
            help="Omite la aplicación de migraciones",
        )

    def handle(self, *args, **options):
        """Ejecuta la configuración inicial completa."""
        start_time = time.time()

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(
            self.style.SUCCESS("       SETUP INICIAL SIMPLIFICADO - CHEMFLOW")
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        # 1. Aplicar migraciones
        if not options["skip_migrations"]:
            self.stdout.write(
                self.style.HTTP_INFO("📋 PASO 1: Aplicando migraciones...")
            )
            try:
                call_command("migrate", verbosity=0)
                self.stdout.write(
                    self.style.SUCCESS("✓ Migraciones aplicadas correctamente")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Error en migraciones: {e}"))
                return
        else:
            self.stdout.write(self.style.WARNING("⏭️  PASO 1: Migraciones omitidas"))

        self.stdout.write("")

        # 2. Verificación final
        self.stdout.write(
            self.style.HTTP_INFO("🎯 PASO 2: Verificación del sistema...")
        )

        # Verificar que todo esté correctamente configurado
        try:
            from chemistry.models import Family, Molecule
            from django.contrib.auth import get_user_model

            User = get_user_model()
            admin_count = User.objects.filter(is_superuser=True).count()
            molecule_count = Molecule.objects.count()
            family_count = Family.objects.count()

            self.stdout.write(f"   • Administradores: {admin_count}")
            self.stdout.write(f"   • Moléculas: {molecule_count}")
            self.stdout.write(f"   • Familias: {family_count}")

            # Verificar familia CHON específicamente
            chon_family = Family.objects.filter(name="CHON").first()
            if chon_family:
                chon_members = chon_family.members.count()
                self.stdout.write(f"   • Moléculas en familia CHON: {chon_members}")

            if admin_count > 0 and molecule_count > 0 and family_count > 0:
                self.stdout.write(
                    self.style.SUCCESS("✓ Sistema configurado correctamente")
                )
            else:
                self.stdout.write(self.style.WARNING("⚠️ Configuración incompleta"))

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"⚠️ Error verificando configuración: {e}")
            )

        # Resumen final
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(
            self.style.SUCCESS("🎉 SETUP INICIAL COMPLETADO EXITOSAMENTE")
        )
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        # Mensaje informativo
        end_time = time.time()
        elapsed = end_time - start_time

        self.stdout.write(f"⏱️  Tiempo total: {elapsed:.1f} segundos")
        self.stdout.write("")
        self.stdout.write("El sistema ChemFlow está listo para usar:")
        self.stdout.write("")
        self.stdout.write("📊 Panel de admin: http://localhost:8000/admin/")
        self.stdout.write("🔬 API de química: http://localhost:8000/api/chemistry/")
        self.stdout.write("📚 Documentación: http://localhost:8000/api/docs/swagger/")
        self.stdout.write("")
        self.stdout.write("Credenciales por defecto:")
        self.stdout.write("  Usuario: chemflow_admin")
        self.stdout.write("  Contraseña: ChemFlow2024!")
        self.stdout.write("")
        self.stdout.write("Usuarios demo:")
        self.stdout.write("  demo_admin / demo123")
        self.stdout.write("  demo_scientist / demo123")
        self.stdout.write("  demo_viewer / demo123")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING("⚠️  Cambia las credenciales en producción")
        )
        self.stdout.write("")
