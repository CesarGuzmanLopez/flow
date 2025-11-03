"""Type stubs for django.http extensions."""

from typing import Any

from django.http.request import HttpRequest as DjangoHttpRequest
from django.http.response import Http404 as DjangoHttp404
from django.http.response import HttpResponse as DjangoHttpResponse
from django.http.response import JsonResponse as DjangoJsonResponse
from django.http.response import StreamingHttpResponse as DjangoStreamingHttpResponse

# Re-export django types
Http404 = DjangoHttp404
JsonResponse = DjangoJsonResponse
StreamingHttpResponse = DjangoStreamingHttpResponse
HttpResponse = DjangoHttpResponse

class QueryDict(dict[str, Any]):
    """QueryDict type for request.query_params."""

    pass

# Extend HttpRequest to add DRF's query_params attribute
class HttpRequest(DjangoHttpRequest):
    """Extended HttpRequest with DRF query_params."""

    query_params: QueryDict
__all__ = [
    "HttpRequest",
    "HttpResponse",
    "QueryDict",
    "Http404",
    "JsonResponse",
    "StreamingHttpResponse",
]
