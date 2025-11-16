# System Agents - Design Document

**Version:** 0.8.0-dev  
**Date:** November 16, 2025  
**Status:** Design Phase

---

## Executive Summary

Agent Foundry's core platform consists of **4 system agents** that provide channel adaptation, orchestration, context management, and response coherence. These are **platform code**, not customer-deployed agents.

**Key Principle:** Context and state are paramount to user experience.

---

## System Agent Overview

### The 4 Core Agents

```
User (Voice/Chat)
        ↓
    io_agent ——————————— Channel formatting layer
        ↓
  supervisor_agent ——— State manager & orchestrator
    /           \
   /             \
context_agent   coherence_agent
   |                  |
   |                  |
   └────────┬─────────┘
            ↓
     [Customer Workers]
     • pm_agent (example)
     • qa_agent (example)
     • ticket_agent (example)
```

### Agent Responsibilities

| Agent | Tier | Role | Critical For |
|-------|------|------|--------------|
| **io_agent** | 0 | I/O Adapter | Channel detection, formatting (SSML/Cards) |
| **supervisor_agent** | 0 | Orchestrator | Routing, state management, LangGraph flow |
| **context_agent** | 0 | Memory | Session state (Redis), User context (PostgreSQL) |
| **coherence_agent** | 0 | Compiler | Buffer async responses, dedup, resolve conflicts |

---

## Architecture

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────┐
│                 MarshalAgent                        │
│  - Manages all agent lifecycles                     │
│  - Hot-reloads YAML changes                         │
│  - Health monitoring                                │
└────────────┬────────────────────────────────────────┘
             │
   ┌─────────┴──────────┬──────────────┬─────────────┐
   │                    │              │             │
   ▼                    ▼              ▼             ▼
io_agent        supervisor_agent  context_agent  coherence_agent
(Platform)      (Platform)        (Platform)     (Platform)
   │                    │              │             │
   │                    └──────┬───────┘             │
   │                           │                     │
   │                           ▼                     │
   │              ┌──────────────────────┐           │
   │              │  Customer Workers     │           │
   │              │  - pm_agent          │           │
   │              │  - qa_agent          │           │
   │              │  - ticket_agent      │           │
   │              └──────────────────────┘           │
   └───────────────────────┬─────────────────────────┘
                           ▼
                    [Final Output]
```

### Data Flow

```
1. User Input (Voice/Chat)
        ↓
2. io_agent
   - Detect channel (voice/chat/api)
   - Normalize input format
   - Extract session metadata
        ↓
3. supervisor_agent
   - Load session state from context_agent
   - Determine routing (pm_agent, qa_agent, etc.)
   - Dispatch to worker(s)
        ↓
4. Worker Agents (Async)
   pm_agent (2s)    → "3 stories in backlog"
   ticket_agent (5s) → "2 critical bugs"
   qa_agent (3s)     → "1 failing test"
        ↓
5. coherence_agent
   - Buffer responses (wait 10s)
   - Deduplicate information
   - Resolve conflicts
   - Compile coherent output
        ↓
6. io_agent (Output Formatting)
   - Voice: SSML tags, prosody
   - Chat: Adaptive Cards, markdown
   - API: Structured JSON
        ↓
7. User receives coherent response
```

---

## Agent Specifications

### 1. io_agent (I/O Adapter)

**Purpose:** Pure I/O relay - NO business logic

**Responsibilities:**
- **Input:** Detect channel type (voice/chat/api)
- **Input:** Normalize format to standard message structure
- **Output:** Format responses per channel:
  - **Voice:** SSML with prosody tags
  - **Chat:** Adaptive Cards, rich markdown
  - **API:** Structured JSON

**NOT Responsible For:**
- Routing decisions (that's supervisor)
- Context retrieval (that's context_agent)
- Response compilation (that's coherence_agent)

**YAML Skeleton:**
```yaml
metadata:
  id: io_agent
  name: "I/O Adapter Agent"
  version: "0.1.0"
  type: platform
  description: "Channel detection and format adaptation"
  
spec:
  workflow:
    type: langgraph_stateful
    
    nodes:
      - id: detect_channel
        type: tool
        tool: channel_detector
        
      - id: normalize_input
        type: tool
        tool: input_normalizer
        
      - id: format_output
        type: tool
        tool: output_formatter
        
    edges:
      - from: START
        to: detect_channel
        
      - from: detect_channel
        to: normalize_input
        
      - from: normalize_input
        to: supervisor_agent  # Hand off
        
      - from: supervisor_agent  # Receives final
        to: format_output
        
      - from: format_output
        to: END
```

**MCP Tools Required:**
```python
# backend/mcp/tools/io_tools.py

@mcp_tool
async def channel_detector(
    message: str,
    metadata: Dict
) -> ChannelType:
    """Detect input channel: voice, chat, or api"""
    pass

@mcp_tool
async def input_normalizer(
    raw_input: Any,
    channel: ChannelType
) -> NormalizedMessage:
    """Normalize input to standard format"""
    pass

@mcp_tool
async def output_formatter(
    content: str,
    channel: ChannelType,
    metadata: Dict
) -> FormattedOutput:
    """Format output for target channel"""
    # Voice: Add SSML tags
    # Chat: Add Adaptive Card structure
    # API: Structure as JSON
    pass
```

**State Schema:**
```python
class IOState(TypedDict):
    """io_agent state"""
    channel: str  # "voice" | "chat" | "api"
    raw_input: Any
    normalized_message: str
    session_id: str
    user_id: str
    timestamp: str
    
    # Output state
    raw_response: str
    formatted_output: Any  # SSML | AdaptiveCard | JSON
```

---

### 2. supervisor_agent (Orchestrator)

**Purpose:** The multi-agent orchestration brain

**Responsibilities:**
- **Routing:** Determine which worker agent(s) to call
- **State Management:** Manage conversation flow state
- **Decision Making:** Choose actions based on user intent
- **Redis Integration:** Load/save session state via context_agent

**NOT Responsible For:**
- I/O formatting (that's io_agent)
- Historical context (that's context_agent)
- Response compilation (that's coherence_agent)

**YAML Skeleton:**
```yaml
metadata:
  id: supervisor_agent
  name: "Supervisor Agent"
  version: "0.1.0"
  type: platform
  description: "Multi-agent orchestrator and state manager"
  
spec:
  workflow:
    type: langgraph_stateful
    
    nodes:
      - id: load_context
        type: delegate
        delegate_to: context_agent
        
      - id: analyze_intent
        type: llm
        model: claude-sonnet-4
        prompt: |
          Based on this normalized message and context,
          determine which worker agents to invoke.
          
          Available workers: pm_agent, qa_agent, ticket_agent
          
          Message: {message}
          Context: {context}
        
      - id: route_to_workers
        type: parallel_delegate
        # Dynamically routes to 1+ workers
        
      - id: save_state
        type: delegate
        delegate_to: context_agent
        
    edges:
      - from: START
        to: load_context
        
      - from: load_context
        to: analyze_intent
        
      - from: analyze_intent
        to: route_to_workers
        condition: has_workers  # Conditional edge
        
      - from: route_to_workers
        to: coherence_agent  # Hand off responses
        
      - from: coherence_agent  # Receives compiled output
        to: save_state
        
      - from: save_state
        to: END
```

**MCP Tools Required:**
```python
# backend/mcp/tools/supervisor_tools.py

@mcp_tool
async def worker_router(
    intent: str,
    available_workers: List[str]
) -> List[str]:
    """Determine which workers to invoke"""
    pass

@mcp_tool
async def parallel_worker_executor(
    workers: List[str],
    message: str,
    context: Dict
) -> List[WorkerResponse]:
    """Execute multiple workers in parallel"""
    # Returns list of (worker_id, response, latency)
    pass
```

**State Schema:**
```python
class SupervisorState(TypedDict):
    """supervisor_agent state"""
    session_id: str
    user_id: str
    normalized_message: str
    conversation_context: Dict  # From context_agent
    
    # Intent analysis
    detected_intent: str
    confidence: float
    target_workers: List[str]
    
    # Worker responses
    worker_responses: List[Dict]
    compiled_response: str  # From coherence_agent
    
    # Metadata
    turn_number: int
    timestamp: str
```

---

### 3. context_agent (Memory)

**Purpose:** "Context and state are paramount to user experience"

**Responsibilities:**
- **Session State (Redis):**
  - Current conversation messages
  - Active workers
  - Pending actions
  - Channel type
  - TTL: 1 hour
  
- **User Context (PostgreSQL):**
  - User profile (name, email, preferences)
  - Conversation history (all sessions)
  - Created artifacts (stories, tickets)
  - Interaction patterns
  - Persistent, queryable

- **Context Enrichment:**
  - Add historical context to incoming messages
  - Provide "You mentioned X last week" insights

**NOT Responsible For:**
- Routing (that's supervisor)
- Response formatting (that's io_agent)
- Response compilation (that's coherence_agent)

**YAML Skeleton:**
```yaml
metadata:
  id: context_agent
  name: "Context Agent"
  version: "0.1.0"
  type: platform
  description: "Session state and user context manager"
  
spec:
  workflow:
    type: langgraph_stateful
    
    nodes:
      - id: load_session_state
        type: tool
        tool: redis_session_loader
        
      - id: load_user_context
        type: tool
        tool: postgres_user_loader
        
      - id: enrich_message
        type: llm
        model: claude-sonnet-4
        prompt: |
          Enrich this message with relevant context.
          
          Current message: {message}
          Session history: {session}
          User profile: {profile}
          Past artifacts: {artifacts}
          
          Provide enriched context summary.
        
      - id: save_session_state
        type: tool
        tool: redis_session_saver
        
      - id: save_user_context
        type: tool
        tool: postgres_user_saver
        
    edges:
      - from: START
        to: load_session_state
        
      - from: load_session_state
        to: load_user_context
        
      - from: load_user_context
        to: enrich_message
        condition: has_history  # Skip if new user
        
      - from: enrich_message
        to: END  # Return enriched context
        
      # Separate save flow
      - from: START
        to: save_session_state
        condition: save_mode
        
      - from: save_session_state
        to: save_user_context
        
      - from: save_user_context
        to: END
```

**MCP Tools Required:**
```python
# backend/mcp/tools/context_tools.py

@mcp_tool
async def redis_session_loader(
    session_id: str
) -> SessionState:
    """Load ephemeral session state from Redis"""
    # Returns: messages, active_workers, channel, metadata
    pass

@mcp_tool
async def redis_session_saver(
    session_id: str,
    state: SessionState
) -> bool:
    """Save session state to Redis with 1h TTL"""
    pass

@mcp_tool
async def postgres_user_loader(
    user_id: str
) -> UserContext:
    """Load persistent user context from PostgreSQL"""
    # Returns: profile, history, artifacts, preferences
    pass

@mcp_tool
async def postgres_user_saver(
    user_id: str,
    context: UserContext
) -> bool:
    """Save user context to PostgreSQL"""
    pass

@mcp_tool
async def context_enricher(
    message: str,
    session: SessionState,
    user: UserContext
) -> EnrichedContext:
    """Add relevant historical context to message"""
    pass
```

**State Schema:**
```python
class ContextState(TypedDict):
    """context_agent state"""
    session_id: str
    user_id: str
    
    # Session state (Redis)
    session_messages: List[Dict]
    active_workers: List[str]
    channel: str
    session_metadata: Dict
    
    # User context (PostgreSQL)
    user_profile: Dict
    conversation_history: List[Dict]
    created_artifacts: List[Dict]
    preferences: Dict
    
    # Enrichment
    enriched_context: str
    relevant_history: List[str]
```

**Storage Architecture:**
```
┌─────────────────────────────────────────┐
│         Redis (Session State)           │
├─────────────────────────────────────────┤
│ Key: session:{session_id}               │
│ Value: {                                │
│   messages: [...],                      │
│   active_workers: [...],                │
│   channel: "voice",                     │
│   metadata: {...}                       │
│ }                                       │
│ TTL: 3600 seconds (1 hour)              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│      PostgreSQL (User Context)          │
├─────────────────────────────────────────┤
│ Table: users                            │
│  - user_id (PK)                         │
│  - name, email, created_at              │
│  - preferences (JSONB)                  │
│                                         │
│ Table: conversation_history             │
│  - id (PK)                              │
│  - user_id (FK)                         │
│  - session_id                           │
│  - messages (JSONB)                     │
│  - timestamp                            │
│                                         │
│ Table: artifacts                        │
│  - id (PK)                              │
│  - user_id (FK)                         │
│  - type (story/ticket/etc)              │
│  - content (JSONB)                      │
│  - created_at                           │
└─────────────────────────────────────────┘
```

---

### 4. coherence_agent (Compiler)

**Purpose:** Multi-worker response coordination

**Responsibilities:**
- **Buffer:** Wait for async worker responses
- **Deduplicate:** Remove redundant information
- **Resolve Conflicts:** Handle contradictory responses
- **Compile:** Create coherent, unified output

**Why Critical:**
Without coherence_agent:
```
User: "What should I work on today?"
supervisor → pm_agent (2s) → "3 stories"
supervisor → ticket_agent (5s) → "2 bugs"
supervisor → qa_agent (3s) → "1 test"

[3 separate messages arrive at different times]
User: "This is confusing..."
```

With coherence_agent:
```
User: "What should I work on today?"
supervisor → [pm, ticket, qa agents in parallel]
coherence_agent → waits 10s, receives all 3
coherence_agent → compiles:
  "Based on your workload: 2 critical bugs (highest priority),
   1 failing test, and 3 backlog stories. Start with the bugs."

User: "Perfect, thanks!"
```

**YAML Skeleton:**
```yaml
metadata:
  id: coherence_agent
  name: "Coherence Agent"
  version: "0.1.0"
  type: platform
  description: "Multi-worker response compiler"
  
spec:
  workflow:
    type: langgraph_stateful
    
    nodes:
      - id: collect_responses
        type: buffer
        timeout: 10  # Wait up to 10s for all workers
        
      - id: deduplicate
        type: tool
        tool: response_deduplicator
        
      - id: resolve_conflicts
        type: llm
        model: claude-sonnet-4
        prompt: |
          Multiple agents provided these responses.
          Some may contradict or overlap.
          
          Responses: {responses}
          
          Create a coherent, unified response that:
          1. Resolves any conflicts
          2. Removes duplication
          3. Prioritizes information logically
          4. Maintains natural flow
        
      - id: compile_output
        type: tool
        tool: response_compiler
        
    edges:
      - from: START
        to: collect_responses
        
      - from: collect_responses
        to: deduplicate
        
      - from: deduplicate
        to: resolve_conflicts
        condition: has_conflicts
        
      - from: deduplicate
        to: compile_output
        condition: no_conflicts
        
      - from: resolve_conflicts
        to: compile_output
        
      - from: compile_output
        to: END
```

**MCP Tools Required:**
```python
# backend/mcp/tools/coherence_tools.py

@mcp_tool
async def response_buffer(
    worker_ids: List[str],
    timeout_seconds: int = 10
) -> List[WorkerResponse]:
    """Wait for multiple worker responses"""
    # Collects responses as they arrive
    # Returns after timeout OR all workers respond
    pass

@mcp_tool
async def response_deduplicator(
    responses: List[WorkerResponse]
) -> List[WorkerResponse]:
    """Remove duplicate information across responses"""
    # Uses semantic similarity to detect duplicates
    pass

@mcp_tool
async def conflict_detector(
    responses: List[WorkerResponse]
) -> List[Conflict]:
    """Detect contradictory information"""
    # E.g., pm_agent says "3 stories" but qa_agent says "0 stories"
    pass

@mcp_tool
async def response_compiler(
    responses: List[WorkerResponse],
    conflicts_resolved: bool
) -> CompiledResponse:
    """Compile into coherent final output"""
    pass
```

**State Schema:**
```python
class CoherenceState(TypedDict):
    """coherence_agent state"""
    session_id: str
    user_id: str
    
    # Input
    worker_responses: List[Dict]  # From supervisor
    expected_workers: List[str]
    timeout_seconds: int
    
    # Processing
    collected_responses: List[Dict]
    duplicates_removed: List[Dict]
    detected_conflicts: List[Dict]
    conflicts_resolved: bool
    
    # Output
    compiled_response: str
    response_metadata: Dict  # Which workers contributed
```

**Timeout Strategy:**
```python
# Dynamic timeouts per worker type
WORKER_TIMEOUTS = {
    "pm_agent": 30,      # Complex Notion queries
    "qa_agent": 15,      # Test status checks
    "ticket_agent": 20,  # GitHub API calls
    "governance_agent": 5  # Fast PII checks
}

# Coherence waits for max timeout OR all workers
timeout = max([WORKER_TIMEOUTS[w] for w in expected_workers])
```

---

## MCP Tools Architecture

### Tool Organization

```
backend/mcp/tools/
├── __init__.py
├── io_tools.py          # io_agent tools
│   ├── channel_detector
│   ├── input_normalizer
│   └── output_formatter
│
├── supervisor_tools.py  # supervisor_agent tools
│   ├── worker_router
│   └── parallel_worker_executor
│
├── context_tools.py     # context_agent tools
│   ├── redis_session_loader
│   ├── redis_session_saver
│   ├── postgres_user_loader
│   ├── postgres_user_saver
│   └── context_enricher
│
├── coherence_tools.py   # coherence_agent tools
│   ├── response_buffer
│   ├── response_deduplicator
│   ├── conflict_detector
│   └── response_compiler
│
└── schemas.py           # Pydantic models for all tools
```

### Tool Registration Pattern

```python
# backend/main.py

from mcp.tools import (
    io_tools,
    supervisor_tools,
    context_tools,
    coherence_tools
)

# Register all system agent tools
app.include_router(io_tools.router, prefix="/api/tools/io", tags=["io"])
app.include_router(supervisor_tools.router, prefix="/api/tools/supervisor", tags=["supervisor"])
app.include_router(context_tools.router, prefix="/api/tools/context", tags=["context"])
app.include_router(coherence_tools.router, prefix="/api/tools/coherence", tags=["coherence"])
```

---

## Integration with Marshal Agent

### Discovery Pattern

Marshal Agent automatically loads system agents from YAML:

```
agents/
├── io_agent.agent.yaml
├── supervisor_agent.agent.yaml
├── context_agent.agent.yaml
├── coherence_agent.agent.yaml
│
└── workers/  # Customer agents
    ├── pm_agent.agent.yaml
    ├── qa_agent.agent.yaml
    └── ticket_agent.agent.yaml
```

### System Agent Flag

```yaml
# All system agents have this metadata
metadata:
  type: platform  # vs "worker"
  managed_by: marshal
  hot_reload: true
  health_check: true
```

### Validation

Marshal validates:
- ✅ All 4 system agents present
- ✅ Required MCP tools available
- ✅ Redis/PostgreSQL connections healthy
- ✅ State schemas compatible
- ❌ Blocks startup if any missing

---

## State Management

### State Flow

```
1. io_agent: IOState
        ↓
2. supervisor_agent: SupervisorState
        ↓ (parallel)
3a. context_agent: ContextState
3b. Worker agents: WorkerState
        ↓
4. coherence_agent: CoherenceState
        ↓
5. io_agent: IOState (output)
```

### State Persistence

| Agent | State Storage | Lifetime | Why |
|-------|---------------|----------|-----|
| io_agent | In-memory | Request scope | Ephemeral I/O |
| supervisor_agent | Redis | Session (1h) | Multi-turn context |
| context_agent | Redis + PostgreSQL | Session + Persistent | User memory |
| coherence_agent | In-memory | Request scope | Response compilation |

---

## Error Handling

### Failure Modes

**io_agent fails:**
```
- Fallback to plain text output
- Log error to context_agent
- Notify observability_agent (future)
```

**supervisor_agent fails:**
```
- Direct routing to default worker (pm_agent)
- Log critical error
- Alert escalation_agent (future)
```

**context_agent fails:**
```
- Continue without context enrichment
- Treat as new user/session
- Log warning
```

**coherence_agent fails:**
```
- Return first worker response
- Log warning about missing coherence
```

### Circuit Breaker

```python
# Each agent implements circuit breaker
MAX_FAILURES = 5
FAILURE_WINDOW = 60  # seconds

if agent.failures > MAX_FAILURES in FAILURE_WINDOW:
    agent.state = "CIRCUIT_OPEN"
    # Route around failed agent
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| io_agent latency | <100ms | Input normalization + output formatting |
| supervisor_agent latency | <500ms | Context load + routing decision |
| context_agent latency | <200ms | Redis + PostgreSQL queries |
| coherence_agent latency | <timeout | Dynamic based on workers |
| **Total e2e latency** | <35s | User input → formatted output |

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)

**Deliverables:**
- ✅ io_agent YAML + implementation
- ✅ supervisor_agent YAML + implementation
- ✅ context_agent YAML + implementation
- ✅ coherence_agent YAML + implementation
- ✅ All MCP tools implemented
- ✅ Redis integration
- ✅ PostgreSQL schema
- ✅ Marshal integration
- ✅ Unit tests (>80% coverage)

**Files to Create:**
```
agents/
├── io_agent.agent.yaml
├── supervisor_agent.agent.yaml
├── context_agent.agent.yaml
├── coherence_agent.agent.yaml
│
├── workers/
│   └── io_agent.py
│   └── supervisor_agent.py
│   └── context_agent.py
│   └── coherence_agent.py

backend/mcp/tools/
├── io_tools.py
├── supervisor_tools.py
├── context_tools.py
├── coherence_tools.py
└── schemas.py

tests/unit/agents/
├── test_io_agent.py
├── test_supervisor_agent.py
├── test_context_agent.py
└── test_coherence_agent.py
```

### Phase 2: Integration Testing (Week 2)

**Deliverables:**
- ✅ E2E voice flow test
- ✅ E2E chat flow test
- ✅ Multi-worker coordination test
- ✅ Context persistence test
- ✅ Performance benchmarks
- ✅ Error handling validation

### Phase 3: Production Hardening (Week 3)

**Deliverables:**
- ✅ Circuit breakers
- ✅ Rate limiting
- ✅ Observability hooks
- ✅ Admin UI for agent status
- ✅ Health check dashboards

---

## Success Criteria

### Functional Requirements

- ✅ User can start voice conversation
- ✅ io_agent detects channel=voice
- ✅ supervisor_agent routes to 2+ workers
- ✅ context_agent enriches with "Sarah has created 12 stories"
- ✅ Workers respond async at different times
- ✅ coherence_agent waits, compiles coherent response
- ✅ io_agent formats as SSML for voice
- ✅ User hears natural, contextual response
- ✅ Conversation state persists in Redis
- ✅ Next message in session has full context

### Non-Functional Requirements

- ✅ <35s e2e latency (p95)
- ✅ >99.5% system agent availability
- ✅ <1s hot-reload time
- ✅ Zero state loss on agent restart (Redis/PostgreSQL)

---

## Open Questions

1. **Supervisor Routing Logic:**
   - LLM-based intent classification OR rule-based?
   - **Recommendation:** Start LLM-based, add rules for performance

2. **Coherence Timeout:**
   - Fixed 10s OR dynamic per worker?
   - **Recommendation:** Dynamic based on worker history

3. **Context Enrichment:**
   - Always enrich OR only when relevant?
   - **Recommendation:** Always enrich, but limit to top 3 relevant items

4. **State Schema Versions:**
   - How to handle schema evolution?
   - **Recommendation:** Include version in state, migrate on load

5. **Redis vs PostgreSQL Split:**
   - Is this the right boundary?
   - **Recommendation:** Yes - ephemeral session vs persistent user

---

## Approval Required

**This design requires approval before implementation.**

Key decisions to confirm:
- ✅ 4 system agents (io, supervisor, context, coherence)
- ✅ Redis for session state, PostgreSQL for user context
- ✅ All tools at MCP server level
- ✅ Marshal manages all agents
- ✅ LangGraph for orchestration

**Apply this design, or do you have notes?**

---

**Document Status:** Ready for Review  
**Next Steps:** Create YAML files + MCP tools  
**Maintainer:** Agent Foundry Team  
**Version:** 0.8.0-dev
