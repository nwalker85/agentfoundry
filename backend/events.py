"""
Event Bus System for Agent Foundry
Pub/Sub pattern: Database changes broadcast events, components subscribe to what they need.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """All event types that can be broadcast in the system."""

    # Organization events
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"

    # Domain events
    DOMAIN_CREATED = "domain.created"
    DOMAIN_UPDATED = "domain.updated"
    DOMAIN_DELETED = "domain.deleted"

    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATUS_CHANGED = "agent.status_changed"

    # Instance events
    INSTANCE_CREATED = "instance.created"
    INSTANCE_UPDATED = "instance.updated"
    INSTANCE_DELETED = "instance.deleted"

    # Deployment events
    DEPLOYMENT_STARTED = "deployment.started"
    DEPLOYMENT_COMPLETED = "deployment.completed"
    DEPLOYMENT_FAILED = "deployment.failed"

    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"


@dataclass
class Event:
    """Standard event structure for all broadcasts."""

    type: EventType
    timestamp: str
    data: dict[str, Any]
    organization_id: str | None = None
    domain_id: str | None = None
    actor: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return asdict(self)

    def matches_filter(self, filter_dict: dict[str, Any]) -> bool:
        """Check if event matches subscription filter."""
        for key, value in filter_dict.items():
            if key == "type":
                # Support wildcard matching: "agent.*" matches all agent events
                pattern = value
                if pattern.endswith(".*"):
                    prefix = pattern[:-2]
                    if not self.type.startswith(prefix):
                        return False
                elif pattern != self.type:
                    return False
            elif key == "organization_id":
                if self.organization_id != value:
                    return False
            elif key == "domain_id":
                if self.domain_id != value:
                    return False
        return True


class EventBus:
    """
    Central event bus for pub/sub pattern.

    Usage:
        # Publish event
        await event_bus.publish(Event(
            type=EventType.AGENT_CREATED,
            timestamp=datetime.utcnow().isoformat(),
            data={"id": "agt-001", "name": "customer-support-agent"},
            organization_id="quant",
            domain_id="demo"
        ))

        # Subscribe to events
        async def handler(event: Event):
            print(f"Received: {event.type}")

        event_bus.subscribe(handler, filter={"type": "agent.*", "organization_id": "quant"})
    """

    def __init__(self):
        self._subscribers: list[tuple[Callable, dict[str, Any]]] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: asyncio.Task | None = None

    async def start(self):
        """Start the event bus worker."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("🚀 EventBus started")

    async def stop(self):
        """Stop the event bus worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 EventBus stopped")

    def subscribe(self, handler: Callable[[Event], Any], filter: dict[str, Any] | None = None):
        """
        Subscribe to events.

        Args:
            handler: Async function to call when event matches filter
            filter: Dict to filter events (e.g., {"type": "agent.*", "organization_id": "quant"})
        """
        self._subscribers.append((handler, filter or {}))
        logger.info(f"📡 New subscriber: {handler.__name__} with filter {filter}")

    def unsubscribe(self, handler: Callable):
        """Unsubscribe a handler."""
        self._subscribers = [(h, f) for h, f in self._subscribers if h != handler]

    async def publish(self, event: Event):
        """
        Publish an event to all matching subscribers.

        Events are queued and processed asynchronously to avoid blocking.
        """
        await self._event_queue.put(event)
        logger.debug(f"📨 Event published: {event.type}")

    async def _process_events(self):
        """Worker that processes events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._dispatch_event(event)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

    async def _dispatch_event(self, event: Event):
        """Dispatch event to all matching subscribers."""
        for handler, filter_dict in self._subscribers:
            try:
                if event.matches_filter(filter_dict):
                    # Call handler (may be sync or async)
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)


# Global event bus instance
event_bus = EventBus()


# Helper functions for common events
async def emit_agent_created(agent_data: dict[str, Any]):
    """Emit agent created event."""
    await event_bus.publish(
        Event(
            type=EventType.AGENT_CREATED,
            timestamp=datetime.utcnow().isoformat(),
            data=agent_data,
            organization_id=agent_data.get("organization_id"),
            domain_id=agent_data.get("domain_id"),
        )
    )


async def emit_agent_updated(agent_data: dict[str, Any]):
    """Emit agent updated event."""
    await event_bus.publish(
        Event(
            type=EventType.AGENT_UPDATED,
            timestamp=datetime.utcnow().isoformat(),
            data=agent_data,
            organization_id=agent_data.get("organization_id"),
            domain_id=agent_data.get("domain_id"),
        )
    )


async def emit_agent_deleted(agent_id: str, organization_id: str, domain_id: str):
    """Emit agent deleted event."""
    await event_bus.publish(
        Event(
            type=EventType.AGENT_DELETED,
            timestamp=datetime.utcnow().isoformat(),
            data={"id": agent_id},
            organization_id=organization_id,
            domain_id=domain_id,
        )
    )


async def emit_organization_created(org_data: dict[str, Any]):
    """Emit organization created event."""
    await event_bus.publish(
        Event(
            type=EventType.ORGANIZATION_CREATED,
            timestamp=datetime.utcnow().isoformat(),
            data=org_data,
        )
    )


async def emit_domain_created(domain_data: dict[str, Any]):
    """Emit domain created event."""
    await event_bus.publish(
        Event(
            type=EventType.DOMAIN_CREATED,
            timestamp=datetime.utcnow().isoformat(),
            data=domain_data,
            organization_id=domain_data.get("organization_id"),
        )
    )
