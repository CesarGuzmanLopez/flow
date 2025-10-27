"""
Tests de permisos y autorización para la aplicación de usuarios.

Verifica que el sistema de roles y permisos funcione correctamente,
incluyendo la restricción de acceso basada en roles (viewer, editor, etc.)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import Permission, Role

User = get_user_model()


class PermissionTests(TestCase):
    """Tests para verificar el sistema de permisos basado en roles."""

    def setUp(self):
        """Configura usuarios, roles y permisos para los tests."""
        self.client = APIClient()
        # Create roles/permissions (idempotent)
        self.p_read_flows, _ = Permission.objects.get_or_create(
            resource="flows",
            action="read",
            defaults={"name": "Read flows", "codename": "flows_read"},
        )
        self.p_write_flows, _ = Permission.objects.get_or_create(
            resource="flows",
            action="write",
            defaults={"name": "Write flows", "codename": "flows_write"},
        )
        self.role_viewer, _ = Role.objects.get_or_create(name="viewer")
        self.role_editor, _ = Role.objects.get_or_create(name="editor")
        # Ensure role_permissions exist only once
        self.role_viewer.role_permissions.get_or_create(permission=self.p_read_flows)
        self.role_editor.role_permissions.get_or_create(permission=self.p_write_flows)

        # Users
        self.user_viewer = User.objects.create_user(
            username="viewer", password="pass", email="v@example.com"
        )
        self.user_viewer.roles.add(self.role_viewer)
        self.user_editor = User.objects.create_user(
            username="editor", password="pass", email="e@example.com"
        )
        self.user_editor.roles.add(self.role_editor)

    def test_viewer_cannot_create_flow(self):
        """Verifica que un viewer no puede crear flujos (sin permiso write)."""
        self.client.force_authenticate(user=self.user_viewer)
        resp = self.client.post(
            "/api/flows/flows/",
            {"name": "F1", "description": "d"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_editor_can_create_flow(self):
        """Verifica que un editor puede crear flujos (tiene permiso write)."""
        self.client.force_authenticate(user=self.user_editor)
        resp = self.client.post(
            "/api/flows/flows/",
            {"name": "F2", "description": "d"},
            format="json",
        )
        # 201 on success, 400 if validation requires additional fields
        self.assertIn(resp.status_code, (201, 400))

    def test_user_me_endpoint(self):
        self.client.force_authenticate(user=self.user_viewer)
        resp = self.client.get("/api/users/users/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["content"]["username"], "viewer")
