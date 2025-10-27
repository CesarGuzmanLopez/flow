"""
Standard JSON renderer that wraps all API responses in a unified envelope.

Envelope shape:
{
    "status": <http_status_code>,
    "message": "<short human message>",
    "content": <original payload or {}>
}

The renderer is defensive:
- Skips wrapping for drf-spectacular schema and docs views.
- Skips wrapping if the view sets `skip_standard_envelope = True`.
- Preserves paginated structures inside `content`.
- For errors (4xx/5xx), moves `detail` into `message` and keeps the rest in `content`.
- For 204 No Content, leaves body empty (no envelope) to comply with HTTP.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from rest_framework import status as drf_status
from rest_framework.renderers import JSONRenderer

logger = logging.getLogger(__name__)


def _default_message_for_status(status_code: int) -> str:
    mapping = {
        200: "OK",
        201: "Created",
        202: "Accepted",
        204: "No Content",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
    }
    return mapping.get(status_code, "OK" if 200 <= status_code < 300 else "Error")


class StandardJSONRenderer(JSONRenderer):
    charset = "utf-8"

    def render(
        self,
        data: Any,
        accepted_media_type: Optional[str] = None,
        renderer_context: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        if not renderer_context:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get("response")
        view = renderer_context.get("view")

        # If no response (unlikely) just render as-is
        if response is None:
            return super().render(data, accepted_media_type, renderer_context)

        # Respect 204 No Content semantics: no body
        if response.status_code == drf_status.HTTP_204_NO_CONTENT:
            return super().render(None, accepted_media_type, renderer_context)

        # Skip wrapping for schema/docs views (drf-spectacular)
        try:
            from drf_spectacular.views import (
                SpectacularAPIView,
                SpectacularRedocView,
                SpectacularSwaggerView,
            )

            if view and isinstance(
                view, (SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView)
            ):
                return super().render(data, accepted_media_type, renderer_context)
        except Exception:
            # If imports fail or anything odd happens, proceed with normal wrapping
            pass

        # Allow per-view opt-out
        if getattr(view, "skip_standard_envelope", False):
            return super().render(data, accepted_media_type, renderer_context)

        # If data already looks enveloped, render as-is
        if isinstance(data, dict) and {"status", "content"}.issubset(data.keys()):
            return super().render(data, accepted_media_type, renderer_context)

        status_code = int(getattr(response, "status_code", 200))
        message = _default_message_for_status(status_code)

        content: Any
        if isinstance(data, dict):
            # If DRF error response, move `detail` to message
            if status_code >= 400 and "detail" in data:
                try:
                    message = str(data.get("detail")) or message
                except Exception:
                    # best-effort only
                    pass
                content = {k: v for k, v in data.items() if k != "detail"}
            else:
                content = data
        elif data is None:
            content = {}
        else:
            # lists or primitives
            content = data

        envelope = {"status": status_code, "message": message, "content": content}
        return super().render(envelope, accepted_media_type, renderer_context)
