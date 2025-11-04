"""
Pytest configuration for chemistry providers tests.

Auto-configures Django when pytest-django markers are detected.
"""

import os


def pytest_configure(config):
    """Configure Django settings for pytest if not already configured."""
    # Only configure if Django is available and settings aren't configured
    try:
        from django.conf import settings

        if not settings.configured:
            # Set Django settings module from environment or use default
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")

            # Import Django and setup
            import django

            django.setup()
    except ImportError:
        # Django not available, tests requiring it will be skipped
        pass
