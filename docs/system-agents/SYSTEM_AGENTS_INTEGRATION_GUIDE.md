# System Agents Integration Guide

## Overview

This guide explains how to integrate and use the 7 platform system agents in
Agent Foundry. These agents form the runtime infrastructure that enables all
customer worker agents to function reliably.

---

## Agent Tiers

### **Tier 0: Foundation (4 Agents)** ✅

Core platform - required for any agent execution

1. **io_agent** - Interface & channel management
2. **supervisor_agent** - Orchestration & routing
3. **context_agent** - State & memory
4. **coherence_agent** - Response assembly

### **Tier 1: Production (3 Agents)** ⚠️ NEW!

Essential for production readiness

5. **exception_agent** - Error handling & resilience
6. **observability_agent** - Monitoring & tracing
7. **governance_agent** - Security & compliance

---

## Quick Start

### 1. Import the Agents

```python
from agents.io_agent import IOAgent
from agents.supervisor_agent import SupervisorAgent
from agents.workers.context_agent import ContextAgent
from agents.workers.coherence_agent import CoherenceAgent
from agents.workers.exception_agent import ExceptionAgent
from agents.workers.observability_agent import ObservabilityAgent
from agents.workers.governance_agent import GovernanceAgent
```

### 2. Initialize the Platform Stack

```python
# Tier 0: Foundation
io_agent = IOAgent()
supervisor_agent = SupervisorAgent()
context_agent = ContextAgent()
coherence_agent = CoherenceAgent()

# Tier 1: Production
exception_agent = ExceptionAgent()
observability_agent = ObservabilityAgent(langsmith_enabled=False)
governance_agent = GovernanceAgent()
```

### 3. Process a User Message

```python
# User input arrives
user_input = "Create a story for user authentication"
session_id = "session_123"
user_id = "user_456"

# Go through the platform stack
response = await io_agent.process_message(
    user_message=user_input,
    session_id=session_id,
    user_id=user_id,
    channel="chat"
)

# Response is automatically:
# - Routed by supervisor
# - Enriched with context
# - Protected by exception handling
# - Monitored by observability
# - Secured by governance
# - Assembled by coherence
```

---

## Integration Patterns

### Pattern 1: Simple Customer Worker

For a single customer worker (e.g., pm_agent):

```python
# The supervisor_agent already wraps pm_agent
# Just call io_agent and it handles everything
response = await io_agent.handle_chat_message(
    message="Create story",
    session_id=session_id
)
```

**Flow:**

```
User → io_agent → supervisor → context → pm_agent → coherence → io_agent → User
```

### Pattern 2: Multi-Worker with Parallel Execution

For multiple customer workers executing in parallel:

```python
from agents.workers.pm_agent import PMAgent
from agents.workers.ticket_agent import TicketAgent

# Initialize workers
pm_agent = PMAgent()
ticket_agent = TicketAgent()

# Supervisor executes them in parallel
worker_responses = await supervisor_agent.execute_parallel_workers(
    worker_agents=[pm_agent, ticket_agent],
    state={"current_input": user_input}
)

# Coherence compiles the responses
final_response = await coherence_agent.process(worker_responses)
```

### Pattern 3: With Error Handling

Wrap any node execution with exception_agent:

```python
async def my_risky_node(state):
    # This might fail
    result = await call_external_api()
    return result

# Execute with resilience
result = await exception_agent.execute_with_resilience(
    node_func=my_risky_node,
    state=current_state,
    config={
        'max_retries': 3,
        'timeout_seconds': 60,
        'fallback_func': my_fallback,
        'enable_hitl': True
    }
)
```

### Pattern 4: With Observability

Trace any agent execution:

```python
# Start trace
trace_id = await observability_agent.start_trace(
    agent_id="pm_agent",
    execution_id=execution_id
)

# Execute node
start_time = time.time()
result = await pm_agent.process(input)
duration_ms = (time.time() - start_time) * 1000

# Log execution
await observability_agent.log_node_execution(
    trace_id=trace_id,
    node_id="create_story",
    input_state=input_state,
    output_state=result,
    duration_ms=duration_ms,
    tokens_used=250,
    cost_usd=0.001
)

# End trace
summary = await observability_agent.end_trace(trace_id)
```

### Pattern 5: With Governance

Filter sensitive data and enforce policies:

```python
# Filter PII/PHI from user input
filtered_input = await governance_agent.filter_sensitive_data(
    text=user_input,
    filter_pii=True,
    filter_phi=True  # Enable for healthcare
)

# Check rate limits
rate_check = await governance_agent.enforce_rate_limit(
    user_id=user_id,
    action="create_story",
    limit=100,
    window_seconds=3600
)

if not rate_check['allowed']:
    return "Rate limit exceeded. Please try again later."

# Enforce policy
policy_check = await governance_agent.enforce_policy(
    action="tool_execution",
    params={
        'tool_name': 'web_search',
        'estimated_cost': 0.05
    }
)

if not policy_check['allowed']:
    return f"Policy violation: {policy_check['violations']}"

# Inject secrets for tools
config = await governance_agent.inject_secrets(
    tool_name="openai",
    config={"model": "gpt-4"}
)
# config now has {'model': 'gpt-4', 'api_key': '<secret>'}
```

---

## Configuration

### Agent YAML Configuration

Each agent has a YAML config file in `/agents/`:

- `dev_io_agent.yaml`
- `dev_supervisor_agent.yaml`
- `dev_context_agent.yaml`
- `dev-cohenrence_agent.yaml`
- `dev_exception_agent.yaml` ⭐ NEW
- `dev_observability_agent.yaml` ⭐ NEW
- `dev_governance_agent.yaml` ⭐ NEW

### UI Configuration

Use the System Agents UI at `/system-agents` to configure:

1. **General**: Version, phase, workflow settings
2. **Resources**: Memory, timeouts, token limits
3. **Integrations**: Redis, PostgreSQL, external services
4. **Observability**: Trace levels, metrics, logging
5. **Health Checks**: Monitoring intervals

### Programmatic Configuration

```python
# Configure exception agent
exception_agent = ExceptionAgent()
# Default: 3 retries, 60s timeout, exponential backoff

# Configure observability agent
observability_agent = ObservabilityAgent(langsmith_enabled=True)

# Configure governance agent
governance_agent = GovernanceAgent()
await governance_agent.update_policy({
    'max_cost_per_request': 2.0,
    'allowed_tools': ['web_search', 'calculator'],
    'blocked_tools': ['dangerous_tool']
})
```

---

## Architecture Diagrams

### Complete Stack

```
┌──────────────────────────────────────────────────────────┐
│                       USER                               │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │      io_agent        │ ← Channel detection
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  governance_agent    │ ← Security layer
              │  • Filter PII/PHI    │
              │  • Rate limiting     │
              │  • Policy enforcement│
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  supervisor_agent    │ ← Orchestration
              └──────┬───────┬───────┘
                     │       │
        ┌────────────┘       └───────────┐
        │                                │
        ▼                                ▼
┌───────────────┐              ┌──────────────────┐
│ context_agent │              │ exception_agent  │
│ • Load state  │              │ • Wrap execution │
│ • Checkpoint  │              │ • Retry logic    │
└───────┬───────┘              │ • Circuit breaker│
        │                      └────────┬─────────┘
        │                               │
        └───────────┬───────────────────┘
                    │
                    ▼
          ┌──────────────────┐
          │ Customer Workers │
          │ • pm_agent       │
          │ • ticket_agent   │
          │ • custom agents  │
          └────────┬─────────┘
                   │
                   ▼
         ┌──────────────────────┐
         │ observability_agent  │ ← Monitoring
         │ • Trace execution    │
         │ • Collect metrics    │
         └────────┬─────────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │  coherence_agent     │ ← Assembly
         └────────┬─────────────┘
                  │
                  ▼
         ┌──────────────────────┐
         │     io_agent         │ ← Output
         └────────┬─────────────┘
                  │
                  ▼
          ┌──────────────┐
          │  USER        │
          └──────────────┘
```

### State Flow

```
Redis (Session State)
       ↕
  context_agent
       ↕
  supervisor_agent
       ↕
  Customer Workers

PostgreSQL (User Context)
       ↕
  context_agent
```

---

## Feature Matrix

| Feature                   | Agent               | Status     |
| ------------------------- | ------------------- | ---------- |
| **Channel Detection**     | io_agent            | ✅         |
| **Input Normalization**   | io_agent            | ✅         |
| **Output Formatting**     | io_agent            | ✅         |
| **SSML Generation**       | io_agent            | 🔄 TODO    |
| **Orchestration**         | supervisor_agent    | ✅         |
| **Multi-Agent Routing**   | supervisor_agent    | ✅         |
| **Parallel Execution**    | supervisor_agent    | ✅ NEW     |
| **Streaming Mode**        | supervisor_agent    | ✅ NEW     |
| **Session State**         | context_agent       | ✅         |
| **User Context**          | context_agent       | 🔄 Partial |
| **Checkpointing**         | context_agent       | ✅ NEW     |
| **State Snapshots**       | context_agent       | ✅ NEW     |
| **Response Assembly**     | coherence_agent     | ✅         |
| **Deduplication**         | coherence_agent     | ✅         |
| **Conflict Resolution**   | coherence_agent     | 🔄 TODO    |
| **Retry Logic**           | exception_agent     | ✅ NEW     |
| **Circuit Breaker**       | exception_agent     | ✅ NEW     |
| **Fallback Execution**    | exception_agent     | ✅ NEW     |
| **HITL Escalation**       | exception_agent     | ✅ NEW     |
| **Dead Letter Queue**     | exception_agent     | ✅ NEW     |
| **Execution Tracing**     | observability_agent | ✅ NEW     |
| **Metrics Collection**    | observability_agent | ✅ NEW     |
| **State Snapshots**       | observability_agent | ✅ NEW     |
| **Anomaly Detection**     | observability_agent | ✅ NEW     |
| **LangSmith Integration** | observability_agent | 🔄 TODO    |
| **PII Filtering**         | governance_agent    | ✅ NEW     |
| **PHI Filtering**         | governance_agent    | ✅ NEW     |
| **Rate Limiting**         | governance_agent    | ✅ NEW     |
| **Policy Enforcement**    | governance_agent    | ✅ NEW     |
| **Secrets Management**    | governance_agent    | ✅ NEW     |
| **Audit Logging**         | governance_agent    | ✅ NEW     |

Legend:

- ✅ Implemented
- ✅ NEW Newly implemented
- 🔄 Partial implementation
- 🔄 TODO Not yet implemented

---

## Best Practices

### 1. Always Use Exception Agent for External Calls

```python
# BAD
result = await external_api.call()

# GOOD
result = await exception_agent.execute_with_resilience(
    node_func=lambda s: external_api.call(),
    state=state,
    config={'max_retries': 3, 'timeout_seconds': 30}
)
```

### 2. Always Trace Execution in Production

```python
trace_id = await observability_agent.start_trace(agent_id, execution_id)
# ... execute nodes ...
await observability_agent.end_trace(trace_id)
```

### 3. Always Filter Sensitive Data

```python
# Before passing to LLM
filtered = await governance_agent.filter_sensitive_data(user_input)
llm_response = await llm.invoke(filtered['filtered_text'])
```

### 4. Use Checkpoints for Long Conversations

```python
# Every N turns, create checkpoint
if message_count % 10 == 0:
    await context_agent.checkpoint_state(
        session_id=session_id,
        checkpoint_id=f"checkpoint_{message_count}",
        state=current_state
    )
```

### 5. Monitor Circuit Breakers

```python
# Check circuit breaker status
breakers = await exception_agent.get_circuit_breaker_status()
for service, status in breakers.items():
    if status['state'] == 'open':
        logger.warning(f"Circuit breaker OPEN for {service}")
```

---

## API Reference

### IO Agent

```python
class IOAgent:
    def detect_channel(channel_hint, **metadata) -> str
    async def process_message(user_message, session_id, user_id, channel, **metadata) -> str
    async def handle_chat_message(message, session_id) -> str
    async def handle_voice_message(transcribed_text, session_id, room_name) -> str
```

### Supervisor Agent

```python
class SupervisorAgent:
    async def process(io_state: IOState) -> str
    async def execute_parallel_workers(worker_agents: List, state: Dict) -> Dict
    async def execute_with_timeout(node_func, state, timeout_seconds) -> Any
    async def enforce_recursion_limit(current_depth, max_depth) -> bool
    async def execute_with_streaming(state, stream_mode) -> Any
```

### Context Agent

```python
class ContextAgent:
    async def process(session_id, user_id, current_input) -> Dict
    async def update_session_state(session_id, user_message, assistant_response)
    async def checkpoint_state(session_id, checkpoint_id, state)
    async def restore_checkpoint(session_id, checkpoint_id) -> Optional[Dict]
    async def get_state_snapshot(session_id, node_id) -> Dict
    async def list_checkpoints(session_id) -> List[Dict]
    async def get_conversation_context(session_id, lookback=10) -> List[Dict]
```

### Coherence Agent

```python
class CoherenceAgent:
    async def process(worker_responses: Dict[str, str]) -> str
    async def validate_coherence(compiled_response: str) -> Dict
```

### Exception Agent ⭐

```python
class ExceptionAgent:
    async def execute_with_resilience(node_func, state, config) -> Dict
    async def get_dead_letter_queue() -> List[Dict]
    async def retry_dead_letter_item(index, node_func) -> Dict
    async def get_circuit_breaker_status() -> Dict
    async def reset_circuit_breaker(service_key)
    async def analyze_error_pattern(errors: List[str]) -> Dict
```

### Observability Agent ⭐

```python
class ObservabilityAgent:
    async def start_trace(agent_id, execution_id, metadata) -> str
    async def log_node_execution(trace_id, node_id, input_state, output_state, duration_ms, ...)
    async def create_state_snapshot(trace_id, node_id, state)
    async def end_trace(trace_id) -> Dict
    async def get_trace(trace_id) -> Optional[Dict]
    async def get_agent_traces(agent_id, limit=100) -> List[Dict]
    async def get_metrics(agent_id, time_window_hours=24) -> AgentMetrics
    async def get_execution_playback(trace_id) -> Optional[List[Dict]]
    async def detect_performance_degradation(agent_id, threshold_increase=1.5) -> Dict
    async def export_traces(agent_id, format='json') -> str
```

### Governance Agent ⭐

```python
class GovernanceAgent:
    async def filter_pii(text, redact_mode='mask') -> Dict
    async def filter_phi(text, redact_mode='mask') -> Dict
    async def filter_sensitive_data(text, filter_pii=True, filter_phi=False) -> Dict
    async def enforce_rate_limit(user_id, action, limit=100, window_seconds=3600) -> Dict
    async def validate_permissions(user_id, action, resource) -> Dict
    async def inject_secrets(tool_name, config) -> Dict
    async def store_secret(tool_name, secret_key, secret_value)
    async def enforce_policy(action, params) -> Dict
    async def get_audit_log(user_id, event_type, limit=100) -> List[Dict]
    async def update_policy(policy_updates: Dict)
    async def get_policies() -> Dict
    async def check_compliance(text, compliance_standard='general') -> Dict
```

---

## Troubleshooting

### Agent Not Responding

1. Check health status: `/system-agents` UI
2. Check logs: `docker-compose logs -f <service>`
3. Check circuit breakers: `await exception_agent.get_circuit_breaker_status()`

### High Latency

1. Check metrics: `await observability_agent.get_metrics(agent_id)`
2. Check for degradation:
   `await observability_agent.detect_performance_degradation(agent_id)`
3. Review traces:
   `await observability_agent.get_agent_traces(agent_id, limit=50)`

### Rate Limits Hit

1. Check current limits: `await governance_agent.get_policies()`
2. Update policies:
   `await governance_agent.update_policy({'max_cost_per_request': 2.0})`

### Memory Leaks

1. Check context agent sessions: In-memory store grows unbounded currently
2. TODO: Add Redis integration for persistent storage
3. Implement session cleanup:
   `await context_agent.clear_session(old_session_id)`

---

## Next Steps

1. **Connect Redis** for real session state persistence
2. **Connect PostgreSQL** for user context and audit logs
3. **Implement LangSmith integration** in observability_agent
4. **Add AWS Secrets Manager** integration in governance_agent
5. **Create monitoring dashboard** using observability_agent metrics
6. **Set up alerts** for circuit breaker openings and anomalies
7. **Write tests** for each agent

---

## Support

- **Documentation**: `/docs/SYSTEM_AGENTS_IMPLEMENTATION.md`
- **Architecture**: `/docs/FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md`
- **Configuration**: Use `/system-agents` UI
- **Code**: `/agents/` directory

## Changelog

- **v1.0.0** (2025-11-16): Initial implementation of all 7 system agents
  - Tier 0: io, supervisor, context, coherence
  - Tier 1: exception, observability, governance
  - System Agents UI created
  - Integration guide written
