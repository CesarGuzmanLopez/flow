"""
Comando de Django para poblar flujos de ejemplo en el sistema.

Crea flujos de trabajo de ejemplo con sus ramas, pasos y versiones
para diferentes usuarios.
"""

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
        # TODO: Verificar que existan usuarios si es necesario
        # try:
        #     editor = User.objects.get(username="editor")
        #     scientist = User.objects.get(username="scientist")
        # except User.DoesNotExist:
        #     self.stdout.write(
        #         self.style.ERROR(
        #             "Error: Usuarios no encontrados. "
        #             "Ejecuta primero: python manage.py seed_users"
        #         )
        #     )
        #     return

        # Eliminar flujos existentes si se solicita
        if options["delete"]:
            deleted = Flow.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminados {deleted[0]} flujos existentes")
                )

        # TODO: Agregar datos reales de flujos aquí
        # flows_data = [
        #     {
        #         "name": "...",
        #         "description": "...",
        #         "owner": editor,
        #         "steps": [
        #             {
        #                 "name": "...",
        #                 "description": "...",
        #                 "step_type": "...",
        #                 "config": {...},
        #             },
        #         ],
        #     },
        # ]

        created_flows = []
        # for flow_data in flows_data:
        #     steps_data = flow_data.pop("steps", [])
        #
        #     # Crear flujo
        #     flow = Flow.objects.create(
        #         name=flow_data["name"],
        #         description=flow_data["description"],
        #         owner=flow_data["owner"],
        #     )
        #     created_flows.append(flow)
        #
        #     self.stdout.write(self.style.SUCCESS(f"\n✓ Creado flujo: {flow.name}"))
        #
        #     # Inicializar rama principal
        #     try:
        #         flow_services.initialize_main_branch(flow, flow.owner)
        #         self.stdout.write("  → Rama principal inicializada")
        #     except ValueError:
        #         pass
        #
        #     # Crear una versión del flujo primero
        #     version = FlowVersion.objects.create(
        #         flow=flow,
        #         version_number=1,
        #         created_by=flow.owner,
        #         metadata={
        #             "description": f"Versión inicial de {flow.name}",
        #             "semantic_version": "1.0.0",
        #         },
        #         is_frozen=False,
        #     )
        #     self.stdout.write(
        #         f"  → Versión: {version.metadata.get('semantic_version', version.version_number)}"
        #     )
        #
        #     # Crear pasos asociados a la versión
        #     for idx, step_data in enumerate(steps_data):
        #         step = Step.objects.create(
        #             flow_version=version,
        #             name=step_data["name"],
        #             description=step_data.get("description", ""),
        #             step_type=step_data.get("step_type", "generic"),
        #             config=step_data.get("config", {}),
        #             order=idx + 1,
        #         )
        #         self.stdout.write(f"  → Paso {step.order}: {step.name}")

        # Resumen
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
