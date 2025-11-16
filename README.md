## Agent Foundry

**Agent Foundry** is a modern **agentic platform** for building, deploying, and operating AI agents – including voice agents, LangGraph-based workflows, and a visual Forge builder – on both **local Docker** and **AWS ECS** infrastructure.

### Doc Map (Start Here)

- **Onboarding:** `START_HERE.md`
- **Local development:** `DOCKER_DEV_WORKFLOW.md`
- **AWS deployment (ECS/Fargate):** `DEPLOYMENT.md`
- **LiveKit / voice stack:** `LIVEKIT_SETUP.md`
- **Domain Intelligence / DIS & Forge:** `docs/FOUNDARY_INSTANCE_ARCHITECTURE.md`, `docs/FULLY_AGENTIC_FOUNDRY_ROADMAP.md`, `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md`
- **Debugging & diagnostics:** `scripts/README.md`, `scripts/QUICK_REFERENCE.md`, `docs/BACKLOG_DEBUGGING_GUIDE.md`, `docs/WEBSOCKET_IMPLEMENTATION_PLAN.md`

---

## What Agent Foundry Provides

- **Agentic OS**
  - LangGraph-based agents (PM agent + future system agents)
  - Forge visual graph editor (see `docs/FORGE_AI_USER_GUIDE.md` and `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md`)
  - Domain Intelligence (DIS) dossiers compiled into executable agents (`compiler/`)
- **Modern UI**
  - Next.js 14 App Router in `app/`
  - Shadcn UI + Ravenhelm dark theme
  - Global app shell (TopNav + LeftNav + dashboard, projects, instances, artifacts, chat)
- **Voice & LiveKit**
  - LiveKit-powered voice transport (now containerized in Docker)
  - `backend/livekit_service.py` + `backend/voice_agent_worker.py` for session management
  - Planned rich voice UI and voice I/O agents
- **Production-Oriented Runtime**
  - FastAPI backend with health checks and voice endpoints (`backend/`)
  - DIS compiler service (`compiler/`) for turning DIS JSON into agent manifests
  - AWS-ready deployment via ECR + ECS + ALB (`infra/`)

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
  - `agentfoundry-ui`, `agentfoundry-backend`, `agentfoundry-compiler`, `agentfoundry-forge`

Deployments are driven by:

- `./configure_build_env.sh` – one-time Docker buildx + ECR login
- `./deploy_dev.sh` – build linux/amd64 images, push to ECR, and run `aws ecs update-service --force-new-deployment` for UI and API

See `DEPLOYMENT.md` for the full AWS deployment workflow.

---

## Quick Orientation

- **Frontend**
  - Next.js app entry: `app/layout.tsx`, `app/page.tsx`
  - Navigation shell: `app/components/layout/TopNav.tsx`, `LeftNav.tsx`, `AppMenu.tsx`
  - Chat UI: `app/chat/page.tsx` and `app/chat/components/*`
  - Forge builder: `app/forge/*`
- **Backend**
  - Core API: `backend/main.py`
  - LiveKit integration: `backend/livekit_service.py`
  - Voice worker: `backend/voice_agent_worker.py`
- **Agents & Forge**
  - LangGraph PM agent: `agent/pm_graph.py`
  - YAML agent registry: `agents/` + `agents/agents.manifest.yaml`
  - Forge runtime service: `forge_service/main.py`
- **Compiler / DIS**
  - DIS compiler: `compiler/dis_compiler.py`, `compiler/main.py`
  - DIS / LangGraph design docs: `docs/FOUNDARY_INSTANCE_ARCHITECTURE.md`, `docs/FULLY_AGENTIC_FOUNDRY_ROADMAP.md`

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

Details and day‑to‑day workflow (hot reload, rebuild rules, common issues) live in `DOCKER_DEV_WORKFLOW.md`.

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
  - `./scripts/monitor_local_health.sh` – checks Docker, ports, LiveKit, backend, compiler
  - `./scripts/start-services.sh` – convenience wrapper around `./start_foundry.sh`
  - `DOCKER_DEV_WORKFLOW.md` – common Docker dev issues and fixes
- **AWS / ECS**
  - `./scripts/monitor_aws_health.sh` – ECS service + ALB sanity checks (dev)
  - `./scripts/check_alb_targets.sh` – ALB target group health for UI/API
  - `verify_deployment_setup.sh` – verifies local deployment prerequisites
- **Feature‑specific guides**
  - Backlog / stories: `docs/BACKLOG_DEBUGGING_GUIDE.md`
  - WebSockets / chat: `docs/WEBSOCKET_IMPLEMENTATION_PLAN.md`, `docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md`
  - LiveKit: `LIVEKIT_SETUP.md` and `LIVEKIT_DOCKER_MIGRATION.md` (migration history)

See `scripts/README.md` and `scripts/QUICK_REFERENCE.md` for a concise index of helper scripts.

---

## Status & License

- **Status:** Active development – v0.8.x agentic platform, ECS‑ready
- **Latest UI milestone:** `progressaudit/FRONTEND_PROFESSIONAL_UI_COMPLETE.md`
- **Latest infra milestone:** `INFRASTRUCTURE_STATUS.md`

This repository is **private – internal use only**.

