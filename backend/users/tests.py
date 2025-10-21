"""
Tests básicos para la aplicación de usuarios.

Archivo de pruebas de humo (smoke tests) para verificar que el módulo
de usuarios se carga correctamente.
"""

from django.test import TestCase


class UsersSmokeTest(TestCase):
    """Test de humo básico para la app de users."""

    def test_smoke(self):
        """Verifica que los tests se ejecutan correctamente."""
        self.assertTrue(True)
