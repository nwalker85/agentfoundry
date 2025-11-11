# Engineering Department — Environment Configuration

## Overview

This document defines the current local development environment for the Engineering Department PoC.

## System Context

**Host Machine:** MacBook Pro M5  
**User:** nate  
**Local Path:** `/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment`  
**Python Version:** 3.12 (venv at `venv/`)  
**Node Version:** 20.18.0 (Next.js 14.2.33)  
**Containerization:** Docker Desktop (Compose v2.24+)  
**Telemetry Stack:** Local OTEL Collector → Tempo (traces) / Loki (logs)  
**IDE:** VS Code (Python, Docker, REST Client, ESLint, Prettier extensions enabled)

---

## Core Directories

| Path | Purpose |
|------|----------|
| `/app/` | Next.js front-end (chat, backlog, settings) |
| `/agent/` | LangGraph PM agent (logic + prompts) |
| `/mcp/` | MCP server and tool definitions |
| `/core/` | Shared dataclasses, audit, enums |
| `/infra/` | Dockerfiles, Compose, collector config |
| `/audit/` | JSONL logs and traces |
| `/docs/` | Project documentation, ADRs |

---

## Environment Variables

| Key | Description |
|-----|--------------|
| `OPENAI_API_KEY` | LLM provider API key (local dev only) |
| `NOTION_API_TOKEN` | Private integration token for Notion workspace |
| `NOTION_DATABASE_STORIES_ID` | Story DB ID |
| `NOTION_DATABASE_EPICS_ID` | Epic DB ID |
| `GITHUB_TOKEN` | PAT with repo + issue + PR write scopes |
| `GITHUB_REPO` | Target repo for issue/PR automation |
| `GITHUB_DEFAULT_BRANCH` | Main branch (default: `main`) |
| `TENANT_ID` | `local-dev` (for multi-tenant test isolation) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Local collector URL |
| `ENVIRONMENT` | `development` |

All variables stored in `.env.local` (not committed). Template available in `.env.example`.

---

## Service Commands

```bash
# Activate Python environment
source venv/bin/activate

# Start MCP server (FastAPI)
python mcp_server.py

# Start Next.js UI
npm run dev

# Run Notion smoke test
python test_notion.py

# Run E2E tests
python test_e2e.py

# Combined (Docker Compose - when available)
docker compose up --build

# Run agent tests (when test suite exists)
pytest agent/tests/
```

---

## Observability Notes

- `mcp_server.py` logs emit environment and tenant identifiers for traceability
- JSONL audit output persists under `audit/` directory
- OpenTelemetry collector wiring planned for Phase 4 (Observability & Governance)
