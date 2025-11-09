Engineering Department — Artifact Master Index (v0.1)

Source-of-truth catalog for all project artifacts (PoC → Production). Use this to locate, govern, and evolve the system. Keep updated at the end of each working session.

1) Quick Context

Program: Agentic Engineering Department (Next.js UI + LangGraph PM + MCP to Notion/GitHub)

Standards: Enterprise Multi‑Platform Architecture Scaffold v1.0 (MCP‑first, CloudEvents, OTel, AIP style)

SSOTs: Notion (backlog), Git (code, docs), Audit JSONL (actions), OTel (traces/metrics/logs)

2) File & Folder Naming Convention (Scalable)

Pattern:

<AREA>__<ARTIFACT>__v<YYYYMMDD>.<ext>

AREA ∈ {ARCH, ADR, DOCS, PLAN, POC, UI, AGENT, MCP, API, O11Y, SEC, RUN, OPS}

ARTIFACT = kebab-case summary (e.g., current-state, lessons-learned, environment)

vYYYYMMDD = date-based version; bump on material change (pair with Git history)

Optional suffixes: __DRAFT, __PRIVATE (auto‑ignore via .gitignore rule below)

Examples:

DOCS__current-state__v20251109.md

DOCS__lessons-learned__v20251109.md

DOCS__environment__v20251109.md

POC__implementation-scope__v20251109.md

PLAN__implementation-project-plan__v20251109.md

ARCH__system-context__v20251109.md

ADR__0001-stack-selection__v20251109.md

Canonical directories:

/docs           # human-facing docs & governance
/adr            # Architecture Decision Records
/api            # OpenAPI/AsyncAPI specs, clients
/mcp            # server + tools + schemas
/agent          # LangGraph graphs/prompts/evals
/app            # Next.js UI (App Router)
/infra          # docker/compose/otel configs
/audit          # jsonl append-only logs
/tests          # e2e + eval harness

3) Git Ignore Policy (Common Patterns)

Add to project .gitignore:

# Secrets & local configs
.env*
*.secrets.*
*_PRIVATE.*
*_private.*

# Local state & outputs
/audit/*.jsonl
/audit/*.ndjson
/tests/output/
/tmp/

# Tooling caches
node_modules/
.next/
coverage/
.pytest_cache/
__pycache__/

# Generated specs/clients
/api/generated/
/docs/generated/

# OS/editor
.DS_Store
.vscode/
.idea/

Rationale:

Prevents accidental leakage (tokens, private notes) via _PRIVATE suffix and .env*.

Keeps transient audit & test outputs out of VCS.

Segregates generated clients/specs from hand-edited sources.

4) Artifact Catalog (Live Index)

Update Status/Owner/Next Action each session. Prefix new entries with AREA and follow naming pattern.

4.1 Governance & State

AREA

Artifact (File)

Path

Owner

Status

Next Action

DOCS

DOCS__current-state__v20251109.md

/docs/

Director

In Progress

Update after MCP tool smoke test

DOCS

DOCS__lessons-learned__v20251109.md

/docs/

Director

Drafted

Add notes post Phase 1

DOCS

DOCS__environment__v20251109.md

/docs/

EA

Drafted

Validate Notion DB IDs + GitHub repo

PLAN

PLAN__implementation-project-plan__v20251109.md

/docs/

EA

Committed

Convert to backlog items

POC

POC__implementation-scope__v20251109.md

/docs/

EA

Committed

Keep aligned with UI/BFF changes

4.2 Architecture & Decisions

AREA

Artifact

Path

Owner

Status

Next Action

ARCH

ARCH__system-context__v20251109.md

/docs/

EA

Draft

Add C4 container view

ADR

ADR__0001-stack-selection__v20251109.md

/adr/

ARB

Draft

Approve Next.js + LangGraph + FastAPI

ADR

ADR__0002-observability-audit__v20251109.md

/adr/

ARB

Draft

Define trace attrs & redaction rules

4.3 APIs, Events, MCP

AREA

Artifact

Path

Owner

Status

Next Action

API

API__openapi-bff__v20251109.yaml

/api/

BE

Draft

Define /chat/pm, /status, /work/top

API

API__asyncapi-events__v20251109.yaml

/api/

EA

Backlog

Enumerate task lifecycle events

MCP

MCP__tool-contracts__v20251109.json

/mcp/schemas/

BE

Draft

Finalize notion.*, github.*, file.log_action

4.4 Agent, UI, Tests

AREA

Artifact

Path

Owner

Status

Next Action

AGENT

AGENT__pm-graph__v20251109.py

/agent/

PE

In Progress

Wire understand → plan → act

UI

UI__chat-page__v20251109.tsx

/app/app/chat/

FE

In Progress

Add streaming + action cards

TESTS

TESTS__demo-mcp-flow__v20251109.md

/tests/

QA

Backlog

Record green path steps

4.5 Infra, Observability, Security

AREA

Artifact

Path

Owner

Status

Next Action

O11Y

O11Y__otel-collector-config__v20251109.yaml

/infra/otel/

SRE

Backlog

Configure OTLP + Loki/Tempo

RUN

RUN__docker-compose__v20251109.yaml

/infra/

SRE

Draft

Build multi-service up

SEC

SEC__ci-policy__v20251109.md

/docs/

SEC

Backlog

Define gates: SBOM, SAST/DAST, evals

5) Active Work Queue (Today → Next)

MCP tool green path — notion.create_story, github.create_issue, file.log_action

PM graph integration — connect LangGraph → MCP (idempotent create)

Next.js /chat — stream agent replies; render result cards with links

6) Definition of Done (Artifact-Level)

Each artifact carries AREA prefix + versioned filename

Linked in this index with Status/Owner/Next Action

Non-public or sensitive drafts use __PRIVATE suffix

Changes reflected in CURRENT STATE and Lessons Learned

7) Maintenance Rules

Update this master index every session end (5 minutes)

Close the loop: when an artifact advances, update Status and Next Action here

Purge old date versions as needed; keep last 3 material versions per artifact

8) References

Enterprise Multi‑Platform Architecture Scaffold (v1.0)

Engineering Department PoC Scope & Implementation Plan

Notion + GitHub integration credentials (ENVIRONMENT doc)

