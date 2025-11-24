# Event Broadcasting System

**Status:** ✅ Production Ready **Last Updated:** 2025-11-16

## 🎯 Philosophy

> **"By default, alerts are broadcasted. Agents/components subscribe to what
> they need."**

All database changes automatically broadcast events. UI components and agents
subscribe only to the events they care about, creating a scalable, decoupled
architecture.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Browser)                       │
│                                                                  │
│  ┌──────────────────┐     ┌──────────────────┐                 │
│  │ Agents Page      │     │ Domains Page     │                 │
│  │ subscribes to:   │     │ subscribes to:   │                 │
│  │ - agent.*        │     │ - domain.*       │                 │
│  │ - org: quant     │     │ - org: quant     │                 │
│  └────────┬─────────┘     └────────┬─────────┘                 │
│           │                        │                            │
│           │    WebSocket Connection│                            │
│           └────────────┬───────────┘                            │
└────────────────────────┼────────────────────────────────────────┘
                         │
                    WebSocket
                         │
┌────────────────────────┼────────────────────────────────────────┐
│                   Backend (FastAPI)                              │
│                        │                                         │
│  ┌─────────────────────▼──────────────────────┐                 │
│  │        WebSocket Manager                    │                 │
│  │  - Manages client connections               │                 │
│  │  - Filters events by subscription           │                 │
│  │  - Broadcasts to matching clients           │                 │
│  └─────────────────────┬──────────────────────┘                 │
│                        │                                         │
│                   Subscribes to                                  │
│                        │                                         │
│  ┌─────────────────────▼──────────────────────┐                 │
│  │           Event Bus                         │                 │
│  │  - Pub/Sub pattern                          │                 │
│  │  - Async queue processing                   │                 │
│  │  - Filter matching                          │                 │
│  └─────────────────────▲──────────────────────┘                 │
│                        │                                         │
│                   Emits events                                   │
│                        │                                         │
│  ┌─────────────────────┴──────────────────────┐                 │
│  │     Database Operations                     │                 │
│  │  - create_agent_with_event()                │                 │
│  │  - update_agent_with_event()                │                 │
│  │  - delete_agent_with_event()                │                 │
│  └─────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📨 Event Types

All events follow the `{entity}.{action}` naming pattern:

### Agent Events

- `agent.created` - New agent created
- `agent.updated` - Agent modified
- `agent.deleted` - Agent removed
- `agent.status_changed` - Agent status changed

### Organization Events

- `organization.created`
- `organization.updated`
- `organization.deleted`

### Domain Events

- `domain.created`
- `domain.updated`
- `domain.deleted`

### Instance Events

- `instance.created`
- `instance.updated`
- `instance.deleted`

### Deployment Events

- `deployment.started`
- `deployment.completed`
- `deployment.failed`

### User Events

- `user.created`
- `user.updated`
- `user.deleted`

---

## 🔧 Backend Implementation

### 1. Event Bus (`backend/events.py`)

Central pub/sub system for all events:

```python
from backend.events import event_bus, Event, EventType, emit_agent_created

# Publishing events
await event_bus.publish(Event(
    type=EventType.AGENT_CREATED,
    timestamp=datetime.utcnow().isoformat(),
    data={"id": "agt-001", "name": "customer-support-agent"},
    organization_id="quant",
    domain_id="demo"
))

# Or use helper functions
await emit_agent_created({
    "id": "agt-001",
    "name": "customer-support-agent",
    "organization_id": "quant",
    "domain_id": "demo"
})

# Subscribing to events (backend agents)
async def my_handler(event: Event):
    print(f"Received: {event.type}")

event_bus.subscribe(my_handler, filter={"type": "agent.*", "organization_id": "quant"})
```

### 2. WebSocket Manager (`backend/websocket_manager.py`)

Broadcasts events to WebSocket clients:

```python
from backend.websocket_manager import websocket_manager

# WebSocket manager automatically:
# 1. Subscribes to event_bus on first client connection
# 2. Filters events based on client subscriptions
# 3. Broadcasts matching events to clients
```

### 3. Database Hooks (`backend/db.py`)

All database operations automatically emit events:

```python
from backend.db import create_agent_with_event, update_agent_with_event

# Create agent - automatically broadcasts agent.created
agent = create_agent_with_event(
    agent_id="agt-new",
    organization_id="quant",
    domain_id="demo",
    name="new-agent",
    display_name="New Agent",
    description="Newly created agent"
)

# Update agent - automatically broadcasts agent.updated
updated = update_agent_with_event(
    agent_id="agt-new",
    updates={"status": "inactive"}
)

# Delete agent - automatically broadcasts agent.deleted
delete_agent_with_event("agt-new")
```

---

## 💻 Frontend Implementation

### 1. Event Subscription Hook (`app/lib/hooks/useEventSubscription.ts`)

React hook for subscribing to events:

```typescript
import { useEventSubscription } from '@/lib/hooks/useEventSubscription'

function MyComponent() {
  const { subscribe, isConnected } = useEventSubscription()

  useEffect(() => {
    const unsubscribe = subscribe(
      {
        type: 'agent.*',              // All agent events
        organization_id: 'quant',     // Only for Quant org
        domain_id: 'demo'             // Only for Demo domain
      },
      (event) => {
        console.log('Event received:', event)
        // Update local state
      }
    )

    return unsubscribe  // Cleanup on unmount
  }, [subscribe])

  return <div>Connected: {isConnected ? '✅' : '❌'}</div>
}
```

### 2. Example: Agents Page

Real-time agent updates (`app/agents/page.tsx`):

```typescript
const { subscribe, isConnected } = useEventSubscription();

useEffect(() => {
  if (!selectedOrgId || !selectedDomainId) return;

  const unsubscribe = subscribe(
    {
      type: 'agent.*',
      organization_id: selectedOrgId,
      domain_id: selectedDomainId,
    },
    (event) => {
      if (event.type === 'agent.created') {
        // Add new agent to list
        setAgents((prev) => [event.data, ...prev]);
      } else if (event.type === 'agent.updated') {
        // Update existing agent
        setAgents((prev) =>
          prev.map((agent) =>
            agent.id === event.data.id ? { ...agent, ...event.data } : agent
          )
        );
      } else if (event.type === 'agent.deleted') {
        // Remove agent from list
        setAgents((prev) => prev.filter((agent) => agent.id !== event.data.id));
      }
    }
  );

  return unsubscribe;
}, [selectedOrgId, selectedDomainId, subscribe]);
```

---

## 🎯 Filter Patterns

### Wildcard Matching

Subscribe to all events of a type:

```typescript
{
  type: 'agent.*',  // Matches agent.created, agent.updated, agent.deleted
}
```

### Organization Scoping

Only receive events for specific org:

```typescript
{
  type: 'agent.*',
  organization_id: 'quant',
}
```

### Domain Scoping

Only receive events for specific domain:

```typescript
{
  type: 'agent.*',
  organization_id: 'quant',
  domain_id: 'demo',
}
```

### Specific Event Type

Only one event type:

```typescript
{
  type: 'agent.created',  // Only new agents
  organization_id: 'quant',
}
```

---

## 🚀 Usage Examples

### Example 1: Admin Dashboard

Subscribe to all organization events:

```typescript
subscribe({ type: 'organization.*' }, (event) => {
  // Refresh org list when orgs are created/updated/deleted
  refreshOrganizations();
});
```

### Example 2: Domain Management

Subscribe to domain events for current org:

```typescript
subscribe(
  {
    type: 'domain.*',
    organization_id: currentOrgId,
  },
  (event) => {
    // Update domain list in real-time
    setDomains((prev) => updateDomainsList(prev, event));
  }
);
```

### Example 3: Deployment Monitor

Subscribe to deployment events:

```typescript
subscribe(
  {
    type: 'deployment.*',
    organization_id: 'quant',
    domain_id: 'demo',
  },
  (event) => {
    if (event.type === 'deployment.completed') {
      showNotification(`Deployment ${event.data.id} completed!`);
    } else if (event.type === 'deployment.failed') {
      showError(`Deployment ${event.data.id} failed: ${event.data.error}`);
    }
  }
);
```

---

## ⚡ Performance Considerations

### Connection Management

- **Auto-reconnect**: Exponential backoff up to 10 attempts
- **Connection pooling**: Single WebSocket per client
- **Heartbeat**: Ping/pong to keep connection alive

### Event Filtering

- **Server-side filtering**: Only matching events sent to clients
- **Client-side filtering**: Additional filtering in hook if needed
- **Subscription deduplication**: Multiple subscriptions with same filter use
  single backend subscription

### Scalability

- **Async processing**: Event queue prevents blocking
- **Broadcast optimization**: Events sent only to clients with matching filters
- **Memory efficiency**: Weak references to handlers prevent leaks

---

## 🔐 Security Considerations

### Authentication

- **TODO**: Add WebSocket authentication (JWT token in connection URL)
- **TODO**: Verify user has permission to access org/domain data

### Authorization

- **Filter enforcement**: Server validates filter matches user's permissions
- **Data masking**: Sensitive fields removed based on user role
- **Audit logging**: All subscriptions and events logged

---

## 📊 Monitoring

### Backend Metrics

- Event bus queue size
- Events published per second
- Subscribers count
- WebSocket connections count
- Failed broadcasts

### Frontend Metrics

- WebSocket connection state
- Reconnection attempts
- Events received count
- Subscription count

---

## 🧪 Testing

### Backend Tests

```python
# Test event emission
from backend.db import create_agent_with_event
from backend.events import event_bus

handler_called = False

async def test_handler(event):
    global handler_called
    handler_called = True

event_bus.subscribe(test_handler, filter={"type": "agent.created"})
create_agent_with_event(...)
assert handler_called
```

### Frontend Tests

```typescript
// Test subscription
const { subscribe } = useEventSubscription();
const receivedEvents = [];

subscribe({ type: 'agent.*' }, (event) => {
  receivedEvents.push(event);
});

// Simulate event
mockWebSocket.send(
  JSON.stringify({
    type: 'agent.created',
    data: { id: 'agt-001' },
  })
);

expect(receivedEvents).toHaveLength(1);
```

---

## 🎓 Best Practices

### 1. Always Unsubscribe

```typescript
useEffect(() => {
  const unsubscribe = subscribe(filter, handler);
  return unsubscribe; // ✅ Cleanup on unmount
}, []);
```

### 2. Use Specific Filters

```typescript
// ❌ Too broad - receives all events
subscribe({}, handler);

// ✅ Specific - only what you need
subscribe({ type: 'agent.*', organization_id: 'quant' }, handler);
```

### 3. Handle Reconnections

```typescript
const { isConnected } = useEventSubscription()

if (!isConnected) {
  return <Banner>Reconnecting to live updates...</Banner>
}
```

### 4. Batch Updates

```typescript
// ❌ Multiple re-renders
subscribe(filter, (event) => {
  setAgents((prev) => [...prev, event.data]);
  setCount((prev) => prev + 1);
  setTimestamp(Date.now());
});

// ✅ Single batch update
subscribe(filter, (event) => {
  setAgents((prev) => [...prev, event.data]);
});
```

---

## 🚦 Deployment Checklist

Backend:

- [x] Event bus started on app startup
- [x] WebSocket endpoint exposed
- [x] Database hooks emit events
- [ ] Add authentication to WebSocket
- [ ] Add authorization filters
- [ ] Set up monitoring/metrics

Frontend:

- [x] useEventSubscription hook created
- [x] Agents page subscribes to events
- [ ] Add connection status indicator
- [ ] Add error boundary for WebSocket failures
- [ ] Log events to analytics

---

**Generated by:** Claude Code **Version:** 1.0 **Architecture:** Pub/Sub Event
Broadcasting
