"""
Middleware to enforce a standard response envelope for all JSON API endpoints.

Envelope:
{
  "status": <http_status_code>,
  "message": "<short message>",
  "content": <original_json_payload>
}

This runs after DRF rendering so it also covers views that bypass DRF renderers
(e.g., custom views or third-party views). It only wraps responses that:
- are under the /api/ path,
- have content-type application/json,
- are not 204 No Content,
- are not the OpenAPI schema or docs endpoints,
- are not already enveloped (has both 'status' and 'content').
"""

from __future__ import annotations

import json
from typing import Callable

from django.http import HttpRequest, HttpResponse


def _default_message(status_code: int) -> str:
    if 200 <= status_code < 300:
        return (
            "OK"
            if status_code == 200
            else "Created"
            if status_code == 201
            else "Success"
        )
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
    return "Error"


class StandardResponseEnvelopeMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        # Only process JSON under /api/
        path = request.path or ""
        ctype = (response.headers.get("Content-Type") or "").split(";")[0].strip()

        if not path.startswith("/api/"):
            return response
        if path.startswith("/api/schema") or path.startswith("/api/docs"):
            return response
        if response.status_code == 204:
            return response
        if ctype != "application/json":
            return response

        try:
            raw = response.content.decode(response.charset or "utf-8")
            data = json.loads(raw) if raw else None
        except Exception:
            return response

        # Skip if already enveloped
        if isinstance(data, dict) and {"status", "content"}.issubset(data.keys()):
            return response

        status_code = int(getattr(response, "status_code", 200))
        message = _default_message(status_code)

        if isinstance(data, dict) and "detail" in data and status_code >= 400:
            try:
                message = str(data.get("detail")) or message
            except Exception:
                pass
            content = {k: v for k, v in data.items() if k != "detail"}
        else:
            content = {} if data is None else data

        enveloped = {"status": status_code, "message": message, "content": content}
        response.content = json.dumps(enveloped).encode(response.charset or "utf-8")
        # Update Content-Length if present
        if "Content-Length" in response.headers:
            response.headers["Content-Length"] = str(len(response.content))
        return response
