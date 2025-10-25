"""
Test comprehensivo de todas las operaciones CRUD de Chemistry Views.

Verifica que las vistas puedan realizar todas las operaciones en la base de datos:
- CRUD completo para todas las entidades
- Operaciones especiales (from_smiles, add_property, generate_properties)
- Auditoría correcta (created_by, updated_by)
- Filtrado por usuario
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from users.models import Permission, Role

from chemistry.models import (
    Family,
    FamilyMember,
    Molecule,
)

User = get_user_model()


@override_settings(CHEM_ENGINE="mock")
class ChemistryViewsCRUDTests(TestCase):
    """Tests comprehensivos de CRUD para todas las vistas de Chemistry."""

    def setUp(self):
        """Configura usuario con permisos completos."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="scientist", email="scientist@test.com", password="testpass123"
        )

        # Crear permisos y rol
        read_permission, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="read",
            defaults={"name": "Chemistry Read", "codename": "chemistry_read"},
        )
        write_permission, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="write",
            defaults={"name": "Chemistry Write", "codename": "chemistry_write"},
        )
        delete_permission, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="delete",
            defaults={"name": "Chemistry Delete", "codename": "chemistry_delete"},
        )
        role, _ = Role.objects.get_or_create(name="scientist")
        role.role_permissions.get_or_create(permission=read_permission)
        role.role_permissions.get_or_create(permission=write_permission)
        role.role_permissions.get_or_create(permission=delete_permission)
        self.user.roles.add(role)

        self.client.force_authenticate(user=self.user)

    def test_molecule_full_crud_cycle(self):
        """Test CRUD completo para moléculas."""
        # CREATE - Crear molécula normal
        molecule_data = {
            "name": "Test Molecule",
            "smiles": "CCO",
            "inchi": "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
        }
        response = self.client.post("/api/chemistry/molecules/", molecule_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        molecule_id = response.data["id"]
        self.assertEqual(response.data["created_by"], self.user.id)

        # READ - Obtener molécula
        response = self.client.get(f"/api/chemistry/molecules/{molecule_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Molecule")

        # UPDATE - Actualizar molécula
        update_data = {"name": "Updated Molecule"}
        response = self.client.patch(
            f"/api/chemistry/molecules/{molecule_id}/", update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Molecule")
        self.assertEqual(response.data["updated_by"], self.user.id)

        # DELETE - Eliminar molécula
        response = self.client.delete(f"/api/chemistry/molecules/{molecule_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verificar que fue eliminada
        response = self.client.get(f"/api/chemistry/molecules/{molecule_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_molecule_from_smiles_creation(self):
        """Test creación de molécula desde SMILES."""
        smiles_data = {
            "smiles": "CCO",
            "name": "Ethanol",
            "extra_metadata": {"source": "test"},
        }
        response = self.client.post(
            "/api/chemistry/molecules/from_smiles/", smiles_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Ethanol")
        self.assertEqual(response.data["created_by"], self.user.id)
        self.assertIn("source", response.data["metadata"])

    def test_molecule_add_property(self):
        """Test agregar propiedad a molécula."""
        # Crear molécula primero
        molecule = Molecule.objects.create(
            name="Test Mol", smiles="CCO", created_by=self.user
        )

        # Agregar propiedad
        property_data = {
            "property_type": "LogP",
            "value": "2.5",
            "units": "log(octanol/water)",
            "method": "calculated",
        }
        response = self.client.post(
            f"/api/chemistry/molecules/{molecule.id}/add_property/", property_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["property_type"], "LogP")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_family_full_crud_cycle(self):
        """Test CRUD completo para familias."""
        # CREATE - Crear familia
        family_data = {
            "name": "Test Family",
            "description": "Test family description",
            "family_hash": "test_hash_123",
            "provenance": "user",
        }
        response = self.client.post("/api/chemistry/families/", family_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        family_id = response.data["id"]
        self.assertEqual(response.data["created_by"], self.user.id)

        # READ - Obtener familia
        response = self.client.get(f"/api/chemistry/families/{family_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Family")

        # UPDATE - Actualizar familia
        update_data = {"description": "Updated description"}
        response = self.client.patch(
            f"/api/chemistry/families/{family_id}/", update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["description"], "Updated description")
        self.assertEqual(response.data["updated_by"], self.user.id)

        # DELETE - Eliminar familia
        response = self.client.delete(f"/api/chemistry/families/{family_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_family_from_smiles_creation(self):
        """Test creación de familia desde lista de SMILES."""
        smiles_data = {
            "name": "Alcohol Family",
            "smiles_list": ["CCO", "CCCO", "CCCCO"],
            "provenance": "test",
        }
        response = self.client.post("/api/chemistry/families/from_smiles/", smiles_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Alcohol Family")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_family_generate_properties(self):
        """Test generación de propiedades para familia usando nuevo sistema."""
        # Crear familia con moléculas
        family = Family.objects.create(
            name="Test Family",
            family_hash="test_hash",
            provenance="test",
            created_by=self.user,
        )

        # Crear moléculas y miembros
        mol1 = Molecule.objects.create(name="Mol1", smiles="CCO", created_by=self.user)
        mol2 = Molecule.objects.create(name="Mol2", smiles="CCCO", created_by=self.user)
        FamilyMember.objects.create(family=family, molecule=mol1)
        FamilyMember.objects.create(family=family, molecule=mol2)

        # Generar propiedades usando el nuevo endpoint
        response = self.client.post(
            f"/api/chemistry/families/{family.id}/generate-properties/admetsa/rdkit/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("properties_created", response.data)

    def test_family_add_property(self):
        """Test agregar propiedad a familia."""
        # Crear familia
        family = Family.objects.create(
            name="Test Family",
            family_hash="test_hash",
            provenance="test",
            created_by=self.user,
        )

        # Agregar propiedad
        property_data = {
            "property_type": "AvgLogP",
            "value": "3.2",
            "units": "average",
            "method": "calculated",
        }
        response = self.client.post(
            f"/api/chemistry/families/{family.id}/add_property/", property_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["property_type"], "AvgLogP")
        self.assertEqual(response.data["created_by"], self.user.id)

    def test_molecular_properties_crud(self):
        """Test CRUD para propiedades moleculares."""
        # Crear molécula
        molecule = Molecule.objects.create(
            name="Test Mol", smiles="CCO", created_by=self.user
        )

        # CREATE propiedad
        property_data = {
            "molecule": molecule.id,
            "property_type": "MW",
            "value": "46.07",
            "units": "g/mol",
        }
        response = self.client.post(
            "/api/chemistry/molecular-properties/", property_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        prop_id = response.data["id"]

        # READ propiedad
        response = self.client.get(f"/api/chemistry/molecular-properties/{prop_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # UPDATE propiedad
        update_data = {"value": "46.08"}
        response = self.client.patch(
            f"/api/chemistry/molecular-properties/{prop_id}/", update_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_by"], self.user.id)

        # DELETE propiedad
        response = self.client.delete(f"/api/chemistry/molecular-properties/{prop_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_family_properties_crud(self):
        """Test CRUD para propiedades de familias."""
        # Crear familia
        family = Family.objects.create(
            name="Test Family",
            family_hash="test_hash",
            provenance="test",
            created_by=self.user,
        )

        # CREATE propiedad
        property_data = {
            "family": family.id,
            "property_type": "AvgMW",
            "value": "150.5",
            "units": "g/mol",
        }
        response = self.client.post("/api/chemistry/family-properties/", property_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        prop_id = response.data["id"]

        # READ, UPDATE, DELETE similares a molecular properties
        response = self.client.get(f"/api/chemistry/family-properties/{prop_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_family_members_crud(self):
        """Test CRUD para miembros de familias."""
        # Crear entidades
        family = Family.objects.create(
            name="Test Family",
            family_hash="test_hash",
            provenance="test",
            created_by=self.user,
        )
        molecule = Molecule.objects.create(
            name="Test Mol", smiles="CCO", created_by=self.user
        )

        # CREATE miembro
        member_data = {"family": family.id, "molecule": molecule.id}
        response = self.client.post("/api/chemistry/family-members/", member_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        member_id = response.data["id"]

        # READ miembro
        response = self.client.get(f"/api/chemistry/family-members/{member_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # DELETE miembro
        response = self.client.delete(f"/api/chemistry/family-members/{member_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_mine_endpoints_filtering(self):
        """Test que los endpoints /mine filtren correctamente por usuario."""
        # Crear otro usuario
        other_user = User.objects.create_user(username="other", password="pass")

        # Crear datos para cada usuario
        Molecule.objects.create(name="My Mol", created_by=self.user)
        Molecule.objects.create(name="Other Mol", created_by=other_user)

        Family.objects.create(
            name="My Family",
            family_hash="hash1",
            provenance="test",
            created_by=self.user,
        )
        Family.objects.create(
            name="Other Family",
            family_hash="hash2",
            provenance="test",
            created_by=other_user,
        )

        # Test molecules/mine/
        response = self.client.get("/api/chemistry/molecules/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {mol["name"] for mol in response.data}
        self.assertIn("My Mol", names)
        self.assertNotIn("Other Mol", names)

        # Test families/mine/
        response = self.client.get("/api/chemistry/families/mine/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {fam["name"] for fam in response.data}
        self.assertIn("My Family", names)
        self.assertNotIn("Other Family", names)

    def test_complete_workflow(self):
        """Test workflow completo: crear molécula → crear familia → agregar propiedades."""
        # 1. Crear moléculas desde SMILES
        molecules_data = [
            {"smiles": "CCO", "name": "Ethanol"},
            {"smiles": "CCCO", "name": "Propanol"},
            {"smiles": "CCCCO", "name": "Butanol"},
        ]

        molecule_ids = []
        for mol_data in molecules_data:
            response = self.client.post(
                "/api/chemistry/molecules/from_smiles/", mol_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            molecule_ids.append(response.data["id"])

        # 2. Crear familia desde SMILES
        family_data = {
            "name": "Alcohol Series",
            "smiles_list": ["CCO", "CCCO", "CCCCO"],
            "provenance": "workflow_test",
        }
        response = self.client.post("/api/chemistry/families/from_smiles/", family_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        family_id = response.data["id"]

        # 3. Generar propiedades ADMETSA usando nuevo sistema
        response = self.client.post(
            f"/api/chemistry/families/{family_id}/generate-properties/admetsa/rdkit/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Agregar propiedad personalizada a familia
        custom_property = {
            "property_type": "Series_Type",
            "value": "Alcohol",
            "method": "manual_classification",
        }
        response = self.client.post(
            f"/api/chemistry/families/{family_id}/add_property/", custom_property
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 5. Verificar que todo se creó correctamente
        response = self.client.get(f"/api/chemistry/families/{family_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["properties"]) > 0)

    def test_error_handling(self):
        """Test manejo de errores en operaciones especiales."""
        # Test SMILES inválido
        invalid_smiles = {"smiles": "INVALID_SMILES_XXXX", "name": "Invalid Molecule"}
        response = self.client.post(
            "/api/chemistry/molecules/from_smiles/", invalid_smiles
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
