## Agent Foundry – Start Here (v0.9)

**Goal:** Get a new engineer productive in <30 minutes with a clear path for
local development, AWS deployment, and the Forge visual editor.

---

## 1. TL;DR – What You're Looking At

**Agent Foundry v0.9** is a production-ready **agentic platform**:

### Core Features
- **Forge Visual Graph Editor** - Build LangGraph agents with drag-and-drop
- **Agent Version Control** - Auto-increment versions, deploy specific versions
- **Voice Integration** - LiveKit WebRTC with Deepgram STT + OpenAI TTS
- **Multi-Tenant** - Organizations → Domains with RBAC and Zitadel SSO
- **7 System Agents** - IO, Supervisor, Context, Coherence, Exception, Observability, Governance

### Key Locations
- **Frontend**: `app/app/` - 18 pages (graphs, agents, chat, tools, admin)
- **Backend**: `backend/main.py` - 47+ API endpoints
- **Agents**: `agents/` - YAML manifests + runtime registry
- **Compiler**: `compiler/` - DIS → Agent conversion

### Runtime Topology
- **Local**: Docker Compose (LiveKit, Redis, PostgreSQL, backend) + Next.js
- **AWS**: ECR → ECS Fargate → ALB → `foundry.ravenhelm.ai`

### Reading Order
1. This file – `START_HERE.md`
2. Local dev guide – `docs/DOCKER_DEV_WORKFLOW.md`
3. Forge guide – `docs/FORGE_AI_USER_GUIDE.md`
4. AWS deployment – `docs/DEPLOYMENT.md`

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
  - Notion: `NOTION_API_TOKEN`, `NOTION_DATABASE_STORIES_ID`,
    `NOTION_DATABASE_EPICS_ID`
  - GitHub: `GITHUB_TOKEN`, `GITHUB_REPO`
- **LiveKit / voice**
  - For local Docker LiveKit, defaults in `.env.example` are fine; see
    `LIVEKIT_SETUP.md` for details.

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
  - WebSockets: `docs/WEBSOCKET_IMPLEMENTATION_PLAN.md`,
    `docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md`

---

## 3. Deploy to AWS Dev (ECS / Fargate)

Use this once you’re comfortable locally. This is the **current, supported**
path for Agent Foundry in AWS.

### 3.1 One-Time AWS Setup

1. **AWS account & credentials**
   - Configure AWS CLI with the target account (e.g. the `122441748701` dev
     account).
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
   - Target groups `agentfoundry-ui-tg` (port 3000) and `agentfoundry-api-tg`
     (port 8000)
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

See `DEPLOYMENT.md` for the full AWS deployment guide (including DNS, SSL, and
teardown).

---

## 4. Forge Visual Graph Editor

The Forge editor is the primary way to create and manage agents in v0.9.

### Quick Tour

1. **Navigate to Graphs**: `http://localhost:3000/app/graphs`
2. **Create New Agent**: Click "New Graph" → Enter name → Select organization/domain
3. **Add Nodes**: Right-click canvas → Add Process, Decision, Tool Call nodes
4. **Connect Nodes**: Drag from output handle to input handle
5. **Configure Nodes**: Click node → Edit in side panel (name, prompts, conditions)
6. **Save**: Cmd+S or click Save → Version auto-increments (0.0.1 → 0.0.2)
7. **Deploy**: Open version dropdown → Click "Deploy" on desired version

### Key Features
- **Version History**: Dropdown shows all saved versions with timestamps
- **Deploy Workflow**: Mark a specific version as "deployed" for production
- **State Schema**: Define state variables in the "State" tab
- **Triggers**: Configure event triggers in the "Triggers" tab
- **Unsaved Changes**: Dialog warns before navigating away with unsaved work

### Documentation
- `docs/FORGE_AI_USER_GUIDE.md` – Full Forge user guide
- `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md` – LangGraph feature coverage

---

## 5. System Agents

Agent Foundry includes 7 system agents that handle platform-level concerns:

| Agent | Purpose |
|-------|---------|
| **IO Agent** | Input/output adapter, channel routing |
| **Supervisor** | Orchestration and worker agent routing |
| **Context** | State management and session context |
| **Coherence** | Response assembly and consistency |
| **Exception** | Error handling and resilience |
| **Observability** | Metrics, tracing, activity logging |
| **Governance** | Security policies and compliance |

### Documentation
- `docs/SYSTEM_AGENTS_DESIGN.md` – Architecture overview
- `docs/SYSTEM_AGENTS_IMPLEMENTATION.md` – Implementation details

---

## 6. LiveKit / Voice Stack

Voice is optional but powerful. Here's where the pieces live:

### Code
- `backend/livekit_service.py` – Session creation, tokens, room management
- `backend/voice_agent_worker.py` – Voice I/O agent handling
- `livekit-config.yaml` – Server config for Docker LiveKit service

### Documentation
- `docs/LIVEKIT_SETUP.md` – LiveKit + Docker + backend wiring

---

## 7. Where to Go Next

### Day 1
- Get the stack running locally (`./start_foundry.sh`, `npm run dev`)
- Open Forge at `http://localhost:3000/app/graphs`
- Create your first agent graph

### Day 2-3
- Explore the codebase:
  - `backend/main.py` – API endpoints
  - `backend/db.py` – Database layer
  - `app/app/graphs/` – Forge frontend
- Review Forge docs: `docs/FORGE_AI_USER_GUIDE.md`

### When Touching Infra
- Read `docs/DEPLOYMENT.md`
- Use `./scripts/monitor_aws_health.sh`

---

## Summary

After completing this guide, you should be able to:

- Run Agent Foundry locally with Docker Compose + Next.js
- Create and deploy agents using the Forge visual editor
- Understand the multi-agent architecture (IO → Supervisor → Workers)
- Know where to find documentation for each subsystem
- Deploy to AWS ECS/Fargate when ready
