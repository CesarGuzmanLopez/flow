"""
Tests básicos para la aplicación de notificaciones.

Archivo de pruebas de humo (smoke tests) para verificar que el módulo
de notificaciones se carga correctamente.
"""

from django.test import TestCase


class NotificationsSmokeTest(TestCase):
    """Test de humo básico para la app de notifications."""

    def test_smoke(self):
        """Verifica que los tests se ejecutan correctamente."""
        self.assertTrue(True)
