"""
Tests comprehensivos para modelos del módulo Chemistry.

Prueba todas las funcionalidades de los modelos incluyendo:
- Validaciones
- Relaciones
- Campos de auditoría
- Constraints únicos
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from chemistry.models import (
    Family,
    FamilyMember,
    FamilyProperty,
    MolecularProperty,
    Molecule,
)

User = get_user_model()


class MoleculeModelTests(TestCase):
    """Tests para el modelo Molecule."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )

    def test_create_molecule_minimal(self):
        """Test creación de molécula con campos mínimos."""
        molecule = Molecule.objects.create(
            name="Test Molecule", smiles="CCO", created_by=self.user
        )
        self.assertEqual(molecule.name, "Test Molecule")
        self.assertEqual(molecule.smiles, "CCO")
        self.assertEqual(molecule.created_by, self.user)
        self.assertFalse(molecule.frozen)

    def test_molecule_inchikey_unique(self):
        """Test que InChIKey es único."""
        Molecule.objects.create(
            name="Molecule 1",
            inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
            created_by=self.user,
        )

        with self.assertRaises(IntegrityError):
            Molecule.objects.create(
                name="Molecule 2",
                inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
                created_by=self.user,
            )

    def test_molecule_str_representation(self):
        """Test representación string de molécula."""
        # Con nombre
        molecule = Molecule.objects.create(name="Ethanol", created_by=self.user)
        self.assertEqual(str(molecule), "Ethanol")

        # Sin nombre, con InChIKey
        molecule2 = Molecule.objects.create(inchikey="TEST-KEY", created_by=self.user)
        self.assertEqual(str(molecule2), "TEST-KEY")

        # Sin nombre ni InChIKey
        molecule3 = Molecule.objects.create(created_by=self.user)
        self.assertEqual(str(molecule3), f"Molecule {molecule3.pk}")

    def test_molecule_audit_fields(self):
        """Test campos de auditoría."""
        molecule = Molecule.objects.create(name="Test", created_by=self.user)

        # Verificar creación
        self.assertEqual(molecule.created_by, self.user)
        self.assertIsNotNone(molecule.created_at)
        self.assertIsNotNone(molecule.updated_at)
        self.assertIsNone(molecule.updated_by)

        # Actualizar molécula
        molecule.name = "Updated Test"
        molecule.updated_by = self.admin
        molecule.save()

        self.assertEqual(molecule.updated_by, self.admin)


class FamilyModelTests(TestCase):
    """Tests para el modelo Family."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    def test_create_family(self):
        """Test creación de familia."""
        family = Family.objects.create(
            name="Test Family",
            family_hash="test_hash_123",
            provenance="test",
            created_by=self.user,
        )

        self.assertEqual(family.name, "Test Family")
        self.assertEqual(family.family_hash, "test_hash_123")
        self.assertEqual(family.provenance, "test")
        self.assertTrue(family.frozen)  # Default True
        self.assertEqual(family.created_by, self.user)

    def test_family_str_representation(self):
        """Test representación string de familia."""
        family = Family.objects.create(
            name="Alcohols", family_hash="hash", provenance="test", created_by=self.user
        )
        self.assertEqual(str(family), "Alcohols")

        family2 = Family.objects.create(
            family_hash="hash2", provenance="test", created_by=self.user
        )
        self.assertEqual(str(family2), f"Family {family2.pk}")


class MolecularPropertyModelTests(TestCase):
    """Tests para el modelo MolecularProperty."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.molecule = Molecule.objects.create(
            name="Test Molecule", created_by=self.user
        )

    def test_create_molecular_property(self):
        """Test creación de propiedad molecular."""
        prop = MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="MolWt",
            value="180.16",
            units="g/mol",
            method="rdkit",
            created_by=self.user,
        )

        self.assertEqual(prop.molecule, self.molecule)
        self.assertEqual(prop.property_type, "MolWt")
        self.assertEqual(prop.value, "180.16")
        self.assertEqual(prop.units, "g/mol")
        self.assertEqual(prop.created_by, self.user)

    def test_molecular_property_unique_constraint(self):
        """Test constraint único por molécula, propiedad y método."""
        MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="MolWt",
            method="rdkit",
            value="180.16",
            created_by=self.user,
        )

        with self.assertRaises(IntegrityError):
            MolecularProperty.objects.create(
                molecule=self.molecule,
                property_type="MolWt",
                method="rdkit",
                value="180.17",
                created_by=self.user,
            )

    def test_molecular_property_str_representation(self):
        """Test representación string de propiedad molecular."""
        prop = MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="LogP",
            value="2.5",
            units="log units",
            created_by=self.user,
        )
        self.assertEqual(str(prop), "LogP=2.5 (log units)")


class FamilyPropertyModelTests(TestCase):
    """Tests para el modelo FamilyProperty."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.family = Family.objects.create(
            name="Test Family",
            family_hash="hash",
            provenance="test",
            created_by=self.user,
        )

    def test_create_family_property(self):
        """Test creación de propiedad de familia."""
        prop = FamilyProperty.objects.create(
            family=self.family,
            property_type="avg_MolWt",
            value="150.5",
            units="g/mol",
            method="aggregation",
            created_by=self.user,
        )

        self.assertEqual(prop.family, self.family)
        self.assertEqual(prop.property_type, "avg_MolWt")
        self.assertEqual(prop.value, "150.5")

    def test_family_property_unique_constraint(self):
        """Test constraint único por familia, propiedad y método."""
        FamilyProperty.objects.create(
            family=self.family,
            property_type="avg_MolWt",
            method="aggregation",
            value="150.5",
            created_by=self.user,
        )

        with self.assertRaises(IntegrityError):
            FamilyProperty.objects.create(
                family=self.family,
                property_type="avg_MolWt",
                method="aggregation",
                value="150.6",
                created_by=self.user,
            )


class FamilyMemberModelTests(TestCase):
    """Tests para el modelo FamilyMember."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.family = Family.objects.create(
            name="Test Family",
            family_hash="hash",
            provenance="test",
            created_by=self.user,
        )
        self.molecule = Molecule.objects.create(
            name="Test Molecule", created_by=self.user
        )

    def test_create_family_member(self):
        """Test creación de membresía familia-molécula."""
        member = FamilyMember.objects.create(family=self.family, molecule=self.molecule)

        self.assertEqual(member.family, self.family)
        self.assertEqual(member.molecule, self.molecule)

    def test_family_member_unique_constraint(self):
        """Test constraint único por familia y molécula."""
        FamilyMember.objects.create(family=self.family, molecule=self.molecule)

        with self.assertRaises(IntegrityError):
            FamilyMember.objects.create(family=self.family, molecule=self.molecule)

    def test_family_member_str_representation(self):
        """Test representación string de membresía."""
        member = FamilyMember.objects.create(family=self.family, molecule=self.molecule)
        expected = f"{self.molecule} in {self.family}"
        self.assertEqual(str(member), expected)


class RelationshipTests(TestCase):
    """Tests para relaciones entre modelos."""

    def setUp(self):
        """Configura datos de prueba."""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.molecule = Molecule.objects.create(
            name="Test Molecule", created_by=self.user
        )
        self.family = Family.objects.create(
            name="Test Family",
            family_hash="hash",
            provenance="test",
            created_by=self.user,
        )

    def test_molecule_properties_relationship(self):
        """Test relación molécula-propiedades."""
        # Crear propiedades
        prop1 = MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="MolWt",
            value="100",
            created_by=self.user,
        )
        prop2 = MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="LogP",
            value="2.5",
            created_by=self.user,
        )

        # Verificar relación
        self.assertEqual(self.molecule.properties.count(), 2)
        self.assertIn(prop1, self.molecule.properties.all())
        self.assertIn(prop2, self.molecule.properties.all())

    def test_family_members_relationship(self):
        """Test relación familia-miembros."""
        molecule2 = Molecule.objects.create(name="Molecule 2", created_by=self.user)

        # Crear membresías
        FamilyMember.objects.create(family=self.family, molecule=self.molecule)
        FamilyMember.objects.create(family=self.family, molecule=molecule2)

        # Verificar relación
        self.assertEqual(self.family.members.count(), 2)
        self.assertEqual(self.molecule.families.count(), 1)

    def test_cascade_delete_molecule(self):
        """Test eliminación en cascada de molécula."""
        # Crear propiedades y membresías
        MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="MolWt",
            value="100",
            created_by=self.user,
        )
        FamilyMember.objects.create(family=self.family, molecule=self.molecule)

        # Eliminar molécula
        self.molecule.delete()

        # Verificar que se eliminaron propiedades y membresías asociadas
        self.assertEqual(MolecularProperty.objects.count(), 0)
        self.assertEqual(
            FamilyMember.objects.filter(family=self.family).count(),
            0,
        )
        # Pero la familia sigue existiendo
        self.assertTrue(Family.objects.filter(id=self.family.id).exists())
