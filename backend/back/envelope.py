"""
DRF mixin to enforce a standard response envelope at the Response.data level.

Envelope:
{
  "status": <http_status_code>,
  "message": "<short message>",
  "content": <original_payload>
}

Attach this mixin to APIView/ViewSet classes (before DRF base class) to ensure
`resp.data` from tests is already enveloped (renderer-agnostic).
"""

from __future__ import annotations

from typing import Any, Protocol, cast

from rest_framework import status as drf_status
from rest_framework.response import Response


class HasFinalizeResponse(Protocol):
    """Protocol for objects that have finalize_response method."""

    def finalize_response(
        self, request: Any, response: Any, *args: Any, **kwargs: Any
    ) -> Any: ...


def _default_message_for_status(status_code: int) -> str:
    if status_code == 200:
        return "OK"
    if status_code == 201:
        return "Created"
    if status_code == 202:
        return "Accepted"
    if status_code == 204:
        return "No Content"
    if status_code == 400:
        return "Bad Request"
    if status_code == 401:
        return "Unauthorized"
    if status_code == 403:
        return "Forbidden"
    if status_code == 404:
        return "Not Found"
    if status_code == 409:
        return "Conflict"
    if status_code == 422:
        return "Unprocessable Entity"
    if status_code >= 500:
        return "Internal Server Error"
    return "OK" if 200 <= status_code < 300 else "Error"


class StandardEnvelopeMixin:
    """Mixin to wrap DRF Response.data into a standard envelope shape.

    Set `skip_standard_envelope = True` on views that must opt out.
    """

    skip_standard_envelope: bool = False

    def finalize_response(
        self, request: Any, response: Any, *args: Any, **kwargs: Any
    ) -> Any:
        # Wrap BEFORE DRF renders the response so that tests see enveloped resp.data
        if isinstance(response, Response):
            if (
                not self.skip_standard_envelope
                and response.status_code != drf_status.HTTP_204_NO_CONTENT
            ):
                data = response.data
                if not (
                    isinstance(data, dict)
                    and {"status", "content"}.issubset(data.keys())
                ):
                    status_code = int(getattr(response, "status_code", 200))
                    message = _default_message_for_status(status_code)
                    if (
                        isinstance(data, dict)
                        and status_code >= 400
                        and "detail" in data
                    ):
                        try:
                            message = str(data.get("detail")) or message
                        except Exception:
                            pass
                        content: Any = {k: v for k, v in data.items() if k != "detail"}
                    else:
                        content = {} if data is None else data
                    response.data = {
                        "status": status_code,
                        "message": message,
                        "content": content,
                    }

        # Now let DRF render - superclass will have finalize_response at runtime
        parent = cast(HasFinalizeResponse, super())
        return parent.finalize_response(request, response, *args, **kwargs)
