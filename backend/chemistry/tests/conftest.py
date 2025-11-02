from typing import Any

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_flows_migrations(django_db_setup: Any, django_db_blocker: Any) -> None:
    """Ensure the `flows` app models and migrations are available before tests run.

    This fixture runs once per test session (autouse). It will attempt to import
    the Flow model; if import fails, it will run migrations for the `flows` app
    against the test database to create the necessary tables.

    We use `django_db_blocker` to temporarily allow database access during
    pytest-django session setup.
    """
    with django_db_blocker.unblock():
        try:
            # Simple import check
            from flows.models import Flow  # noqa: F401
        except Exception:
            # Try to apply migrations for the flows app and re-import
            from django.core.management import call_command

            # Apply migrations for the flows app only. Verbosity 0 keeps test output clean.
            call_command("migrate", "flows", verbosity=0)

            # Re-import to ensure model is available
            from flows.models import Flow  # noqa: F401

        # No return value needed; if anything fails an exception will bubble up
