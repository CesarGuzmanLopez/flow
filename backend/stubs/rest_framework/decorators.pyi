"""Type stubs for rest_framework.decorators."""

from typing import Any, Callable, List, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

def api_view(http_method_names: list[str]) -> Callable[[F], F]: ...
def action(
    methods: Optional[List[str]] = None,
    detail: bool = True,
    url_path: Optional[str] = None,
    url_name: Optional[str] = None,
    suffix: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[F], F]: ...
