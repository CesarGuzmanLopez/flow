from typing import Any, Dict, Optional

from ..domain.repository import FlowData, FlowRepository, InMemoryFlowRepository


class FlowEngine:
    """High-level helper to orchestrate flow creation and step appends.

    This sits in the application layer and depends on the FlowRepository port.
    """

    def __init__(self, repo: FlowRepository | None = None):
        self.repo = repo or InMemoryFlowRepository()

    def create_flow(
        self, name: str, owner: Any, metadata: Optional[Dict] = None
    ) -> str:
        return self.repo.create_flow(name=name, owner=owner, metadata=metadata)

    def add_step(
        self, flow_id: str, payload: Dict, expected_version: int | None = None
    ) -> int:
        data = FlowData(cursor=0, payload=payload, metadata={})
        return self.repo.append(
            flow_id=flow_id, data=data, expected_version=expected_version
        )

    def create_branch(
        self, flow_id: str, from_cursor: int, branch_name: str, owner: Any
    ) -> str:
        return self.repo.branch(
            flow_id=flow_id,
            from_cursor=from_cursor,
            branch_name=branch_name,
            owner=owner,
        )

    def snapshot(self, flow_id: str) -> Dict:
        return self.repo.snapshot(flow_id=flow_id)
