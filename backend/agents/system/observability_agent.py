"""
Observability Agent - System Agent
Broadcasts agent activity to connected WebSocket clients for real-time monitoring
and persists activities to database via MCP tools.
"""

import asyncio
import logging
from dataclasses import asdict, dataclass
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class AgentActivity:
    """Represents a single agent activity event"""

    agent_id: str
    agent_name: str
    event_type: Literal[
        "started",
        "processing",
        "tool_call",
        "completed",
        "error",
        "interrupted",
        "resumed",
        "user_message",
        "agent_message",
    ]
    timestamp: float
    message: str
    metadata: dict | None = None


class ObservabilityAgent:
    """
    Broadcasts agent activity to connected WebSocket clients and persists to database.

    This agent provides two functions:
    1. Real-time WebSocket broadcasting for live UI updates
    2. Persistent storage via MCP tools for historical queries
    """

    def __init__(self):
        # Map: session_id -> list of WebSocket connections
        self.connections: dict[str, list] = {}
        # Flag to enable/disable persistence (can be toggled for testing)
        self.persistence_enabled = True

    async def register_connection(self, session_id: str, websocket):
        """Register a WebSocket connection for a session"""
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)
        logger.info(
            f"Registered WebSocket for session {session_id}. Total connections: {len(self.connections[session_id])}"
        )

    async def unregister_connection(self, session_id: str, websocket):
        """Remove a WebSocket connection"""
        if session_id in self.connections:
            try:
                self.connections[session_id].remove(websocket)
                logger.info(
                    f"Unregistered WebSocket for session {session_id}. Remaining: {len(self.connections[session_id])}"
                )
            except ValueError:
                pass  # Already removed
            if not self.connections[session_id]:
                del self.connections[session_id]
                logger.debug(f"Removed session {session_id} (no more connections)")

    async def broadcast_activity(self, session_id: str, activity: AgentActivity):
        """
        Broadcast agent activity to all clients and persist to database.

        This method:
        1. Persists the activity to the database (fire-and-forget, non-blocking)
        2. Broadcasts to WebSocket clients for real-time updates
        """
        # 1. Persist activity to database (non-blocking)
        if self.persistence_enabled:
            asyncio.create_task(self._persist_activity(session_id, activity))

        # 2. Broadcast to WebSocket clients
        if session_id not in self.connections:
            logger.debug(f"No connections for session {session_id}, skipping broadcast")
            return

        message = {"type": "agent_activity", **asdict(activity)}

        logger.debug(f"Broadcasting activity: {activity.agent_name} - {activity.event_type} - {activity.message[:50]}")

        # Broadcast to all connected clients for this session
        disconnected = []
        for ws in self.connections[session_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending to websocket: {e}")
                disconnected.append(ws)

        # Clean up disconnected websockets
        for ws in disconnected:
            await self.unregister_connection(session_id, ws)

    async def _persist_activity(self, session_id: str, activity: AgentActivity):
        """
        Persist activity to database via MCP tools.
        This is fire-and-forget - errors are logged but don't block broadcasting.
        """
        try:
            from mcp.tools.observability_tools import save_activity

            activity_id = save_activity(
                session_id=session_id,
                agent_id=activity.agent_id,
                agent_name=activity.agent_name,
                event_type=activity.event_type,
                timestamp=activity.timestamp,
                message=activity.message,
                metadata=activity.metadata,
            )
            logger.debug(f"Persisted activity {activity_id}")

        except ImportError:
            # MCP tools not available (e.g., in tests)
            logger.debug("MCP observability tools not available, skipping persistence")
        except Exception as e:
            # Log but don't fail - persistence should never block real-time updates
            logger.warning(f"Failed to persist activity: {e}")


# Singleton instance
observability_agent = ObservabilityAgent()
