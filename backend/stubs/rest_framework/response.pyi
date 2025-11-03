"""Type stubs for rest_framework.response."""

from typing import Any, Dict, Optional

from django.http import HttpResponse

class Response(HttpResponse):
    """DRF Response class."""

    data: Any
    status_code: int

    def __init__(
        self,
        data: Any = None,
        status: Optional[int] = None,
        template_name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        exception: bool = False,
        content_type: Optional[str] = None,
    ) -> None: ...

__all__ = ["Response"]
