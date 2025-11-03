"""Type stubs for rest_framework.renderers."""

from typing import Any, Dict

from django.http import HttpRequest

class BaseRenderer:
    """Base renderer class."""

    media_type: str
    format: str
    charset: str | None

    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: Dict[str, Any] | None = None,
    ) -> bytes: ...

class JSONRenderer(BaseRenderer):
    """JSON renderer."""

    media_type: str = "application/json"
    format: str = "json"

class BrowsableAPIRenderer(BaseRenderer):
    """Browsable API renderer."""

    media_type: str = "text/html"
    format: str = "api"

__all__ = ["BaseRenderer", "JSONRenderer", "BrowsableAPIRenderer"]
