"""
Tests básicos para la aplicación de química.

Archivo de pruebas de humo (smoke tests) para verificar que el módulo
de chemistry se carga correctamente.
"""

from django.test import TestCase


class ChemistrySmokeTest(TestCase):
    """Test de humo básico para la app de chemistry."""

    def test_smoke(self):
        """Verifica que los tests se ejecutan correctamente."""
        # Basic smoke test to ensure test discovery picks up this file
        self.assertTrue(True)
