"""
Custom exception handler that returns errors using the standard envelope.

Ensures all error responses have the shape:
{
    "status": <http_status_code>,
    "message": "<error summary>",
    "content": { ... extra error details ... }
}
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    response = drf_exception_handler(exc, context)

    if response is not None:
        data = response.data
        message = "Error"
        content: Dict[str, Any] = {}

        if isinstance(data, dict):
            # Move common `detail` key into message
            detail = data.get("detail")
            if detail is not None:
                message = str(detail)
                content = {k: v for k, v in data.items() if k != "detail"}
            else:
                content = data
        else:
            # Non-dict errors (rare) - preserve inside `errors`
            content = {"errors": data}

        response.data = {
            "status": int(getattr(response, "status_code", 500)),
            "message": message,
            "content": content,
        }
        return response

    # If DRF could not handle it, return a generic 500 error envelope
    return Response(
        {"status": 500, "message": "Internal Server Error", "content": {}}, status=500
    )
