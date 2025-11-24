"""
Agent Loader - Dynamically creates agent instances from YAML definitions

Handles:
- Dynamic module imports
- LangGraph StateGraph construction
- Agent instance creation
- Error handling for malformed configs
"""

import importlib
import logging
from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .agent_registry import AgentInstance
from .state import AgentState
from .yaml_validator import AgentYAML, ValidationResult

logger = logging.getLogger(__name__)


class AgentLoader:
    """
    Loads agents from validated YAML configurations.

    Creates LangGraph StateGraph instances with nodes
    defined in the YAML workflow specification.
    """

    def __init__(self):
        """Initialize agent loader."""
        self._handler_cache: dict[str, Callable] = {}
        logger.info("AgentLoader initialized")

    async def load_agent(self, yaml_config: AgentYAML) -> AgentInstance:
        """
        Create agent instance from YAML config.

        Steps:
        1. Validate YAML (already done by Pydantic)
        2. Import handler functions
        3. Build LangGraph StateGraph
        4. Return AgentInstance wrapper

        Args:
            yaml_config: Validated AgentYAML configuration

        Returns:
            AgentInstance ready for execution

        Raises:
            ImportError: If handler modules can't be imported
            ValueError: If graph construction fails
        """
        agent_id = yaml_config.metadata.id
        logger.info(f"Loading agent: {agent_id}")

        try:
            # Build workflow graph
            graph = await self._build_graph(yaml_config)

            # Create instance wrapper
            instance = AgentInstance(config=yaml_config, graph=graph)

            logger.info(f"Successfully loaded agent {agent_id} with {len(yaml_config.spec.workflow.nodes)} nodes")

            return instance

        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}", exc_info=True)
            raise

    async def _build_graph(self, yaml_config: AgentYAML) -> Any:
        """
        Build LangGraph StateGraph from workflow configuration.

        Args:
            yaml_config: Agent configuration

        Returns:
            Compiled StateGraph
        """
        workflow_config = yaml_config.spec.workflow

        # Create StateGraph with AgentState
        graph = StateGraph(AgentState)

        # Add nodes
        for node_config in workflow_config.nodes:
            handler = await self._import_handler(node_config.handler)
            graph.add_node(node_config.id, handler)
            logger.debug(f"Added node: {node_config.id}")

        # Add edges
        for node_config in workflow_config.nodes:
            for next_node in node_config.next:
                if next_node == "END":
                    graph.add_edge(node_config.id, END)
                    logger.debug(f"Added edge: {node_config.id} → END")
                else:
                    graph.add_edge(node_config.id, next_node)
                    logger.debug(f"Added edge: {node_config.id} → {next_node}")

        # Set entry point
        graph.set_entry_point(workflow_config.entry_point)
        logger.debug(f"Entry point: {workflow_config.entry_point}")

        # Set up checkpointer for interrupt/resume support
        # Using MemorySaver for now (in-memory, doesn't persist across restarts)
        checkpointer = MemorySaver()

        # Compile graph with checkpointer
        compiled_graph = graph.compile(checkpointer=checkpointer)

        logger.info(
            f"Compiled graph for {yaml_config.metadata.id} with checkpointer "
            f"(recursion_limit={workflow_config.recursion_limit})"
        )

        return compiled_graph

    async def _import_handler(self, handler_path: str) -> Callable:
        """
        Import handler function from module path.

        Handler path format: "module.path.ClassName.method_name"
        Example: "agents.workers.pm_agent.PMAgent.process"

        Args:
            handler_path: Dotted path to handler

        Returns:
            Callable handler function

        Raises:
            ImportError: If module or class not found
            AttributeError: If method doesn't exist
        """
        # Check cache first
        if handler_path in self._handler_cache:
            logger.debug(f"Using cached handler: {handler_path}")
            return self._handler_cache[handler_path]

        logger.debug(f"Importing handler: {handler_path}")

        try:
            # Split into module.path, ClassName, method_name
            parts = handler_path.rsplit(".", 2)
            if len(parts) != 3:
                raise ValueError(f"Handler path must be module.Class.method, got: {handler_path}")

            module_path, class_name, method_name = parts

            # Import module
            module = importlib.import_module(module_path)
            logger.debug(f"Imported module: {module_path}")

            # Get class
            cls = getattr(module, class_name)
            logger.debug(f"Found class: {class_name}")

            # Instantiate class
            instance = cls()
            logger.debug(f"Instantiated: {class_name}")

            # Get method
            handler = getattr(instance, method_name)
            logger.debug(f"Got method: {method_name}")

            # Cache for future use
            self._handler_cache[handler_path] = handler

            return handler

        except Exception as e:
            logger.error(f"Failed to import handler {handler_path}: {e}")
            raise ImportError(f"Could not import handler '{handler_path}': {e}") from e

    async def validate_yaml(self, yaml_config: AgentYAML) -> ValidationResult:
        """
        Validate agent YAML without actually loading it.

        Performs:
        - Schema validation (already done by Pydantic)
        - Handler import checks
        - Graph construction validation

        Args:
            yaml_config: Configuration to validate

        Returns:
            ValidationResult with errors/warnings
        """
        result = ValidationResult(valid=True, agent_id=yaml_config.metadata.id)

        try:
            # Check all handlers can be imported
            for node_config in yaml_config.spec.workflow.nodes:
                try:
                    await self._import_handler(node_config.handler)
                except Exception as e:
                    result.add_error(f"Node '{node_config.id}' handler import failed: {e}")

            # Validate graph structure (already done by Pydantic, but double-check)
            node_ids = {node.id for node in yaml_config.spec.workflow.nodes}
            entry_point = yaml_config.spec.workflow.entry_point

            if entry_point not in node_ids:
                result.add_error(f"Entry point '{entry_point}' not in nodes")

            # Check for unreachable nodes
            reachable = set()
            to_visit = [entry_point]

            while to_visit:
                current = to_visit.pop()
                if current in reachable or current == "END":
                    continue
                reachable.add(current)

                # Find this node's next nodes
                for node_config in yaml_config.spec.workflow.nodes:
                    if node_config.id == current:
                        to_visit.extend(node_config.next)

            unreachable = node_ids - reachable
            if unreachable:
                result.add_warning(f"Unreachable nodes: {unreachable}")

            # Check for nodes with no outgoing edges (except if they point to END)
            for node_config in yaml_config.spec.workflow.nodes:
                if not node_config.next:
                    result.add_warning(f"Node '{node_config.id}' has no outgoing edges (will hang if reached)")

        except Exception as e:
            result.add_error(f"Validation failed: {e}")

        return result

    def clear_cache(self) -> None:
        """Clear handler import cache (useful for testing)."""
        self._handler_cache.clear()
        logger.info("Handler cache cleared")
