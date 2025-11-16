## Agent Foundry – Start Here

**Goal:** Get a new engineer productive in \<30 minutes with a clear path for local development, AWS deployment, and where to learn about Domain Intelligence (DIS) and Forge.

---

## 1. TL;DR – What You’re Looking At

- **Agent Foundry** is an **agentic platform**:
  - LangGraph-based agents (`agent/`, `agents/`)
  - Visual Forge builder (`app/forge/*`, `forge_service/`)
  - DIS dossiers compiled into runtime agents (`compiler/`)
  - Voice capabilities via LiveKit (`backend/livekit_service.py`, `backend/voice_agent_worker.py`)
- **Runtime topology**
  - Local: Docker Compose (LiveKit, Redis, backend, compiler) + Next.js dev server
  - AWS: ECR → ECS Fargate → ALB → `foundry.ravenhelm.ai`
- **You should read, in this order:**
  1. This file – `START_HERE.md`
  2. Local dev guide – `DOCKER_DEV_WORKFLOW.md`
  3. AWS deployment – `DEPLOYMENT.md`
  4. DIS / Forge / LangGraph – `docs/FOUNDARY_INSTANCE_ARCHITECTURE.md`, `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md`

---

## 2. Run the Stack Locally (10–15 minutes)

### 2.1 Prerequisites

- **Docker Desktop**
- **Python** 3.11+ (system or pyenv)
- **Node.js** 20+
- **AWS CLI** (only needed for AWS work)

### 2.2 Configure Environment

From the repo root:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

- **Required**
  - `OPENAI_API_KEY=sk-...`
- **Recommended (for real integrations)**
  - Notion: `NOTION_API_TOKEN`, `NOTION_DATABASE_STORIES_ID`, `NOTION_DATABASE_EPICS_ID`
  - GitHub: `GITHUB_TOKEN`, `GITHUB_REPO`
- **LiveKit / voice**
  - For local Docker LiveKit, defaults in `.env.example` are fine; see `LIVEKIT_SETUP.md` for details.

### 2.3 Start Core Services (Docker)

```bash
chmod +x start_foundry.sh
./start_foundry.sh
```

This will:

- Create `.env` → `.env.local` symlink for Docker
- Bring up Docker services:
  - LiveKit (`livekit` container, HTTP/WebSocket on `localhost:7880`)
  - Redis (`redis`)
  - Backend API (`foundry-backend` on `localhost:8000`)
  - Compiler (`foundry-compiler` on `localhost:8002`)

Health checks (optional):

```bash
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:7880
```

### 2.4 Start the Frontend

```bash
npm install      # first time only
npm run dev
```

Open:

- UI shell & dashboard: `http://localhost:3000`
- Chat: `http://localhost:3000/chat`
- (Future) voice UI: `http://localhost:3000/voice` once implemented

### 2.5 Local Debugging & Diagnostics

- Quick health overview:

```bash
./scripts/monitor_local_health.sh
```

- Docker workflow and common issues:
  - See `DOCKER_DEV_WORKFLOW.md`
- Feature-specific debugging:
  - Backlog / stories: `docs/BACKLOG_DEBUGGING_GUIDE.md`
  - WebSockets: `docs/WEBSOCKET_IMPLEMENTATION_PLAN.md`, `docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md`

---

## 3. Deploy to AWS Dev (ECS / Fargate)

Use this once you’re comfortable locally. This is the **current, supported** path for Agent Foundry in AWS.

### 3.1 One-Time AWS Setup

1. **AWS account & credentials**
   - Configure AWS CLI with the target account (e.g. the `122441748701` dev account).
2. **Terraform `infra/`**
   - `cd infra`
   - `cp terraform.tfvars.example terraform.tfvars`
   - Fill in:
     - `project_name = "agentfoundry"`
     - ACM certificate ARN for `foundry.ravenhelm.ai`
     - Any other required variables
   - Apply:

   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

   This will create:

   - VPC, subnets, security groups
   - ALB `agentfoundry-alb`
   - Target groups `agentfoundry-ui-tg` (port 3000) and `agentfoundry-api-tg` (port 8000)
   - ECS cluster `agentfoundry-cluster`
   - ECS services `agentfoundry-ui-svc` and `agentfoundry-api-svc`
   - ECR repositories for UI/backend/compiler/forge
   - Route53 zone for `ravenhelm.ai` with `foundry.ravenhelm.ai` → ALB

3. **Build environment for images (local machine)**

```bash
./configure_build_env.sh
```

This creates a Docker buildx builder (`af-builder`) and logs you into ECR.

### 3.2 Deploy Application Images (Dev)

For each deploy:

```bash
./deploy_dev.sh
```

What it does:

- Builds **linux/amd64** images for:
  - `agentfoundry-ui`
  - `agentfoundry-backend`
  - `agentfoundry-compiler`
  - `agentfoundry-forge`
- Pushes them to ECR
- Runs:
  - `aws ecs update-service --cluster agentfoundry-cluster --service agentfoundry-ui-svc --force-new-deployment`
  - `aws ecs update-service --cluster agentfoundry-cluster --service agentfoundry-api-svc --force-new-deployment`

### 3.3 Validate in AWS

- Visit: `https://foundry.ravenhelm.ai/`
  - `/` should serve the UI
  - `/api/health` (or `/api/*`) should route to the backend
- Use helper scripts:

```bash
./scripts/monitor_aws_health.sh
./scripts/check_alb_targets.sh
```

See `DEPLOYMENT.md` for the full AWS deployment guide (including DNS, SSL, and teardown).

---

## 4. Domain Intelligence (DIS), Forge, and LangGraph

Once you can run locally and understand the AWS path, dig into the core “agentic OS” concepts:

- **Foundry instances & DIS**
  - `docs/FOUNDARY_INSTANCE_ARCHITECTURE.md` – how DIS dossiers, agents, and instances fit together
  - `docs/FULLY_AGENTIC_FOUNDRY_ROADMAP.md` – roadmap toward a fully agentic platform
- **Forge visual builder & LangGraph**
  - `docs/FORGE_AI_USER_GUIDE.md` – UX of the Forge visual builder
  - `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md` – what’s implemented vs full LangGraph feature set (state schema, routing, tools, execution, codegen, etc.)
  - `docs/FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md` – how Forge relates to system agents
- **System Agents**
  - `docs/SYSTEM_AGENTS_DESIGN.md`
  - `docs/SYSTEM_AGENTS_IMPLEMENTATION.md`
  - `docs/SYSTEM_AGENTS_INTEGRATION_GUIDE.md`

For concrete code, start with:

- `agent/pm_graph.py` – main LangGraph PM agent
- `forge_service/main.py` – Forge runtime API
- `compiler/dis_compiler.py` – DIS → agent compilation pipeline

---

## 5. LiveKit / Voice Stack

You don’t need to understand LiveKit on day one, but you should know where the pieces live:

- **Docs**
  - `LIVEKIT_SETUP.md` – current LiveKit + Docker + backend wiring
  - `LIVEKIT_DOCKER_MIGRATION.md` – history and validation of the Docker migration (marked as legacy/migration record)
- **Code**
  - `backend/livekit_service.py` – session creation, tokens, room naming
  - `backend/voice_agent_worker.py` – starting point for voice I/O agents
  - `livekit-config.yaml` – server config used by the Docker LiveKit service

See `LIVEKIT_SETUP.md` for end‑to‑end examples (creating a voice session, testing LiveKit HTTP, and future voice UI plans).

---

## 6. Where to Go Next

- **Day 1**
  - Get the stack running locally (`./start_foundry.sh`, `npm run dev`)
  - Read `DOCKER_DEV_WORKFLOW.md`
  - Skim `docs/ARCHITECTURE.md`
- **Day 2–3**
  - Explore `agent/pm_graph.py`, `backend/main.py`, and `app/chat/page.tsx`
  - Review DIS and Forge docs:
    - `docs/FOUNDARY_INSTANCE_ARCHITECTURE.md`
    - `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md`
- **When touching infra**
  - Read `DEPLOYMENT.md`, `infra/REFACTOR_SUMMARY.md`
  - Use `./scripts/monitor_aws_health.sh` and `./scripts/check_alb_targets.sh`

After you’ve gone through this file and the links above, you should be able to:

- Run Agent Foundry locally
- Understand the major services (UI, backend, compiler, LiveKit)
- Know how the AWS deployment pipeline works
- Know where to learn more about DIS, Forge, and the LangGraph runtime
