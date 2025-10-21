from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Protocol
from uuid import uuid4


@dataclass
class FlowData:
    cursor: int
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowMeta:
    current_cursor: int = 0
    current_version: int = 1
    parent: Optional[str] = None


class FlowRepository(Protocol):
    """Contract for persisting flows and events."""

    def create_flow(
        self, name: str, owner: Any, metadata: Dict[str, Any] | None = None
    ) -> str: ...

    def append(
        self, flow_id: str, data: FlowData, expected_version: int | None = None
    ) -> int: ...

    def branch(
        self, flow_id: str, from_cursor: int, branch_name: str, owner: Any
    ) -> str: ...

    def snapshot(self, flow_id: str) -> Dict[str, Any]: ...

    def get_flow_meta(self, flow_id: str) -> FlowMeta: ...


class InMemoryFlowRepository:
    """Simple in-memory repository for tests and demos."""

    def __init__(self):
        # flows: id -> dict with meta and events
        self._flows: Dict[str, Dict[str, Any]] = {}

    def create_flow(
        self, name: str, owner: Any, metadata: Dict[str, Any] | None = None
    ) -> str:
        flow_id = str(uuid4())
        self._flows[flow_id] = {
            "name": name,
            "owner": owner,
            "meta": FlowMeta(current_cursor=0, current_version=1),
            "events": [],
            "branches": {"principal": {"head": 0, "start_cursor": 0}},
            "snapshots": {},
            "metadata": metadata or {},
        }
        return flow_id

    def append(
        self, flow_id: str, data: FlowData, expected_version: int | None = None
    ) -> int:
        f = self._flows[flow_id]
        meta: FlowMeta = f["meta"]
        if expected_version is not None and expected_version != meta.current_version:
            raise ValueError("version conflict")
        meta.current_cursor += 1
        event = {
            "cursor": meta.current_cursor,
            "payload": data.payload,
            "metadata": data.metadata,
        }
        f["events"].append(event)
        return meta.current_cursor

    def branch(
        self, flow_id: str, from_cursor: int, branch_name: str, owner: Any
    ) -> str:
        f = self._flows[flow_id]
        if branch_name in f["branches"]:
            raise ValueError("branch exists")
        f["branches"][branch_name] = {
            "head": from_cursor,
            "start_cursor": from_cursor,
            "owner": owner,
        }
        return branch_name

    def snapshot(self, flow_id: str) -> Dict[str, Any]:
        f = self._flows[flow_id]
        meta: FlowMeta = f["meta"]
        snapshot = {"cursor": meta.current_cursor, "events": list(f["events"])}
        f["snapshots"][str(meta.current_version)] = snapshot
        meta.current_version += 1
        return snapshot

    def get_flow_meta(self, flow_id: str) -> FlowMeta:
        return self._flows[flow_id]["meta"]
