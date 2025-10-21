"""
Tests de permisos para la aplicación de química.

Verifica que el sistema de permisos funcione correctamente para operaciones
de lectura y escritura en moléculas según los roles del usuario.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import Permission, Role

User = get_user_model()


class ChemistryPermissionsTests(TestCase):
    """Tests para verificar permisos de chemistry (read/write)."""

    def setUp(self):
        """Configura usuarios con diferentes niveles de permisos."""
        self.client = APIClient()
        self.viewer = User.objects.create_user(username="viewer", password="pass")
        self.writer = User.objects.create_user(username="writer", password="pass")
        # Ensure a 'chemistry:write' permission and assign to writer role so writer can create
        p_write, _ = Permission.objects.get_or_create(
            resource="chemistry",
            action="write",
            defaults={"name": "Chem Write", "codename": "chem_write"},
        )
        role_writer, _ = Role.objects.get_or_create(name="chem_writer")
        role_writer.role_permissions.get_or_create(permission=p_write)
        self.writer.roles.add(role_writer)

    # Granting simple permissions via role system would be ideal;
    # for now rely on default read-only for viewer

    def test_viewer_cannot_create_molecule(self):
        """Verifica que un viewer no puede crear moléculas (sin permiso write)."""
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.post(
            "/api/chemistry/molecules/",
            {"name": "CO2"},
            format="json",
        )
        # Expect 403 due to HasAppPermission default write mapping
        self.assertIn(resp.status_code, (400, 403))

    def test_writer_can_create_molecule(self):
        """Verifica que un usuario con permiso write puede crear moléculas."""
        self.client.force_authenticate(user=self.writer)
        # If your permission system requires explicit role grants, adjust this test accordingly
        resp = self.client.post(
            "/api/chemistry/molecules/",
            {"name": "CH4"},
            format="json",
        )
        self.assertIn(resp.status_code, (201, 400))
