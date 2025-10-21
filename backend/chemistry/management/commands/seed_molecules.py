"""
Comando de Django para poblar moléculas de ejemplo en el sistema.

Crea moléculas de ejemplo con sus propiedades para diferentes usuarios,
alineadas con estándares ChEMBL/PubChem.
"""

from chemistry.models import (
    Family,
    FamilyMember,
    FamilyProperty,
    MolecularProperty,
    Molecule,
)
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

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

        # Eliminar moléculas existentes si se solicita
        if options["delete"]:
            deleted = Molecule.objects.all().delete()
            if deleted[0] > 0:
                self.stdout.write(
                    self.style.WARNING(f"Eliminadas {deleted[0]} moléculas existentes")
                )

        # Moléculas de ejemplo
        molecules_data = [
            {
                "name": "Agua",
                "inchikey": "XLYOFNOQVPJJNP-UHFFFAOYSA-N",
                "smiles": "O",
                "canonical_smiles": "O",
                "molecular_formula": "H2O",
                "created_by": editor,
                "metadata": {"common_name": "Water", "cas": "7732-18-5"},
                "properties": [
                    {
                        "property_type": "molecular_weight",
                        "value": "18.015",
                        "units": "g/mol",
                        "is_invariant": True,
                    },
                    {
                        "property_type": "boiling_point",
                        "value": "100",
                        "units": "°C",
                        "method": "experimental",
                    },
                ],
            },
            {
                "name": "Etanol",
                "inchikey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
                "smiles": "CCO",
                "canonical_smiles": "CCO",
                "molecular_formula": "C2H6O",
                "created_by": editor,
                "metadata": {"common_name": "Ethanol", "cas": "64-17-5"},
                "properties": [
                    {
                        "property_type": "molecular_weight",
                        "value": "46.069",
                        "units": "g/mol",
                        "is_invariant": True,
                    },
                    {
                        "property_type": "boiling_point",
                        "value": "78.37",
                        "units": "°C",
                        "method": "experimental",
                    },
                    {
                        "property_type": "density",
                        "value": "0.789",
                        "units": "g/cm³",
                        "method": "experimental",
                    },
                ],
            },
            {
                "name": "Ácido Acético",
                "inchikey": "QTBSBXVTEAMEQO-UHFFFAOYSA-N",
                "smiles": "CC(=O)O",
                "canonical_smiles": "CC(=O)O",
                "molecular_formula": "C2H4O2",
                "created_by": scientist,
                "metadata": {"common_name": "Acetic Acid", "cas": "64-19-7"},
                "properties": [
                    {
                        "property_type": "molecular_weight",
                        "value": "60.052",
                        "units": "g/mol",
                        "is_invariant": True,
                    },
                    {
                        "property_type": "boiling_point",
                        "value": "118",
                        "units": "°C",
                        "method": "experimental",
                    },
                ],
            },
            {
                "name": "Aspirina",
                "inchikey": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                "smiles": "CC(=O)Oc1ccccc1C(=O)O",
                "canonical_smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",
                "molecular_formula": "C9H8O4",
                "created_by": scientist,
                "metadata": {
                    "common_name": "Aspirin",
                    "iupac": "2-acetyloxybenzoic acid",
                    "cas": "50-78-2",
                },
                "properties": [
                    {
                        "property_type": "molecular_weight",
                        "value": "180.159",
                        "units": "g/mol",
                        "is_invariant": True,
                    },
                    {
                        "property_type": "melting_point",
                        "value": "135",
                        "units": "°C",
                        "method": "experimental",
                    },
                ],
            },
            {
                "name": "Cafeína",
                "inchikey": "RYYVLZVUVIJVGH-UHFFFAOYSA-N",
                "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                "canonical_smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
                "molecular_formula": "C8H10N4O2",
                "created_by": scientist,
                "metadata": {"common_name": "Caffeine", "cas": "58-08-2"},
                "properties": [
                    {
                        "property_type": "molecular_weight",
                        "value": "194.194",
                        "units": "g/mol",
                        "is_invariant": True,
                    },
                    {
                        "property_type": "melting_point",
                        "value": "238",
                        "units": "°C",
                        "method": "experimental",
                    },
                ],
            },
        ]

        created_molecules = []
        for mol_data in molecules_data:
            properties = mol_data.pop("properties", [])

            # Crear molécula
            molecule, created = Molecule.objects.get_or_create(
                inchikey=mol_data["inchikey"],
                defaults=mol_data,
            )

            if created:
                created_molecules.append(molecule)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Creada molécula: {molecule.name}")
                )

                # Crear propiedades
                for prop_data in properties:
                    MolecularProperty.objects.create(
                        molecule=molecule,
                        **prop_data,
                    )
                    self.stdout.write(f"  → Propiedad: {prop_data['property_type']}")
            else:
                self.stdout.write(
                    self.style.WARNING(f"⟳ Molécula existente: {molecule.name}")
                )

        # Crear familia de ejemplo
        if created_molecules:
            family, created = Family.objects.get_or_create(
                name="Compuestos Orgánicos Simples",
                defaults={
                    "description": "Familia de compuestos orgánicos básicos",
                    "family_hash": "simple_organics_001",
                    "provenance": "seed_data",
                    "frozen": False,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"\n✓ Creada familia: {family.name}")
                )

                # Agregar propiedades de familia
                FamilyProperty.objects.create(
                    family=family,
                    property_type="average_mw",
                    value="99.70",
                    units="g/mol",
                    method="calculated",
                )

                # Añadir moléculas a la familia
                for molecule in created_molecules[:3]:  # Primeras 3 moléculas
                    FamilyMember.objects.create(family=family, molecule=molecule)
                    self.stdout.write(f"  → Miembro: {molecule.name}")

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.SUCCESS(f"Total de moléculas creadas: {len(created_molecules)}")
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
