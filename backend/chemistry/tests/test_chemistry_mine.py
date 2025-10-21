"""
Tests del endpoint /mine para moléculas.

Verifica que el endpoint 'mine' retorne solo las moléculas creadas
por el usuario autenticado.
"""

from chemistry.models import Molecule
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


class ChemistryMineTests(TestCase):
    """Tests para el endpoint mine de moléculas."""

    def setUp(self):
        """Configura usuarios y moléculas de prueba."""
        self.client = APIClient()
        self.u1 = User.objects.create_user(username="u1", password="pass")
        self.u2 = User.objects.create_user(username="u2", password="pass")
        Molecule.objects.create(name="H2O", created_by=self.u1)
        Molecule.objects.create(name="NaCl", created_by=self.u2)

    def test_mine_returns_only_owned_molecules(self):
        """Verifica que /mine retorna solo moléculas del usuario autenticado."""
        self.client.force_authenticate(user=self.u1)
        resp = self.client.get("/api/chemistry/molecules/mine/")
        self.assertEqual(resp.status_code, 200)
        names = {m["name"] for m in resp.data}
        self.assertEqual(names, {"H2O"})
