

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from flows.models import Flow

User = get_user_model()


class Command(BaseCommand):
    """Comando para crear flujos de ejemplo en el sistema."""

    help = "Crea flujos de trabajo de ejemplo para cada usuario"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Elimina flujos de ejemplo existentes antes de crear nuevos",
        )

    def handle(self, *args, **options):
        """Ejecuta el comando de creación de flujos."""
        # Eliminar flujos existentes si se solicita
        if options["delete"]:
            deleted = Flow.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminados {deleted[0]} flujos existentes")
                )
        created_flows = []
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"Total de flujos creados: {len(created_flows)}")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write("Flujos creados:")
        for flow in created_flows:
            self.stdout.write(f"  • {flow.name} (propietario: {flow.owner.username})")
