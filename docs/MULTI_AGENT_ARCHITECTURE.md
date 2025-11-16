# Agent Foundry Multi-Agent Architecture

**Status:** Design Proposal  
**Version:** 0.8.0-dev  
**Last Updated:** November 15, 2025  
**Architecture Pattern:** LangGraph Multi-Agent Orchestration

---

## Executive Summary

This document proposes a sophisticated multi-agent architecture for Agent Foundry that extends beyond simple task execution to include:
- Channel-aware I/O handling (voice SSML, chat adaptive cards)
- Centralized orchestration and state management
- Compliance and security governance
- User context and personalization
- Response coherence across async agents
- System personality control
- Comprehensive observability
- Graceful error handling and human escalation

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Agent Roster](#agent-roster)
3. [Communication Flow](#communication-flow)
4. [State Management](#state-management)
5. [Channel Adaptation](#channel-adaptation)
6. [Personality Modeling](#personality-modeling)
7. [Implementation Roadmap](#implementation-roadmap)

---

## System Overview

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  • Frontend (Next.js): Chat UI + Voice UI                        │
│  • LiveKit: WebRTC Voice Connection                              │
│  • WebSocket: Real-time bidirectional communication              │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                      io_agent (I/O Handler)                      │
│  • Channel Detection (voice|chat|api)                            │
│  • Input Normalization                                           │
│  • Output Formatting:                                            │
│    - Chat → Adaptive Cards, Markdown                             │
│    - Voice → SSML Tags                                           │
│    - API → JSON Responses                                        │
│  • No Business Logic - Pure I/O Relay                            │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ↓
┌──────────────────────────────────────────────────────────────────┐
│                  supervisor_agent (Orchestrator)                 │
│  • LangGraph StateGraph Coordinator                              │
│  • Agent Routing & Task Distribution                             │
│  • State Management (Redis-backed)                               │
│  • Response Aggregation                                          │
│  • Decision Making & Planning                                    │
└────────┬─────────────────────┬──────────────────────────────────┘
         │                     │
         │     ┌───────────────┴───────────────┬─────────────┐
         │     │                               │             │
         ↓     ↓                               ↓             ↓
┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐
│ personality    │  │ context_agent  │  │  governance  │  │  coherence   │
│    _agent      │  │                │  │    _agent    │  │    _agent    │
│                │  │ • User History │  │              │  │              │
│ • Persona      │  │ • CRM Data     │  │ • Compliance │  │ • Buffer     │
│ • Voice Model  │  │ • Preferences  │  │ • PII Filter │  │ • Dedupe     │
│ • Language     │  │ • Context DB   │  │ • Policy     │  │ • Coherence  │
│ • Greeting     │  │                │  │              │  │ • Timing     │
└────────────────┘  └────────────────┘  └──────────────┘  └──────────────┘
         │                     │                │                │
         │                     │                │                │
         └──────────┬──────────┴────────────────┴────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Worker Agent Layer                            │
├──────────────┬──────────────┬──────────────┬──────────────────────┤
│  pm_agent    │ ticket_agent │  qa_agent    │  future_agents...    │
│              │              │              │                      │
│ • Stories    │ • Tickets    │ • Testing    │ • rag_agent (RAG)    │
│ • Backlog    │ • Bugs       │ • Quality    │ • sre_agent (Ops)    │
│ • Planning   │ • Support    │ • Automation │ • data_agent (ETL)   │
└──────────────┴──────────────┴──────────────┴──────────────────────┘
         │                     │                │
         └──────────┬──────────┴────────────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────────────┐
│                   Support Agent Layer                            │
├──────────────┬──────────────────────────────────────────────────┤
│ observability│  exception_escalation_agent                       │
│    _agent    │                                                   │
│              │  • Error Handling & Recovery                      │
│ • Metrics    │  • Human Handoff (HITL)                           │
│ • Logs       │  • Escalation Routing                             │
│ • Traces     │  • Context Preservation                           │
│ • Dashboards │  • Warm Transfer                                  │
│ • Alerts     │  • Human-AI Liaison                               │
└──────────────┴──────────────────────────────────────────────────┘
         │                     │
         └──────────┬──────────┘
                    │
                    ↓
┌──────────────────────────────────────────────────────────────────┐
│                     External Systems                             │
│  • Notion API (Stories)                                          │
│  • GitHub API (Issues)                                           │
│  • User Context Database (SQLite → PostgreSQL)                   │
│  • Document Store (RAG - future)                                 │
│  • Observability Stack (Grafana LGTM)                            │
│  • Human Agent Platform (HITL)                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Roster

[Full agent descriptions with code examples - see complete doc]

### Core Agents (Phase 1-2)
1. **io_agent** - Channel-aware I/O formatting
2. **supervisor_agent** - Orchestration and state management  
3. **context_agent** - User history and CRM functionality
4. **governance_agent** - Compliance and PII filtering

### Quality Agents (Phase 3)
5. **coherence_agent** - Response buffering and compilation
6. **personality_agent** - System persona control

### Support Agents (Phase 4-5)
7. **observability_agent** - Monitoring and telemetry
8. **exception_escalation_agent** - Error handling and HITL

### Worker Agents (Ongoing)
9. **pm_agent** - Story creation (existing)
10. **ticket_agent** - Issue tracking (future)
11. **qa_agent** - Quality assurance (future)
12. **rag_agent** - Document retrieval (future, post-MVP)

---

## Key Design Decisions

### 1. OCEAN Personality Model (Not MBTI)
**Rationale:**
- Continuous 0-1 scale allows fine-tuning
- Better research validity than MBTI discrete types
- Context-adaptive (can adjust mid-conversation)
- Composable traits

### 2. Coherence Agent Buffer Strategy
**Approach:** Dynamic timeout per agent type
- pm_agent: 30s (Notion API calls)
- governance_agent: 5s (pattern matching)
- context_agent: 10s (database query)

### 3. State Management
**Tech Stack:**
- Redis: Session state (conversations, active agents)
- PostgreSQL: User context (history, preferences)
- Rationale: Redis for ephemeral, PG for durable

### 4. Channel Adaptation
**Voice:** SSML tags (prosody, breaks, emphasis)
**Chat:** Adaptive Cards (rich UI elements)
**API:** Structured JSON

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1)
- [x] LiveKit Docker migration
- [ ] Supervisor agent (LangGraph StateGraph)
- [ ] I/O agent (basic chat + voice)
- [ ] Redis state management

### Phase 2: Context & Governance (Week 2)
- [ ] User context agent + PostgreSQL
- [ ] Governance agent (PII filtering)
- [ ] Context enrichment pipeline

### Phase 3: Quality (Week 3)
- [ ] Coherence agent
- [ ] Personality agent (OCEAN)
- [ ] SSML + Adaptive Card formatting

### Phase 4: Support (Week 4)
- [ ] Exception/escalation agent
- [ ] HITL workflow
- [ ] Error recovery

### Phase 5: Observability (Week 5)
- [ ] Real-time dashboard (WebSocket)
- [ ] Grafana LGTM stack
- [ ] Alerting

---

## Open Questions for Discussion

1. **Personality Model:** Approve OCEAN vs MBTI?
2. **State Storage:** Redis vs PostgreSQL for which data?
3. **Coherence Timeouts:** Fixed vs dynamic per agent?
4. **Human Handoff:** Build custom UI or integrate Zendesk?
5. **RAG Priority:** Include in MVP or defer to post-MVP?

---

## Next Steps

**Immediate:**
1. Review architecture with team
2. Prioritize agent implementation order
3. Spike LangGraph multi-agent patterns
4. Design Redis state schema

**This Week (Nov 15-22):**
- Implement supervisor_agent framework
- Build basic io_agent
- Set up Redis
- Deploy observability agent (basic)

---

**Status:** Proposal - Awaiting Approval  
**Owner:** Architecture Team  
**Next Review:** After stakeholder feedback
