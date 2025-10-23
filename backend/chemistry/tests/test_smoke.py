"""
Smoke tests for the Chemistry app placed under the tests/ package to avoid
module/package name collision with a top-level tests.py.
"""

from django.test import TestCase


class ChemistrySmokeTest(TestCase):
    """Basic smoke test to ensure test discovery works."""

    def test_smoke(self):
        self.assertTrue(True)
