"""Type stubs for Django REST Framework test utilities."""

from typing import Any, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.test.client import Client as DjangoClient
from django.test.client import (
    _MonkeyPatchedWSGIResponse as Django_MonkeyPatchedWSGIResponse,
)

class _MonkeyPatchedWSGIResponse(Django_MonkeyPatchedWSGIResponse):
    """Response object returned by APIClient requests with data attribute."""

    data: Any

class APIClient(DjangoClient):
    """DRF's extended test client with API-specific methods."""

    def force_authenticate(
        self, user: Optional[AbstractBaseUser] = None, token: Optional[Any] = None
    ) -> None: ...

class Client(APIClient):
    """Alias for APIClient for backward compatibility."""

    pass
