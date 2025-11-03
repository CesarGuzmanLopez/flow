"""Type stubs for rest_framework.serializers."""

from typing import Any, Dict, Generic, TypeVar

from django.db.models import Model

_MT = TypeVar("_MT", bound=Model)

class Field:
    """Base field class."""

    def __init__(self, **kwargs: Any) -> None: ...

class Serializer(Generic[_MT]):
    """Base serializer class."""

    data: Dict[str, Any]
    validated_data: Dict[str, Any]
    instance: _MT | None

    def __init__(
        self,
        instance: _MT | None = None,
        data: Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None: ...
    def is_valid(self, raise_exception: bool = False) -> bool: ...
    def save(self, **kwargs: Any) -> _MT: ...
    def create(self, validated_data: Dict[str, Any]) -> _MT: ...
    def update(self, instance: _MT, validated_data: Dict[str, Any]) -> _MT: ...

class ModelSerializer(Serializer[_MT]):
    """Model serializer class."""

    class Meta:
        model: type[_MT]
        fields: str | list[str]
        read_only_fields: list[str]

class CharField(Field):
    """Char field."""

    pass

class IntegerField(Field):
    """Integer field."""

    pass

class BooleanField(Field):
    """Boolean field."""

    pass

class DateTimeField(Field):
    """DateTime field."""

    pass

class EmailField(CharField):
    """Email field."""

    pass

class JSONField(Field):
    """JSON field."""

    pass

class PrimaryKeyRelatedField(Field):
    """Primary key related field."""

    queryset: Any

    def __init__(
        self, queryset: Any = None, many: bool = False, **kwargs: Any
    ) -> None: ...

class SerializerMethodField(Field):
    """Serializer method field."""

    def __init__(self, method_name: str | None = None, **kwargs: Any) -> None: ...

__all__ = [
    "Field",
    "Serializer",
    "ModelSerializer",
    "CharField",
    "IntegerField",
    "BooleanField",
    "DateTimeField",
    "EmailField",
    "JSONField",
    "PrimaryKeyRelatedField",
    "SerializerMethodField",
]
