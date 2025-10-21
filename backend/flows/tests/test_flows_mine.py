"""
Tests del endpoint /mine para flujos de trabajo.

Verifica que el endpoint 'mine' retorne solo los flujos creados
por el usuario autenticado.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from flows.models import Flow
from rest_framework.test import APIClient

User = get_user_model()


class FlowMineTests(TestCase):
    """Tests para el endpoint mine de flujos."""

    def setUp(self):
        """Configura usuarios y flujos de prueba."""
        self.client = APIClient()
        self.u1 = User.objects.create_user(username="u1", password="pass")
        self.u2 = User.objects.create_user(username="u2", password="pass")
        Flow.objects.create(name="F1", description="", owner=self.u1)
        Flow.objects.create(name="F2", description="", owner=self.u2)

    def test_mine_returns_only_owned_flows(self):
        """Verifica que /mine retorna solo flujos del usuario autenticado."""
        self.client.force_authenticate(user=self.u1)
        resp = self.client.get("/api/flows/flows/mine/")
        self.assertEqual(resp.status_code, 200)
        names = {f["name"] for f in resp.data}
        self.assertEqual(names, {"F1"})
