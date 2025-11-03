"""Type stubs for rest_framework.parsers."""

from typing import Any, Dict

from django.http import HttpRequest

class BaseParser:
    """Base parser class."""

    media_type: str

    def parse(
        self,
        stream: Any,
        media_type: str | None = None,
        parser_context: Dict[str, Any] | None = None,
    ) -> Any: ...

class JSONParser(BaseParser):
    """JSON parser."""

    media_type: str = "application/json"

class FormParser(BaseParser):
    """Form parser."""

    media_type: str = "application/x-www-form-urlencoded"

class MultiPartParser(BaseParser):
    """Multipart parser."""

    media_type: str = "multipart/form-data"

class FileUploadParser(BaseParser):
    """File upload parser."""

    media_type: str = "*/*"

__all__ = [
    "BaseParser",
    "JSONParser",
    "FormParser",
    "MultiPartParser",
    "FileUploadParser",
]
