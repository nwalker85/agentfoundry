# Engineering Department — Environment Configuration# Engineering Department — Environment Configuration# Engineering Department — Environment Configuration



## Overview

This document captures the current local development setup for the Engineering Department PoC.

## Overview## Overview

## System Context

**Host Machine:** `MacBook Pro M5`This document captures the current local development setup for the Engineering Department PoC.This document defines the current local development environment for the Engineering Department PoC.

**User:** `nate`

**Workspace Root:** `/Users/nate/Development/1. Projects/Engineering Department/`

**Python Version:** 3.12 (virtual environment at `venv/`)

**Node Version:** 20.18.0 (Next.js 14.2.33)## System Context## System Context

**Containerization:** Docker Desktop (Compose v2.24+)

**Telemetry Stack:** Local OTEL Collector → Tempo (traces) / Loki (logs)**Host Machine:** `MacBook Pro M5`**Host Machine:** `MacBook Pro M5`  

**IDE:** VS Code with Python, Docker, REST Client, ESLint, and Prettier extensions

**User:** `nate`**User:** `nate`  

---

**Workspace Root:** `/Users/nate/Development/1. Projects/Engineering Department/`**Local Path:** `/Users/nate/Development/1. Projects/Engineering Department/`  

## Core Directories

| Path | Purpose |**Python Version:** 3.12 (virtual environment at `venv/`)**Python Version:** 3.12 (venv at `venv/`)  

|------|---------|

| `app/` | Next.js App Router front end (chat, backlog, settings) |**Node Version:** 20.18.0 (Next.js 14.2.33)**Node Version:** 20.18.0 (Next.js 14.2.33)  

| `agent/` | LangGraph PM agent (logic, prompts, tests) |

| `mcp/` | MCP server modules and tool contracts |**Containerization:** Docker Desktop (Compose v2.24+)**Containerization:** Docker Desktop (Compose v2.24+)  

| `core/` | Shared models, audit helpers, utilities |

| `infra/` | Dockerfiles, Compose manifests, collector config |**Telemetry Stack:** Local OTEL Collector → Tempo (traces) / Loki (logs)**Telemetry Stack:** Local OTEL Collector → Tempo (traces) / Loki (logs)  

| `audit/` | JSONL audit log output (planned) |

| `docs/` | Project documentation, ADRs |**IDE:** VS Code with Python, Docker, REST Client, ESLint, and Prettier extensions**IDE:** VS Code (Python, Docker, REST Client, ESLint, Prettier extensions enabled)



---



## Environment Variables------

| Key | Description |

|-----|-------------|

| `OPENAI_API_KEY` | LLM provider API key for local dev |

| `NOTION_API_TOKEN` | Private integration token for Notion workspace |## Core Directories## Core Directories

| `NOTION_DATABASE_STORIES_ID` | Story database identifier |

| `NOTION_DATABASE_EPICS_ID` | Epic database identifier || Path | Purpose || Path | Purpose |

| `GITHUB_TOKEN` | GitHub PAT with repo, issues, PR scopes |

| `GITHUB_REPO` | Target repo for automation (e.g., `org/repo`) ||------|---------||------|----------|

| `GITHUB_DEFAULT_BRANCH` | Default branch (typically `main`) |

| `TENANT_ID` | Tenant scoping flag (`local-dev`) || `app/` | Next.js App Router front end (chat, backlog, settings) || `/app/` | Next.js front-end (chat, backlog, settings) |

| `OTEL_EXPORTER_OTLP_ENDPOINT` | Local collector URL (Phase 4) |

| `ENVIRONMENT` | Runtime environment label (`development`) || `agent/` | LangGraph PM agent (logic, prompts, tests) || `/api/` | FastAPI or Next.js API routes (BFF layer) |



All variables live in `.env.local` (ignored by git). A template is available in `.env.example`.| `mcp/` | MCP server modules and tool contracts || `/agent/` | LangGraph PM agent (logic + prompts) |



---| `core/` | Shared models, audit helpers, utilities || `/mcp/` | MCP server and tool definitions |



## Service Commands| `infra/` | Dockerfiles, Compose manifests, collector config || `/core/` | Shared dataclasses, audit, enums |

```bash

# Activate Python environment| `audit/` | JSONL audit log output (planned) || `/infra/` | Dockerfiles, Compose, collector config |

source venv/bin/activate

| `docs/` | Project documentation, ADRs || `/audit/` | JSONL logs and traces |

# Start MCP server (FastAPI)

python mcp_server.py



# Start Next.js UI (App Router)------

npm run dev --prefix app/



# Run Notion smoke test

"$(pwd)/venv/bin/python" test_notion.py## Environment Variables## Environment Variables



# Combined stack (pending Compose manifests)| Key | Description || Key | Description |

docker compose up --build

```|-----|-------------||-----|--------------|



---| `OPENAI_API_KEY` | LLM provider API key for local dev || `OPENAI_API_KEY` | LLM provider API key (local dev only) |



## Observability Notes| `NOTION_API_TOKEN` | Private integration token for Notion workspace || `NOTION_API_TOKEN` | Private integration token for Notion workspace |

- `mcp_server.py` logs emit environment and tenant identifiers for traceability.

- JSONL audit output will persist under `audit/` once `file.log_action` implementation lands.| `NOTION_DATABASE_STORIES_ID` | Story database identifier || `NOTION_DATABASE_STORIES_ID` | Story DB ID |

- OpenTelemetry collector wiring resumes during Phase 4 (Observability & Governance).

| `NOTION_DATABASE_EPICS_ID` | Epic database identifier || `NOTION_DATABASE_EPICS_ID` | Epic DB ID |

| `GITHUB_TOKEN` | GitHub PAT with repo, issues, PR scopes || `GITHUB_TOKEN` | PAT with repo + issue + PR write scopes |

| `GITHUB_REPO` | Target repo for automation (e.g., `org/repo`) || `GITHUB_REPO` | Target repo for issue/PR automation |

| `GITHUB_DEFAULT_BRANCH` | Default branch (typically `main`) || `GITHUB_DEFAULT_BRANCH` | Main branch (default: `main`) |

| `TENANT_ID` | Tenant scoping flag (`local-dev`) || `TENANT_ID` | `local-dev` (for multi-tenant test isolation) |

| `OTEL_EXPORTER_OTLP_ENDPOINT` | Local collector URL (Phase 4) || `OTEL_EXPORTER_OTLP_ENDPOINT` | Local collector URL |

| `ENVIRONMENT` | Runtime environment label (`development`) || `ENVIRONMENT` | `development` |



All variables live in `.env.local` (ignored by git). A template is available in `.env.example`.All variables stored in `.env.local` (not committed). Template available in `.env.example`.



------



## Service Commands## Service Commands

```bash```bash

# Activate Python environment# Start MCP server (FastAPI)

source venv/bin/activatepython mcp/server.py



# Start MCP server (FastAPI)# Start Next.js UI

python mcp_server.pynpm run dev --prefix app/



# Start Next.js UI (App Router)# Combined (Docker Compose)

npm run dev --prefix app/docker compose up --build



# Run Notion smoke test# Run agent tests

"$(pwd)/venv/bin/python" test_notion.pypytest agent/tests/

# Combined stack (pending Compose manifests)
docker compose up --build
```

---

## Observability Notes

- `mcp_server.py` logs emit environment and tenant identifiers for traceability.
- JSONL audit output will persist under `audit/` once `file.log_action` implementation lands.
- OpenTelemetry collector wiring resumes during Phase 4 (Observability & Governance).
