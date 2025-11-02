"""
Typed step interface, registry, and data stack for flow-agnostic steps.

Goals:
- Strongly-typed inputs/outputs per step using dataclasses
- A DataStack within the StepContext that accumulates typed data produced so far
- Ability to reference prior data by type or by producer step when composing flows

Back-compat: execute_step still accepts a dict and returns StepResult with a dict outputs.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, get_type_hints

TIn = TypeVar("TIn", contravariant=True)
TOut = TypeVar("TOut", covariant=True)


@dataclass
class StepContext:
    user: Any
    data_stack: "DataStack"


@dataclass
class StepResult:
    outputs: Dict[str, Any]
    metadata: Dict[str, Any]
    value: Any | None = None


class StepHandler(Protocol[TIn, TOut]):
    def execute(self, ctx: StepContext, inp: TIn) -> StepResult: ...


@dataclass
class DataItem:
    """Single item stored in the data stack.

    - type_name: semantic identifier for the produced data type
    - value: typed object (often a dataclass instance)
    - source_step: optional step type that produced it
    - step_id: optional persistent step id (when available)
    """

    type_name: str
    value: Any
    source_step: Optional[str] = None
    step_id: Optional[str] = None


class DataStack:
    def __init__(self, items: Optional[List[DataItem]] = None):
        self._items: List[DataItem] = list(items or [])

    def push(self, item: DataItem) -> None:
        self._items.append(item)

    def latest(self, type_name: str) -> Any:
        for it in reversed(self._items):
            if it.type_name == type_name:
                return it.value
        raise KeyError(f"No data of type {type_name} found in stack")

    def all_of(self, type_name: str) -> List[Any]:
        return [it.value for it in self._items if it.type_name == type_name]

    def find(self, *, type_name: str, source_step: Optional[str] = None) -> List[Any]:
        out: List[Any] = []
        for it in self._items:
            if it.type_name != type_name:
                continue
            if source_step is not None and it.source_step != source_step:
                continue
            out.append(it.value)
        return out


@dataclass
class StepSpec:
    step_type: str
    input_cls: Type[Any]
    output_cls: Type[Any]
    produces_type_name: str


_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_step(
    step_type: str, handler: StepHandler, spec: StepSpec | None = None
) -> None:
    _REGISTRY[step_type] = {"handler": handler, "spec": spec}


def get_step(step_type: str) -> StepHandler:
    if step_type not in _REGISTRY:
        raise ValueError(f"Unknown step type: {step_type}")
    return _REGISTRY[step_type]["handler"]


def get_spec(step_type: str) -> StepSpec:
    if step_type not in _REGISTRY or _REGISTRY[step_type].get("spec") is None:
        raise ValueError(f"No spec registered for step type: {step_type}")
    return _REGISTRY[step_type]["spec"]


def _validate_and_build_dataclass(cls: Type[Any], data: Dict[str, Any]) -> Any:
    """Very small runtime validator to construct dataclasses from dicts using annotations."""
    hints = get_type_hints(cls)
    kwargs: Dict[str, Any] = {}
    for field, typ in hints.items():
        if field not in data:
            # allow missing optional fields
            kwargs[field] = None
            continue
        val = data[field]
        # Simple checks for common cases
        origin = getattr(typ, "__origin__", None)
        args = getattr(typ, "__args__", ())
        if origin is list and args:
            if not isinstance(val, list):
                raise TypeError(f"{field} must be List[{args[0]}]")
            if args and args[0] in (str, int, float, bool):
                if not all(isinstance(x, args[0]) for x in val):
                    raise TypeError(f"{field} items must be {args[0]}")
        elif origin is dict and args:
            if not isinstance(val, dict):
                raise TypeError("{field} must be a dict")
        else:
            # primitives best effort
            if (
                typ in (str, int, float, bool)
                and val is not None
                and not isinstance(val, typ)
            ):
                raise TypeError(f"{field} must be {typ}")
        kwargs[field] = val
    return cls(**kwargs)


def execute_step(
    step_type: str, ctx: StepContext, params: Dict[str, Any]
) -> StepResult:
    spec = get_spec(step_type)
    inp = _validate_and_build_dataclass(spec.input_cls, params)
    handler: StepHandler = get_step(step_type)
    result = handler.execute(ctx, inp)
    # If handler returned a typed value, push onto stack under produces_type_name
    if result.value is not None:
        ctx.data_stack.push(
            DataItem(
                type_name=spec.produces_type_name,
                value=result.value,
                source_step=step_type,
            )
        )
    # Ensure outputs is a dict representation for API
    if result.value is not None and not result.outputs:
        if is_dataclass(result.value) and not isinstance(result.value, type):
            result.outputs = asdict(result.value)
        else:
            result.outputs = {"value": result.value}
    return result


def _type_to_str(t: Any) -> str:
    try:
        return str(t).replace("typing.", "")
    except Exception:
        return repr(t)


def dataclass_schema(cls: Type[Any]) -> Dict[str, Any]:
    if not is_dataclass(cls):
        return {"type": "object"}
    fs = []
    hints = get_type_hints(cls)
    for f in fields(cls):
        t = hints.get(f.name, Any)
        fs.append({"name": f.name, "type": _type_to_str(t)})
    return {"type": "object", "fields": fs}


def list_step_specs() -> List[Dict[str, Any]]:
    specs: List[Dict[str, Any]] = []
    for stype, data in _REGISTRY.items():
        spec: Optional[StepSpec] = data.get("spec")
        if not spec:
            continue
        specs.append(
            {
                "step_type": spec.step_type,
                "produces_type": spec.produces_type_name,
                "input_schema": dataclass_schema(spec.input_cls),
                "output_schema": dataclass_schema(spec.output_cls),
            }
        )
    return specs


__all__ = [
    "StepContext",
    "StepResult",
    "StepHandler",
    "register_step",
    "get_step",
    "execute_step",
    "StepSpec",
    "DataStack",
    "DataItem",
    "get_spec",
    "dataclass_schema",
    "list_step_specs",
]
