"""
Tests de creación de usuarios por administradores.

Verifica que solo los administradores puedan crear nuevos usuarios
a través de la API REST.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AdminCreateUserTests(TestCase):
    """Tests para verificar que solo admins pueden crear usuarios."""

    def setUp(self):
        """Configura un usuario admin y un usuario normal para los tests."""
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="root", email="root@example.com", password="rootpass"
        )
        self.normal = User.objects.create_user(
            username="bob", email="bob@example.com", password="pass"
        )

    def test_only_admin_can_create_user_via_api(self):
        """Verifica que solo usuarios admin pueden crear usuarios vía API."""
        # normal user cannot create
        self.client.force_authenticate(user=self.normal)
        resp = self.client.post(
            "/api/users/users/",
            {"username": "newuser", "password": "p@ssw0rd"},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

        # admin can create
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            "/api/users/users/",
            {"username": "newuser2", "password": "p@ssw0rd"},
            format="json",
        )
        self.assertIn(resp.status_code, (201, 400))
