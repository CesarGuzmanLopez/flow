"""Type stubs for drf_spectacular.views."""

from typing import Any

class SpectacularAPIView:
    """OpenAPI schema view."""
    @classmethod
    def as_view(cls, **kwargs: Any) -> Any: ...

class SpectacularSwaggerView:
    """Swagger UI view."""
    @classmethod
    def as_view(cls, **kwargs: Any) -> Any: ...

class SpectacularRedocView:
    """Redoc UI view."""

    @classmethod
    def as_view(cls, **kwargs: Any) -> Any: ...

__all__ = ["SpectacularAPIView", "SpectacularSwaggerView", "SpectacularRedocView"]
