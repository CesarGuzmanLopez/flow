"""
Comando de Django para poblar moléculas de ejemplo en el sistema.

Crea moléculas de ejemplo con sus propiedades para diferentes usuarios,
alineadas con estándares ChEMBL/PubChem.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chemistry import services as chem_services
from chemistry.models import Molecule

User = get_user_model()


class Command(BaseCommand):
    """Comando para crear moléculas de ejemplo en el sistema."""

    help = "Crea moléculas de ejemplo con propiedades para cada usuario"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Elimina moléculas de ejemplo existentes antes de crear nuevas",
        )

    def handle(self, *args, **options):
        """Ejecuta el comando de creación de moléculas."""
        # Obtener un usuario existente o crear uno por defecto para asociar como creador
        creator = User.objects.order_by("id").first()
        if not creator:
            creator = User.objects.create_user(
                username="chemistry-seeder",
                email="seeder@example.com",
                password="chemflow",
            )
            # dar permisos mínimos si tu sistema los usa
            self.stdout.write(
                self.style.WARNING(
                    "Usuario 'chemistry-seeder' creado para ejecutar el seeder"
                )
            )

        # Eliminar moléculas existentes si se solicita
        if options["delete"]:
            deleted = Molecule.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminadas {deleted[0]} moléculas existentes")
                )

        # Elementos a sembrar (en forma atómica para evitar hidrógenos implícitos)
        # Usamos notación de átomos entre corchetes para controlar valencias.
        elements = [
            {"name": "Carbono", "smiles": "[C]"},
            {"name": "Hidrógeno", "smiles": "[H]"},
            {"name": "Nitrógeno", "smiles": "[N]"},
            {"name": "Oxígeno", "smiles": "[O]"},
            {"name": "Fósforo", "smiles": "[P]"},
            {"name": "Azufre", "smiles": "[S]"},
        ]

        created_molecules = []
        for el in elements:
            try:
                mol = chem_services.create_molecule_from_smiles(
                    smiles=el["smiles"],
                    created_by=creator,
                    name=el["name"],
                    extra_metadata={"seed": True, "kind": "element"},
                )
                created_molecules.append(mol)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Creada molécula: {mol.name} ({el['smiles']})"
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Error creando {el['name']} ({el['smiles']}): {exc}"
                    )
                )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"Total de moléculas creadas: {len(created_molecules)}")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
