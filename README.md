## Agent Foundry

**Agent Foundry** is an enterprise platform for building, deploying, and operating
AI agents – essentially **"Heroku for AI Agents"**. It transforms domain expertise
into production-ready AI systems through a declarative, LangGraph-first approach.

### Doc Map

| Document | Purpose |
|----------|---------|
| `START_HERE.md` | 30-minute onboarding guide |
| `ROADMAP.md` | Feature backlog and release plan |
| `docs/DOCKER_DEV_WORKFLOW.md` | Local development |
| `docs/DEPLOYMENT.md` | AWS ECS/Fargate deployment |
| `docs/FORGE_AI_USER_GUIDE.md` | Forge visual editor |
| `docs/LIVEKIT_SETUP.md` | Voice integration |
| `docs/ARCHITECTURE.md` | System design |

---

## Core Architecture: Control Plane vs Data Plane

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE (Foundry)                  │
│  Design • Configure • Deploy • Observe • Govern             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  Forge  │  │Manifests│  │  RBAC   │  │ Monitor │        │
│  │ (Build) │  │ (Config)│  │ (AuthZ) │  │ (Trace) │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ↓ Deploy
┌─────────────────────────────────────────────────────────────┐
│                    DATA PLANE (Instances)                   │
│  Runtime • Traffic • Execution • State                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Instance: org/domain/env/instance                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │   │
│  │  │ LangGraph│  │   MCP    │  │  Redis   │          │   │
│  │  │  Agents  │  │  Tools   │  │  State   │          │   │
│  │  └──────────┘  └──────────┘  └──────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Key insight**: Foundry manages creation; Instances run independently once deployed.

---

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **LangGraph-First** | All reasoning flows through deterministic state graphs. No direct LLM calls bypassing the graph. |
| **Manifest-Driven** | YAML manifests are the source of truth. Agents, deployments, and configs are declarative. |
| **MCP Everywhere** | Tools standardized via Model Context Protocol → n8n workflows. No custom integrations per agent. |
| **Multi-Tenant** | Organization → Domain → Project → Instance hierarchy from day one. |
| **Security by Default** | RBAC, field-level encryption, audit logging built-in. |

---

## Agent Execution Model

Every request flows through the system agent chain:

```
User Input
    ↓
IOAgent (I/O adapter, STT/TTS)
    ↓
Supervisor Agent (routes to correct domain agent)
    ↓
Domain Agent (PM, Banking, Support, etc.)
    ├── Calls MCP Tools (Notion, GitHub, etc.)
    ├── Updates State (Redis checkpointing)
    └── Returns structured response
    ↓
IOAgent (format response)
    ↓
User Output
```

**LangGraph Pattern** - Agents are state machines:
- **Nodes**: Pure async functions (understand, plan, execute)
- **Edges**: Deterministic Python routing (not LLM decisions)
- **State**: Typed dictionary with message history + domain fields
- **Checkpointing**: Redis stores state for long-running sessions

---

## Technology Stack

### Frontend (Next.js 14 + React 18)
| Category | Technologies |
|----------|--------------|
| Core | Next.js 14, React 18, TypeScript 5.3 |
| UI | Shadcn/ui, Radix primitives, Tailwind CSS 3.4 |
| State | Zustand, TanStack Query |
| Voice/RT | LiveKit Client, Socket.IO |
| Graphs | ReactFlow 11.11 (workflow editor) |
| Editor | Monaco Editor (code/YAML) |

### Backend (FastAPI + Python 3.12)
| Category | Technologies |
|----------|--------------|
| Core | FastAPI 0.109, Uvicorn, Pydantic 2.9 |
| AI/Agents | LangChain 1.0.8, LangGraph 1.0.3 |
| LLM | OpenAI, Anthropic Claude |
| Voice | LiveKit 1.0, Deepgram (STT), ElevenLabs/OpenAI (TTS) |
| Database | PostgreSQL 16, SQLAlchemy 2.0 |
| Cache | Redis 7 |

### Infrastructure (Docker Compose)
| Service | Purpose | Port |
|---------|---------|------|
| LiveKit | WebRTC voice/video | 7880 |
| Redis | State/cache/sessions | 6379 |
| PostgreSQL | Control plane DB | 5432 |
| LocalStack | AWS emulation (Secrets, S3) | 4566 |
| Prometheus | Metrics collection | 9090 |
| Tempo | Distributed tracing | 4317 |

---

## What Agent Foundry Provides

### Forge Visual Graph Editor
- Drag-and-drop LangGraph workflow builder
- Node types: Process, Decision, Tool Call, Entry, End
- State schema and trigger configuration
- Version control with auto-increment and deploy workflow
- YAML ↔ Graph conversion with Python code generation

### 7 System Agents
| Agent | Purpose |
|-------|---------|
| IO Agent | Input/output adapter, channel routing, STT/TTS |
| Supervisor | Orchestration and worker agent routing |
| Context | State management and session context |
| Coherence | Response assembly and consistency |
| Exception | Error handling and resilience |
| Observability | Metrics, tracing, activity logging |
| Governance | Security policies and compliance |

### Multi-Tenant Control Plane
- Organizations → Domains → Environments hierarchy
- Row-Level Security (RLS) in PostgreSQL
- RBAC with Zitadel SSO integration

### Voice Pipeline
- LiveKit WebRTC (self-hosted, containerized)
- Deepgram/Silero STT → LangGraph Agent → ElevenLabs/OpenAI TTS
- Multi-turn conversations with context preservation

### MCP Tool Integration
- Model Context Protocol for standardized tool access
- n8n workflow automation (400+ integrations)
- Health monitoring and configuration per tool

---

## High-Level Architecture

### Local (Docker + Next.js)

At development time you run:

- `docker compose` stack:
  - **LiveKit**: `livekit/livekit-server` (WebRTC, ws://localhost:7880)
  - **Redis**: state / checkpointing
  - **Backend API**: FastAPI on `http://localhost:8000`
  - **Compiler**: FastAPI on `http://localhost:8002`
- **Next.js UI**: `npm run dev` serving `http://localhost:3000`

Conceptually:

```
Browser (Next.js UI, port 3000)
  ├─ HTTP → Backend API (port 8000)         # /api/* routes
  ├─ WebSocket → Backend (chat / streaming) # text agents
  └─ WebRTC (ws) → LiveKit (port 7880)      # voice media/signaling

Backend (FastAPI)
  ├─ LangGraph agents in `agent/`
  ├─ Voice session + token issuance
  ├─ Integration layer (Notion, GitHub, etc.)
  └─ Redis for state/checkpointing

Compiler
  └─ DIS dossiers → agent YAML / workflows (saved into `agents/`)
```

See `START_HERE.md` and `DOCKER_DEV_WORKFLOW.md` for how to run this stack.

### AWS (ECS / Fargate + ALB + ECR)

Terraform in `infra/` provisions:

- **VPC + subnets** for the Agent Foundry cluster
- **ALB** `agentfoundry-alb` with:
  - `/` → UI target group (`agentfoundry-ui-tg`, port 3000)
  - `/api/*` → API target group (`agentfoundry-api-tg`, port 8000)
- **Route 53 & DNS**
  - Hosted zone for `ravenhelm.ai`
  - `foundry.ravenhelm.ai` → ALB (A-record alias)
- **ECS Fargate services**
  - `agentfoundry-ui-svc` (UI container from ECR)
  - `agentfoundry-api-svc` (backend container from ECR)
- **ECR repositories**
  - `agentfoundry-ui`, `agentfoundry-backend`, `agentfoundry-compiler`,
    `agentfoundry-forge`

Deployments are driven by:

- `./configure_build_env.sh` – one-time Docker buildx + ECR login
- `./deploy_dev.sh` – build linux/amd64 images, push to ECR, and run
  `aws ecs update-service --force-new-deployment` for UI and API

See `DEPLOYMENT.md` for the full AWS deployment workflow.

---

## Quick Orientation

### Frontend (`app/`)
- **Entry**: `app/layout.tsx`, `app/page.tsx` (Dashboard)
- **Navigation**: `app/components/layout/TopNav.tsx`, `LeftNav.tsx`
- **Key Pages** (under `app/app/`):
  - `/graphs` - Forge visual graph editor
  - `/agents` - Agent registry with metrics
  - `/chat` - Chat playground with voice support
  - `/tools` - Integration tool catalog
  - `/monitoring` - Real-time agent monitoring
  - `/admin` - Database and system administration

### Backend (`backend/`)
- **Core API**: `main.py` (47+ endpoints, ~2100 lines)
- **Database**: `db.py` (PostgreSQL with RLS)
- **Voice**: `livekit_service.py`, `voice_agent_worker.py`
- **Routes**: `routes/` (hierarchy, favorites, secrets, monitoring)
- **Services**: `services/` (agent deployer, storage)

### Agents (`agents/`)
- **System Agents**: `dev_*.yaml` (IO, Supervisor, Context, etc.)
- **User Agents**: `user/{org}/{domain}/*.yaml`
- **Registry**: `agents.manifest.yaml`
- **Runtime**: `agent_loader.py`, `agent_registry.py`, `marshal_agent.py`

### Compiler (`compiler/`)
- **DIS Compiler**: `dis_compiler.py` - DIS → Agent conversion
- **API**: `main.py` (port 8002)

For a guided onboarding path, follow `START_HERE.md`.

---

## Running Locally (Overview)

See `START_HERE.md` for the full walkthrough. At a glance:

1. **Clone and configure**
   - Copy env: `cp .env.example .env.local`
   - Set at minimum: `OPENAI_API_KEY=...` and LiveKit keys if using real voice
2. **Start core services (Docker)**
   - `./start_foundry.sh`
   - This:
     - Ensures `.env` symlink for Docker
     - Brings up LiveKit, Redis, backend, compiler via `docker compose`
3. **Start the UI (Next.js)**
   - `npm install` (first time)
   - `npm run dev`
4. **Validate**
   - UI: `http://localhost:3000`
   - Backend: `http://localhost:8000/health`
   - Compiler: `http://localhost:8002/health`
   - LiveKit: `http://localhost:7880`
5. **Diagnostics**
   - Local health: `./scripts/monitor_local_health.sh`

Details and day‑to‑day workflow (hot reload, rebuild rules, common issues) live
in `DOCKER_DEV_WORKFLOW.md`.

---

## Key Documentation

- **Architecture & Roadmap**
  - `docs/ARCHITECTURE.md` – overall system design
  - `docs/MULTI_AGENT_ARCHITECTURE.md` – multi‑agent and system agent plans
  - `docs/FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md` – Forge vs system agents
  - `docs/FULLY_AGENTIC_FOUNDRY_ROADMAP.md` – long‑term roadmap
- **Forge & LangGraph**
  - `docs/FORGE_AI_USER_GUIDE.md`
  - `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md`
- **System Agents**
  - `docs/SYSTEM_AGENTS_DESIGN.md`
  - `docs/SYSTEM_AGENTS_IMPLEMENTATION.md`
  - `docs/SYSTEM_AGENTS_INTEGRATION_GUIDE.md`
- **Testing & Quality**
  - `docs/TESTING_GUIDE.md`
  - `tests/` – unit, integration, e2e, and UAT suites

---

## Debugging & Diagnostics

- **Local stack**
  - `./scripts/monitor_local_health.sh` – checks Docker, ports, LiveKit,
    backend, compiler
  - `./scripts/start-services.sh` – convenience wrapper around
    `./start_foundry.sh`
  - `DOCKER_DEV_WORKFLOW.md` – common Docker dev issues and fixes
- **AWS / ECS**
  - `./scripts/monitor_aws_health.sh` – ECS service + ALB sanity checks (dev)
  - `./scripts/check_alb_targets.sh` – ALB target group health for UI/API
  - `verify_deployment_setup.sh` – verifies local deployment prerequisites
- **Feature‑specific guides**
  - Backlog / stories: `docs/BACKLOG_DEBUGGING_GUIDE.md`
  - WebSockets / chat: `docs/WEBSOCKET_IMPLEMENTATION_PLAN.md`,
    `docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md`
  - LiveKit: `LIVEKIT_SETUP.md` and `LIVEKIT_DOCKER_MIGRATION.md` (migration
    history)

See `scripts/README.md` and `scripts/QUICK_REFERENCE.md` for a concise index of
helper scripts.

---

## Target Use Cases

1. **Regulated Industries** (Banking, Healthcare) - Compliance, auditability, domain expertise critical
2. **Voice AI** - Call center automation with STT → Agent → TTS pipeline
3. **Enterprise Workflows** - Natural language interfaces to business systems
4. **Platform Operations** - "How many agents in prod?" → SQL → Answer

---

## Status

**Version:** v0.9.0 – Production-ready platform with complete Forge editor

### What's Complete
- LangGraph orchestration with 7 system agents
- Forge visual graph builder with version control
- MCP tool integration gateway
- RBAC with Zitadel SSO
- Voice pipeline (LiveKit + Deepgram + ElevenLabs)
- AWS ECS/Fargate deployment
- Multi-tenant control plane with RLS

### v0.9 Highlights
- **Forge Graph Editor** with version management and deploy workflow
- **Agent Version Control** - Auto-increment, deploy specific versions, history tracking
- **Real-time Monitoring** - Agent metrics, activity streams, health checks
- **RBAC Integration** - Zitadel SSO with permission-based access
- **Enhanced Delete** - Proper cleanup of database, YAML files, and registry

### In Progress
- Enhanced observability dashboards
- Multi-tenant routing improvements
- Voice UI enhancements

---

**Quant Project** – This repository is maintained on Quant's company GitHub.
