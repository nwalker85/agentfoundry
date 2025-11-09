# Engineering Department — Environment Configuration

## Overview
This document defines the current local development environment for the Engineering Department PoC.

## System Context
**Host Machine:** `MacBook Pro M5`  
**User:** `nate`  
**Local Path:** `/Users/nate/Development/1. Projects/Engineering Department/`  
**Python Version:** 3.11+  
**Node Version:** 20.x (Next.js 14)  
**Containerization:** Docker Desktop (Compose v2.24+)  
**Telemetry Stack:** Local OTEL Collector → Tempo (traces) / Loki (logs)  
**IDE:** VS Code (Python, Docker, REST Client, ESLint, Prettier extensions enabled)

---

## Core Directories
| Path | Purpose |
|------|----------|
| `/app/` | Next.js front-end (chat, backlog, settings) |
| `/api/` | FastAPI or Next.js API routes (BFF layer) |
| `/agent/` | LangGraph PM agent (logic + prompts) |
| `/mcp/` | MCP server and tool definitions |
| `/core/` | Shared dataclasses, audit, enums |
| `/infra/` | Dockerfiles, Compose, collector config |
| `/audit/` | JSONL logs and traces |

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
# Start MCP server (FastAPI)
python mcp/server.py

# Start Next.js UI
npm run dev --prefix app/

# Combined (Docker Compose)
docker compose up --build

# Run agent tests
pytest agent/tests/