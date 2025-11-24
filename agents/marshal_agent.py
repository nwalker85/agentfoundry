"""
Marshal Agent - Meta-agent that manages the agent registry

Responsibilities:
- Load agents from YAML files at startup
- Monitor agent directory for file changes (hot-reload)
- Validate agent configurations
- Maintain agent registry
- Run health checks
- Report status to admin endpoints

Architecture:
    ┌─────────────────┐
    │ MarshalAgent    │
    ├─────────────────┤
    │ File Watcher ───┼──> YAML changes
    │ Agent Loader ───┼──> Create instances
    │ Registry     ───┼──> Store agents
    │ Health Monitor ─┼──> Check health
    └─────────────────┘
"""

import asyncio
import logging
from pathlib import Path

from pydantic import ValidationError

from .agent_loader import AgentLoader
from .agent_registry import AgentRegistry
from .file_watcher import AgentFileWatcher, FileChangeType
from .health_monitor import HealthMonitor
from .yaml_validator import AgentYAML, ValidationResult

logger = logging.getLogger(__name__)


class MarshalAgent:
    """
    Meta-agent that orchestrates agent lifecycle.

    Features:
    - Auto-load agents from YAML files
    - Hot-reload on file changes
    - Health monitoring
    - Validation reporting
    - Admin API integration

    Usage:
        marshal = MarshalAgent(agents_dir="/path/to/agents")
        await marshal.start()

        # Marshal runs in background, managing agents
        # Access agents via marshal.registry

        await marshal.stop()
    """

    def __init__(
        self,
        agents_dir: str | Path,
        enable_file_watcher: bool = True,
        enable_health_monitor: bool = True,
        health_check_interval: int = 60,
    ):
        """Initialize Marshal Agent.

        Args:
            agents_dir: Directory containing .agent.yaml files
            enable_file_watcher: Enable hot-reload on file changes
            enable_health_monitor: Enable periodic health checks
            health_check_interval: Seconds between health checks
        """
        self.agents_dir = Path(agents_dir)
        self.enable_file_watcher = enable_file_watcher
        self.enable_health_monitor = enable_health_monitor

        # Initialize components
        self.registry = AgentRegistry()
        self.loader = AgentLoader()
        self.health_monitor = HealthMonitor(registry=self.registry, check_interval_seconds=health_check_interval)

        # File watcher (initialized later)
        self.file_watcher: AgentFileWatcher | None = None

        # Background tasks
        self._tasks: list[asyncio.Task] = []
        self._running = False

        # Validation results cache
        self._validation_errors: dict[str, ValidationResult] = {}

        logger.info(
            f"MarshalAgent initialized for directory: {self.agents_dir} "
            f"(watcher={enable_file_watcher}, health={enable_health_monitor})"
        )

    async def start(self):
        """Start Marshal Agent.

        Steps:
        1. Load all existing agents
        2. Start file watcher (if enabled)
        3. Start health monitor (if enabled)
        """
        logger.info("🚀 Starting Marshal Agent...")
        self._running = True

        try:
            # Load existing agents
            await self._load_all_agents()

            # Start file watcher
            if self.enable_file_watcher:
                self.file_watcher = AgentFileWatcher(watch_path=self.agents_dir, on_change=self._handle_file_change)

                watcher_task = asyncio.create_task(self.file_watcher.start(), name="file-watcher")
                self._tasks.append(watcher_task)
                logger.info("✓ File watcher started")

            # Start health monitor
            if self.enable_health_monitor:
                monitor_task = asyncio.create_task(self.health_monitor.start(), name="health-monitor")
                self._tasks.append(monitor_task)

                # Give task time to start
                await asyncio.sleep(0.01)

                logger.info("✓ Health monitor started")

            logger.info(f"✅ Marshal Agent started successfully ({await self.registry.count()} agents loaded)")

        except Exception as e:
            logger.error(f"Failed to start Marshal Agent: {e}", exc_info=True)
            await self.stop()
            raise

    async def stop(self):
        """Stop Marshal Agent.

        Gracefully shuts down all components.
        """
        logger.info("🛑 Stopping Marshal Agent...")
        self._running = False

        # Stop file watcher
        if self.file_watcher:
            await self.file_watcher.stop()

        # Stop health monitor
        if self.health_monitor:
            await self.health_monitor.stop()

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("✅ Marshal Agent stopped")

    async def _load_all_agents(self):
        """Load all agent YAML files from directory.

        Called at startup to initialize registry.
        """
        logger.info(f"Loading agents from: {self.agents_dir}")

        if not self.agents_dir.exists():
            logger.warning(f"Agents directory does not exist: {self.agents_dir}")
            return

        # Find all .agent.yaml files
        yaml_files = list(self.agents_dir.glob("*.agent.yaml"))
        logger.info(f"Found {len(yaml_files)} agent YAML files")

        # Load each agent
        loaded_count = 0
        for yaml_file in yaml_files:
            try:
                await self._load_agent_file(yaml_file)
                loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load {yaml_file.name}: {e}", exc_info=True)

        logger.info(f"Loaded {loaded_count}/{len(yaml_files)} agents successfully")

    async def _load_agent_file(self, yaml_path: Path):
        """Load a single agent YAML file.

        Args:
            yaml_path: Path to .agent.yaml file

        Raises:
            ValidationError: If YAML is invalid
            ImportError: If handler modules can't be imported
        """
        logger.info(f"Loading agent: {yaml_path.name}")

        # Extract agent ID from filename as fallback
        agent_id = yaml_path.stem.replace(".agent", "")

        # Clear any previous validation errors for this agent
        self._validation_errors.pop(agent_id, None)

        try:
            # Parse and validate YAML
            agent_config = AgentYAML.from_yaml_file(str(yaml_path))
            agent_id = agent_config.metadata.id  # Override with actual ID if valid

            logger.debug(f"Parsed YAML for {agent_id}")

            # Validate configuration
            validation_result = await self.loader.validate_yaml(agent_config)

            if not validation_result.valid:
                # Store validation errors
                self._validation_errors[agent_id] = validation_result

                error_msg = "; ".join(validation_result.errors)
                logger.error(f"❌ Validation failed for {agent_id}: {error_msg}")
                raise ValueError(f"Validation failed: {error_msg}")

            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"⚠️  {agent_id}: {warning}")

            # Load agent instance
            instance = await self.loader.load_agent(agent_config)

            # Register agent
            await self.registry.register(agent_id, instance)

            logger.info(
                f"✅ Loaded {agent_id} v{agent_config.metadata.version} ({len(agent_config.spec.workflow.nodes)} nodes)"
            )

        except ValidationError as e:
            # Store Pydantic validation errors
            result = ValidationResult(valid=False, agent_id=agent_id)
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                result.add_error(f"{field}: {error['msg']}")

            self._validation_errors[agent_id] = result

            logger.error(f"Failed to load {yaml_path.name}: {len(result.errors)} validation error(s)")
            raise

        except Exception as e:
            logger.error(f"Failed to load {yaml_path.name}: {e}")
            raise

    async def _handle_file_change(self, change_type: FileChangeType, file_path: Path):
        """Handle file system change event.

        Args:
            change_type: Type of change (added/modified/deleted)
            file_path: Path to changed file
        """
        logger.info(f"File {change_type.value}: {file_path.name}")

        try:
            if change_type == FileChangeType.ADDED:
                await self._handle_agent_added(file_path)

            elif change_type == FileChangeType.MODIFIED:
                await self._handle_agent_modified(file_path)

            elif change_type == FileChangeType.DELETED:
                await self._handle_agent_deleted(file_path)

        except Exception as e:
            logger.error(f"Error handling {change_type.value} for {file_path.name}: {e}", exc_info=True)

    async def _handle_agent_added(self, file_path: Path):
        """Handle new agent file.

        Args:
            file_path: Path to new YAML file
        """
        logger.info(f"Loading new agent: {file_path.name}")
        await self._load_agent_file(file_path)

    async def _handle_agent_modified(self, file_path: Path):
        """Handle modified agent file (hot-reload).

        Args:
            file_path: Path to modified YAML file
        """
        logger.info(f"Reloading modified agent: {file_path.name}")

        # Extract agent ID from filename as fallback
        agent_id = file_path.stem.replace(".agent", "")

        # Clear any previous validation errors for this agent
        self._validation_errors.pop(agent_id, None)

        try:
            # Load new version
            agent_config = AgentYAML.from_yaml_file(str(file_path))
            agent_id = agent_config.metadata.id  # Override with actual ID if valid

            # Validate
            validation_result = await self.loader.validate_yaml(agent_config)

            if not validation_result.valid:
                self._validation_errors[agent_id] = validation_result
                error_msg = "; ".join(validation_result.errors)
                logger.error(f"❌ Reload validation failed for {agent_id}: {error_msg}")
                return

            # Load new instance
            new_instance = await self.loader.load_agent(agent_config)

            # Hot-reload in registry
            await self.registry.reload(agent_id, new_instance)

            logger.info(f"🔄 Reloaded {agent_id} v{agent_config.metadata.version}")

        except ValidationError as e:
            # Store Pydantic validation errors
            result = ValidationResult(valid=False, agent_id=agent_id)
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                result.add_error(f"{field}: {error['msg']}")

            self._validation_errors[agent_id] = result

            logger.error(f"Failed to reload {file_path.name}: {len(result.errors)} validation error(s)")

        except Exception as e:
            logger.error(f"Failed to reload {file_path.name}: {e}", exc_info=True)

    async def _handle_agent_deleted(self, file_path: Path):
        """Handle deleted agent file.

        Args:
            file_path: Path to deleted YAML file
        """
        # Extract agent ID from filename
        # Assumes format: {agent-id}.agent.yaml
        agent_id = file_path.stem.replace(".agent", "")

        logger.info(f"Unloading deleted agent: {agent_id}")

        success = await self.registry.unregister(agent_id)

        if success:
            logger.info(f"🗑️  Unloaded {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} was not in registry")

        # Clear validation errors
        self._validation_errors.pop(agent_id, None)

    async def reload_agent(self, agent_id: str) -> bool:
        """Manually reload a specific agent.

        Args:
            agent_id: Agent to reload

        Returns:
            True if reloaded successfully, False otherwise
        """
        logger.info(f"Manual reload requested for: {agent_id}")

        # Find YAML file
        yaml_file = self.agents_dir / f"{agent_id}.agent.yaml"

        if not yaml_file.exists():
            logger.error(f"YAML file not found for {agent_id}")
            return False

        try:
            await self._handle_agent_modified(yaml_file)
            return True
        except Exception as e:
            logger.error(f"Failed to reload {agent_id}: {e}")
            return False

    async def validate_agent(self, agent_id: str) -> ValidationResult:
        """Validate a specific agent without loading it.

        Args:
            agent_id: Agent to validate

        Returns:
            ValidationResult
        """
        yaml_file = self.agents_dir / f"{agent_id}.agent.yaml"

        if not yaml_file.exists():
            result = ValidationResult(valid=False, agent_id=agent_id)
            result.add_error(f"YAML file not found: {yaml_file}")
            return result

        try:
            agent_config = AgentYAML.from_yaml_file(str(yaml_file))
            return await self.loader.validate_yaml(agent_config)
        except Exception as e:
            result = ValidationResult(valid=False, agent_id=agent_id)
            result.add_error(f"Failed to parse YAML: {e}")
            return result

    def get_validation_errors(self) -> dict[str, ValidationResult]:
        """Get all validation errors.

        Returns:
            Dictionary of agent_id -> ValidationResult
        """
        return self._validation_errors.copy()

    async def get_status_summary(self) -> dict:
        """Get complete status summary for all agents.

        Returns:
            Dictionary with agent counts, health, and metrics
        """
        total_agents = await self.registry.count()
        healthy_agents = await self.registry.get_healthy_count()

        health_summary = self.health_monitor.get_health_summary()

        agent_list = []
        for agent_id, instance in (await self.registry.list_all()).items():
            agent_list.append(
                {
                    "id": agent_id,
                    "name": instance.metadata.name,
                    "version": instance.metadata.version,
                    "state": instance.status.state,
                    "phase": instance.status.phase,
                    "uptime_seconds": instance.status.uptime_seconds,
                    "total_executions": instance.status.total_executions,
                    "success_rate": instance.status.success_rate,
                }
            )

        return {
            "marshal": {
                "running": self._running,
                "file_watcher_enabled": self.enable_file_watcher,
                "health_monitor_enabled": self.enable_health_monitor,
                "agents_dir": str(self.agents_dir),
            },
            "agents": {
                "total": total_agents,
                "healthy": healthy_agents,
                "unhealthy": total_agents - healthy_agents,
                "list": agent_list,
            },
            "health": health_summary,
            "validation_errors": len(self._validation_errors),
        }

    @property
    def is_running(self) -> bool:
        """Check if Marshal is running."""
        return self._running
