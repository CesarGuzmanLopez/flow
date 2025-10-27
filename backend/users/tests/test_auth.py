"""
Tests de autenticación JWT para ChemFlow.

Verifica que el login con JWT funcione correctamente y retorne
los tokens de acceso y refresh junto con los datos del usuario.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class AuthTests(TestCase):
    """Tests para verificar la autenticación JWT."""

    def setUp(self):
        """Configura el cliente de pruebas y un usuario de ejemplo."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="alice", email="a@example.com", password="pass"
        )

    def test_login_returns_user_and_tokens(self):
        """Verifica que el login retorne tokens JWT y datos del usuario."""
        resp = self.client.post(
            "/api/token/", {"username": "alice", "password": "pass"}, format="json"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("content", resp.data)
        self.assertIn("access", resp.data["content"])
        self.assertIn("refresh", resp.data["content"])
        self.assertIn("user", resp.data["content"])
        self.assertEqual(resp.data["content"]["user"]["username"], "alice")
