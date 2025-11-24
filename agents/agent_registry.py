"""
Agent Registry - Central registry for all loaded agents

Maintains in-memory registry of agent instances with optional Redis persistence.
Thread-safe with async support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .yaml_validator import AgentStatus, AgentYAML

logger = logging.getLogger(__name__)


@dataclass
class AgentInstance:
    """Wrapper for a loaded agent instance.

    Holds both the configuration and runtime graph.
    """

    config: AgentYAML
    graph: Any  # CompiledStateGraph from LangGraph
    loaded_at: datetime = field(default_factory=datetime.now)
    last_invoked: datetime | None = None
    invocation_count: int = 0
    error_count: int = 0

    @property
    def metadata(self):
        """Convenience accessor for metadata."""
        return self.config.metadata

    @property
    def status(self):
        """Convenience accessor for status."""
        return self.config.status

    async def invoke(self, input_data: dict) -> dict:
        """Invoke the agent graph.

        Args:
            input_data: Input state for the graph

        Returns:
            Output state from the graph

        Raises:
            Exception: If invocation fails
        """
        try:
            self.last_invoked = datetime.now()
            self.invocation_count += 1

            # Invoke the compiled graph
            result = await self.graph.ainvoke(input_data)

            # Update success metrics
            self._update_success_metrics()

            return result

        except Exception as e:
            self.error_count += 1
            self._update_error_metrics()
            logger.error(f"Agent {self.metadata.id} invocation failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Run health check on this agent.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple ping - just check if graph is available
            if self.graph is None:
                return False

            # Could add more sophisticated checks here
            # For now, just verify graph is compiled
            return True

        except Exception as e:
            logger.error(f"Health check failed for {self.metadata.id}: {e}")
            return False

    def _update_success_metrics(self):
        """Update success rate and latency metrics."""
        if self.last_invoked:
            # Calculate success rate
            total = self.invocation_count
            successes = total - self.error_count
            self.status.success_rate = successes / total if total > 0 else 0.0

            # Update uptime
            uptime = (datetime.now() - self.loaded_at).total_seconds()
            self.status.uptime_seconds = int(uptime)

            # Update execution count
            self.status.total_executions = total

    def _update_error_metrics(self):
        """Update error metrics."""
        self._update_success_metrics()  # Recalculate success rate


class AgentRegistry:
    """
    Central registry for all agents.

    Stores:
    - In-memory: Dict[agent_id, AgentInstance]
    - Redis (future): Persistent metadata

    Thread-safe with asyncio locks.
    """

    def __init__(self):
        self._agents: dict[str, AgentInstance] = {}
        self._lock = asyncio.Lock()
        self._redis = None  # TODO: Add Redis connection
        logger.info("AgentRegistry initialized")

    async def register(self, agent_id: str, instance: AgentInstance) -> None:
        """Register a new agent.

        Args:
            agent_id: Unique agent identifier
            instance: AgentInstance to register
        """
        async with self._lock:
            if agent_id in self._agents:
                logger.warning(f"Overwriting existing agent: {agent_id}")

            self._agents[agent_id] = instance
            instance.status.state = "active"
            instance.status.last_heartbeat = datetime.now().isoformat()

            logger.info(f"Registered agent: {agent_id} (v{instance.metadata.version})")

            # TODO: Persist to Redis

    async def unregister(self, agent_id: str) -> bool:
        """Unregister an agent.

        Args:
            agent_id: Agent to unregister

        Returns:
            True if agent was unregistered, False if not found
        """
        async with self._lock:
            if agent_id in self._agents:
                instance = self._agents[agent_id]
                instance.status.state = "inactive"

                del self._agents[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")

                # TODO: Remove from Redis
                return True

            logger.warning(f"Attempted to unregister unknown agent: {agent_id}")
            return False

    async def get(self, agent_id: str) -> AgentInstance | None:
        """Get agent by ID.

        Args:
            agent_id: Agent to retrieve

        Returns:
            AgentInstance if found, None otherwise
        """
        async with self._lock:
            return self._agents.get(agent_id)

    async def exists(self, agent_id: str) -> bool:
        """Check if agent exists in registry.

        Args:
            agent_id: Agent to check

        Returns:
            True if agent exists, False otherwise
        """
        async with self._lock:
            return agent_id in self._agents

    async def list_all(self) -> dict[str, AgentInstance]:
        """List all registered agents.

        Returns:
            Copy of agents dictionary
        """
        async with self._lock:
            return self._agents.copy()

    async def list_ids(self) -> list[str]:
        """List all agent IDs.

        Returns:
            List of agent IDs
        """
        async with self._lock:
            return list(self._agents.keys())

    async def reload(self, agent_id: str, new_instance: AgentInstance) -> None:
        """Hot-reload an agent.

        Gracefully replaces existing agent with new instance.

        Args:
            agent_id: Agent to reload
            new_instance: New AgentInstance
        """
        async with self._lock:
            old_instance = self._agents.get(agent_id)

            if old_instance:
                # Preserve metrics from old instance
                new_instance.invocation_count = old_instance.invocation_count
                new_instance.error_count = old_instance.error_count
                new_instance.loaded_at = old_instance.loaded_at

                logger.info(
                    f"Reloading agent {agent_id}: {old_instance.metadata.version} → {new_instance.metadata.version}"
                )

            # Register new instance
            self._agents[agent_id] = new_instance
            new_instance.status.state = "active"
            new_instance.status.last_heartbeat = datetime.now().isoformat()

            logger.info(f"Reloaded agent: {agent_id}")

    async def update_status(self, agent_id: str, status: AgentStatus) -> bool:
        """Update agent status.

        Args:
            agent_id: Agent to update
            status: New status

        Returns:
            True if updated, False if agent not found
        """
        async with self._lock:
            instance = self._agents.get(agent_id)
            if instance:
                instance.config.status = status
                return True
            return False

    async def count(self) -> int:
        """Get count of registered agents.

        Returns:
            Number of registered agents
        """
        async with self._lock:
            return len(self._agents)

    async def get_healthy_count(self) -> int:
        """Get count of healthy (active) agents.

        Returns:
            Number of agents in 'active' state
        """
        async with self._lock:
            return sum(1 for instance in self._agents.values() if instance.status.state == "active")

    async def clear(self) -> None:
        """Clear all agents (for testing)."""
        async with self._lock:
            self._agents.clear()
            logger.warning("All agents cleared from registry")
