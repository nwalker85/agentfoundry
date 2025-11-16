"""Admin MCP Tool Implementation.

Exposes the ObjectAdminAgent over HTTP/MCP so the UI can list/get core objects.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from mcp.schemas import ToolResponse
from agent.object_admin_agent import ObjectAdminAgent, ObjectType, OperationType, ObjectAdminState


class ListObjectsRequest(BaseModel):
  object_type: ObjectType = Field(..., description="organization | domain | instance | user")
  organization_id: Optional[str] = Field(None, description="Optional org filter")
  domain_id: Optional[str] = Field(None, description="Optional domain filter")
  environment: Optional[str] = Field(None, description="Optional environment filter (instances)")


class GetObjectRequest(BaseModel):
  object_type: ObjectType = Field(..., description="organization | domain | instance | user")
  id: str = Field(..., description="Primary key of the object")


class AdminTool:
  """MCP-facing wrapper around ObjectAdminAgent."""

  def __init__(self) -> None:
    self.agent = ObjectAdminAgent()

  async def list_objects(self, request: ListObjectsRequest) -> ToolResponse:
    state: ObjectAdminState = {
      "object_type": request.object_type,
      "operation": "list",
      "organization_id": request.organization_id,
      "domain_id": request.domain_id,
      "environment": request.environment,
    }
    result_state = await self.agent.run(state)
    if result_state.get("error"):
      return ToolResponse(success=False, error=result_state["error"])
    return ToolResponse(success=True, data=result_state.get("result", []))

  async def get_object(self, request: GetObjectRequest) -> ToolResponse:
    state: ObjectAdminState = {
      "object_type": request.object_type,
      "operation": "get",
      "id": request.id,
    }
    result_state = await self.agent.run(state)
    if result_state.get("error"):
      return ToolResponse(success=False, error=result_state["error"])
    return ToolResponse(success=True, data=result_state.get("result"))


