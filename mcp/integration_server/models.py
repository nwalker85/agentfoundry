"""Pydantic models describing the MCP ↔ n8n manifest contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class SchemaDefinition(BaseModel):
    """JSON schema blob for validating input or output payloads."""

    type: Literal["object"] = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool = True


class ExamplePair(BaseModel):
    """Example input/output pair for the manifest."""

    input: dict[str, Any]
    output: dict[str, Any]


class Metadata(BaseModel):
    """Free-form metadata block."""

    authType: str | None = None
    n8nWorkflowId: str | None = None
    docsUrl: HttpUrl | None = None
    owner: str | None = None


class N8NConfig(BaseModel):
    """How to call the n8n workflow behind a tool."""

    type: Literal["webhook"] = "webhook"
    url: HttpUrl
    timeoutSeconds: int = 30


class ToolManifest(BaseModel):
    """Single tool definition bridging MCP to n8n."""

    toolName: str
    displayName: str
    description: str
    category: str
    logo: str
    tags: list[str] = Field(default_factory=list)
    n8n: N8NConfig
    inputSchema: SchemaDefinition
    outputSchema: SchemaDefinition
    examples: list[ExamplePair] = Field(default_factory=list)
    metadata: Metadata = Field(default_factory=Metadata)

    def normalized_name(self) -> str:
        return self.toolName.lower()
