"""Type stubs for django.test.client module."""

from typing import Any, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponse

class _MonkeyPatchedWSGIResponse(HttpResponse):
    """Django test client response."""

    data: Any

class Client:
    """Django test client."""

    def __init__(self, **defaults: Any) -> None: ...
    def get(
        self, path: str, data: Any = None, **extra: Any
    ) -> _MonkeyPatchedWSGIResponse: ...
    def post(
        self, path: str, data: Any = None, **extra: Any
    ) -> _MonkeyPatchedWSGIResponse: ...
    def put(
        self, path: str, data: Any = None, **extra: Any
    ) -> _MonkeyPatchedWSGIResponse: ...
    def patch(
        self, path: str, data: Any = None, **extra: Any
    ) -> _MonkeyPatchedWSGIResponse: ...
    def delete(
        self, path: str, data: Any = None, **extra: Any
    ) -> _MonkeyPatchedWSGIResponse: ...
    def force_authenticate(
        self, user: Optional[AbstractBaseUser] = None, token: Optional[Any] = None
    ) -> None: ...
