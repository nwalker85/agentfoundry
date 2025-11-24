"""
WebSocket Manager for Broadcasting Events
Connects the EventBus to WebSocket clients, allowing UI components to subscribe to real-time updates.
"""

import logging

from fastapi import WebSocket

from backend.events import Event, event_bus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts events to subscribed clients.

    Architecture:
    1. Client connects via WebSocket
    2. Client sends subscription message: {"action": "subscribe", "filter": {"type": "agent.*", "organization_id": "quant"}}
    3. WebSocketManager subscribes to EventBus with that filter
    4. When matching events occur, they're broadcast to the client
    """

    def __init__(self):
        # Map of websocket -> subscription filters
        self._connections: dict[WebSocket, dict[str, any]] = {}
        self._event_bus_handler_registered = False

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self._connections[websocket] = {}  # Start with no filter (receives nothing)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self._connections)}")

        # Register event bus handler if this is the first connection
        if not self._event_bus_handler_registered:
            event_bus.subscribe(self._handle_event)
            self._event_bus_handler_registered = True

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self._connections:
            del self._connections[websocket]
            logger.info(f"❌ WebSocket disconnected. Total connections: {len(self._connections)}")

    async def handle_message(self, websocket: WebSocket, message: dict):
        """
        Handle incoming WebSocket messages from clients.

        Supported messages:
        - Subscribe: {"action": "subscribe", "filter": {"type": "agent.*", "organization_id": "quant"}}
        - Unsubscribe: {"action": "unsubscribe"}
        - Ping: {"action": "ping"}
        """
        action = message.get("action")

        if action == "subscribe":
            filter_dict = message.get("filter", {})
            self._connections[websocket] = filter_dict
            logger.info(f"📡 Client subscribed with filter: {filter_dict}")

            # Send confirmation
            await websocket.send_json(
                {
                    "type": "subscription_confirmed",
                    "filter": filter_dict,
                    "timestamp": Event(type="", timestamp="", data={}).timestamp,
                }
            )

        elif action == "unsubscribe":
            self._connections[websocket] = {}
            logger.info("🔕 Client unsubscribed")

            await websocket.send_json({"type": "unsubscribed", "timestamp": ""})

        elif action == "ping":
            await websocket.send_json({"type": "pong"})

        else:
            logger.warning(f"Unknown action: {action}")

    async def _handle_event(self, event: Event):
        """
        Handler called by EventBus when events are published.
        Broadcasts events to all WebSocket clients with matching filters.
        """
        disconnected = []

        for websocket, filter_dict in self._connections.items():
            # Check if event matches client's filter
            if event.matches_filter(filter_dict):
                try:
                    await websocket.send_json(event.to_dict())
                except Exception as e:
                    logger.error(f"Failed to send to client: {e}")
                    disconnected.append(websocket)

        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients (regardless of filter)."""
        disconnected = []

        for websocket in self._connections.keys():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to client: {e}")
                disconnected.append(websocket)

        for ws in disconnected:
            self.disconnect(ws)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
