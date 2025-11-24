"""
WebSocket handler for real-time communication
"""

from datetime import datetime

from fastapi import WebSocket
from pydantic import BaseModel


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.message_queues: dict[str, list[dict]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        # Send any queued messages
        if session_id in self.message_queues:
            for message in self.message_queues[session_id]:
                await self.send_message(session_id, message)
            del self.message_queues[session_id]

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
        else:
            # Queue message for when client reconnects
            if session_id not in self.message_queues:
                self.message_queues[session_id] = []
            self.message_queues[session_id].append(message)

    async def broadcast(self, message: dict, exclude: str | None = None):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for session_id, websocket in self.active_connections.items():
            if session_id != exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {session_id}: {e}")
                    disconnected.append(session_id)

        # Clean up disconnected clients
        for session_id in disconnected:
            self.disconnect(session_id)


class WebSocketMessage(BaseModel):
    """WebSocket message model."""

    type: str  # message, tool_execution, status, error, ping, pong
    data: dict | None = None
    timestamp: str = None
    session_id: str | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


async def handle_websocket_message(
    websocket: WebSocket,
    session_id: str,
    message: dict,
    pm_agent,
    audit_tool,
    manager: ConnectionManager,
    form_data_agent=None,
):
    """Handle incoming WebSocket messages."""
    msg_type = message.get("type")

    # Handle ping/pong for heartbeat
    if msg_type == "ping":
        await manager.send_message(session_id, {"type": "pong", "timestamp": datetime.utcnow().isoformat()})
        return

    # Handle field population via tool_execution
    if msg_type == "tool_execution":
        data = message.get("data", {}) or {}
        tool = data.get("tool")

        if tool == "form_data.populate":
            if not form_data_agent:
                await manager.send_message(
                    session_id,
                    {
                        "type": "error",
                        "data": {"error": "FormDataAgent not available"},
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                return

            context = data.get("context", {}) or {}
            try:
                result_state = await form_data_agent.populate_fields(
                    org_id=context.get("organization_id", "default-org"),
                    domain_id=context.get("domain_id", "default-domain"),
                    environment=context.get("environment", "dev"),
                    instance_id=context.get("instance_id", "dev"),
                    field_id=context.get("field_id", "instances_for_org_domain"),
                )

                if result_state.get("error"):
                    await manager.send_message(
                        session_id,
                        {
                            "type": "error",
                            "data": {"error": result_state["error"]},
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                else:
                    await manager.send_message(
                        session_id,
                        {
                            "type": "tool_execution",
                            "data": {
                                "tool": tool,
                                "context": context,
                                "result": result_state.get("result"),
                            },
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )
                return
            except Exception as e:
                print(f"Error in FormDataAgent via WebSocket: {e}")
                await manager.send_message(
                    session_id,
                    {
                        "type": "error",
                        "data": {"error": str(e)},
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
                return

    # Handle chat messages
    if msg_type == "message":
        data = message.get("data", {})
        user_message = data.get("content")

        if not user_message:
            await manager.send_message(
                session_id,
                {
                    "type": "error",
                    "data": {"error": "No message content provided"},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            return

        try:
            # Send typing indicator
            await manager.send_message(
                session_id,
                {
                    "type": "status",
                    "data": {"status": "processing", "message": "Understanding your request..."},
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Process message through agent
            if pm_agent:
                # Note: stream_callback support can be added to PM agent in future
                result = await pm_agent.process_message(user_message)

                # Send response
                response_data = {"content": result.get("response", "Processing complete"), "artifacts": []}

                # Add artifacts if any
                if result.get("story_created"):
                    response_data["artifacts"].append({"type": "story", "data": result["story_created"]})
                if result.get("issue_created"):
                    response_data["artifacts"].append({"type": "issue", "data": result["issue_created"]})

                await manager.send_message(
                    session_id, {"type": "message", "data": response_data, "timestamp": datetime.utcnow().isoformat()}
                )

                # Log to audit
                if audit_tool:
                    await audit_tool.log_action(
                        actor=f"ws-{session_id}",
                        tool="pm_agent",
                        action="websocket_chat",
                        input_data={"message": user_message},
                        output_data=result,
                        result="success",
                    )
            else:
                # Fallback response if agent not available
                await manager.send_message(
                    session_id,
                    {
                        "type": "message",
                        "data": {"content": "PM Agent is not available. Please try again later.", "artifacts": []},
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

        except Exception as e:
            print(f"Error processing WebSocket message: {e}")
            await manager.send_message(
                session_id, {"type": "error", "data": {"error": str(e)}, "timestamp": datetime.utcnow().isoformat()}
            )

            # Log error
            if audit_tool:
                await audit_tool.log_action(
                    actor=f"ws-{session_id}",
                    tool="pm_agent",
                    action="websocket_chat",
                    input_data={"message": user_message},
                    output_data=None,
                    result="failure",
                    error=str(e),
                )


# Create global connection manager
manager = ConnectionManager()
