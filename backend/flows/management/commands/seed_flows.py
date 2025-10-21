"""
Comando de Django para poblar flujos de ejemplo en el sistema.

Crea flujos de trabajo de ejemplo con sus ramas, pasos y versiones
para diferentes usuarios.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from flows import services as flow_services
from flows.models import Flow, FlowVersion, Step

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
        # Verificar que existan usuarios
        try:
            editor = User.objects.get(username="editor")
            scientist = User.objects.get(username="scientist")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "Error: Usuarios no encontrados. "
                    "Ejecuta primero: python manage.py seed_users"
                )
            )
            return

        # Eliminar flujos existentes si se solicita
        if options["delete"]:
            deleted = Flow.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminados {deleted[0]} flujos existentes")
                )

        # Flujos de ejemplo
        flows_data = [
            {
                "name": "Síntesis de Aspirina",
                "description": "Flujo de trabajo para la síntesis de ácido acetilsalicílico",
                "owner": scientist,
                "steps": [
                    {
                        "name": "Preparación de reactivos",
                        "description": "Pesar y preparar ácido salicílico y anhídrido acético",
                        "step_type": "preparation",
                        "config": {
                            "materials": ["salicylic_acid", "acetic_anhydride"],
                            "quantities": {"salicylic_acid": "2.0g"},
                        },
                    },
                    {
                        "name": "Reacción de acetilación",
                        "description": "Mezclar reactivos y calentar",
                        "step_type": "reaction",
                        "config": {
                            "temperature": "85°C",
                            "time": "15min",
                            "catalyst": "H3PO4",
                        },
                    },
                    {
                        "name": "Cristalización",
                        "description": "Enfriar y cristalizar el producto",
                        "step_type": "purification",
                        "config": {"method": "cooling", "solvent": "water"},
                    },
                ],
            },
            {
                "name": "Análisis de Pureza",
                "description": "Flujo de trabajo para análisis de pureza por HPLC",
                "owner": editor,
                "steps": [
                    {
                        "name": "Preparación de muestra",
                        "description": "Disolver muestra en solvente apropiado",
                        "step_type": "preparation",
                        "config": {"solvent": "methanol", "concentration": "1mg/mL"},
                    },
                    {
                        "name": "Análisis HPLC",
                        "description": "Inyectar y analizar por HPLC",
                        "step_type": "analysis",
                        "config": {
                            "method": "HPLC",
                            "column": "C18",
                            "flow_rate": "1.0mL/min",
                        },
                    },
                ],
            },
            {
                "name": "Caracterización Molecular",
                "description": "Flujo para caracterización completa de nuevos compuestos",
                "owner": scientist,
                "steps": [
                    {
                        "name": "Espectroscopía IR",
                        "description": "Obtener espectro infrarrojo",
                        "step_type": "characterization",
                        "config": {"technique": "FTIR", "range": "4000-400 cm-1"},
                    },
                    {
                        "name": "RMN de protón",
                        "description": "Espectro de resonancia magnética nuclear 1H",
                        "step_type": "characterization",
                        "config": {"technique": "1H-NMR", "solvent": "CDCl3"},
                    },
                    {
                        "name": "Espectrometría de masas",
                        "description": "Determinar masa molecular exacta",
                        "step_type": "characterization",
                        "config": {"technique": "MS", "ionization": "ESI"},
                    },
                ],
            },
        ]

        created_flows = []
        for flow_data in flows_data:
            steps_data = flow_data.pop("steps", [])

            # Crear flujo
            flow = Flow.objects.create(
                name=flow_data["name"],
                description=flow_data["description"],
                owner=flow_data["owner"],
            )
            created_flows.append(flow)

            self.stdout.write(self.style.SUCCESS(f"\n✓ Creado flujo: {flow.name}"))

            # Inicializar rama principal
            try:
                flow_services.initialize_main_branch(flow, flow.owner)
                self.stdout.write("  → Rama principal inicializada")
            except ValueError:
                pass

            # Crear una versión del flujo primero
            version = FlowVersion.objects.create(
                flow=flow,
                version_number=1,
                created_by=flow.owner,
                metadata={
                    "description": f"Versión inicial de {flow.name}",
                    "semantic_version": "1.0.0",
                },
                is_frozen=False,
            )
            self.stdout.write(
                f"  → Versión: {version.metadata.get('semantic_version', version.version_number)}"
            )

            # Crear pasos asociados a la versión
            for idx, step_data in enumerate(steps_data):
                step = Step.objects.create(
                    flow_version=version,
                    name=step_data["name"],
                    description=step_data.get("description", ""),
                    step_type=step_data.get("step_type", "generic"),
                    config=step_data.get("config", {}),
                    order=idx + 1,
                )
                self.stdout.write(f"  → Paso {step.order}: {step.name}")

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
