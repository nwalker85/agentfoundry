Engineering Department — Local PoC Implementation Scope

(Aligned with Enterprise Multi-Platform Architecture Scaffold v1.0)

⸻

1. Objective

Build a local, production-aligned proof of concept for an agentic engineering
control plane where a Project Manager (PM) agent coordinates software work
through conversational input. The PoC connects a Next.js chat UI, a
LangGraph-based PM agent, and an MCP server exposing tools for Notion (backlog)
and GitHub (issues/PRs). All components are deployable locally and form the
foundation for a fully governed, multi-tenant enterprise implementation.

⸻

2. Success Criteria • User can chat with the PM agent to create, update, and
   query backlog items. • The agent autonomously:
   1. Creates a Story in Notion (linked to an Epic).
   2. Opens a corresponding GitHub issue with AC/DoD and metadata.
   3. Returns both links in chat. • Queries such as “Show top 5 P0/P1 stories
      this week” or “Open draft PR for issue #123” execute successfully. • All
      actions generate audit logs with timestamps, actor IDs, and tool results.

⸻

3. Target Architecture

[User] ↓ [Next.js Web UI (Chat + Backlog + Settings)] ↓ (WebSocket/SSE) [BFF/API
Layer (FastAPI or Next.js API routes)] ↓ [LangGraph PM Agent (Understand → Plan
→ Act)] ↓ (MCP calls) [MCP Server: notion.*, github.*, file.* tools] ├── Notion
API (Epics, Stories) ├── GitHub API (Issues, PRs) └── Local JSONL audit log

Planes • Control Plane: Identity, audit, tool governance, DoD policies. • Data
Plane: Notion databases, GitHub repo, audit files. • Event Plane: Chat requests,
MCP calls, task lifecycle events. • Observability Plane: OpenTelemetry traces,
JSONL logs.

⸻

4. Core Components

4.1 Web UI (Production-Aligned) • Framework: Next.js (App Router, TypeScript,
Tailwind, shadcn/ui). • Pages: • /chat — conversational task intake and results.
• /backlog — view of Notion Stories (P0–P3). • /settings — environment
variables, API connection checks. • Features: • Message thread with streaming
responses. • Tool-action cards (Story/Issue links, AC/DoD preview). • Connection
and trace indicators. • Accessibility (WCAG 2.1 AA) and OTel web SDK.

4.2 PM Agent (LangGraph) • Flow: understand → plan → act. • Responsibilities: •
Parse user intent (create, query, update). • Validate required fields (epic,
title, priority, AC, DoD). • Generate structured task payload. • Invoke MCP
tools (Notion, GitHub). • Return structured results and confirmations. •
Policies: • ≤2 clarification questions per task. • Idempotency key per creation
(hash of title + epic). • Redaction of sensitive values. • Definition of Done
(DoD): tested, documented, compliant, no critical vulns.

4.3 MCP Server • Framework: FastAPI with uvicorn. • Tools: •
notion.create_story(epic_title, story_title, priority, ac[], dod[]) •
notion.list_top_items(limit, priorities[]) • github.create_issue(repo, title,
body, labels[]) • github.open_pr(repo, head, base, title, body, draft=True) •
file.log_action(actor, tool, input, output) • Contracts: OpenAPI (REST) +
internal JSON schema for LangGraph validation. • Security: Token-based auth,
redaction, least-privilege scopes, idempotency enforcement. • Observability:
OTLP traces + JSONL append logs.

⸻

5. Data & Configuration

5.1 Notion • Databases: • Epics: Title, Status, Priority. • Stories: Name, Epic
(relation), Priority (select), Status, AC, DoD, GitHub URL. • Schema
Enforcement: Verified at MCP server startup.

5.2 GitHub • Repo: Dedicated PoC repo under personal org. • Artifacts: • Issues
mirror Notion Stories with body template (AC, DoD, source links). • Draft PR
creation from branches named feat/{issue-number}-{slug}. • Labels: priority/P0,
source/agent-pm.

5.3 Environment (.env)

OPENAI_API_KEY=... NOTION_API_TOKEN=... NOTION_DATABASE_STORIES_ID=...
NOTION_DATABASE_EPICS_ID=... GITHUB_TOKEN=... GITHUB_REPO=org/repo
GITHUB_DEFAULT_BRANCH=main TENANT_ID=local-dev

⸻

6. Directory Layout

engineering-dept/ ├── app/ # Next.js UI │ ├── app/chat/ │ ├── app/backlog/ │ ├──
app/settings/ │ └── components/ ├── api/ # Next.js API routes or FastAPI BFF ├──
agent/ # LangGraph PM agent │ ├── graph.py │ ├── policy.py │ └── tests/ ├──
mcp/ # MCP server + tools │ ├── server.py │ ├── tools_github.py │ ├──
tools_notion.py │ ├── tools_file.py │ └── schemas/ ├── core/ # Shared models and
audit │ ├── models.py │ ├── audit.py │ └── utils.py ├── infra/ # Docker,
Compose, collector config ├── .env.example ├── requirements.txt └── README.md

⸻

7. Workflow Example (End-to-End)
   1. User: “Create Story ‘Add healthcheck endpoint’ under Epic ‘Platform
      Hardening’ as P1.”
   2. PM Agent: • Confirms missing AC/DoD if necessary. • Calls
      notion.create_story(...) → returns Story URL. • Calls
      github.create_issue(...) → returns Issue URL. • Logs both via
      file.log_action.
   3. Chat UI: Displays confirmation card with Story + Issue links.
   4. Audit: JSONL log entry with {request_id, actor, tool, input, output}.
   5. Query: “Show top 5 P0/P1 tasks this week.” → MCP notion.list_top_items() →
      tabular reply.

⸻

8. Observability & Audit • Logs: • ./audit/actions.jsonl — append-only. • Each
   line includes timestamp, actor, tenant, tool, input_hash, result. • Traces: •
   OTel client on UI + server; correlated traceparent propagation. • Metrics: •
   Task success rate, MCP latency, DoD compliance rate, token cost (optional).

⸻

9. Non-Functional Requirements

Category Requirement Availability Local PoC (single-node, Docker) Security Token
redaction, Argon2id password policy if auth added Auditability All MCP calls
logged and replayable Accessibility WCAG 2.1 AA; keyboard-navigable chat
Observability OTLP traces; JSONL audit logs Compliance GDPR/CCPA alignment; no
PII in telemetry Extensibility Future integration of QA, SRE, AIOps agents
Performance ≤500 ms response for Notion/GitHub create Cost Awareness Track token
usage per task in logs

⸻

10. Definition of Done • Chat UI live at http://localhost:3000/chat • PM Agent
    can autonomously create Story + GitHub issue • Notion query (list_top_items)
    returns correct data • All actions logged with full trace context • Docker
    Compose spins up MCP + UI + Agent stack cleanly • ADR-001 (“Stack
    selection”) and ADR-002 (“Audit policy”) committed • Accessibility and basic
    test suite passing in CI

⸻

11. Risks & Mitigation

Risk Mitigation Notion field mismatch Runtime schema discovery + config cache
API rate limits Backoff + idempotent retries Prompt drift Versioned prompt
templates + eval tests Auth/token leaks Redaction middleware + secret scanning
Future integration debt Maintain clear MCP tool boundaries

⸻

12. Future Extensions • Add status mirroring (PR merged → Story Done). •
    Introduce QA agent for automated verification. • Implement SRE & AIOps
    agents for monitoring loops. • Expand to multi-tenant control plane (Org →
    Team → Project). • Integrate with Trust Center for compliance evidence.

⸻

Progress Snapshot (as of 2025-11-09)

- Completed: Python 3.12 environment rebuilt, MCP server scaffold online (`/`,
  `/health`, `/api/status`), Next.js dashboard landing page deployed, Notion
  smoke test validated credentials.
- In Flight: Chat/backlog/settings UI flows, MCP tool contracts (Notion story
  create/list, GitHub issue create) with schema enforcement, JSONL audit and
  idempotency protections.
- Next Up: Connect LangGraph PM agent skeleton to MCP endpoints and expose
  authenticated tool routes; propagate status telemetry into UI dashboard.

⸻

Summary

This PoC is not disposable—it’s the seed of the production system. By using the
final technology stack (Next.js, LangGraph, MCP, OpenTelemetry, Notion, GitHub),
it builds a stable foundation for the future Engineering Department control
plane, ready to evolve into a full, multi-agent enterprise platform.
