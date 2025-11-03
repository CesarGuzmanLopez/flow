"""Type stubs for rest_framework.routers."""

from typing import Any, List, Tuple

from django.urls import URLPattern

class BaseRouter:
    """Base router class."""

    registry: List[Tuple[str, Any, str]]

    def register(
        self, prefix: str, viewset: Any, basename: str | None = None
    ) -> None: ...
    @property
    def urls(self) -> List[URLPattern]: ...

class SimpleRouter(BaseRouter):
    """Simple router for basic routing."""

    pass

class DefaultRouter(SimpleRouter):
    """Default router with API root view."""

    pass

__all__ = ["BaseRouter", "SimpleRouter", "DefaultRouter"]
