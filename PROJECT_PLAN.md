# Engineering Department — Project Plan

## Executive Summary
**Program:** Agentic Engineering Department  
**Status:** Phase 3 Complete - MCP Tools & Basic Agent Integration Operational  
**Architecture:** Next.js UI + PM Agent + MCP Server (Notion/GitHub/Audit)  
**Updated:** November 9, 2025

## Current Implementation Phase

### ✅ Phase 1: Foundation (COMPLETE)
- Python 3.12 environment with venv
- FastAPI MCP server scaffold
- Next.js 14.2.33 UI with App Router
- Environment configuration (.env.local)
- Basic health/status endpoints

### ✅ Phase 2: MCP Tool Layer (COMPLETE)
- **NotionTool**: Story CRUD with idempotency protection
- **GitHubTool**: Issue/PR creation with metadata embedding
- **AuditTool**: JSONL append-only logs with query interface
- Schema-first design with Pydantic models
- REST API endpoints with OpenAPI compatibility

### ✅ Phase 3: Agent Integration (COMPLETE - Simplified)
- SimplePMAgent implemented (avoiding LangGraph compatibility issues)
- Message parsing and task extraction
- Story → Issue creation workflow
- E2E test suite operational
- Idempotency protection verified

### 🔄 Phase 4: Production Hardening (IN PLANNING)
- WebSocket/SSE transport for real-time updates
- Conversation Synthesis Agent extraction
- Redis integration for session state
- OpenTelemetry instrumentation
- Supervisor agent pool architecture

### 📋 Phase 5: Multi-Agent Orchestration (FUTURE)
- LangGraph integration (pending dependency resolution)
- Engineer agents (BE/FE/ML/PE/DATA)
- QA agent with automated verification
- SRE/AIOps agents for monitoring
- Judge/ARB for conflict resolution

## Technical Architecture

### Current Stack
```
[User] 
   ↓ (HTTP - for now)
[Next.js Web UI (Chat + Backlog + Settings)]
   ↓ (REST API)
[MCP Server v0.2.0 (FastAPI)]
   ├── NotionTool → Notion API
   ├── GitHubTool → GitHub API
   └── AuditTool → JSONL Files
   
[SimplePMAgent] → MCP Server (via HTTP)
```

### Target Architecture (Unchanged)
```
[User] 
   ↓ (WebSocket/SSE)
[Next.js Web UI]
   ↓
[Conversation Agent (per user)]
   ↓
[Supervisor Pool (LangGraph)]
   ↓
[MCP Server + Tools]
   ↓
[External Systems]
```

## Implementation Decisions

### Architectural Decisions Made

1. **Simplified Agent Approach**
   - Decision: Implement SimplePMAgent without LangGraph
   - Rationale: Avoid pydantic/langsmith compatibility issues
   - Impact: Faster delivery, easier debugging, clear upgrade path

2. **Idempotency Strategy**
   - Decision: Content-based hashing at tool level
   - Implementation: SHA256 hash of title+epic
   - Storage: In-memory cache (Redis planned)

3. **Audit Architecture**
   - Decision: JSONL append-only files
   - Location: `/audit/actions_YYYYMMDD.jsonl`
   - Query: Built-in filtering and pagination

4. **Schema Enforcement**
   - Decision: Pydantic models for all I/O
   - Benefit: Type safety, automatic validation
   - Documentation: Auto-generated OpenAPI schemas

### Technical Debt Acknowledged

1. **LangGraph Compatibility**
   - Issue: ForwardRef._evaluate() errors with current versions
   - Mitigation: SimplePMAgent provides functionality
   - Resolution: Pin compatible versions or wait for fixes

2. **Real-time Transport**
   - Current: Polling/REST only
   - Needed: WebSocket or SSE
   - Timeline: Phase 4 priority

3. **Memory Persistence**
   - Current: In-memory only
   - Needed: Redis for session state
   - Impact: Server restarts lose context

## Milestone Schedule

### M0: Foundation ✅ COMPLETE
- MCP server operational
- Basic UI deployed
- Environment configured
- Tools initialized

### M1: Core Workflow ✅ COMPLETE
- Story creation working
- GitHub integration active
- Audit logging functional
- E2E tests passing

### M2: Agent Intelligence (CURRENT)
- [x] Basic PM agent operational
- [ ] Conversation memory
- [ ] Context preservation
- [ ] Multi-turn interactions

### M3: Production Features (Q4 2025)
- [ ] WebSocket transport
- [ ] Redis integration
- [ ] OpenTelemetry traces
- [ ] Error recovery
- [ ] Rate limiting

### M4: Scale & Multi-Agent (Q1 2026)
- [ ] Supervisor pool
- [ ] Engineer agents
- [ ] QA automation
- [ ] Load balancing
- [ ] Multi-tenant isolation

## Risk Register

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| LangGraph compatibility | High | SimplePMAgent alternative | ✅ Mitigated |
| Notion API changes | Medium | Schema discovery at startup | 🔄 Monitoring |
| Token leakage | High | Redaction middleware | ✅ Implemented |
| Rate limits | Medium | Backoff + idempotency | ✅ Implemented |
| Memory loss | Low | Redis integration planned | 📋 Planned |

## Success Metrics

### Current Performance
- Story creation: ~2-3 seconds
- Issue creation: ~1-2 seconds  
- Idempotency check: <100ms
- Audit write: <10ms

### Target SLOs
- API latency p95: <500ms
- Story creation success: >99%
- Audit completeness: 100%
- Idempotency accuracy: 100%

## Resource Requirements

### Current Team
- 1x Full-stack engineer (You)
- 1x AI assistant (Me)

### Infrastructure
- Local development environment
- GitHub personal account
- Notion workspace
- OpenAI API access

### Estimated Costs
- OpenAI API: ~$5-10/month (dev)
- Notion API: Free tier
- GitHub: Free tier
- Infrastructure: Local only

## Definition of Done

### Phase 3 Completion Criteria ✅
- [x] MCP tools implemented with schemas
- [x] PM agent can create stories
- [x] GitHub issues created with links
- [x] Idempotency protection working
- [x] Audit logs queryable
- [x] E2E tests passing

### Phase 4 Entry Criteria
- [ ] WebSocket server endpoint
- [ ] Client reconnection logic
- [ ] Redis connection pool
- [ ] Session state management
- [ ] Real-time event streaming

## Next Actions

### Immediate (This Week)
1. Wire Next.js chat UI to SimplePMAgent
2. Implement WebSocket transport layer
3. Add Redis for conversation memory
4. Create streaming response handler

### Short-term (This Month)
1. Extract Conversation Agent pattern
2. Implement session lifecycle manager
3. Add OpenTelemetry instrumentation
4. Build supervisor agent prototype

### Long-term (Q1 2026)
1. Resolve LangGraph compatibility
2. Implement full multi-agent orchestra
3. Add QA and SRE agents
4. Deploy to cloud infrastructure

## Communication Plan

### Documentation
- Current State: Updated after each session
- Lessons Learned: Captured continuously
- ADRs: Created for major decisions
- API Docs: Auto-generated from schemas

### Stakeholder Updates
- Daily: Current State document
- Weekly: Progress against plan
- Monthly: Architecture review

## Appendix: Quick Commands

```bash
# Start MCP Server
cd "/Users/nate/Development/1. Projects/Engineering Department"
source venv/bin/activate
python mcp_server.py

# Run E2E Tests (separate terminal)
source venv/bin/activate
python test_e2e.py

# Start Next.js UI
npm run dev

# Check Integration Status
curl http://localhost:8001/api/status
```

---

*Last Updated: November 9, 2025*  
*Next Review: End of Phase 4*
