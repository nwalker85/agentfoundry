# Forge vs. System Agents: Architectural Separation

## Overview

After reviewing the FORGE_LANGGRAPH_GAP_ANALYSIS.md, it's clear that many
"missing features" are actually **runtime concerns** that should be handled by
**system-level agents**, not the Forge UI.

**Key Principle:**

- **Forge** = Design-time (visual builder, configuration)
- **System Agents** = Runtime (execution, state management, monitoring)

---

## Feature Classification

### 🎨 FORGE UI RESPONSIBILITY (Design-Time)

These features belong in the Forge visual builder:

#### 1. **State Schema Design** ✅ Forge

- Visual state field editor
- Type selection (list, dict, string, int, etc.)
- Reducer configuration (add, replace, custom)
- State field documentation
- **Why Forge**: Customers need to design their state schema visually

#### 2. **Node Configuration** ✅ Forge

- Visual node properties editor
- Prompt template editor for LLM nodes
- System message configuration
- Model selection (GPT-4, Claude, etc.)
- Temperature, token limits
- Tool selection from catalog
- Conditional logic builder
- **Why Forge**: Visual configuration of what nodes should do

#### 3. **Graph Structure** ✅ Forge

- Visual flow design (nodes + edges)
- START/END node placement
- Conditional routing design
- Subgraph composition
- Parallel execution definition
- **Why Forge**: Visual workflow design

#### 4. **Tool Catalog** ✅ Forge

- Browse available tools
- Tool schema display
- Parameter mapping UI
- Tool selection for nodes
- **Why Forge**: Design-time tool selection

#### 5. **Validation** ✅ Forge

- Graph structure validation (cycles, orphans, missing START/END)
- State schema validation
- Node configuration validation
- YAML/Code generation validation
- **Why Forge**: Pre-deployment checks

#### 6. **Code Generation** ✅ Forge

- Generate LangGraph Python code
- Generate TypeScript code
- YAML export
- **Why Forge**: Output from visual design

#### 7. **Configuration Management** ✅ Forge

- Agent metadata (name, version, description)
- Environment-specific configs (dev/staging/prod)
- Deployment settings
- **Why Forge**: Design-time metadata

---

### 🤖 SYSTEM AGENT RESPONSIBILITY (Runtime)

These features should be handled by platform agents:

#### 1. **State Persistence** → **context_agent** ⭐ CRITICAL

- **What it does**:
  - Runtime state storage (Redis)
  - State versioning and snapshots
  - Checkpointing for long-running agents
  - Thread/session management
  - State recovery after failures
  - State access control
- **Why System Agent**: Runtime concern, needs to work across all customer
  agents
- **Already exists**: context_agent handles session state!

**Recommendation**: Extend context_agent to support:

```python
# context_agent should handle
- Checkpoint creation/restoration
- State snapshots for debugging
- Cross-invocation state persistence
- State versioning (for rollback)
```

#### 2. **Execution & Orchestration** → **supervisor_agent** ⭐ CRITICAL

- **What it does**:
  - Graph compilation and execution
  - Node execution orchestration
  - Parallel execution (Send API, map-reduce)
  - Loop/cycle protection (recursion limits)
  - Streaming mode handling
  - Command API execution
- **Why System Agent**: Runtime orchestration, supervisor already does this!
- **Already exists**: supervisor_agent orchestrates execution!

**Recommendation**: Enhance supervisor_agent to support:

```python
# supervisor_agent should handle
- Parallel worker execution (already partially does)
- Loop iteration limits
- Streaming vs batch mode
- Dynamic routing at runtime
```

#### 3. **Error Handling & Resilience** → **NEW: exception_agent** ⚠️ MISSING (Tier 1)

- **What it does**:
  - Runtime error capture
  - Automatic retry logic (with exponential backoff)
  - Fallback path execution
  - Circuit breaker patterns
  - Dead letter queue for failed messages
  - Error recovery strategies
  - Human-in-the-loop (HITL) escalation
- **Why System Agent**: Runtime resilience, needs to wrap all executions
- **Status**: Mentioned in your architecture as "exception_escalation_agent"

**Recommendation**: Create exception_agent:

```python
class ExceptionAgent:
    """
    Handles runtime errors, retries, and fallbacks.
    Wraps all customer worker executions.
    """
    async def execute_with_resilience(self, node_func, state, config):
        retry_count = config.get('max_retries', 3)
        for attempt in range(retry_count):
            try:
                return await node_func(state)
            except Exception as e:
                if attempt < retry_count - 1:
                    await self.exponential_backoff(attempt)
                else:
                    return await self.handle_failure(e, state)
```

#### 4. **Observability & Monitoring** → **NEW: observability_agent** ⚠️ MISSING (Tier 1)

- **What it does**:
  - Execution trace collection
  - Performance metrics (latency, throughput)
  - State snapshots at each node
  - Execution playback/debugging
  - Cost tracking (token usage, API calls)
  - Real-time monitoring dashboards
  - Anomaly detection
- **Why System Agent**: Runtime monitoring, needs to observe all executions
- **Status**: Mentioned in your architecture

**Recommendation**: Create observability_agent:

```python
class ObservabilityAgent:
    """
    Monitors all agent executions in real-time.
    Collects traces, metrics, and state snapshots.
    """
    async def trace_execution(self, agent_id, node_id, state, result):
        trace = {
            'timestamp': now(),
            'agent_id': agent_id,
            'node_id': node_id,
            'input_state': state,
            'output_state': result,
            'duration_ms': ...,
            'tokens_used': ...,
        }
        await self.store_trace(trace)
```

#### 5. **Security & Governance** → **NEW: governance_agent** ⚠️ MISSING (Tier 1)

- **What it does**:
  - Runtime PII/PHI filtering
  - Policy enforcement (rate limits, allowed tools)
  - Secrets management (API keys, credentials)
  - Access control validation
  - Audit logging
  - Compliance checks
- **Why System Agent**: Runtime security, needs to guard all executions
- **Status**: Mentioned in your architecture

**Recommendation**: Create governance_agent:

```python
class GovernanceAgent:
    """
    Enforces policies and security at runtime.
    Filters sensitive data, manages secrets.
    """
    async def enforce_policies(self, state, action):
        # Check rate limits
        # Filter PII/PHI
        # Validate permissions
        # Inject secrets securely
        # Log for audit
```

#### 6. **Tool Execution** → **Extend supervisor_agent or NEW: tool_agent**

- **What it does**:
  - Runtime tool invocation
  - Tool result handling
  - Tool authentication/authorization
  - Tool timeout management
  - Tool error handling
  - Multi-tool parallel execution
- **Why System Agent**: Runtime execution concern
- **Status**: Partially in supervisor, could be separate agent

**Recommendation**: Either extend supervisor or create tool_agent:

```python
class ToolAgent:
    """
    Handles tool execution at runtime.
    Manages tool auth, timeouts, errors.
    """
    async def execute_tool(self, tool_name, parameters, context):
        tool = self.registry.get_tool(tool_name)
        # Authenticate
        # Execute with timeout
        # Handle errors
        # Return result
```

#### 7. **Message Management** → **Extend context_agent**

- **What it does**:
  - Message history management
  - Message type handling (HumanMessage, AIMessage, ToolMessage)
  - Message transformations
  - Message deduplication
  - Message archival
- **Why System Agent**: Runtime concern, related to state
- **Status**: Partially in context_agent

**Recommendation**: Extend context_agent:

```python
# context_agent should handle
- add_messages() helper
- Message type transformations
- Message history trimming (keep last N)
- Message archival to PostgreSQL
```

#### 8. **Resource Management** → **NEW: resource_agent** (Future)

- **What it does**:
  - Rate limiting (API calls, tokens)
  - Timeout enforcement
  - Memory management
  - Cost tracking and budgets
  - Queue management
  - Load balancing
- **Why System Agent**: Runtime resource allocation
- **Status**: Could be part of supervisor, or separate

---

### 🔄 HYBRID (Both Forge UI + System Agents)

These features need both design-time configuration (Forge) and runtime execution
(agents):

#### 1. **Testing & Debugging** (Hybrid)

- **Forge UI**: Test case design, mock data, expected outputs, test runner UI
- **System Agents**: Actual execution, state capture, result validation
- **How they work together**:
  - Forge provides test UI with "Run Test" button
  - Forge sends test request to supervisor_agent
  - Agents execute with test mode flag
  - Observability_agent captures detailed traces
  - Results return to Forge UI for display

#### 2. **Tracing Configuration** (Hybrid)

- **Forge UI**: Configure what to trace, LangSmith integration settings
- **System Agents**: Actual trace collection and sending
- **How they work together**:
  - Forge configures: `trace_level: "debug", langsmith_enabled: true`
  - Observability_agent reads config and collects traces
  - Traces sent to LangSmith in real-time

#### 3. **Error Handling Strategy** (Hybrid)

- **Forge UI**: Define fallback paths, retry policies
- **System Agents**: Execute retries and fallbacks at runtime
- **How they work together**:
  - Forge defines: "On error in node X, retry 3 times, then route to
    fallback_node"
  - Exception_agent executes this strategy at runtime

#### 4. **Performance Limits** (Hybrid)

- **Forge UI**: Set timeout, memory, rate limits
- **System Agents**: Enforce limits at runtime
- **How they work together**:
  - Forge configures: `timeout: 60s, max_concurrent: 10`
  - Resource_agent enforces these limits during execution

---

## Proposed System Agent Architecture

### Tier 0: Existing (Production Now) ✅

```
io_agent          → Interface & channel management
supervisor_agent  → Orchestration & routing
context_agent     → State & memory
coherence_agent   → Response assembly
```

### Tier 1: Critical for Production (Week 2-3) ⚠️

```
exception_agent      → Error handling, retries, fallbacks
observability_agent  → Monitoring, traces, metrics
governance_agent     → Security, PII filtering, policies
```

### Tier 2: Future Enhancements

```
tool_agent       → Dedicated tool execution (or extend supervisor)
resource_agent   → Rate limiting, cost tracking (or extend supervisor)
analytics_agent  → Usage analytics, insights
```

---

## Data Flow: Forge to System Agents

### Design-Time (Forge UI)

```
Customer uses Forge to design agent:
1. Draws nodes and edges visually
2. Configures state schema
3. Sets up error handling rules
4. Configures tracing
5. Clicks "Deploy"

Forge outputs:
- YAML configuration file
- Python code (optional)
- Deployment manifest

Saved to: /agents/customer_agent.yaml
```

### Runtime (System Agents)

```
User interacts with deployed agent:
1. io_agent receives input
2. supervisor_agent loads customer_agent.yaml
3. supervisor orchestrates workflow:
   - Calls context_agent for state
   - Executes customer worker nodes
   - exception_agent wraps each node
   - observability_agent traces everything
   - governance_agent filters PII
4. coherence_agent compiles response
5. io_agent formats output

All runtime concerns handled by platform agents!
```

---

## Recommendations

### 1. **Extend Existing Tier 0 Agents** ✅

#### context_agent enhancements:

```python
# Add to context_agent
- checkpoint_state(session_id, checkpoint_id)
- restore_checkpoint(session_id, checkpoint_id)
- get_state_snapshot(session_id, node_id)
- store_message_history(session_id, messages)
- get_message_history(session_id, limit=10)
```

#### supervisor_agent enhancements:

```python
# Add to supervisor_agent
- execute_parallel_workers(workers, state)
- enforce_recursion_limit(current_depth, max_depth)
- handle_streaming_mode(stream=True)
- execute_with_timeout(node_func, timeout_seconds)
```

#### coherence_agent enhancements:

```python
# Add to coherence_agent
- Already good! Maybe add:
- compile_with_priority(responses, priority_weights)
```

### 2. **Create Tier 1 Agents** ⚠️ (Week 2-3)

#### exception_agent (NEW):

```python
class ExceptionAgent:
    """Runtime error handling and resilience"""
    - execute_with_retry(node_func, max_retries=3)
    - handle_timeout(node_func, timeout_seconds)
    - execute_fallback(fallback_path, state)
    - escalate_to_human(error, state)
    - apply_circuit_breaker(service_name)
```

#### observability_agent (NEW):

```python
class ObservabilityAgent:
    """Runtime monitoring and tracing"""
    - start_trace(agent_id, execution_id)
    - log_node_execution(node_id, state, result)
    - track_metrics(latency, tokens, cost)
    - create_execution_snapshot(state)
    - send_to_langsmith(trace_data)
```

#### governance_agent (NEW):

```python
class GovernanceAgent:
    """Security and policy enforcement"""
    - filter_pii(text)
    - filter_phi(text)
    - enforce_rate_limit(user_id, action)
    - validate_permissions(user_id, action)
    - inject_secrets(tool_name, config)
    - audit_log(action, user_id, result)
```

### 3. **Forge UI Updates** (Separate from agents)

Forge should focus on:

- ✅ State schema designer (visual)
- ✅ Enhanced node configuration
- ✅ Tool catalog browser
- ✅ Error handling rules designer
- ✅ Test case designer
- ✅ Validation before deploy
- ✅ Code generation

Forge should NOT try to:

- ❌ Execute agents (that's supervisor's job)
- ❌ Store runtime state (that's context_agent's job)
- ❌ Monitor performance (that's observability_agent's job)
- ❌ Handle errors at runtime (that's exception_agent's job)

### 4. **Communication Protocol**

Forge → System Agents:

```typescript
// Forge deploys agent
POST /api/agents/deploy
{
  "agent_yaml": "...",
  "environment": "production"
}

// Forge triggers test
POST /api/agents/test
{
  "agent_id": "customer_agent",
  "test_case": { "input": "...", "expected": "..." }
}

// System agents execute and return results
```

System Agents → Forge:

```python
# System agents send execution data back
websocket.send({
  "type": "execution_trace",
  "agent_id": "customer_agent",
  "nodes_executed": [...],
  "state_snapshots": [...],
  "metrics": {...}
})

# Forge displays in real-time
```

---

## Summary Table

| Feature                    | Owner               | Tier | Status              |
| -------------------------- | ------------------- | ---- | ------------------- |
| **State Schema Design**    | Forge UI            | -    | 🔴 Missing          |
| **State Persistence**      | context_agent       | 0    | ✅ Exists (enhance) |
| **Node Configuration**     | Forge UI            | -    | 🟡 Partial          |
| **Graph Execution**        | supervisor_agent    | 0    | ✅ Exists (enhance) |
| **Error Handling UI**      | Forge UI            | -    | 🔴 Missing          |
| **Error Handling Runtime** | exception_agent     | 1    | 🔴 Missing          |
| **Tool Catalog**           | Forge UI            | -    | 🔴 Missing          |
| **Tool Execution**         | supervisor_agent    | 0    | 🟡 Partial          |
| **Testing UI**             | Forge UI            | -    | 🔴 Missing          |
| **Testing Execution**      | supervisor_agent    | 0    | 🟡 Partial          |
| **Trace Config**           | Forge UI            | -    | 🔴 Missing          |
| **Trace Collection**       | observability_agent | 1    | 🔴 Missing          |
| **Security Config**        | Forge UI            | -    | 🔴 Missing          |
| **Security Runtime**       | governance_agent    | 1    | 🔴 Missing          |
| **Message Types**          | context_agent       | 0    | 🟡 Partial          |
| **Response Assembly**      | coherence_agent     | 0    | ✅ Exists           |
| **Channel Handling**       | io_agent            | 0    | ✅ Exists           |

---

## Conclusion

**Key Insight**: About **60% of the "Forge gaps"** are actually **system agent
concerns**!

### What Forge Should Focus On:

1. Visual workflow designer (nodes, edges, state schema)
2. Configuration UI (prompts, tools, conditions)
3. Validation and code generation
4. Test case designer
5. Deployment UI

### What System Agents Should Handle:

1. **Execution** (supervisor_agent)
2. **State & Memory** (context_agent)
3. **Error Handling** (exception_agent - NEW)
4. **Monitoring** (observability_agent - NEW)
5. **Security** (governance_agent - NEW)
6. **Response Assembly** (coherence_agent)
7. **I/O** (io_agent)

### Priority:

1. ✅ **Week 1**: System Agents UI (DONE!)
2. 🔨 **Week 2**: Create Tier 1 agents (exception, observability, governance)
3. 🔨 **Week 3**: Enhance Forge UI for design-time features
4. 🔨 **Week 4**: Connect Forge to system agents for testing/deployment

This architecture properly separates **design concerns** (Forge) from **runtime
concerns** (System Agents), making both more maintainable and scalable.
