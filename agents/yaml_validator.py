"""
YAML Validator - Pydantic models for agent YAML schema validation

Validates agent configuration files against the canonical schema.
Used by Marshal Agent to ensure all agents are properly configured.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class WorkflowType(str, Enum):
    """Supported workflow types."""

    LANGGRAPH_STATE_GRAPH = "langgraph.StateGraph"
    LANGGRAPH_PREGEL = "langgraph.Pregel"
    SIMPLE_CHAIN = "simple.chain"


class NodeConfig(BaseModel):
    """LangGraph node configuration."""

    id: str = Field(..., description="Unique node identifier")
    handler: str = Field(..., description="Module path to handler function")
    description: str = Field(..., description="Node purpose description")
    next: list[str] = Field(default_factory=list, description="Next node IDs or END")
    timeout_seconds: int = Field(default=30, ge=1, le=300)

    @field_validator("handler")
    @classmethod
    def validate_handler_path(cls, v: str) -> str:
        """Ensure handler path has at least module.Class.method format."""
        parts = v.split(".")
        if len(parts) < 3:
            raise ValueError(f"Handler must be module.Class.method format, got: {v}")
        return v


class WorkflowConfig(BaseModel):
    """Workflow graph configuration."""

    type: WorkflowType
    entry_point: str = Field(..., description="Starting node ID")
    recursion_limit: int = Field(default=100, ge=10, le=1000)
    nodes: list[NodeConfig] = Field(..., min_length=1)

    @field_validator("entry_point")
    @classmethod
    def validate_entry_point(cls, v: str, info) -> str:
        """Ensure entry_point references an actual node."""
        # Note: We can't validate against nodes here due to validator order
        # This will be validated in the full model validator
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate cross-field constraints."""
        # Ensure entry_point exists in nodes
        node_ids = {node.id for node in self.nodes}
        if self.entry_point not in node_ids:
            raise ValueError(f"Entry point '{self.entry_point}' not found in nodes: {node_ids}")

        # Validate all 'next' references
        for node in self.nodes:
            for next_id in node.next:
                if next_id not in node_ids and next_id != "END":
                    raise ValueError(f"Node '{node.id}' references unknown next node: {next_id}")


class AgentMetadata(BaseModel):
    """Agent metadata."""

    id: str = Field(..., pattern=r"^[a-z0-9-]+$", description="Agent ID (lowercase, hyphens)")
    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="SemVer format")
    description: str = Field(..., min_length=1, max_length=500)
    tags: list[str] = Field(default_factory=list)
    created: str = Field(..., description="ISO 8601 datetime")
    updated: str = Field(..., description="ISO 8601 datetime")

    @field_validator("created", "updated")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        """Ensure datetime strings are valid ISO 8601."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 datetime: {v}") from e
        return v


class ParameterConfig(BaseModel):
    """Agent parameter definition."""

    name: str
    type: str  # 'integer', 'float', 'string', 'boolean'
    default: Any
    description: str
    min: Any | None = None
    max: Any | None = None
    enum: list[str] | None = None


class IntegrationConfig(BaseModel):
    """External integration configuration."""

    type: str  # 'notion', 'openai', 'github', etc.
    required: bool = True
    operations: list[str] = Field(default_factory=list)
    # Allow additional fields for integration-specific config
    model_config = {"extra": "allow"}


class ResourceLimits(BaseModel):
    """Resource limits for agent execution."""

    max_concurrent_tasks: int = Field(default=3, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=10, le=3600)
    memory_mb: int = Field(default=512, ge=128, le=4096)
    max_tokens_per_request: int = Field(default=4000, ge=100, le=128000)


class ObservabilityConfig(BaseModel):
    """Observability and telemetry configuration."""

    trace_level: str = Field(default="info", pattern=r"^(debug|info|warning|error)$")
    metrics_enabled: bool = True
    metrics_interval_seconds: int = Field(default=30, ge=10, le=300)
    log_retention_days: int = Field(default=30, ge=1, le=365)
    structured_logging: bool = True


class HealthCheckConfig(BaseModel):
    """Health check configuration."""

    enabled: bool = True
    interval_seconds: int = Field(default=60, ge=10, le=600)
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    unhealthy_threshold: int = Field(default=3, ge=1, le=10)


class AgentSpec(BaseModel):
    """Agent specification."""

    capabilities: list[str] = Field(..., min_length=1)
    parameters: list[ParameterConfig] = Field(default_factory=list)
    workflow: WorkflowConfig
    integrations: list[IntegrationConfig] = Field(default_factory=list)
    resource_limits: ResourceLimits = Field(default_factory=ResourceLimits)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)


class AgentStatus(BaseModel):
    """Agent runtime status (managed by Marshal)."""

    phase: str = Field(default="alpha", pattern=r"^(alpha|beta|production|deprecated)$")
    state: str = Field(default="inactive", pattern=r"^(active|inactive|paused|error)$")
    last_heartbeat: str | None = None
    uptime_seconds: int = Field(default=0, ge=0)
    total_executions: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    avg_latency_ms: float = Field(default=0.0, ge=0.0)
    error_message: str | None = None


class AgentYAML(BaseModel):
    """Complete agent YAML schema.

    This is the canonical schema for all agent definitions.
    Marshal Agent uses this to validate and load agents.

    Example:
        ```yaml
        apiVersion: engineering-dept/v1
        kind: Agent
        metadata:
          id: pm-agent
          name: Project Manager Agent
          version: 1.0.0
          ...
        spec:
          capabilities:
            - requirement_analysis
          workflow:
            type: langgraph.StateGraph
            entry_point: understand
            nodes:
              - id: understand
                handler: agents.workers.pm_agent.PMAgent.process
                ...
        status:
          phase: production
          state: active
        ```
    """

    apiVersion: str = Field(
        ..., pattern=r"^engineering-dept/v\d+$", description="API version (e.g., engineering-dept/v1)"
    )
    kind: str = Field(..., pattern=r"^Agent$", description="Resource kind (must be 'Agent')")
    metadata: AgentMetadata
    spec: AgentSpec
    status: AgentStatus = Field(default_factory=AgentStatus)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (for serialization)."""
        return self.model_dump(mode="json", exclude_none=True)

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "AgentYAML":
        """Load and validate from YAML file.

        Args:
            file_path: Path to .agent.yaml file

        Returns:
            Validated AgentYAML instance

        Raises:
            ValidationError: If YAML is invalid
        """
        from pathlib import Path

        import yaml

        yaml_path = Path(file_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Agent YAML not found: {file_path}")

        with open(yaml_path) as f:
            raw_data = yaml.safe_load(f)

        return cls(**raw_data)


class ValidationResult(BaseModel):
    """Result of agent YAML validation."""

    valid: bool
    agent_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)
