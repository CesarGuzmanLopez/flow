"""
Pytest configuration for toxicology provider tests.

Ensures Django models and database are available for background job tests.
"""

from typing import Any

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_django_for_tests(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Configure Django and create necessary tables for toxicology job tests.

    This runs once per test session and ensures:
    1. Django is properly configured
    2. Database tables are created for background_jobs models
    """
    with django_db_blocker.unblock():
        from django.core.management import call_command

        # Create tables for all apps (migrations)
        call_command("migrate", "--run-syncdb", verbosity=0)
