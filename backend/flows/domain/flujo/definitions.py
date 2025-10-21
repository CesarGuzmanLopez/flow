"""
Generic flow definitions (step-agnostic) to allow predefined flows like CADMA
and user-defined flows using the same structure.

A FlowDefinition is an ordered list of step definitions with names, types and
static configs (defaults). The orchestrator / UI can provide runtime params to
fill or override configs when instantiating the flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class FlowStepDef:
    """Definition for a single step in a flow template.

    - name: human-friendly name for the step
    - step_type: registered step type
    - description: optional description
    - config: default config/params for the step (can be overridden at instantiation)
    - requires: optional list of indices (0-based) of prior steps this step depends on
    """

    name: str
    step_type: str
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    requires: List[int] = field(default_factory=list)


@dataclass
class FlowDefinition:
    """Complete flow definition with a key and ordered steps."""

    key: str
    name: str
    description: str
    steps: List[FlowStepDef]
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


# Registry for definitions (in-memory; can be moved to DB later)
_DEFINITIONS: Dict[str, FlowDefinition] = {}


def register_definition(defn: FlowDefinition) -> None:
    _DEFINITIONS[defn.key] = defn


def get_definition(key: str) -> FlowDefinition:
    if key not in _DEFINITIONS:
        raise KeyError(f"Flow definition not found: {key}")
    return _DEFINITIONS[key]


def list_definitions() -> List[Dict[str, Any]]:
    return [
        {
            "key": d.key,
            "name": d.name,
            "description": d.description,
            "version": d.version,
            "steps": [
                {
                    "name": s.name,
                    "step_type": s.step_type,
                    "description": s.description,
                }
                for s in d.steps
            ],
        }
        for d in _DEFINITIONS.values()
    ]


__all__ = [
    "FlowStepDef",
    "FlowDefinition",
    "register_definition",
    "get_definition",
    "list_definitions",
]
