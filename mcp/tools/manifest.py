"""Manifest MCP Tool Implementation.

Exposes operations for managing agent manifests via the MCP server.
This is a thin wrapper around the LangGraph-based ManifestAgent.
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from mcp.schemas import ToolResponse
from agent.manifest_agent import ManifestAgent


class RegisterAgentRequest(BaseModel):
  """Request schema for registering/updating an agent binding in a manifest."""

  agent_id: str = Field(..., description="Logical agent identifier")
  agent_yaml: str = Field(..., description="Full agent YAML specification")
  yaml_path: Optional[str] = Field(
    default=None,
    description="Relative path under agents/ for the YAML file (defaults to <env>_<agent_id>.yaml)",
  )

  organization_id: str
  organization_name: str
  domain_id: str
  domain_name: str
  environment: str = Field(..., description="Environment: dev | staging | prod")
  instance_id: str = Field(..., description="Instance identifier within environment")

  author: str
  last_editor: Optional[str] = None
  tags: List[str] = Field(default_factory=list)
  is_system_agent: bool = False
  system_tier: Optional[int] = Field(
    default=None,
    description="System tier (0 = foundation, 1 = production). Omit for custom agents.",
  )


class ManifestTool:
  """MCP-facing wrapper around ManifestAgent."""

  def __init__(self) -> None:
    self.agent = ManifestAgent()

  async def register_agent(self, request: RegisterAgentRequest) -> ToolResponse:
    """Create or update an agent YAML + manifest binding."""
    try:
      result = await self.agent.create_or_update_agent_binding(
        agent_id=request.agent_id,
        agent_yaml=request.agent_yaml,
        yaml_path=request.yaml_path,
        organization_id=request.organization_id,
        organization_name=request.organization_name,
        domain_id=request.domain_id,
        domain_name=request.domain_name,
        environment=request.environment,
        instance_id=request.instance_id,
        author=request.author,
        last_editor=request.last_editor,
        tags=request.tags,
        is_system_agent=request.is_system_agent,
        system_tier=request.system_tier,
      )
      return ToolResponse(success=True, data=result)
    except Exception as e:
      return ToolResponse(success=False, error=str(e))


