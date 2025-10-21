"""
Tests básicos para la aplicación de flujos de trabajo.

Archivo de pruebas de humo (smoke tests) para verificar que el módulo
de flows se carga correctamente.
"""

from django.test import TestCase


class FlowsSmokeTest(TestCase):
    """Test de humo básico para la app de flows."""

    def test_smoke(self):
        """Verifica que los tests se ejecutan correctamente."""
        self.assertTrue(True)
