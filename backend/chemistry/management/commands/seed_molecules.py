"""
Comando de Django para poblar moléculas de ejemplo en el sistema.

Crea moléculas de ejemplo con sus propiedades para diferentes usuarios,
alineadas con estándares ChEMBL/PubChem.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chemistry.models import (
    Molecule,
)

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

        # Eliminar moléculas existentes si se solicita
        if options["delete"]:
            deleted = Molecule.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminadas {deleted[0]} moléculas existentes")
                )

        # TODO: Agregar datos reales de moléculas aquí
        # molecules_data = [
        #     {
        #         "name": "...",
        #         "inchikey": "...",
        #         "smiles": "...",
        #         "canonical_smiles": "...",
        #         "molecular_formula": "...",
        #         "created_by": editor,
        #         "metadata": {...},
        #         "properties": [...],
        #     },
        # ]

        created_molecules = []
        # for mol_data in molecules_data:
        #     properties = mol_data.pop("properties", [])
        #
        #     # Crear molécula
        #     molecule, created = Molecule.objects.get_or_create(
        #         inchikey=mol_data["inchikey"],
        #         defaults=mol_data,
        #     )
        #
        #     if created:
        #         created_molecules.append(molecule)
        #         self.stdout.write(
        #             self.style.SUCCESS(f"✓ Creada molécula: {molecule.name}")
        #         )
        #
        #         # Crear propiedades
        #         for prop_data in properties:
        #             MolecularProperty.objects.create(
        #                 molecule=molecule,
        #                 **prop_data,
        #             )
        #             self.stdout.write(f"  → Propiedad: {prop_data['property_type']}")
        #     else:
        #         self.stdout.write(
        #             self.style.WARNING(f"⟳ Molécula existente: {molecule.name}")
        #         )

        # TODO: Crear familias de moléculas aquí si es necesario
        # if created_molecules:
        #     family, created = Family.objects.get_or_create(
        #         name="...",
        #         defaults={
        #             "description": "...",
        #             "family_hash": "...",
        #             "provenance": "seed_data",
        #             "frozen": False,
        #         },
        #     )
        #
        #     if created:
        #         self.stdout.write(
        #             self.style.SUCCESS(f"\n✓ Creada familia: {family.name}")
        #         )
        #
        #         # Agregar propiedades de familia
        #         FamilyProperty.objects.create(
        #             family=family,
        #             property_type="...",
        #             value="...",
        #             units="...",
        #             method="...",
        #         )
        #
        #         # Añadir moléculas a la familia
        #         for molecule in created_molecules[:3]:
        #             FamilyMember.objects.create(family=family, molecule=molecule)
        #             self.stdout.write(f"  → Miembro: {molecule.name}")

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"Total de moléculas creadas: {len(created_molecules)}")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
