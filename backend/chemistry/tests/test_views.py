"""
Tests comprehensivos para las vistas del módulo Chemistry.

Prueba todos los endpoints REST API incluyendo:
- CRUD de moléculas
- CRUD de familias
- CRUD de propiedades
- Permisos y autenticación
- Filtros por usuario
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from users.models import Permission, Role

from chemistry.models import Family, MolecularProperty, Molecule

User = get_user_model()


@override_settings(CHEM_ENGINE="mock")
class MoleculeViewSetTests(TestCase):
    """Tests para MoleculeViewSet."""

    def setUp(self):
        """Configura datos de prueba."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@test.com", password="otherpass"
        )

        # Crear/obtener permisos (evitar duplicados si ya fueron sembrados)
        self.read_perm, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="read",
            defaults={"name": "Chemistry Read", "codename": "chemistry_read"},
        )
        self.write_perm, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="write",
            defaults={"name": "Chemistry Write", "codename": "chemistry_write"},
        )

        # Crear/obtener roles
        self.reader_role, _ = Role.objects.get_or_create(name="Chemistry Reader")
        self.writer_role, _ = Role.objects.get_or_create(name="Chemistry Writer")

        self.reader_role.role_permissions.get_or_create(permission=self.read_perm)
        self.writer_role.role_permissions.get_or_create(permission=self.read_perm)
        self.writer_role.role_permissions.get_or_create(permission=self.write_perm)

    def test_list_molecules_unauthenticated(self):
        """Test acceso sin autenticación."""
        response = self.client.get("/api/chemistry/molecules/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_molecules_authenticated(self):
        """Test listado de moléculas autenticado."""
        self.user.roles.add(self.reader_role)
        self.client.force_authenticate(user=self.user)

        # Crear moléculas
        Molecule.objects.create(name="Mol1", created_by=self.user)
        Molecule.objects.create(name="Mol2", created_by=self.other_user)

        response = self.client.get("/api/chemistry/molecules/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Reader ve todas

    def test_list_molecules_mine_filter(self):
        """Test filtro 'mine' para ver solo moléculas propias."""
        self.client.force_authenticate(user=self.user)

        # Crear moléculas
        mol1 = Molecule.objects.create(name="Mol1", created_by=self.user)
        Molecule.objects.create(name="Mol2", created_by=self.other_user)

        response = self.client.get("/api/chemistry/molecules/?mine=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], mol1.id)

    def test_mine_endpoint(self):
        """Test endpoint /mine/ específico."""
        self.client.force_authenticate(user=self.user)

        # Crear moléculas
        mol1 = Molecule.objects.create(name="Mol1", created_by=self.user)
        Molecule.objects.create(name="Mol2", created_by=self.other_user)

        response = self.client.get("/api/chemistry/molecules/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], mol1.id)

    def test_create_molecule_success(self):
        """Test creación exitosa de molécula."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        data = {"name": "Ethanol", "smiles": "CCO", "metadata": {"source": "test"}}

        response = self.client.post("/api/chemistry/molecules/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Ethanol")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_create_molecule_without_permission(self):
        """Test creación sin permisos de escritura."""
        self.user.roles.add(self.reader_role)
        self.client.force_authenticate(user=self.user)

        data = {"name": "Test", "smiles": "CCO"}

        response = self.client.post("/api/chemistry/molecules/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_molecule(self):
        """Test obtener detalle de molécula."""
        self.user.roles.add(self.reader_role)
        self.client.force_authenticate(user=self.user)

        molecule = Molecule.objects.create(name="Test", created_by=self.user)

        response = self.client.get(f"/api/chemistry/molecules/{molecule.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], molecule.id)

    def test_update_molecule(self):
        """Test actualización de molécula."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        molecule = Molecule.objects.create(name="Test", created_by=self.user)

        data = {"name": "Updated Test"}
        response = self.client.patch(
            f"/api/chemistry/molecules/{molecule.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Test")

        # Verificar auditoría
        molecule.refresh_from_db()
        self.assertEqual(molecule.updated_by, self.user)

    def test_delete_molecule(self):
        """Test eliminación de molécula."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        molecule = Molecule.objects.create(name="Test", created_by=self.user)

        response = self.client.delete(f"/api/chemistry/molecules/{molecule.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Molecule.objects.filter(id=molecule.id).exists())


class FamilyViewSetTests(TestCase):
    """Tests para FamilyViewSet."""

    def setUp(self):
        """Configura datos de prueba."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

        # Crear/obtener permisos y roles
        self.write_perm, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="write",
            defaults={"name": "Chemistry Write", "codename": "chemistry_write"},
        )
        self.writer_role, _ = Role.objects.get_or_create(name="Chemistry Writer")
        self.writer_role.role_permissions.get_or_create(permission=self.write_perm)

    def test_create_family(self):
        """Test creación de familia."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        data = {"name": "Test Family", "family_hash": "test_hash", "provenance": "test"}

        response = self.client.post("/api/chemistry/families/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Test Family")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_family_mine_endpoint(self):
        """Test endpoint /mine/ para familias."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/chemistry/families/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MolecularPropertyViewSetTests(TestCase):
    """Tests para MolecularPropertyViewSet."""

    def setUp(self):
        """Configura datos de prueba."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.molecule = Molecule.objects.create(name="Test", created_by=self.user)

        # Crear/obtener permisos y roles
        self.write_perm, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="write",
            defaults={"name": "Chemistry Write", "codename": "chemistry_write"},
        )
        self.writer_role, _ = Role.objects.get_or_create(name="Chemistry Writer")
        self.writer_role.role_permissions.get_or_create(permission=self.write_perm)

    def test_create_molecular_property(self):
        """Test creación de propiedad molecular."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        data = {
            "molecule": self.molecule.id,
            "property_type": "MolWt",
            "value": "180.16",
            "units": "g/mol",
            "method": "rdkit",
        }

        response = self.client.post(
            "/api/chemistry/molecular-properties/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["property_type"], "MolWt")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_update_molecular_property_audit(self):
        """Test auditoría en actualización de propiedad."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        prop = MolecularProperty.objects.create(
            molecule=self.molecule,
            property_type="MolWt",
            value="180.16",
            created_by=self.user,
        )

        data = {"value": "180.17"}
        response = self.client.patch(
            f"/api/chemistry/molecular-properties/{prop.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar auditoría
        prop.refresh_from_db()
        self.assertEqual(prop.updated_by, self.user)


class FamilyPropertyViewSetTests(TestCase):
    """Tests para FamilyPropertyViewSet."""

    def setUp(self):
        """Configura datos de prueba."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )
        self.family = Family.objects.create(
            name="Test Family",
            family_hash="hash",
            provenance="test",
            created_by=self.user,
        )

        # Crear permisos
        self.write_perm = Permission.objects.create(
            resource="chemistry", action="write", name="Chemistry Write"
        )
        self.writer_role = Role.objects.create(name="Chemistry Writer")
        self.writer_role.role_permissions.create(permission=self.write_perm)

    def test_create_family_property(self):
        """Test creación de propiedad de familia."""
        self.user.roles.add(self.writer_role)
        self.client.force_authenticate(user=self.user)

        data = {
            "family": self.family.id,
            "property_type": "avg_MolWt",
            "value": "150.5",
            "units": "g/mol",
            "method": "aggregation",
        }

        response = self.client.post(
            "/api/chemistry/family-properties/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["property_type"], "avg_MolWt")
        self.assertEqual(response.data["created_by"], self.user.id)


class PermissionTests(TestCase):
    """Tests específicos de permisos."""

    def setUp(self):
        """Configura datos de prueba."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    def test_no_permission_access(self):
        """Test acceso sin permisos."""
        self.client.force_authenticate(user=self.user)

        # Sin roles/permisos no puede acceder
        response = self.client.get("/api/chemistry/molecules/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_access(self):
        """Test acceso de superusuario."""
        admin = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )
        self.client.force_authenticate(user=admin)

        response = self.client.get("/api/chemistry/molecules/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
