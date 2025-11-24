"""
Deep Agent Middleware Wrappers

Provides middleware components for deep agent workflows:
- TodoList: Task planning and decomposition
- Filesystem: File operations with auto-offloading
- SubAgent: Hierarchical agent delegation
- Summarization: Context management for large outputs
- Prompt Caching: Anthropic prompt caching for efficiency

Install dependencies:
    pip install deepagents tavily-python
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)


class TodoListMiddleware:
    """
    Middleware for task planning and decomposition.

    Provides write_todos and read_todos tools for breaking down
    complex requests into executable subtasks.
    """

    def __init__(self):
        self.todos: list[dict[str, Any]] = []

    def write_todos(self, tasks: list[dict[str, str]]) -> str:
        """
        Write a list of todos for task planning.

        Args:
            tasks: List of task dicts with 'id', 'description', 'status'

        Returns:
            Confirmation message
        """
        self.todos = tasks
        return f"Created {len(tasks)} todos"

    def read_todos(self) -> list[dict[str, Any]]:
        """Read current todo list"""
        return self.todos

    def discover_cibc_tools(self, category: str | None = None, agent_group: str | None = None) -> list[dict[str, Any]]:
        """
        Discover available CIBC tools from function catalog.

        Args:
            category: Filter by category (card_lifecycle, security_fraud, etc.)
            agent_group: Filter by agent group (group_1_card_lifecycle, etc.)

        Returns:
            List of tool definitions with name, description, input_schema
        """
        try:
            import json

            from db import get_connection

            conn = get_connection()
            cur = conn.cursor()

            # Build query with filters
            query = """
                SELECT id, name, display_name, description, category,
                       input_schema, output_schema, tags, metadata
                FROM function_catalog
                WHERE id LIKE 'cibc-%' AND is_active = 1
            """
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if agent_group:
                query += " AND json_extract(metadata, '$.agent_group') = ?"
                params.append(agent_group)

            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            tools = []
            for row in rows:
                tools.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "display_name": row["display_name"],
                        "description": row["description"],
                        "category": row["category"],
                        "input_schema": json.loads(row["input_schema"]) if row["input_schema"] else {},
                        "output_schema": json.loads(row["output_schema"]) if row["output_schema"] else {},
                        "tags": json.loads(row["tags"]) if row["tags"] else [],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    }
                )

            logger.info(f"Discovered {len(tools)} CIBC tools (category={category}, agent_group={agent_group})")
            return tools

        except Exception as e:
            logger.error(f"Error discovering CIBC tools: {e}", exc_info=True)
            return []

    def discover_cibc_agents(self, agent_group: str | None = None) -> list[dict[str, Any]]:
        """
        Discover available CIBC agent workflows from agents table.

        Args:
            agent_group: Filter by tags (e.g., "agent-group-1")

        Returns:
            List of agent definitions with id, name, description
        """
        try:
            import json

            from db import get_connection

            conn = get_connection()
            cur = conn.cursor()

            # Query CIBC agents
            query = """
                SELECT id, name, display_name, description, type, status,
                       organization_id, domain_id, tags
                FROM agents
                WHERE organization_id = 'cibc'
                  AND domain_id = 'card-services'
                  AND status = 'active'
            """
            params = []

            # Note: tags filter would require JSON array search
            # For now, return all and filter in Python if needed

            cur.execute(query, params)
            rows = cur.fetchall()
            conn.close()

            agents = []
            for row in rows:
                tags = json.loads(row["tags"]) if row["tags"] else []

                # Filter by agent_group tag if specified
                if agent_group and agent_group not in tags:
                    continue

                agents.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "display_name": row["display_name"],
                        "description": row["description"],
                        "type": row["type"],
                        "status": row["status"],
                        "organization_id": row["organization_id"],
                        "domain_id": row["domain_id"],
                        "tags": tags,
                    }
                )

            logger.info(f"Discovered {len(agents)} CIBC agents (agent_group={agent_group})")
            return agents

        except Exception as e:
            logger.error(f"Error discovering CIBC agents: {e}", exc_info=True)
            return []

    def populate_tasks_from_catalog(
        self, user_request: str, tools: list[dict[str, Any]], agents: list[dict[str, Any]]
    ) -> str:
        """
        Analyze user request and create tasks using available tools/agents.

        Args:
            user_request: User's natural language request
            tools: Available CIBC tools from discover_cibc_tools()
            agents: Available CIBC agents from discover_cibc_agents()

        Returns:
            Confirmation message with task count
        """
        # This is a placeholder - actual implementation would use LLM
        # to intelligently match request to tools/agents
        # For now, just store the catalog for planning

        logger.info(f"Analyzing request with {len(tools)} tools and {len(agents)} agents")

        # Store catalog for planner to use
        catalog_summary = {
            "user_request": user_request,
            "available_tools": len(tools),
            "available_agents": len(agents),
            "tool_categories": list(set(t.get("category") for t in tools)),
            "agent_groups": list(
                set(tag for a in agents for tag in a.get("tags", []) if tag.startswith("agent-group-"))
            ),
        }

        logger.info(f"Catalog summary: {catalog_summary}")

        return f"Analyzed request with {len(tools)} tools and {len(agents)} agents available"

    def get_tools(self):
        """Get tools for LangGraph integration"""
        return [
            {
                "name": "write_todos",
                "description": "Create a list of subtasks to accomplish the goal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "description": {"type": "string"},
                                    "status": {"type": "string", "enum": ["pending", "in_progress", "complete"]},
                                },
                            },
                        }
                    },
                },
                "function": self.write_todos,
            },
            {
                "name": "read_todos",
                "description": "Read the current list of todos",
                "parameters": {"type": "object", "properties": {}},
                "function": self.read_todos,
            },
            {
                "name": "discover_cibc_tools",
                "description": "Discover available CIBC tools from function catalog by category or agent group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Filter by category (card_lifecycle, security_fraud, request_orchestration, session_verification, delivery_fulfillment)",
                        },
                        "agent_group": {
                            "type": "string",
                            "description": "Filter by agent group (group_1_card_lifecycle, group_2_security_fraud, etc.)",
                        },
                    },
                },
                "function": self.discover_cibc_tools,
            },
            {
                "name": "discover_cibc_agents",
                "description": "Discover available CIBC agent workflows from agents table",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_group": {
                            "type": "string",
                            "description": "Filter by agent group tag (agent-group-1, agent-group-2, etc.)",
                        }
                    },
                },
                "function": self.discover_cibc_agents,
            },
            {
                "name": "populate_tasks_from_catalog",
                "description": "Analyze user request and create tasks using available CIBC tools and agents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_request": {"type": "string"},
                        "tools": {"type": "array"},
                        "agents": {"type": "array"},
                    },
                },
                "function": self.populate_tasks_from_catalog,
            },
        ]


class FilesystemMiddleware:
    """
    Middleware for filesystem operations with context management.

    Provides tools for reading, writing, and searching files.
    Automatically offloads large outputs to reduce token usage.
    """

    def __init__(self, base_path: str = "./agent_workspace"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def ls(self, path: str = ".") -> str:
        """List directory contents"""
        full_path = os.path.join(self.base_path, path)
        try:
            items = os.listdir(full_path)
            return "\n".join(items)
        except Exception as e:
            return f"Error: {e!s}"

    def read_file(self, filepath: str) -> str:
        """Read file contents"""
        full_path = os.path.join(self.base_path, filepath)
        try:
            with open(full_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error: {e!s}"

    def write_file(self, filepath: str, content: str) -> str:
        """Write content to file"""
        full_path = os.path.join(self.base_path, filepath)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Wrote {len(content)} characters to {filepath}"
        except Exception as e:
            return f"Error: {e!s}"

    def edit_file(self, filepath: str, old_text: str, new_text: str) -> str:
        """Edit file by replacing text"""
        content = self.read_file(filepath)
        if "Error:" in content:
            return content

        if old_text not in content:
            return f"Error: Text not found in {filepath}"

        new_content = content.replace(old_text, new_text)
        return self.write_file(filepath, new_content)

    def glob(self, pattern: str) -> str:
        """Find files matching pattern"""
        import glob as glob_module

        full_pattern = os.path.join(self.base_path, pattern)
        matches = glob_module.glob(full_pattern, recursive=True)
        relative_matches = [os.path.relpath(m, self.base_path) for m in matches]
        return "\n".join(relative_matches)

    def grep(self, pattern: str, filepath: str = None) -> str:
        """Search for pattern in files"""
        import re

        if filepath:
            content = self.read_file(filepath)
            if "Error:" in content:
                return content
            matches = [line for line in content.split("\n") if re.search(pattern, line)]
            return "\n".join(matches)
        else:
            return "Error: filepath required"

    def get_tools(self):
        """Get tools for LangGraph integration"""
        return [
            {"name": "ls", "function": self.ls},
            {"name": "read_file", "function": self.read_file},
            {"name": "write_file", "function": self.write_file},
            {"name": "edit_file", "function": self.edit_file},
            {"name": "glob", "function": self.glob},
            {"name": "grep", "function": self.grep},
        ]


class SubAgentMiddleware:
    """
    Middleware for spawning and managing sub-agents.

    Enables hierarchical task delegation to specialized agents.
    """

    def __init__(self, parent_state: dict[str, Any]):
        self.parent_state = parent_state
        self.subagents: dict[str, Any] = {}

    def spawn_subagent(self, name: str, description: str, task: str, tools: list[str] | None = None) -> str:
        """
        Spawn a sub-agent to handle a specific task.

        Args:
            name: Sub-agent identifier
            description: What the sub-agent specializes in
            task: Specific task to delegate
            tools: Available tools for the sub-agent

        Returns:
            Sub-agent result or reference
        """
        logger.info(f"Spawning sub-agent: {name} for task: {task}")

        # Store sub-agent reference
        self.subagents[name] = {"description": description, "task": task, "tools": tools or [], "status": "pending"}

        return f"Sub-agent '{name}' spawned for: {task}"

    def get_subagent_result(self, name: str) -> dict[str, Any] | None:
        """Get result from a sub-agent"""
        return self.subagents.get(name)

    def get_tools(self):
        """Get tools for LangGraph integration"""
        return [
            {"name": "spawn_subagent", "function": self.spawn_subagent},
            {"name": "get_subagent_result", "function": self.get_subagent_result},
        ]


class SummarizationMiddleware:
    """
    Middleware for context management and summarization.

    Automatically offloads large outputs to files and provides summaries
    to stay within context windows.
    """

    def __init__(self, size_threshold: int = 170000):
        """
        Args:
            size_threshold: Character count threshold for offloading
        """
        self.size_threshold = size_threshold
        self.offloaded_content: dict[str, str] = {}

    def maybe_summarize(self, content: str, key: str) -> str:
        """
        Summarize content if it exceeds threshold.

        Args:
            content: Content to potentially summarize
            key: Identifier for the content

        Returns:
            Summary or original content
        """
        if len(content) > self.size_threshold:
            # Store full content
            self.offloaded_content[key] = content

            # Create summary (simple truncation for now)
            summary = content[:1000] + f"\n\n... (truncated, {len(content)} total chars, stored as '{key}')"
            return summary

        return content

    def retrieve_content(self, key: str) -> str | None:
        """Retrieve offloaded content by key"""
        return self.offloaded_content.get(key)


def create_deep_agent_config(
    model: str = "claude-sonnet-4-5-20250929",
    system_prompt: str | None = None,
    enable_todos: bool = True,
    enable_filesystem: bool = True,
    enable_subagents: bool = False,
    enable_summarization: bool = True,
    workspace_path: str = "./agent_workspace",
) -> dict[str, Any]:
    """
    Create a deep agent configuration with middleware stack.

    Args:
        model: LLM model to use
        system_prompt: System prompt for the agent
        enable_todos: Enable TodoList middleware
        enable_filesystem: Enable Filesystem middleware
        enable_subagents: Enable SubAgent middleware
        enable_summarization: Enable Summarization middleware
        workspace_path: Base path for filesystem operations

    Returns:
        Configuration dict for deep agent setup
    """
    middleware = []
    tools = []

    if enable_todos:
        todo_mw = TodoListMiddleware()
        middleware.append(todo_mw)
        tools.extend(todo_mw.get_tools())

    if enable_filesystem:
        fs_mw = FilesystemMiddleware(base_path=workspace_path)
        middleware.append(fs_mw)
        tools.extend(fs_mw.get_tools())

    if enable_subagents:
        # SubAgent middleware needs parent state at runtime
        pass  # Configured at execution time

    if enable_summarization:
        summ_mw = SummarizationMiddleware()
        middleware.append(summ_mw)

    return {
        "model": model,
        "system_prompt": system_prompt,
        "middleware": middleware,
        "tools": tools,
        "workspace_path": workspace_path,
    }
