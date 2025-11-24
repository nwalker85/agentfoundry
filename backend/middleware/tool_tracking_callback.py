"""
LangGraph Tool Tracking Callback Handler
Intercepts tool calls and broadcasts them as activity events for real-time monitoring.
Also persists tool invocations to the database for historical analytics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from langchain_core.agents import AgentAction
from langchain_core.callbacks import AsyncCallbackHandler

logger = logging.getLogger(__name__)


class ToolTrackingCallback(AsyncCallbackHandler):
    """
    Async callback handler that tracks tool executions and broadcasts activity events.
    Also persists tool invocations to the tool_invocations table.
    """

    def __init__(self, session_id: str, agent_id: str, agent_name: str, persist_to_db: bool = True):
        super().__init__()
        self.session_id = session_id
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.persist_to_db = persist_to_db
        self.tool_start_times: dict[str, float] = {}
        self.tool_invocation_ids: dict[str, str] = {}  # run_id -> invocation_id
        self.tool_inputs: dict[str, str] = {}  # run_id -> input

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool starts executing"""
        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        tool_name = serialized.get("name", "unknown_tool")
        run_id_str = str(run_id)
        self.tool_start_times[run_id_str] = time.time()
        self.tool_inputs[run_id_str] = input_str

        # Generate invocation ID for database tracking
        invocation_id = str(uuid4())
        self.tool_invocation_ids[run_id_str] = invocation_id

        logger.info(f"🔧 Tool started: {tool_name}")

        # Broadcast activity
        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="tool_call",
                timestamp=time.time(),
                message=f"Calling tool: {tool_name}",
                metadata={
                    "tool": tool_name,
                    "input": input_str[:500],  # Truncate long inputs
                    "status": "started",
                    "run_id": run_id_str,
                    "invocation_id": invocation_id,
                },
            ),
        )

        # Persist to database (fire-and-forget)
        if self.persist_to_db:
            asyncio.create_task(
                self._persist_tool_start(
                    invocation_id=invocation_id, tool_name=tool_name, input_str=input_str, metadata=metadata
                )
            )

    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool finishes executing"""
        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        run_id_str = str(run_id)

        # Calculate duration
        duration = None
        duration_ms = None
        if run_id_str in self.tool_start_times:
            duration = time.time() - self.tool_start_times[run_id_str]
            duration_ms = int(duration * 1000)
            del self.tool_start_times[run_id_str]

        # Get invocation ID
        invocation_id = self.tool_invocation_ids.pop(run_id_str, None)

        # Clean up stored input
        self.tool_inputs.pop(run_id_str, None)

        # Extract tool name from kwargs or use generic name
        tool_name = kwargs.get("name", "tool")

        logger.info(
            f"✅ Tool completed: {tool_name} (duration: {duration:.2f}s)"
            if duration
            else f"✅ Tool completed: {tool_name}"
        )

        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="tool_call",
                timestamp=time.time(),
                message=f"Tool {tool_name} completed",
                metadata={
                    "tool": tool_name,
                    "output": output[:500] if output else None,  # Truncate long outputs
                    "status": "completed",
                    "duration": duration,
                    "run_id": run_id_str,
                    "invocation_id": invocation_id,
                },
            ),
        )

        # Persist completion to database
        if self.persist_to_db and invocation_id:
            asyncio.create_task(
                self._persist_tool_end(
                    invocation_id=invocation_id, output=output, duration_ms=duration_ms, status="success"
                )
            )

    async def on_tool_error(
        self,
        error: Exception,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when a tool execution fails"""
        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        run_id_str = str(run_id)

        # Calculate duration
        duration = None
        duration_ms = None
        if run_id_str in self.tool_start_times:
            duration = time.time() - self.tool_start_times[run_id_str]
            duration_ms = int(duration * 1000)
            del self.tool_start_times[run_id_str]

        # Get invocation ID
        invocation_id = self.tool_invocation_ids.pop(run_id_str, None)

        # Clean up stored input
        self.tool_inputs.pop(run_id_str, None)

        tool_name = kwargs.get("name", "tool")

        logger.error(f"❌ Tool failed: {tool_name} - {error!s}")

        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="error",
                timestamp=time.time(),
                message=f"Tool {tool_name} failed: {str(error)[:200]}",
                metadata={
                    "tool": tool_name,
                    "error": str(error),
                    "status": "failed",
                    "duration": duration,
                    "run_id": run_id_str,
                    "invocation_id": invocation_id,
                },
            ),
        )

        # Persist error to database
        if self.persist_to_db and invocation_id:
            asyncio.create_task(
                self._persist_tool_end(
                    invocation_id=invocation_id,
                    output=None,
                    duration_ms=duration_ms,
                    status="failed",
                    error_message=str(error),
                )
            )

    async def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when an agent decides to take an action"""
        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        logger.info(f"🤔 Agent action: {action.tool}")

        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message=f"Planning to use tool: {action.tool}",
                metadata={
                    "tool": action.tool,
                    "tool_input": str(action.tool_input)[:500],
                    "log": action.log[:200] if action.log else None,
                },
            ),
        )

    # =========================================================================
    # Database Persistence Methods
    # =========================================================================

    async def _persist_tool_start(
        self, invocation_id: str, tool_name: str, input_str: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Persist tool invocation start to database"""
        try:
            from backend.db import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO tool_invocations (
                    id, agent_id, function_id, session_id,
                    input, status, started_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    invocation_id,
                    self.agent_id,
                    tool_name,  # Using tool_name as function_id for now
                    self.session_id,
                    json.dumps({"raw": input_str[:10000]}),  # Store input as JSON
                    "running",
                    datetime.utcnow().isoformat(),
                    json.dumps(metadata or {}),
                ),
            )

            conn.commit()
            logger.debug(f"Persisted tool start: {invocation_id}")

        except Exception as e:
            logger.warning(f"Failed to persist tool start: {e}")

    async def _persist_tool_end(
        self,
        invocation_id: str,
        output: str | None,
        duration_ms: int | None,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Persist tool invocation completion to database"""
        try:
            from backend.db import get_db_connection

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE tool_invocations
                SET output = ?,
                    status = ?,
                    completed_at = ?,
                    duration_ms = ?,
                    error_message = ?
                WHERE id = ?
            """,
                (
                    json.dumps({"raw": output[:10000] if output else None}),
                    status,
                    datetime.utcnow().isoformat(),
                    duration_ms,
                    error_message,
                    invocation_id,
                ),
            )

            conn.commit()
            logger.debug(f"Persisted tool end: {invocation_id} ({status})")

        except Exception as e:
            logger.warning(f"Failed to persist tool end: {e}")
