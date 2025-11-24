"""
Agent Deployment Service
Handles end-to-end deployment of agents from Forge UI to production
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.converters.react_flow_to_python import reactflow_to_python, validate_graph

logger = logging.getLogger(__name__)


def sanitize_identifier(name: str) -> str:
    """Convert any string to a valid Python identifier by replacing hyphens with underscores."""
    return name.replace("-", "_")


class AgentDeployer:
    """
    Service for deploying agents from visual designer to production.

    Flow:
    1. Validate graph structure
    2. Generate Python LangGraph code
    3. Generate YAML agent manifest
    4. Save files to agents/ directory
    5. Trigger Marshal hot-reload
    """

    def __init__(self, agents_dir: Path | None = None):
        """Initialize deployer with agents directory."""
        if agents_dir is None:
            # Default to /app/agents in production, or project root in dev
            self.agents_dir = Path(__file__).parent.parent.parent / "agents"
        else:
            self.agents_dir = Path(agents_dir)

        # Ensure directory exists
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"AgentDeployer initialized with directory: {self.agents_dir}")

    async def deploy_agent(
        self, agent_id: str, agent_name: str, graph_data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Deploy an agent from graph data.

        Args:
            agent_id: Unique agent ID (e.g., "cibc-card-agent")
            agent_name: Display name for agent
            graph_data: ReactFlow graph (nodes, edges)
            metadata: Optional metadata (description, tags, etc.)

        Returns:
            Deployment result with file paths and status
        """
        logger.info(f"🚀 Deploying agent: {agent_id}")

        try:
            # 1. Validate graph
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            logger.info(f"Validating graph with {len(nodes)} nodes and {len(edges)} edges")
            logger.info(f"Node types: {[n.get('type') for n in nodes]}")

            validation = validate_graph(nodes, edges)

            if not validation["valid"]:
                logger.error(f"Validation failed: {validation['errors']}")
                logger.error(f"Graph data: {graph_data}")
                raise ValueError(f"Invalid graph: {validation['errors']}")

            # 2. Generate Python code (use sanitized module name)
            sanitized_id = sanitize_identifier(agent_id)
            python_code = reactflow_to_python(
                {"nodes": graph_data.get("nodes", []), "edges": graph_data.get("edges", []), "agentName": sanitized_id}
            )

            # 3. Generate YAML manifest
            yaml_content = self._generate_yaml_manifest(
                agent_id=agent_id,
                sanitized_id=sanitized_id,
                agent_name=agent_name,
                metadata=metadata or {},
                graph_data=graph_data,
            )

            # 4. Save files (use sanitized name for Python module)
            python_file = self.agents_dir / f"{sanitized_id}.py"
            yaml_file = self.agents_dir / f"{agent_id}.agent.yaml"

            # Write Python file
            with open(python_file, "w") as f:
                f.write(python_code)
            logger.info(f"✅ Saved Python: {python_file}")

            # Write YAML file
            with open(yaml_file, "w") as f:
                f.write(yaml_content)
            logger.info(f"✅ Saved YAML: {yaml_file}")

            # 5. Trigger hot-reload (if Marshal is available)
            await self._trigger_hot_reload(agent_id)

            return {
                "success": True,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "files": {"python": str(python_file), "yaml": str(yaml_file)},
                "deployed_at": datetime.utcnow().isoformat(),
                "validation": validation,
            }

        except Exception as e:
            logger.error(f"❌ Deployment failed for {agent_id}: {e}", exc_info=True)
            return {"success": False, "agent_id": agent_id, "error": str(e)}

    def _generate_yaml_manifest(
        self, agent_id: str, sanitized_id: str, agent_name: str, metadata: dict[str, Any], graph_data: dict[str, Any]
    ) -> str:
        """Generate YAML agent manifest matching Marshal's AgentYAML schema."""

        # Handle empty description (Pydantic requires at least 1 character)
        description = metadata.get("description", "").strip() or f"{agent_name} - deployed from Forge"
        tags = metadata.get("tags", []) or ["forge-deployed", "custom-agent"]

        # Get nodes from graph for workflow
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        # Generate timestamp
        now = datetime.utcnow().isoformat() + "Z"

        # Build workflow nodes (create simple handler references)
        workflow_nodes = []
        for node in nodes:
            node_id = node.get("id", "")
            node_type = node.get("type", "")
            node_data = node.get("data", {})

            # Skip entry point nodes - they don't have handlers
            if node_type == "entryPoint":
                continue

            # Sanitize node_id for Python function names
            sanitized_node_id = sanitize_identifier(node_id)

            # Generate class name from agent ID
            class_name = f"{sanitized_id.replace('_', ' ').title().replace(' ', '')}Agent"

            # Python class names cannot start with a digit - prefix with "Agent" if needed
            if class_name[0].isdigit():
                class_name = f"Agent{class_name}"

            # Find next nodes from edges
            next_nodes = []
            for edge in edges:
                if edge.get("source") == node_id:
                    target = edge.get("target", "")
                    # Check if target is an end node
                    target_node = next((n for n in nodes if n.get("id") == target), None)
                    if target_node and target_node.get("type") == "end":
                        next_nodes.append("END")
                    else:
                        next_nodes.append(target)

            if not next_nodes:
                next_nodes = ["END"]

            workflow_nodes.append(
                {
                    "id": node_id,
                    "handler": f"agents.{sanitized_id}.{class_name}.process_{sanitized_node_id}",
                    "description": node_data.get("label", node_type),
                    "next": next_nodes,
                }
            )

        # Find entry point (first node or entry point type)
        entry_point = "START"
        for node in nodes:
            if node.get("type") == "entryPoint":
                # Find first connected node
                for edge in edges:
                    if edge.get("source") == node.get("id"):
                        entry_point = edge.get("target", "START")
                        break
                break

        # Build YAML content in correct schema format
        yaml_content = f"""apiVersion: engineering-dept/v1
kind: Agent

metadata:
  id: {agent_id}
  name: {agent_name}
  version: "1.0.0"
  description: "{description}"
  tags: [{", ".join(tags)}]
  created: "{now}"
  updated: "{now}"

spec:
  capabilities:
    - reasoning
    - conversation
    - task_execution

  parameters: []

  workflow:
    type: langgraph.StateGraph
    entry_point: {entry_point}
    recursion_limit: 100
    nodes:
{
            chr(10).join(
                f'''      - id: {n['id']}
        handler: {n['handler']}
        description: "{n['description']}"
        next: [{', '.join(n['next'])}]
        timeout_seconds: 30'''
                for n in workflow_nodes
            )
        }

  integrations: []

  resource_limits:
    max_concurrent_tasks: 3
    timeout_seconds: 300
    memory_mb: 512
    max_tokens_per_request: 4000

  observability:
    trace_level: info
    metrics_enabled: true
    metrics_interval_seconds: 30
    log_retention_days: 30
    structured_logging: true

  health_check:
    enabled: true
    interval_seconds: 60
    timeout_seconds: 5
    unhealthy_threshold: 3

status:
  phase: alpha
  state: active
  last_heartbeat: null
  uptime_seconds: 0
  total_executions: 0
  success_rate: 0.0
  avg_latency_ms: 0.0
  error_message: null
"""
        return yaml_content

    async def _trigger_hot_reload(self, agent_id: str):
        """
        Trigger Marshal agent hot-reload.

        In production, this would call the Marshal API.
        For now, we rely on Marshal's file watcher to pick up changes.
        """
        logger.info(f"🔄 Triggering hot-reload for {agent_id}")

        # Option 1: Marshal file watcher (automatic)
        # - Just saving the file triggers reload

        # Option 2: Explicit reload API call (if needed)
        # try:
        #     async with httpx.AsyncClient() as client:
        #         response = await client.post(
        #             f"http://localhost:8000/api/agents/{agent_id}/reload"
        #         )
        #         logger.info(f"Reload API response: {response.status_code}")
        # except Exception as e:
        #     logger.warning(f"Could not trigger reload API: {e}")

        logger.info("✅ Hot-reload triggered (file watcher will pick up changes)")


# Singleton instance
agent_deployer = AgentDeployer()
