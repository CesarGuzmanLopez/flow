"""Type stubs for rest_framework.permissions."""

from typing import Any, Tuple

from django.http import HttpRequest

# Safe HTTP methods that don't modify data
SAFE_METHODS: Tuple[str, str, str] = ("GET", "HEAD", "OPTIONS")

class BasePermission:
    """Base permission class."""

    def has_permission(self, request: HttpRequest, view: Any) -> bool: ...

    # Check if the user has permission to access the view
    def has_object_permission(
        self, request: HttpRequest, view: Any, obj: Any
    ) -> bool: ...

class IsAuthenticated(BasePermission):
    """Permission that requires authentication."""

    pass

class IsAuthenticatedOrReadOnly(BasePermission):
    """Permission that allows read-only for unauthenticated users."""

    pass

class AllowAny(BasePermission):
    """Permission that allows any access."""

    pass

class IsAdminUser(BasePermission):
    """Permission that requires admin user."""

    pass

__all__ = [
    "BasePermission",
    "IsAuthenticated",
    "IsAuthenticatedOrReadOnly",
    "AllowAny",
    "IsAdminUser",
]
