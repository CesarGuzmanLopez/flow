"""Type stubs for django.test module."""

from typing import Any, Callable, TypeVar

from django.test.client import Client as Client
from django.test.testcases import TestCase as TestCase

_F = TypeVar("_F", bound=Callable[..., Any])

def override_settings(**kwargs: Any) -> Callable[[_F], _F]:
    """Decorator to temporarily override settings for a test."""
    ...

__all__ = ["Client", "TestCase", "override_settings"]
