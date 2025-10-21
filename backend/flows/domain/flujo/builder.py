"""
Builder utilities to instantiate a Flow and initial FlowVersion from a FlowDefinition.
"""

from __future__ import annotations

from typing import Any, Dict

from django.db import transaction
from flows.models import Flow, FlowVersion, Step, StepDependency

from .definitions import FlowDefinition


@transaction.atomic
def create_flow_from_definition(
    *,
    owner: Any,
    defn: FlowDefinition,
    name: str | None = None,
    params_override: Dict[int, Dict] | None = None,
) -> Flow:
    """
    Create a Flow and an initial FlowVersion with Steps from the given definition.

    params_override: optional dict mapping step index -> dict of params to
    merge into default config.
    """
    flow = Flow.objects.create(
        name=name or defn.name,
        description=defn.description,
        owner=owner,
    )
    version = FlowVersion.objects.create(
        flow=flow,
        version_number=1,
        parent_version=None,
        created_by=owner,
        metadata={"definition_key": defn.key, "definition_version": defn.version},
        is_frozen=False,
    )

    created_steps: list[Step] = []
    for idx, sdef in enumerate(defn.steps):
        cfg = dict(sdef.config)
        if params_override and idx in params_override:
            # shallow merge; caller can pass full config if needed
            cfg.update(params_override[idx])
        step = Step.objects.create(
            flow_version=version,
            name=sdef.name,
            description=sdef.description,
            step_type=sdef.step_type,
            order=idx + 1,
            config=cfg,
        )
        created_steps.append(step)

    # create dependencies
    for idx, sdef in enumerate(defn.steps):
        if sdef.requires:
            for req_idx in sdef.requires:
                StepDependency.objects.create(
                    step=created_steps[idx], depends_on_step=created_steps[req_idx]
                )

    return flow


__all__ = ["create_flow_from_definition"]
