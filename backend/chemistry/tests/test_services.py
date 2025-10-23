"""
Tests comprehensivos para servicios del módulo Chemistry.

Prueba toda la lógica de negocio incluyendo:
- Creación de moléculas desde SMILES
- Gestión de familias
- Cálculo de propiedades ADMETSA
- Validaciones y manejo de errores
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from chemistry import services as chem_services
from chemistry.models import (
    FamilyProperty,
    MolecularProperty,
    Molecule,
)

User = get_user_model()


@override_settings(CHEM_ENGINE="mock")
class ChemistryServicesTests(TestCase):
    """Tests para servicios de chemistry usando mock engine."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )

    def test_create_molecule_from_smiles_success(self):
        """Test creación exitosa de molécula desde SMILES."""
        molecule = chem_services.create_molecule_from_smiles(
            smiles="CCO", created_by=self.user, name="Ethanol"
        )

        self.assertEqual(molecule.name, "Ethanol")
        self.assertEqual(molecule.smiles, "CCO")
        self.assertEqual(molecule.created_by, self.user)
        self.assertIsNotNone(molecule.inchikey)
        self.assertIn("descriptors", molecule.metadata)

    def test_create_molecule_from_smiles_empty_smiles(self):
        """Test validación de SMILES vacío."""
        with self.assertRaises(ValidationError) as cm:
            chem_services.create_molecule_from_smiles(smiles="", created_by=self.user)
        self.assertIn("SMILES cannot be empty", str(cm.exception))

    def test_create_molecule_from_smiles_no_user(self):
        """Test validación de usuario requerido."""
        with self.assertRaises(ValueError) as cm:
            chem_services.create_molecule_from_smiles(smiles="CCO", created_by=None)
        self.assertIn("created_by is required", str(cm.exception))

    def test_create_molecule_from_smiles_duplicate_inchikey(self):
        """Test deduplicación por InChIKey."""
        # Crear primera molécula
        mol1 = chem_services.create_molecule_from_smiles(
            smiles="CCO", created_by=self.user, name="Ethanol 1"
        )

        # Crear segunda molécula con mismo SMILES
        mol2 = chem_services.create_molecule_from_smiles(
            smiles="CCO", created_by=self.user, name="Ethanol 2"
        )

        # Debe ser la misma molécula
        self.assertEqual(mol1.id, mol2.id)
        self.assertEqual(mol1.name, "Ethanol 1")  # No se actualiza el nombre

    def test_create_family_from_smiles_success(self):
        """Test creación exitosa de familia desde SMILES."""
        family = chem_services.create_family_from_smiles(
            name="Alcohols",
            smiles_list=["CO", "CCO", "CCCO"],
            created_by=self.user,
            provenance="test",
        )

        self.assertEqual(family.name, "Alcohols")
        self.assertEqual(family.provenance, "test")
        self.assertEqual(family.created_by, self.user)
        self.assertEqual(family.members.count(), 3)

    def test_create_family_from_smiles_empty_name(self):
        """Test validación de nombre vacío."""
        with self.assertRaises(ValidationError) as cm:
            chem_services.create_family_from_smiles(
                name="", smiles_list=["CCO"], created_by=self.user
            )
        self.assertIn("Family name cannot be empty", str(cm.exception))

    def test_create_family_from_smiles_empty_list(self):
        """Test validación de lista vacía."""
        with self.assertRaises(ValidationError) as cm:
            chem_services.create_family_from_smiles(
                name="Test", smiles_list=[], created_by=self.user
            )
        self.assertIn("SMILES list cannot be empty", str(cm.exception))

    def test_create_family_from_smiles_deduplication(self):
        """Test deduplicación de moléculas en familia."""
        family = chem_services.create_family_from_smiles(
            name="Test Family",
            smiles_list=["CCO", "CCO", "CO"],  # CCO duplicado
            created_by=self.user,
        )

        # Solo debe haber 2 moléculas únicas
        self.assertEqual(family.members.count(), 2)

    def test_filter_molecules_for_user_superuser(self):
        """Test filtro para superusuario ve todas las moléculas."""
        # Crear moléculas de diferentes usuarios
        mol1 = Molecule.objects.create(name="Mol1", created_by=self.user)
        mol2 = Molecule.objects.create(name="Mol2", created_by=self.admin)

        qs = Molecule.objects.filter(id__in=[mol1.id, mol2.id])
        filtered = chem_services.filter_molecules_for_user(qs, self.admin)

        self.assertEqual(filtered.count(), 2)
        self.assertIn(mol1, filtered)
        self.assertIn(mol2, filtered)

    def test_filter_molecules_for_user_regular_user(self):
        """Test filtro para usuario regular ve solo sus moléculas."""
        # Crear moléculas de diferentes usuarios
        mol1 = Molecule.objects.create(name="Mol1", created_by=self.user)
        mol2 = Molecule.objects.create(name="Mol2", created_by=self.admin)

        qs = Molecule.objects.all()
        filtered = chem_services.filter_molecules_for_user(qs, self.user)

        self.assertEqual(filtered.count(), 1)
        self.assertIn(mol1, filtered)
        self.assertNotIn(mol2, filtered)

    def test_generate_admetsa_for_family(self):
        """Test generación de propiedades ADMETSA para familia."""
        # Crear familia con moléculas
        family = chem_services.create_family_from_smiles(
            name="Test Family", smiles_list=["CCO", "CO"], created_by=self.user
        )

        # Generar ADMETSA
        result = chem_services.generate_admetsa_for_family(
            family_id=family.id, created_by=self.user
        )

        self.assertEqual(result["family_id"], family.id)
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["molecules"]), 2)

        # Verificar que se crearon propiedades moleculares
        props_count = MolecularProperty.objects.filter(
            molecule__in=family.members.values_list("molecule_id", flat=True),
            property_type__in=chem_services.ADMETSA_PROPERTIES,
        ).count()
        self.assertGreater(props_count, 0)

    def test_create_single_molecule_family(self):
        """Test creación de familia con una sola molécula."""
        molecule = Molecule.objects.create(
            name="Aspirin", smiles="CC(=O)OC1=CC=CC=C1C(=O)O", created_by=self.user
        )

        family = chem_services.create_single_molecule_family(
            name="Aspirin Family",
            molecule=molecule,
            created_by=self.user,
            provenance="reference",
        )

        self.assertEqual(family.name, "Aspirin Family")
        self.assertEqual(family.provenance, "reference")
        self.assertEqual(family.members.count(), 1)
        self.assertEqual(family.members.first().molecule, molecule)

    def test_generate_substituted_family(self):
        """Test generación de familia de sustituciones."""
        # Crear moléculas base
        base_mol = Molecule.objects.create(
            name="Benzene", smiles="C1=CC=CC=C1", created_by=self.user
        )

        result = chem_services.generate_substituted_family(
            name="Substituted Benzenes",
            base_molecule_ids=[base_mol.id],
            substituent_smiles_list=["CH3", "OH"],
            positions=[1, 2],
            created_by=self.user,
            provenance="substitutions",
        )

        self.assertEqual(result["family_name"], "Substituted Benzenes")
        self.assertGreater(result["count"], 0)
        self.assertEqual(result["positions"], [1, 2])

    def test_compute_family_admetsa_aggregates(self):
        """Test cálculo de agregados ADMETSA para familia."""
        # Crear familia y generar propiedades
        family = chem_services.create_family_from_smiles(
            name="Test Family", smiles_list=["CCO", "CO"], created_by=self.user
        )

        chem_services.generate_admetsa_for_family(
            family_id=family.id, created_by=self.user
        )

        # Calcular agregados
        result = chem_services.compute_family_admetsa_aggregates(
            family_id=family.id, created_by=self.user
        )

        self.assertEqual(result["family_id"], family.id)
        self.assertGreater(result["count"], 0)
        self.assertIsInstance(result["aggregates"], dict)

        # Verificar que se crearon propiedades de familia
        family_props = FamilyProperty.objects.filter(
            family=family, property_type__startswith="ADMETSA.avg."
        )
        self.assertGreater(family_props.count(), 0)


class ChemistryServicesErrorHandlingTests(TestCase):
    """Tests para manejo de errores en servicios."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    @patch("chemistry.providers.engine.smiles_to_inchi")
    def test_create_molecule_chemistry_engine_error(self, mock_engine):
        """Test manejo de errores del engine de química."""
        mock_engine.side_effect = Exception("Invalid SMILES")

        with self.assertRaises(ValidationError) as cm:
            chem_services.create_molecule_from_smiles(
                smiles="INVALID", created_by=self.user
            )
        self.assertIn("Invalid SMILES or chemistry engine error", str(cm.exception))

    def test_generate_substituted_family_no_base_molecules(self):
        """Test validación de moléculas base faltantes."""
        with self.assertRaises(ValueError) as cm:
            chem_services.generate_substituted_family(name="Test", created_by=self.user)
        self.assertIn("No base molecules provided", str(cm.exception))

    def test_generate_substituted_family_no_substituents(self):
        """Test validación de sustituyentes faltantes."""
        mol = Molecule.objects.create(name="Test", created_by=self.user)

        with self.assertRaises(ValueError) as cm:
            chem_services.generate_substituted_family(
                name="Test", base_molecule_ids=[mol.id], created_by=self.user
            )
        self.assertIn("No substituents provided", str(cm.exception))
