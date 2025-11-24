# Agent Foundry - Platform Deep Dive

**Version:** 0.8.1-dev **Last Updated:** November 17, 2025 **Status:**
Production-ready UI shell, AWS ECS deployment ready

---

## Executive Summary

**Agent Foundry** is a modern **agentic platform** for building, deploying, and
operating AI agents at enterprise scale. Positioned as "Heroku for AI Agents,"
it enables organizations to transform domain expertise into production-ready AI
systems through a declarative approach using the Domain Intelligence
Specification (DIS).

**Current Version:** v0.8.1-dev **Status:** Active development -
production-ready UI shell, AWS ECS deployment ready

---

## 🏗️ High-Level Architecture

### The Platform Concept

Agent Foundry is **a platform run by AI agents, for building AI agents**. The
platform itself is orchestrated by system agents that handle:

- **Marshal Agent** - YAML validation, hot-reload, health monitoring
- **Admin Assistant** - User onboarding, troubleshooting, navigation
- **DataAgent** - NL→SQL queries for control plane
- **IOAgent** - LiveKit integration, voice/video adaptation
- **Supervisor Agent** - Routes user input to domain-specific agents

### Information Hierarchy

```
Organization (tenant/billing boundary)
  ├─ Projects (work initiatives)
  ├─ Domains (knowledge verticals - REUSABLE across projects)
  └─ Teams (functional groups)

Example: CIBC Organization
  ├─ Projects: Card Services, Investment Platform, Mobile Banking
  ├─ Domains: Banking, Customer Service, Fraud Prevention (shared across projects)
  └─ Teams: Card Support Team, Security Team, Engineering Team
```

This structure enables **domain knowledge reuse** - the "Banking" domain can
power multiple projects simultaneously.

---

## 🛠️ Infrastructure

### Local Development (Docker Compose)

**Stack Components:**

```yaml
services:
  - livekit: # WebRTC voice/video (port 7880)
  - redis: # State management & checkpointing
  - foundry-backend: # FastAPI (port 8000)
  - foundry-compiler: # DIS→YAML compiler (port 8002)
  - forge-service: # Visual agent builder (port 8003)
  - agent-foundry-ui: # Next.js (port 3000)
  - voice-agent-worker: # LiveKit agent worker
  - n8n: # Workflow automation (port 5678)
  - mcp-integration: # MCP tool gateway (port 8100)
  - postgres: # Control plane DB (port 5432)
```

**Start Command:**

```bash
./start_foundry.sh    # Brings up Docker services
npm run dev          # Starts Next.js UI
```

### AWS Deployment (ECS Fargate + ALB)

**Terraform-managed infrastructure (`infra/`):**

- **VPC + Subnets** - Isolated network for Agent Foundry cluster
- **ALB** `agentfoundry-alb` routing:
  - `/` → UI target group (port 3000)
  - `/api/*` → API target group (port 8000)
- **ECS Services:**
  - `agentfoundry-ui-svc` (UI container)
  - `agentfoundry-api-svc` (backend container)
- **ECR Repositories:**
  - `agentfoundry-ui`
  - `agentfoundry-backend`
  - `agentfoundry-compiler`
  - `agentfoundry-forge`
- **Route 53** - DNS: `foundry.ravenhelm.ai` → ALB

**Deployment Script:**

```bash
./configure_build_env.sh  # One-time buildx + ECR login
./deploy_dev.sh          # Build linux/amd64, push to ECR, force deploy
```

**Monitoring Scripts:**

```bash
./scripts/monitor_local_health.sh   # Docker, ports, services
./scripts/monitor_aws_health.sh     # ECS + ALB health
./scripts/check_alb_targets.sh      # Target group status
```

---

## 💻 Technology Stack

### Frontend (Next.js 14 + React 18)

**Framework:**

- Next.js 14 App Router
- React 18.2.0
- TypeScript 5.3.3

**UI Components:**

- Shadcn UI + Radix UI primitives
- Ravenhelm dark theme
- TailwindCSS 3.4 + tailwindcss-animate
- Framer Motion for animations

**Key Libraries:**

- **LiveKit:** `@livekit/components-react` 2.9.15 - Voice/video UI
- **ReactFlow:** 11.11.4 - Visual graph editor (Forge)
- **Monaco Editor:** 4.7.0 - Code editing
- **TanStack Query:** 5.17.0 - Server state management
- **Zustand:** 4.5.0 - Client state management
- **React Hook Form + Zod** - Form validation
- **NextAuth:** 4.24.13 - Authentication

### Backend (FastAPI + Python 3.12)

**Core Stack:**

```python
# Web Framework
fastapi==0.121.2
uvicorn==0.38.0

# LLM & Agent Framework
langchain==1.0.7
langgraph==1.0.3
langchain-openai==1.0.3
langchain-anthropic==1.0.4
anthropic==0.73.0
openai==2.8.0

# Voice Integration
livekit==1.0.19
livekit-agents==1.2.18
livekit-plugins-deepgram==1.2.18
livekit-plugins-openai==1.2.18
livekit-plugins-elevenlabs==1.2.18

# Databases
psycopg2-binary==2.9.10  # PostgreSQL
motor==3.7.0             # MongoDB (async)
redis==7.0.1             # Cache/state

# Security
bcrypt==4.2.1            # Password hashing
PyJWT==2.10.1            # JWT tokens

# Utilities
httpx==0.28.1            # Async HTTP
pydantic==2.12.4         # Data validation
python-dotenv==1.2.1     # Env management
```

### Databases

**SQLite** (Control Plane - Primary in dev):

- Organizations, domains, projects, teams
- Agents, deployments, sessions
- RBAC (roles, permissions, user_roles)
- Forge (state_schemas, triggers, workflows, graphs)
- Location: `data/foundry.db`

**PostgreSQL** (Production):

- Same schema as SQLite (portable)
- Row-Level Security (RLS) for multi-tenancy
- Backup/restore utilities

**MongoDB** (Dossier Storage - Isolated):

- DIS dossiers with encryption
- Isolated security boundary
- Document-based storage for complex schemas

**Redis**:

- LangGraph checkpointing
- LiveKit session state
- Agent draft autosave (24h TTL)
- Permission caching

---

## 🎯 Core Features & Use Cases

### 1. Visual Agent Builder (Forge)

**What It Does:**

- Drag-and-drop LangGraph agent designer
- ReactFlow-based graph editor
- Node types: Entry Point, Listen, Process, Respond, Decision, Tool Call, End
- Real-time Python code generation
- Autosave to Redis (3s interval)
- Git-like versioning with commits

**Use Case:** Build a customer support agent by connecting nodes visually
instead of writing Python code.

### 2. Domain Intelligence Compiler

**What It Does:**

- Upload DIS dossiers (JSON) → Generate agent YAML
- Parses domain knowledge into executable agents
- Template-based code generation
- Automatic agent registration

**Use Case:** A banking compliance expert uploads a `cibc-fraud-detection.json`
dossier. The compiler generates `fraud-detection-agent.yaml` with all rules
encoded, ready to deploy.

### 3. Voice Agents (LiveKit)

**What It Does:**

- Real-time voice conversations with agents
- Speech-to-Text (Deepgram)
- Text-to-Speech (OpenAI or ElevenLabs)
- WebRTC media transport
- Voice session management with tokens

**Use Case:** Customer calls CIBC card services, speaks to voice agent for fraud
verification, agent routes to PWM specialist if needed.

### 4. Multi-Agent Orchestration (LangGraph)

**Canonical Flow:**

```
User Input
   ↓
IOAgent (I/O Adapter)
   ↓
Supervisor Agent (routes based on intent)
   ├─→ PM Agent (project management)
   ├─→ Banking Agent (banking domain)
   ├─→ Support Agent (customer service)
   └─→ Tool Agent (executes MCP tools)
   ↓
IOAgent (formats response)
   ↓
User Output (text or voice)
```

**Key Principle:** ALL reasoning flows through LangGraph StateGraph - no direct
LLM calls bypassing the graph.

### 5. MCP Tool Integration (n8n)

**What It Does:**

- n8n workflow automation integration
- 1000+ pre-built integrations (Notion, GitHub, Slack, etc.)
- MCP gateway translates agent tool calls → n8n workflows
- Health tracking and metrics per tool

**Use Case:** Agent needs to create a Notion story → calls `create_notion_story`
tool → MCP gateway invokes n8n workflow → story created in Notion.

### 6. Natural Language Queries (DataAgent)

**What It Does:**

- Natural language → SQL translation
- Query control plane (orgs, domains, agents, deployments)
- LangGraph-based NL→SQL→results pipeline

**Use Case:** Admin asks "How many agents are deployed in production?" →
DataAgent generates SQL, executes, returns answer.

---

## 🔒 Security & RBAC

### Role-Based Access Control

**Architecture:**

```
Platform Owner (global)
  ↓
Organization Admin (org-level)
  ↓
├─ Project Admin
├─ Domain Admin
└─ Team Lead
  ↓
Team Member / User
```

**Permission Model:**

```
<resource>:<action>:<scope>

Examples:
- agent:create          # Create agents in org
- agent:read:org        # View all agents
- agent:update:self     # Update own agents
- session:terminate:org # Terminate any session
- llm:quota:read:self   # View own LLM usage
```

**Features:**

- Fine-grained permissions (atomic authorities)
- API key support for programmatic access
- Service accounts for backend services
- Audit logging for all privileged operations
- LLM usage tracking and quota enforcement
- Row-Level Security (RLS) in PostgreSQL

### Multi-Tenant Isolation

**Mechanisms:**

1. **Database RLS policies** - Postgres session variables (`app.current_org`)
2. **Organization-scoped API keys**
3. **Team-based access control**
4. **Domain visibility rules**

**Example RLS Context:**

```python
# Set RLS context per request
await set_rls_context(request, context)
# All queries automatically filtered by org_id
```

### Authentication

**Supported Methods:**

- Google SSO (NextAuth)
- JWT tokens for session management
- API keys (`ak_live_...`) for programmatic access
- Service account credentials

**Environment Security:**

- Secrets in `.env.local` (never committed)
- Encrypted MongoDB dossier storage
- API key hashing with bcrypt
- TLS/SSL in production (Route 53 + ALB)

---

## 📁 Codebase Organization

```
agentfoundry/
├── app/                          # Next.js 14 frontend
│   ├── components/layout/        # TopNav, LeftNav, AppMenu
│   ├── api/                      # Next.js API routes
│   ├── app/                      # App Router pages
│   │   ├── page.tsx              # Dashboard
│   │   ├── agents/               # Agent management UI (DELETED in refactor)
│   │   ├── chat/                 # Text chat UI (DELETED)
│   │   └── forge/                # Visual agent builder (DELETED)
│   ├── lib/                      # Client utilities
│   └── providers.tsx             # Context providers
│
├── backend/                      # FastAPI server
│   ├── main.py                   # Core API (1878 lines!)
│   ├── db.py                     # SQLite/PostgreSQL database
│   ├── livekit_service.py        # LiveKit integration
│   ├── rbac_service.py           # RBAC business logic
│   ├── rbac_middleware.py        # Auth/authz decorators
│   ├── routes/                   # API route modules
│   │   ├── hierarchy.py          # Org/domain/project CRUD
│   │   ├── storage_routes.py     # Agent storage & versioning
│   │   ├── function_catalog.py   # MCP tool catalog
│   │   └── favorites.py          # User favorites
│   ├── agents/                   # System agents
│   │   └── supervisor_agent.py   # Central routing agent
│   ├── api/                      # Additional API modules
│   │   └── monitoring.py         # Metrics & health
│   └── middleware/               # Request/response middleware
│
├── agent/                        # LangGraph agents (Python)
│   ├── pm_graph.py               # PM agent (LangGraph 1.0)
│   ├── data_agent.py             # NL→SQL agent
│   └── admin_assistant_agent.py  # Platform assistant
│
├── agents/                       # Agent registry (YAML)
│   ├── agents.manifest.yaml      # Agent catalog
│   ├── dev_supervisor_agent.yaml # Supervisor config
│   ├── dev_io_agent.yaml         # Voice I/O agent
│   ├── storage_agent.yaml        # Storage agent
│   └── templates/                # Agent templates
│       ├── user-agent-react.yaml
│       ├── channel-workflow-basic.yaml
│       └── cibc-*.yaml           # CIBC banking templates
│
├── mcp/                          # MCP integration layer
│   ├── integration_server/       # MCP gateway (FastAPI)
│   ├── tools/                    # MCP tool implementations
│   │   ├── n8n_client.py         # n8n integration
│   │   └── storage_tools.py      # Agent storage tools
│   └── converters/               # Code transformers
│       ├── python_to_reactflow.py
│       └── reactflow_to_python.py
│
├── compiler/                     # DIS compiler service
│   ├── main.py                   # Compiler API
│   └── dis_compiler.py           # DIS→YAML generator
│
├── forge_service/                # Forge builder API
│   └── main.py                   # Graph management API
│
├── infra/                        # Terraform AWS infra
│   ├── main.tf                   # VPC, ALB, ECS
│   ├── ecr.tf                    # Container registries
│   └── route53.tf                # DNS configuration
│
├── docs/                         # Comprehensive documentation
│   ├── RBAC_IMPLEMENTATION.md
│   ├── STORAGE_LAYER_IMPLEMENTATION.md
│   ├── FORGE_LANGGRAPH_GAP_ANALYSIS.md
│   ├── PLATFORM_DEEPDIVE.md      # This document
│   └── ... (40+ docs)
│
├── scripts/                      # Ops & admin scripts
│   ├── monitor_local_health.sh
│   ├── monitor_aws_health.sh
│   ├── seed_hierarchy_data.py
│   └── sync_n8n_manifest.py
│
├── tests/                        # Test suites
│   ├── unit/
│   ├── integration/
│   └── test_storage_agent.py
│
├── docker-compose.yml            # Local dev stack
├── .env.example                  # Environment template
├── START_HERE.md                 # Onboarding guide
└── README.md                     # System overview
```

**Notable Deletions (per git status):**

- `app/chat/`, `app/forge/`, `app/agents/` pages deleted (likely migrated to new
  structure)
- Multiple test files removed
- Legacy deployment scripts cleaned up

---

## 🤖 Agent System (LangGraph Architecture)

### Marshal Agent - Platform Orchestrator

**Responsibilities:**

- Load all agents from `agents/` directory
- YAML validation and schema enforcement
- Hot-reload on file changes (file watcher)
- Health monitoring (60s interval)
- Agent registry management
- Metrics collection (uptime, success rate, invocation count)

**Registry Structure:**

```python
agents = {
  "agent_id": AgentInstance(
    metadata: {name, version, description, tags},
    config: {spec, workflow, nodes, edges},
    status: {state, phase, uptime, executions},
    loaded_at, last_invoked
  )
}
```

### LangGraph Pattern

**All agents follow this canonical pattern:**

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Define state
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # ... agent-specific fields

# Define tools
@tool
def my_tool(arg: str) -> str:
    """Tool description for LLM."""
    return f"Result: {arg}"

# Build graph
llm = ChatOpenAI(model="gpt-4")
graph = create_react_agent(llm, tools=[my_tool])

# Invoke
result = await graph.ainvoke({
    "messages": [HumanMessage(content="User input")]
})
```

**Key Principles:**

- NO direct LLM calls outside graph
- NO bypassing StateGraph for reasoning
- ALL state transitions through graph
- Checkpointing via Redis for long-running sessions

### System Agents vs User Agents

**System Agents (Protected):**

- Editable only by Global Admins
- Critical platform functionality
- Examples: Marshal, Supervisor, IOAgent, DataAgent, Admin Assistant

**User Agents:**

- Created by Domain Admins/Developers
- Domain-scoped visibility
- Can be cloned, tested in Playground, deployed

**Channel Workflows:**

- Multi-agent orchestrations for channels (voice, web, SMS)
- Define trigger → graph → response flows
- Stored in `channel_workflows` table

---

## 🎙️ Voice Integration (LiveKit)

### Architecture

```
User speaks
   ↓
LiveKit Room (WebRTC)
   ↓
Deepgram STT → Text
   ↓
IO Agent → Supervisor Agent → Domain Agent
   ↓
Response Text
   ↓
OpenAI/ElevenLabs TTS → Audio
   ↓
LiveKit streams to user
```

### Components

**LiveKit Server:**

- Docker container: `livekit/livekit-server:latest`
- Config: `livekit-config.yaml`
- Ports: 7880 (HTTP/WS), 7881 (RTC TCP), 40000-40100 (UDP)

**Voice Agent Worker:**

- Python worker: `backend/io_agent_worker.py`
- Listens for LiveKit room events
- Routes voice input to Supervisor Agent
- Streams TTS responses back to room

**Frontend Integration:**

- `@livekit/components-react` - React components
- LiveKit room connection via token
- Real-time audio/video UI
- Session management

**Voice Session Flow:**

1. Frontend calls `/api/voice/session` with user_id, agent_id
2. Backend creates LiveKit room and generates token
3. Frontend joins room with token
4. Voice agent worker joins room automatically
5. User speaks → STT → Agent → TTS → User hears response

---

## 💾 Data Layer

### SQLite Schema (Primary in dev)

**Core Tables:**

```sql
-- Tenant hierarchy
organizations (id, name, tier, created_at)
projects (id, organization_id, name, description)
domains (id, organization_id, name, display_name, version)
teams (id, organization_id, name, description, lead_user_id)

-- Users & auth
users (id, email, name, organization_id, created_at)
user_roles (user_id, role_id, organization_id, granted_by)

-- RBAC
roles (id, name, description, scope, is_system)
permissions (id, code, description, resource, action, scope)
role_permissions (role_id, permission_id)
api_keys (id, user_id, key_hash, key_prefix, expires_at)

-- Agents & deployments
agents (id, organization_id, domain_id, name, version, status)
sessions (id, agent_id, user_id, status, started_at)
deployments (id, project_id, agent_id, url, status)

-- Forge designer
state_schemas (id, name, description, fields)
triggers (id, name, type, channel, config)
channel_workflows (id, channel, name, nodes, edges)
graphs (id, type, organization_id, domain_id, metadata, spec)

-- Monitoring
audit_logs (id, user_id, organization_id, action, resource_type)
llm_usage (id, organization_id, user_id, model, tokens, cost)
llm_quotas (id, organization_id, quota_type, limit_value)
```

### Redis Keys

**Agent Drafts:**

```
agent:draft:{agent_id}  # Autosaved ReactFlow graph (24h TTL)
user:drafts:{user_id}   # Set of draft agent IDs
```

**Session State:**

```
session:{session_id}:state  # LangGraph checkpoint
livekit:room:{room_name}    # LiveKit room metadata
```

**Permission Cache:**

```
rbac:user:{user_id}:org:{org_id}:permissions  # Cached permission set (5min TTL)
```

### MongoDB (Dossier Storage)

**Collections:**

```javascript
dossiers {
  _id: ObjectId,
  organization_id: String,
  domain_id: String,
  name: String,
  version: String,
  content: Binary,  // Encrypted DIS JSON
  created_by: String,
  created_at: ISODate
}
```

**Security:**

- Isolated security boundary (separate service)
- Encryption at rest via `DOSSIER_ENCRYPTION_KEY`
- TLS-encrypted connections in production
- Access only via Storage Agent

---

## 🔄 Development Workflow

### Local Development Setup

**1. Prerequisites:**

```bash
# Required
- Docker Desktop
- Node.js 20+
- Python 3.11+

# Optional
- AWS CLI (for AWS work)
```

**2. Environment Configuration:**

```bash
cp .env.example .env.local

# Edit .env.local - Minimum required:
OPENAI_API_KEY=sk-...
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

**3. Start Services:**

```bash
# Terminal 1: Backend services
./start_foundry.sh

# Terminal 2: Frontend
npm install
npm run dev
```

**4. Verify:**

```bash
# Check services
curl http://localhost:8000/health   # Backend
curl http://localhost:3000          # UI
curl http://localhost:7880          # LiveKit
```

### Hot Reload & Development Loop

**Backend (Python):**

- FastAPI auto-reloads on file changes
- Docker volumes mount source code
- Agents hot-reload via Marshal file watcher

**Frontend (Next.js):**

- Fast Refresh for instant updates
- No container restart needed

**Agent Development:**

1. Edit `agents/my-agent.yaml`
2. Marshal detects change → validates → hot-reloads
3. Test in Playground or via API
4. Deploy when ready

### Testing Agent Changes

**Playground (Text):**

```
http://localhost:3000/playground
→ Select agent
→ Type message
→ See response
```

**Voice Testing:**

```
http://localhost:3000/voice
→ Create session
→ Join LiveKit room
→ Speak to agent
```

**API Testing:**

```bash
curl -X POST http://localhost:8000/api/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "my-agent",
    "input": "Hello",
    "session_id": "test-123",
    "route_via_supervisor": true
  }'
```

---

## 🚀 Deployment

### AWS Deployment Flow

**1. One-Time Setup:**

```bash
# Configure AWS CLI
aws configure --profile agentfoundry

# Initialize Terraform
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your AWS account ID, ACM cert ARN

terraform init
terraform plan
terraform apply
```

**2. Configure Build Environment:**

```bash
./configure_build_env.sh
# Creates Docker buildx builder
# Logs into ECR
```

**3. Deploy Application:**

```bash
./deploy_dev.sh
```

**What `deploy_dev.sh` does:**

- Builds linux/amd64 images for:
  - UI (`agentfoundry-ui`)
  - Backend (`agentfoundry-backend`)
  - Compiler (`agentfoundry-compiler`)
  - Forge (`agentfoundry-forge`)
- Pushes to ECR
- Forces ECS service redeployment:
  ```bash
  aws ecs update-service \
    --cluster agentfoundry-cluster \
    --service agentfoundry-ui-svc \
    --force-new-deployment
  ```

**4. Verify Deployment:**

```bash
# Check ECS services
./scripts/monitor_aws_health.sh

# Check ALB target health
./scripts/check_alb_targets.sh

# Visit production URL
open https://foundry.ravenhelm.ai
```

### Production Architecture

```
Internet
   ↓
Route 53 (foundry.ravenhelm.ai)
   ↓
Application Load Balancer
   ├─ Target Group: UI (port 3000)
   │   → ECS Service: agentfoundry-ui-svc
   │      → Fargate Tasks (2+ replicas)
   │         → ECR Image: agentfoundry-ui:latest
   │
   └─ Target Group: API (port 8000)
       → ECS Service: agentfoundry-api-svc
          → Fargate Tasks (2+ replicas)
             → ECR Image: agentfoundry-backend:latest
```

**Features:**

- Auto-scaling based on CPU/memory
- Health checks every 30s
- Zero-downtime deployments
- SSL/TLS termination at ALB
- VPC isolation with security groups

---

## 🎓 Key Use Cases

### 1. Banking - CIBC Card Services

**Scenario:** Customer calls about fraudulent charge

**Flow:**

1. Voice call → LiveKit room
2. IOAgent (STT) → "I see a charge I didn't make"
3. Supervisor routes to `cibc-fraud-detection-agent`
4. Agent:
   - Verifies identity via KYC tools
   - Checks transaction against fraud patterns (MCP tool)
   - Calculates risk score
   - Blocks card if risk > 85
   - Routes to PWM specialist if needed
5. Response via TTS → Customer hears: "I've blocked your card..."

**Templates Available:**

- `cibc-card-activate-ivr.yaml`
- `cibc-card-block-verified.yaml`
- `cibc-session-verify-with-fraud-score.yaml`
- `cibc-session-route-to-pwm.yaml`

### 2. Engineering - Project Management

**Scenario:** Create engineering stories from Slack messages

**Flow:**

1. Slack message: "We need to add user authentication"
2. PM Agent (LangGraph):
   - Parses intent → Create story
   - Extracts: Epic="Auth", Priority=P1
   - Calls `create_notion_story` tool (MCP)
   - n8n workflow creates Notion story
3. Response: "✅ Story created: [Notion URL]"

### 3. Platform Admin - Natural Language Queries

**Scenario:** "How many agents are deployed in production?"

**Flow:**

1. Admin types question in UI
2. DataAgent (LangGraph):
   - NL → SQL: `SELECT COUNT(*) FROM deployments WHERE environment='prod'`
   - Executes query on SQLite
   - Formats result
3. Response: "There are 12 agents deployed in production."

---

## 📊 Current Status & Roadmap

### ✅ Completed (v0.8.0 - v0.8.1)

- LiveKit Docker containerization
- Next.js 14 UI shell with Shadcn
- FastAPI backend with health checks
- LangGraph agent orchestration
- Marshal Agent hot-reload system
- RBAC with fine-grained permissions
- SQLite/PostgreSQL control plane
- Forge visual agent builder (ReactFlow)
- Python ↔ ReactFlow bidirectional conversion
- Agent autosave & git-like versioning
- MCP tool integration (n8n)
- AWS ECS deployment pipeline
- Comprehensive documentation (40+ docs)

### 🚧 In Progress

- Voice UI improvements
- Multi-tenant subdomain routing (`cibc.foundry.ravenhelm.ai`)
- Enhanced monitoring & observability
- Agent marketplace

### 📋 Planned

**Phase 2: Multi-Tenancy & Scale**

- Advanced RBAC (custom roles)
- Audit logs & compliance dashboards
- Domain template marketplace

**Phase 3: Enterprise Features**

- Approval workflows for agent changes
- PCI-DSS/HIPAA compliance checklists
- APM & distributed tracing
- Auto-scaling agent instances

**Phase 4: AI Platform Features**

- Multi-agent conditional workflows
- Advanced RAG (hybrid search, reranking)
- A/B testing for agents
- Conversation analytics

---

## 🔍 Notable Technical Decisions

### Why LangGraph 1.0?

- Canonical pattern for multi-agent orchestration
- Built-in checkpointing for long-running conversations
- Conditional routing without manual state management
- Production-ready reliability

### Why SQLite + PostgreSQL?

- SQLite for fast local dev (zero config)
- Same schema works on PostgreSQL for production
- Easy migration path
- Portable database file for backups

### Why LiveKit over Twilio?

- Self-hosted option (cost control)
- WebRTC for low latency
- Open source with Docker support
- Better integration with LangGraph agents

### Why MCP + n8n?

- 1000+ pre-built integrations (Notion, GitHub, Slack)
- Visual workflow builder for non-developers
- MCP provides standardized tool interface
- Easier than building each integration from scratch

---

## 📚 Essential Documentation

**Start Here:**

- `START_HERE.md` - 30-minute onboarding
- `README.md` - System overview
- `AGENT_FOUNDRY_VISION.md` - Product vision & roadmap

**Architecture:**

- `docs/RBAC_IMPLEMENTATION.md` - Security & permissions
- `docs/STORAGE_LAYER_IMPLEMENTATION.md` - Agent persistence
- `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md` - Forge capabilities
- `docs/ELEVENLABS_INTEGRATION.md` - Voice TTS setup

**Operations:**

- `DOCKER_DEV_WORKFLOW.md` - Local development
- `DEPLOYMENT.md` - AWS deployment guide
- `LIVEKIT_SETUP.md` - Voice infrastructure
- `scripts/QUICK_REFERENCE.md` - Admin commands

---

## 🎯 API Reference

### Core Endpoints

**Health & Status:**

```
GET  /health              # Comprehensive health check
GET  /                    # Root health check
GET  /api/system/metrics  # System metrics
GET  /api/system/logs     # Application logs
```

**Authentication & RBAC:**

```
POST /api/auth/user-permissions  # Get user permissions by email
GET  /api/auth/me                # Get current user info
```

**Voice (LiveKit):**

```
POST   /api/voice/session         # Create voice session
GET    /api/voice/room/{room}     # Get room info
DELETE /api/voice/session/{room}  # End session
```

**Agents:**

```
GET    /api/agents                # List all agents
GET    /api/agents/{id}           # Get agent details
GET    /api/agents/{id}/status    # Get agent status
GET    /api/agents/{id}/health    # Get health metrics
POST   /api/agents/{id}/reload    # Hot-reload agent
POST   /api/agents/validate       # Validate agent YAML
POST   /api/agent/invoke          # Invoke agent via Supervisor
```

**Control Plane:**

```
GET  /api/control/organizations   # List orgs with domains
GET  /api/control/agents          # List agents (filtered)
POST /api/control/query           # NL query via DataAgent
```

**Integrations (MCP):**

```
GET  /api/integrations/tools              # Integration catalog
GET  /api/integrations/tools/{tool}       # Tool details
POST /api/integrations/tools/{tool}/invoke # Invoke tool
GET  /api/integrations/configs            # List configs
POST /api/integrations/configs/{tool}     # Upsert config
```

**Storage (Forge):**

```
POST /api/storage/autosave    # Autosave draft
POST /api/storage/commit      # Commit version
GET  /api/storage/history/:id # Version history
POST /api/storage/restore     # Restore version
GET  /api/storage/draft/:id   # Get draft
POST /api/storage/import      # Import Python code
POST /api/storage/export      # Export to Python
GET  /api/storage/drafts      # List user drafts
```

**Graphs (Unified API):**

```
GET    /api/graphs           # List graphs (filtered)
GET    /api/graphs/{id}      # Get graph
POST   /api/graphs           # Create/update graph
DELETE /api/graphs/{id}      # Delete graph
POST   /api/graphs/{id}/deploy # Deploy graph
```

**Forge Designer:**

```
GET    /api/forge/state-schemas        # List state schemas
POST   /api/forge/state-schemas        # Create/update schema
DELETE /api/forge/state-schemas/{id}   # Delete schema
GET    /api/forge/triggers              # List triggers
POST   /api/forge/triggers              # Create/update trigger
GET    /api/forge/channel-workflows    # List workflows
POST   /api/forge/channel-workflows    # Create/update workflow
POST   /api/designer/generate-python   # ReactFlow → Python
POST   /api/designer/validate-graph    # Validate graph structure
```

**Admin (SQLite):**

```
GET    /api/admin/sqlite/backups        # List backups
POST   /api/admin/sqlite/backups        # Create backup
POST   /api/admin/sqlite/backups/restore # Restore backup
GET    /api/admin/sqlite/tables         # List tables
GET    /api/admin/sqlite/tables/{table}/schema # Table schema
GET    /api/admin/sqlite/tables/{table}/rows   # Table rows
POST   /api/admin/sqlite/tables/{table}/rows   # Insert row
PATCH  /api/admin/sqlite/tables/{table}/rows/{rowid} # Update row
DELETE /api/admin/sqlite/tables/{table}/rows/{rowid} # Delete row
```

**WebSockets:**

```
WS /ws/chat                   # Text chat WebSocket
WS /api/events/subscribe      # Real-time event subscription
```

---

## 🧪 Testing Strategy

### Test Organization

```
tests/
├── unit/                    # Unit tests
│   ├── backend/            # Backend unit tests
│   └── mcp/                # MCP tools unit tests
├── integration/            # Integration tests
│   └── test_mcp_integration_server.py
└── test_storage_agent.py   # Storage agent tests
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_storage_agent.py

# With coverage
pytest --cov=backend --cov=agent --cov=mcp

# Integration tests only
pytest tests/integration/
```

### Test Coverage Areas

**Backend:**

- API endpoint validation
- RBAC permission checks
- Database operations
- Agent invocation
- LiveKit integration

**Agents:**

- LangGraph state transitions
- Tool invocations
- Error handling
- Checkpointing

**MCP:**

- Tool catalog loading
- n8n workflow invocation
- Code conversion (Python ↔ ReactFlow)

---

## 🔧 Troubleshooting

### Common Issues

**Docker Services Won't Start:**

```bash
# Check Docker is running
docker ps

# View service logs
docker-compose logs -f foundry-backend
docker-compose logs -f livekit

# Restart services
docker-compose down
docker-compose up -d
```

**LiveKit Connection Failed:**

```bash
# Check LiveKit is running
curl http://localhost:7880

# Verify environment variables
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Check Docker logs
docker-compose logs livekit
```

**Agent Hot-Reload Not Working:**

```bash
# Check Marshal Agent logs
docker-compose logs foundry-backend | grep Marshal

# Manually reload agent
curl -X POST http://localhost:8000/api/agents/{agent_id}/reload
```

**Database Migration Issues:**

```bash
# Rebuild database
rm data/foundry.db
docker-compose restart foundry-backend
# Backend will recreate schema on startup
```

**Permission Denied Errors:**

```bash
# Check RBAC roles
curl http://localhost:8000/api/auth/user-permissions \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Seed RBAC data
python backend/seed_rbac_sqlite.py
```

---

## 📞 Support & Resources

**Documentation:**

- Platform Deep Dive: `docs/PLATFORM_DEEPDIVE.md` (this document)
- Quick Start: `START_HERE.md`
- Full Docs: `docs/` directory (40+ documents)

**Monitoring:**

- Local Health: `./scripts/monitor_local_health.sh`
- AWS Health: `./scripts/monitor_aws_health.sh`
- Application Logs: `http://localhost:8000/api/system/logs`

**Community:**

- Repository: GitLab (private)
- Issues: Internal tracker
- Domain: `foundry.ravenhelm.ai` (production)

---

## Summary

Agent Foundry is a **production-ready, enterprise-grade agentic platform** that
uniquely combines:

✅ **Domain-centric architecture** (reusable knowledge across projects) ✅
**Visual agent builder** (Forge) with Python codegen ✅ **Voice-first design**
(LiveKit + LangGraph) ✅ **Enterprise RBAC** (fine-grained permissions, RLS) ✅
**Multi-agent orchestration** (Supervisor + domain agents) ✅ **AWS-native
deployment** (ECS Fargate + ALB) ✅ **Comprehensive tooling** (1000+
integrations via n8n) ✅ **Developer experience** (hot-reload, autosave,
git-like versioning)

The platform is **positioned for regulated industries** (banking, healthcare,
aviation) where compliance, auditability, and domain expertise are critical. The
codebase is mature, well-documented, and actively developed.

---

**Document Version:** 1.0 **Last Updated:** November 17, 2025 **Maintained By:**
Platform Team
