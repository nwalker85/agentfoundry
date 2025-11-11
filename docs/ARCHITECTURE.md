# Engineering Department — Architecture Documentation

**Status:** Phase 3 Complete  
**Last Updated:** November 10, 2025  
**Alignment:** Enterprise Multi-Platform Architecture Scaffold v1.0

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Principles](#architectural-principles)
3. [Technology Stack](#technology-stack)
4. [Key Architectural Decisions](#key-architectural-decisions)
5. [Observability & Telemetry](#observability--telemetry)
6. [Lessons Learned](#lessons-learned)
7. [Future Architecture](#future-architecture)

---

## System Overview

### Current Architecture (Phase 3)

```
┌────────────────────────────────────────────────────────────┐
│ User / Client                                               │
└───────────────────────┬────────────────────────────────────┘
                        │ HTTP / REST
                        ↓
┌────────────────────────────────────────────────────────────┐
│ Next.js Web UI (Port 3000)                                 │
│ ├── Chat Interface (planned)                               │
│ ├── Backlog View (planned)                                 │
│ └── Settings (planned)                                     │
└───────────────────────┬────────────────────────────────────┘
                        │ REST API
                        ↓
┌────────────────────────────────────────────────────────────┐
│ MCP Server v0.2.0 (FastAPI - Port 8001)                   │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ API Endpoints                                        │  │
│ │ ├── GET  /                    (health check)        │  │
│ │ ├── GET  /api/status          (integration status)  │  │
│ │ ├── POST /api/tools/notion/*  (story operations)    │  │
│ │ ├── POST /api/tools/github/*  (issue operations)    │  │
│ │ └── GET  /api/tools/audit/*   (audit query)         │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ MCP Tools Layer                                      │  │
│ │ ├── NotionTool   (mcp/tools/notion.py)              │  │
│ │ ├── GitHubTool   (mcp/tools/github.py)              │  │
│ │ └── AuditTool    (mcp/tools/audit.py)               │  │
│ └──────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐  │
│ │ LangGraph PMAgent (agent/pm_graph.py)                │  │
│ │ ├── Message parsing                                  │  │
│ │ ├── Epic/story extraction                            │  │
│ │ └── Workflow orchestration                           │  │
│ └──────────────────────────────────────────────────────┘  │
└───────────┬──────────────┬──────────────┬─────────────────┘
            │              │              │
            ↓              ↓              ↓
    ┌───────────┐  ┌──────────┐  ┌──────────────┐
    │ Notion    │  │ GitHub   │  │ Local Audit  │
    │ API       │  │ API      │  │ JSONL Logs   │
    └───────────┘  └──────────┘  └──────────────┘
```

### Target Architecture (Phase 5)

```
┌────────────────────────────────────────────────────────────┐
│ User / Client                                               │
└───────────────────────┬────────────────────────────────────┘
                        │ WebSocket / SSE
                        ↓
┌────────────────────────────────────────────────────────────┐
│ Next.js Web UI                                             │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────┐
│ Conversation Agent (per user session)                      │
│ ├── Context preservation                                   │
│ ├── Multi-turn dialogue                                    │
│ └── Session memory (Redis)                                 │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────┐
│ Supervisor Pool (LangGraph)                                │
│ ├── PM Agent         (task planning)                       │
│ ├── Engineer Agents  (BE/FE/ML/PE/DATA)                    │
│ ├── QA Agent         (verification)                        │
│ ├── SRE Agent        (monitoring)                          │
│ └── Judge/ARB        (conflict resolution)                 │
└───────────────────────┬────────────────────────────────────┘
                        │
                        ↓
┌────────────────────────────────────────────────────────────┐
│ MCP Server + Tools                                         │
└───────────┬──────────────┬──────────────┬─────────────────┘
            │              │              │
            ↓              ↓              ↓
    ┌───────────┐  ┌──────────┐  ┌──────────────┐
    │ External  │  │ External │  │ Observability│
    │ Systems   │  │ Systems  │  │ Stack        │
    └───────────┘  └──────────┘  └──────────────┘
```

---

## Architectural Principles

### 1. Schema-First Design
- All API endpoints defined with Pydantic models
- Type safety enforced at compile and runtime
- Automatic validation prevents invalid data
- OpenAPI schemas auto-generated from models

### 2. Idempotency by Default
- Content-based hashing for deduplication
- Idempotency keys stored and checked
- Safe to retry any operation
- Prevents duplicate resources

### 3. Audit Everything
- All actions logged to JSONL append-only files
- Request tracking with correlation IDs
- Input/output hashing for integrity
- Queryable audit trail

### 4. Separation of Concerns
- **Tools Layer**: External integrations (Notion, GitHub)
- **Agent Layer**: Business logic and orchestration
- **API Layer**: HTTP endpoints and validation
- **UI Layer**: User interface and presentation

### 5. Fail-Safe Architecture
- Graceful error handling
- No silent failures
- Comprehensive logging
- Clear error messages

---

## Technology Stack

### Backend
- **Runtime**: Python 3.9.6
- **Web Framework**: FastAPI 0.115.5
- **Server**: Uvicorn 0.32.1 (ASGI)
- **Data Validation**: Pydantic 2.10.3
- **HTTP Client**: httpx 0.27.2
- **Async I/O**: aiofiles 24.1.0

### Agent Framework
- **LangChain**: 0.2.16
- **LangGraph**: 0.2.39 ✅ (operational)
- **OpenAI SDK**: 1.57.0

### Frontend
- **Framework**: Next.js 14.2.33 (App Router)
- **Runtime**: Node.js (via npm)
- **Styling**: Tailwind CSS

### External Services
- **Task Management**: Notion API
- **Source Control**: GitHub API
- **AI/ML**: OpenAI GPT-4

### Development Tools
- **Testing**: pytest 8.3.4, pytest-asyncio 0.24.0
- **Code Quality**: black 24.10.0, ruff 0.8.2, mypy 1.13.0
- **Environment**: python-dotenv 1.0.1

---

## Key Architectural Decisions

### Decision 1: LangGraph PM Agent

**Context:** Initially faced LangGraph compatibility issues with dependency versions

**Decision:** Persisted with LangGraph PMAgent, resolved dependency conflicts

**Rationale:**
- AI-powered understanding is core value proposition
- Multi-turn clarification superior to regex parsing
- Validation and planning pipeline worth complexity
- Fixed pydantic/langsmith `ForwardRef._evaluate()` errors

**Impact:**
- ✅ LangGraph PMAgent operational (v0.4.0)
- ✅ GPT-4 powered task understanding
- ✅ Multi-step clarification workflow
- ✅ Validation and planning pipeline
- 📊 Response time: 5-10s (vs 2-3s for simple agent)
- 💰 Cost: ~$0.01-0.02 per story (GPT-4 tokens)

### Decision 2: Next.js Over Streamlit

**Context:** Need production-ready UI framework

**Decision:** Use Next.js with App Router instead of Streamlit

**Rationale:**
- Streamlit not suitable for production
- Next.js provides enterprise-grade features
- TypeScript for type safety
- Better accessibility and governance
- No rework needed for production

**Impact:**
- ✅ Production-ready foundation
- ✅ Modern development experience
- ⚠️ More complex than Streamlit
- ⚠️ Requires frontend expertise

### Decision 3: Content-Based Idempotency

**Context:** Preventing duplicate story/issue creation

**Decision:** SHA256 hash of (title + epic) as idempotency key

**Rationale:**
- Deterministic and consistent
- No database required for PoC
- Works across server restarts (when stored)
- Simple implementation

**Implementation:**
```python
import hashlib

def generate_idempotency_key(title: str, epic: str) -> str:
    content = f"{title}|{epic}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

**Impact:**
- ✅ Prevents duplicates
- ✅ Fast (<100ms check)
- ⚠️ In-memory cache lost on restart
- 📋 Redis migration planned for Phase 4

### Decision 4: JSONL Audit Logs

**Context:** Need compliance-grade audit trail

**Decision:** Append-only JSONL files with async writes

**Rationale:**
- Simple and reliable
- No database required
- Human-readable for debugging
- Append-only ensures integrity
- Easy to migrate to OTel later

**Implementation:**
- File pattern: `/audit/actions_YYYYMMDD.jsonl`
- Daily rotation
- Async writes (non-blocking)
- Queryable via API

**Impact:**
- ✅ Working audit trail
- ✅ No database overhead
- ⚠️ Local storage only
- 📋 OTel migration planned

### Decision 5: OpenAPI-First MCP Tools

**Context:** Need predictable agent behavior

**Decision:** Define all MCP endpoints with Pydantic models first

**Rationale:**
- Auto-generated OpenAPI schemas
- Prevents tool drift
- Type safety guarantees
- Self-documenting APIs

**Impact:**
- ✅ Clear tool contracts
- ✅ Automatic validation
- ✅ Reduced bugs
- ✅ Better DX

---

## Observability & Telemetry

### Current State (Phase 3)

#### Instrumentation
- FastAPI middleware for request tracking
- Request ID generation and propagation
- Response time measurement
- JSONL audit logs

#### Logging
- Console logs for development
- JSONL structured logs for audit
- Correlation IDs for tracing
- No centralized aggregation

#### Metrics
- None (manual observation only)

#### Tracing
- None (single-service architecture)

### Planned Architecture (Phase 4+)

#### Pattern: Collector Sidecar + SDK Instrumentation

```
┌─────────────────────────────────────────────────────────────┐
│ MCP Server (FastAPI)                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ OpenTelemetry SDK (auto-instrumentation)               │ │
│ │ ├── TracerProvider → OTLP → localhost:4317            │ │
│ │ ├── MeterProvider → OTLP → localhost:4317             │ │
│ │ └── LoggerProvider → OTLP → localhost:4317            │ │
│ └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ OTLP
┌───────────────────────────▼─────────────────────────────────┐
│ OTel Collector (sidecar)                                    │
│ ├── Receivers: OTLP (grpc:4317, http:4318)                 │
│ ├── Processors: batch, attributes, redaction, sampling     │
│ └── Exporters: Tempo, Prometheus, Loki, File/Audit         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Grafana LGTM Stack                                          │
│ ├── Tempo (distributed tracing)                            │
│ ├── Mimir (metrics storage)                                │
│ ├── Loki (log aggregation)                                 │
│ └── Grafana (dashboards, alerts, visualization)            │
└─────────────────────────────────────────────────────────────┘
```

#### Instrumentation Strategy

**Layer 1: Automatic Instrumentation**
- FastAPI (HTTP request/response spans)
- httpx (outbound API calls)
- asyncpg (database queries - future)
- Redis (cache operations - future)
- Logging (automatic trace correlation)

**Layer 2: Manual Domain Instrumentation**
- LangGraph agent nodes (understand, plan, act)
- MCP tool invocations
- Idempotency checks
- Audit log writes

**Layer 3: Custom Metrics**
```python
# MCP tool invocation counter
tool_invocation_counter.add(1, {
    "tenant.id": tenant_id,
    "tool.name": "notion.create_story",
    "tool.result": "success",
    "idempotency.hit": "false"
})

# Agent workflow duration
workflow_duration.record(execution_time_ms, {
    "tenant.id": tenant_id,
    "workflow.status": "completed"
})
```

**Layer 4: Structured Logging**
```python
logger.info(
    "story_creation_started",
    tenant_id=tenant_id,
    trace_id=format(span_context.trace_id, '032x'),
    epic_title=request.epic_title,
    story_title=request.story_title
)
```

#### Service Level Objectives (SLOs)

| SLO | Target | Measurement |
|-----|--------|-------------|
| API Latency (p95) | <500ms | HTTP request duration histogram |
| Tool Success Rate | >99.5% | MCP tool invocation counter |
| Workflow Latency (p90) | <30s | End-to-end span duration |

#### Tenant Context Propagation

```python
# Context vars for tenant correlation
tenant_id_context: ContextVar[str] = ContextVar("tenant_id")
scope_id_context: ContextVar[str] = ContextVar("scope_id")

# Middleware extracts from headers
class TenantContextMiddleware:
    async def __call__(self, scope, receive, send):
        tenant_id = extract_from_headers(scope["headers"])
        tenant_id_context.set(tenant_id)
        
        # Inject into OTel span
        span = trace.get_current_span()
        span.set_attribute("tenant.id", tenant_id)
```

#### Audit Log Migration

**Current:** Local JSONL files
**Target:** OTel logs with collector fan-out

**Benefits:**
- Queryable in Grafana Loki
- Compliant file backup (90-day retention)
- Trace correlation for full context
- PII redaction via collector
- Fan-out to SIEM systems

---

## Lessons Learned

### 1. Persistence Pays Off

**Lesson:** Don't give up on core technology choices too easily

**Context:** LangGraph had initial compatibility issues

**Decision:** Debugged and resolved rather than simplifying

**Impact:** Full LangGraph capabilities now operational

### 2. Architectural Continuity

**Lesson:** Choose production-ready tech from day one

**Context:** Initially considered Streamlit for UI

**Decision:** Switched to Next.js early to avoid rework

**Impact:** No migration required for production

### 3. MCP Tool Definition

**Lesson:** Explicit schemas prevent tool drift

**Context:** Agents need predictable tool behavior

**Implementation:** OpenAPI-first with Pydantic models

**Impact:** Fewer bugs, better DX

### 4. Token Handling & Security

**Lesson:** Implement redaction from the start

**Context:** Early logs exposed full API tokens

**Implementation:** Redaction middleware for `*_TOKEN`, `*_KEY`

**Impact:** Security by default

### 5. Notion Schema Volatility

**Lesson:** External APIs change - plan for it

**Context:** Notion API response inconsistencies

**Mitigation:** Dynamic schema discovery at startup + local cache

**Impact:** Resilient to API changes

### 6. Idempotency

**Lesson:** Make idempotency the default

**Context:** Re-runs created duplicate GitHub issues

**Implementation:** Content-based hashing + idempotency keys

**Impact:** Safe to retry operations

### 7. Audit & Observability

**Lesson:** Audit everything from day one

**Context:** Console logs insufficient for debugging

**Implementation:** JSONL append-only logs + correlation IDs

**Impact:** Complete audit trail for compliance

### 8. Prompt Governance

**Lesson:** Version control your prompts

**Context:** LangGraph prompts need tracking for evals

**Implementation:** `policy.py` with template versions

**Impact:** Reproducible agent behavior

### 9. Next.js App Router Discipline

**Lesson:** Follow framework conventions strictly

**Context:** Wrong directory structure caused 404s

**Issue:** Extra nested `app/` directory

**Fix:** Flatten to proper App Router structure

**Impact:** Working routing

### 10. Environment Reprovisioning

**Lesson:** Clean environment > debugging dependency conflicts

**Context:** Pydantic core wheel issues

**Fix:** Rebuild venv from scratch

**Impact:** Stable dependencies

### 11. CLI Output Hygiene

**Lesson:** ASCII over emojis for automation

**Context:** CI/CD encoding issues with emoji indicators

**Fix:** Replace with ASCII in test output

**Impact:** Automation-friendly logs

---

## Security Considerations

### Current Implementations

1. **Token Redaction**
   - Middleware masks `*_TOKEN`, `*_KEY` in logs
   - Prevents accidental exposure

2. **Environment Isolation**
   - All secrets in `.env.local` (git-ignored)
   - `.env.example` for documentation only

3. **Idempotency Keys**
   - Embedded in GitHub issues (non-sensitive)
   - Enables duplicate detection

4. **Audit Integrity**
   - Append-only JSONL files
   - Content hashing for verification
   - Immutable once written

### Planned Enhancements (Phase 4+)

1. **OTel PII Redaction**
   - Collector-level regex filters
   - Email, SSN, credit card patterns
   - API token patterns

2. **Tenant Isolation**
   - Per-tenant data segregation
   - Span attributes for filtering
   - Tenant-aware sampling

3. **Authentication & Authorization**
   - JWT-based auth
   - Role-based access control
   - API key management

---

## Performance Characteristics

### Current Measurements (Phase 3)

| Operation | Latency | Notes |
|-----------|---------|-------|
| Story Creation | 2-3s | Notion API latency |
| Issue Creation | 1-2s | GitHub API latency |
| Idempotency Check | <100ms | In-memory cache |
| Audit Write | <10ms | Async file write |
| Story List Query | 1-2s | Filter complexity dependent |

### Resource Usage

| Resource | Usage | Notes |
|----------|-------|-------|
| Memory | ~150MB | Python + dependencies |
| CPU | <5% idle | 20-30% during requests |
| Disk | <1MB/day | Audit logs |
| Network | ~10KB | Per tool call |

### Scalability Considerations

**Current Bottlenecks:**
- Single-instance server
- In-memory cache (not shared)
- No connection pooling
- Synchronous external API calls (within async context)

**Planned Improvements:**
- Redis for shared cache
- Connection pooling (httpx)
- Horizontal scaling with load balancer
- Async batching for multiple operations

---

## Future Architecture Evolution

### Phase 4: Production Hardening
- WebSocket/SSE for real-time updates
- Redis for session state
- OpenTelemetry full instrumentation
- Container orchestration (Docker Compose → K8s)
- CI/CD pipeline

### Phase 5: Multi-Agent Orchestration
- LangGraph supervisor architecture
- Specialized engineer agents
- QA automation agent
- SRE/monitoring agent
- Conflict resolution (Judge/ARB)

### Outstanding Architectural Questions

1. **Deployment Model**
   - K8s, ECS, or VM-based?
   - Affects collector strategy (sidecar vs daemonset)

2. **Audit Log Storage**
   - Keep JSONL + OTel, or fully migrate?
   - Compliance requirements?

3. **Multi-Tenancy**
   - Database per tenant or schema per tenant?
   - Isolation level requirements?

4. **Gateway Collector**
   - When to introduce centralized aggregation?
   - After horizontal scaling (multiple instances)

5. **Vendor Integrations**
   - Which observability vendors (Datadog, Honeycomb)?
   - Start with LGTM, add on-demand

---

## References

### External Standards
- **Enterprise Multi-Platform Architecture Scaffold v1.0**
- **OpenTelemetry Semantic Conventions**
- **FastAPI Best Practices**
- **LangGraph Architecture Patterns**

### Internal Documentation
- [Project Status](./PROJECT_STATUS.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Artifact Master Index](./artifacts/Artifact_Master_Index.md)

---

**Document Status:** Living document, updated with each phase  
**Next Review:** Phase 4 kickoff  
**Maintainer:** Engineering Department Team

