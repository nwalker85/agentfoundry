"""Data MCP Tool Implementation.

Exposes the DataAgent via MCP-style HTTP endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from agent.data_agent import DataAgent
from mcp.schemas import ToolResponse


class DataQueryRequest(BaseModel):
    """Natural-language data query for control-plane DB."""

    question: str = Field(..., description="Natural language question about orgs/domains/instances/deployments")


class DataTool:
    """MCP-facing wrapper around DataAgent."""

    def __init__(self) -> None:
        self.agent = DataAgent()

    async def query(self, request: DataQueryRequest) -> ToolResponse:
        try:
            state = await self.agent.query(request.question)
            if state.get("error"):
                return ToolResponse(success=False, error=state["error"], data={"sql": state.get("sql")})
            return ToolResponse(success=True, data={"sql": state.get("sql"), "rows": state.get("rows", [])})
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
