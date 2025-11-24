# Agent Foundry - Vision & Architecture

**Version:** 0.8.0  
**Date:** November 16, 2025  
**Status:** MVP Architecture - Ready to Build

---

## Executive Summary

**Agent Foundry** is the enterprise platform for building, deploying, and
managing AI agents at scale. Positioned as "Heroku for AI Agents," it enables
organizations to transform domain expertise into production-ready AI systems
through a declarative approach using the Domain Intelligence Specification
(DIS).

### Core Value Proposition

- **Upload** a DIS dossier (world model) → **Get** a deployed, voice-enabled AI
  agent
- **Reuse** domain knowledge across multiple projects
- **Scale** from prototype to production without infrastructure complexity
- **Comply** with industry regulations through domain-level governance

---

## Product Vision

### The Meta-Platform Concept

Agent Foundry is **a platform run by AI agents, for building AI agents**. The
platform itself is orchestrated by system agents that handle:

- **Marshal Agent**: YAML validation, hot-reload orchestration, health
  monitoring
- **Foundry Admin Assistant**: User onboarding, platform navigation,
  troubleshooting
- **DataAgent**: RAG ingestion, vector store management, dataset indexing
- **IOAgent**: LiveKit integration, voice/video adaptation, real-time
  communication

These system agents are **protected** - editable only by Global Admins - while
user-created agents operate within domain and project boundaries.

### Target Users

1. **Enterprise IT Leaders**: Deploy agents without building AI infrastructure
2. **Domain Experts**: Transform knowledge into agents via DIS Designer
   (separate tool)
3. **Development Teams**: Build custom agents using Forge visual builder or YAML
4. **Business Units**: Rapid prototyping and deployment of domain-specific
   agents

---

## Information Architecture

### Organizational Hierarchy

```
Organization (tenant/billing boundary)
  ├─ Projects (work initiatives)
  ├─ Domains (knowledge verticals)
  └─ Teams (functional groups)

Relationships:
  • Teams ↔ Projects (many:many)
  • Teams ↔ Domains (many:many)
  • Projects ↔ Domains (many:many)
  • Teams → Users (one:many)
```

### Entity Definitions

#### Organization

**Purpose**: Tenant and billing boundary  
**Examples**: "CIBC", "Acme Corp", "Federal Aviation Administration"  
**Attributes**:

- Name, logo, subscription tier
- Global API keys (Anthropic, LiveKit, OpenAI, Deepgram)
- Organization-wide settings (default models, compliance frameworks)

**Ownership**: Managed by Organization Admins

---

#### Project

**Purpose**: Work initiative or product delivery container  
**Examples**: "Card Services Modernization", "Investment Platform Rebuild",
"Mobile Banking App"  
**Attributes**:

- Name, description, timeline
- Associated domains (many:many)
- Assigned teams (many:many)
- Deployments (project-scoped)
- Monitoring (project-scoped)

**Ownership**: Managed by Project Admins

---

#### Domain

**Purpose**: Knowledge vertical or subject matter expertise container  
**Examples**:

- **Industry Verticals**: Banking, Airlines, Utilities, Healthcare
- **Functional Domains**: ITSD, HR, Customer Service, Legal

**Attributes**:

- Name, category (industry vs functional)
- Compliance frameworks (e.g., PCI-DSS, HIPAA, FAA regulations)
- Agents (domain-scoped)
- Datasets (domain-scoped RAG/vector stores)
- Tools (domain-specific MCP integrations)

**Key Capability**: Domains are **reusable across projects**. The "Banking"
domain can power Card Services, Investment Banking, and Mobile Banking projects
simultaneously.

**Ownership**: Managed by Domain Admins (often subject matter experts)

---

#### Team

**Purpose**: Functional group of users organized by role or specialization  
**Examples**: "Card Support Team", "Security Team", "Engineering Team",
"Compliance Auditors"

**Attributes**:

- Name, description, team lead
- Members (users)
- Project assignments (with permissions)
- Domain assignments (with permissions)

**Relationships**:

- A team can work on **multiple projects** (e.g., Security Team works on all
  projects)
- A team can specialize in **multiple domains** (e.g., Card Support Team knows
  Banking + Customer Service)
- Teams bridge **human organization** with **knowledge structure**

**Ownership**: Managed by Team Leads and Organization Admins

---

### Real-World Example

```
CIBC (Organization)
  │
  ├─ Projects
  │    ├─ Card Services Modernization
  │    │    └─ Uses: Banking, Customer Service, Fraud Prevention domains
  │    │
  │    ├─ Investment Platform Rebuild
  │    │    └─ Uses: Banking, Wealth Management domains
  │    │
  │    └─ Mobile Banking App
  │         └─ Uses: Banking, Customer Service domains
  │
  ├─ Domains (Reusable Knowledge)
  │    ├─ Banking
  │    │    ├─ Compliance: PCI-DSS, KYC/AML, Basel III
  │    │    ├─ Agents: fraud-detection, transaction-validator, kyc-screener
  │    │    ├─ Datasets: banking-regulations, product-catalog, risk-models
  │    │    └─ Used by: 3 projects
  │    │
  │    ├─ Customer Service
  │    │    ├─ Frameworks: ITIL, SLA Management
  │    │    ├─ Agents: escalation-router, sentiment-analyzer, ticket-classifier
  │    │    ├─ Datasets: support-scripts, faq-knowledge-base
  │    │    └─ Used by: 2 projects
  │    │
  │    └─ Fraud Prevention
  │         ├─ Compliance: FACTA, GLBA, PSD2
  │         ├─ Agents: anomaly-detector, pattern-matcher, risk-scorer
  │         ├─ Datasets: fraud-patterns, transaction-history
  │         └─ Used by: 2 projects
  │
  └─ Teams (Human Organization)
       ├─ Card Support Team (12 members)
       │    ├─ Works on: Card Services, Mobile Banking
       │    ├─ Specializes in: Banking, Customer Service
       │    └─ Permissions: View, Deploy (no agent editing)
       │
       ├─ Security Team (8 members)
       │    ├─ Works on: All Projects
       │    ├─ Specializes in: Fraud Prevention, Banking
       │    └─ Permissions: View, Edit Agents, Edit Datasets
       │
       └─ Engineering Team (15 members)
            ├─ Works on: All Projects
            ├─ Specializes in: All Domains
            └─ Permissions: Full (infrastructure, deployment, monitoring)
```

---

## Role-Based Access Control (RBAC)

### Role Hierarchy

```
Global Admin (platform-level)
  ↓
Organization Admin (org-level, inherits all org permissions)
  ↓
├─ Project Admin (project-level)
├─ Domain Admin (domain-level)
└─ Team Lead (team-level)
  ↓
Team Member / User (assigned via team membership)
```

### Role Definitions

#### Global Admin

**Scope**: Platform-wide  
**Capabilities**:

- Create/manage organizations
- Edit system agents (Marshal, Admin Assistant, etc.)
- Platform configuration (infrastructure, billing)
- Emergency access to all organizations

**Use Cases**: Platform operators, SRE team

---

#### Organization Admin

**Scope**: Single organization  
**Capabilities**:

- Create projects, domains, teams
- Manage org members and invitations
- Configure org-level API keys and settings
- Access all projects/domains within org
- Assign users to teams
- Create Domain Admins and Project Admins

**Use Cases**: CTO, IT Director, Platform Manager

---

#### Domain Admin

**Scope**: Single domain (e.g., "Banking")  
**Capabilities**:

- Curate domain knowledge (agents, datasets, tools)
- Set domain compliance rules and frameworks
- Manage domain documentation
- Assign teams to domain
- Review/approve agent changes within domain

**Use Cases**: Chief Compliance Officer (Banking domain), ITIL Process Owner
(ITSD domain), Subject Matter Experts

---

#### Project Admin

**Scope**: Single project  
**Capabilities**:

- Manage project settings and metadata
- Add/remove domains from project
- Assign teams to project
- Configure project deployments
- Manage project monitoring and alerting

**Use Cases**: Product Manager, Technical Lead, Delivery Manager

---

#### Team Lead

**Scope**: Single team  
**Capabilities**:

- Manage team membership (add/remove members)
- Request project/domain assignments from admins
- View team performance metrics

**Use Cases**: Engineering Manager, Support Team Lead, Security Team Lead

---

#### Team Member / User

**Scope**: Projects and domains assigned via team membership  
**Capabilities**:

- Use agents in assigned projects/domains
- Deploy agents (if team has permission)
- View monitoring data for team's projects
- Test agents in Playground

**Use Cases**: Engineers, Support Agents, Business Analysts

---

### Permission Model

Permissions are granted **at the team level** when assigning teams to projects
or domains:

#### Team → Project Permissions

```json
{
  "can_view": true,
  "can_deploy": true,
  "can_edit_agents": false,
  "can_configure_channels": false,
  "can_view_monitoring": true
}
```

#### Team → Domain Permissions

```json
{
  "can_view": true,
  "can_edit_agents": false,
  "can_edit_datasets": false,
  "can_create_tools": false
}
```

**Examples**:

- **Card Support Team** → "Card Services Modernization" project:
  - ✓ View, ✓ Deploy, ✗ Edit Agents
- **Security Team** → "Fraud Prevention" domain:

  - ✓ View, ✓ Edit Agents, ✓ Edit Datasets

- **Engineering Team** → All projects, all domains:
  - ✓ Full permissions

---

## Navigation & User Interface

### Context Switching

Users navigate through a **three-level context hierarchy**:

```
┌────────────────────────────────────────────────────────┐
│ 🏭 [CIBC ▾] / [Card Services ▾] / [Banking ▾]  🔔 👤 │
│     Org          Project            Domain             │
└────────────────────────────────────────────────────────┘
```

**Context Selector Behavior**:

- Click **[CIBC ▾]** → Dropdown shows all orgs user has access to
- Click **[Card Services ▾]** → Dropdown shows all projects in CIBC
- Click **[Banking ▾]** → Dropdown shows all domains in Card Services project

**URL Structure (MVP)**:

```
/dashboard?org=cibc&project=card-services&domain=banking
/agents?org=cibc&project=card-services&domain=banking
```

**URL Structure (Future - Subdomains)**:

```
cibc.foundry.ravenhelm.ai/card-services/banking/dashboard
cibc.foundry.ravenhelm.ai/card-services/banking/agents
```

---

### Primary Navigation

```
┌──────────────────────────┐
│ 🏠 Dashboard             │ ← Domain overview within project context
├──────────────────────────┤
│ BUILD                    │
├──────────────────────────┤
│ 🏭 Compiler              │ ← Upload DIS dossiers → Generate agent YAML
│ 🔨 Forge                 │ ← Visual agent builder (manual creation)
├──────────────────────────┤
│ RESOURCES                │
├──────────────────────────┤
│ 🤖 Agents                │ ← Domain-scoped agents
│ 🗄️  Datasets             │ ← Domain-scoped RAG/vector stores
│ 🔧 Tools                 │ ← Domain-specific MCP tools
├──────────────────────────┤
│ DEPLOY & TEST            │
├──────────────────────────┤
│ 🎮 Playground            │ ← Test agents (text + voice)
│ 📡 Channels              │ ← LiveKit rooms, voice/video config
│ 🚀 Deployments           │ ← Active deployments (project-scoped)
│ 📊 Monitoring            │ ← Logs, metrics, events (project-scoped)
├──────────────────────────┤
│ ORGANIZE                 │
├──────────────────────────┤
│ 🌐 Domain Library        │ ← Browse all org domains
│ 📋 Project Overview      │ ← All domains in current project
│ 👥 Teams                 │ ← Org teams (visible to admins)
├──────────────────────────┤
│ SETTINGS                 │
├──────────────────────────┤
│ ⚙️  Domain Settings      │ ← Domain Admin only
│ 📁 Project Settings      │ ← Project Admin only
│ 🏢 Organization          │ ← Org Admin only
│ 👤 Admin                 │ ← Global Admin only
└──────────────────────────┘
```

### Role-Based Visibility

**All Users See**:

- Dashboard, Compiler, Forge
- Agents, Datasets, Tools (view)
- Playground, Channels
- Deployments, Monitoring (for assigned projects)
- Domain Library, Project Overview

**+ Team Lead**:

- Teams page (manage own team)

**+ Domain Admin**:

- Domain Settings (for assigned domains)
- Can edit agents/datasets in domain

**+ Project Admin**:

- Project Settings (for assigned projects)
- Can deploy agents, configure channels

**+ Organization Admin**:

- All of above
- Organization page
- Teams page (create/manage all teams)
- Can create projects, domains, teams

**+ Global Admin**:

- All of above
- Admin page (platform settings)
- Can edit system agents
- Cross-org access

---

## Key Pages & Workflows

### 1. Dashboard (Domain-Scoped)

**Purpose**: At-a-glance view of current domain's health within project context

**Layout**:

```
┌─────────────────────────────────────────────────┐
│ Banking Domain / Card Services Project          │
├─────────────────────────────────────────────────┤
│ Quick Stats                                     │
│ ┌──────────┬──────────┬──────────┬────────────┐ │
│ │ 12       │ 3        │ 2        │ 156        │ │
│ │ Agents   │ Datasets │ Deploy   │ Sessions   │ │
│ └──────────┴──────────┴──────────┴────────────┘ │
│                                                 │
│ Recent Activity                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✓ fraud-detection-agent deployed 2h ago     │ │
│ │ → card-support-agent: 42 sessions today     │ │
│ │ ⚠ kyc-screener: High latency (850ms avg)    │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Quick Actions                                   │
│ [Compile DIS] [Test in Playground] [Deploy]    │
└─────────────────────────────────────────────────┘
```

---

### 2. Compiler

**Purpose**: Upload DIS dossiers → Generate agent YAML → Deploy to domain

**Workflow**:

1. Click "Upload DIS Dossier"
2. Select JSON file (DIS 1.6.0 format)
3. Compiler parses dossier, extracts agents
4. Generates YAML for each agent using domain template
5. Shows preview: `banking-support-agent.yaml`
6. User clicks "Add to Domain"
7. Agent appears in Agents page, ready to deploy

**UI Layout**:

```
┌─────────────────────────────────────────────────┐
│ Compiler                                        │
├─────────────────────────────────────────────────┤
│ [Drop DIS dossier here or click to upload]     │
│                                                 │
│ Recent Compilations                             │
│ ┌─────────────────────────────────────────────┐ │
│ │ ✓ cibc-card-services.json                   │ │
│ │   Generated: 3 agents, 2 datasets           │ │
│ │   Status: Completed                         │ │
│ │   [View YAML] [Add to Domain] [Download]   │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

### 3. Forge

**Purpose**: Visual agent builder for manual creation (no DIS required)

**Question for Nate**: Which scope for MVP?

**Option A: Visual Workflow Builder**

- Drag-drop LangGraph state machine editor
- Node types: Listen, Process, Respond, Tool Call
- Visual connections between states
- Properties panel for each node

**Option B: YAML Editor with Validation**

- Monaco editor with syntax highlighting
- Live schema validation
- Template gallery (customer-support, data-analyst, code-reviewer)
- Preview/test mode

**Option C: Both**

- Toggle between Visual and Code views
- Changes sync bidirectionally

---

### 4. Agents

**Purpose**: Browse and manage domain-scoped agents

**UI Layout**:

```
┌─────────────────────────────────────────────────┐
│ Agents in Banking Domain                        │
│ Filter: [All] [System] [User-Created]          │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ 🤖 fraud-detection-agent                    │ │
│ │ Detects anomalous transaction patterns      │ │
│ │ Tools: risk-scorer, pattern-matcher         │ │
│ │ Status: ● Active (2 deployments)            │ │
│ │ [Edit] [Test] [Deploy] [Clone]             │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🤖 card-support-agent                       │ │
│ │ Handles customer inquiries for credit cards │ │
│ │ Tools: account-lookup, transaction-search   │ │
│ │ Status: ● Active (1 deployment)             │ │
│ │ [Edit] [Test] [Deploy] [Clone]             │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**System Agents** (read-only for non-Global Admins):

```
┌─────────────────────────────────────────────────┐
│ ⚙️  System Agents                               │
│ These agents run the platform itself            │
├─────────────────────────────────────────────────┤
│ 👋 Foundry Admin Assistant                      │
│ 🛡️  Marshal Agent                               │
│ 📊 DataAgent                                     │
│ 📡 IOAgent                                       │
│                                                 │
│ [View Details] (Edit requires Global Admin)    │
└─────────────────────────────────────────────────┘
```

---

### 5. Domain Library

**Purpose**: Browse all domains in organization, add to projects

**UI Layout**:

```
┌─────────────────────────────────────────────────┐
│ CIBC Domain Library                             │
│ Knowledge domains available across organization │
├─────────────────────────────────────────────────┤
│ Industry Verticals                              │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🏦 Banking                                  │ │
│ │ Compliance: PCI-DSS, KYC/AML, Basel III     │ │
│ │ 45 agents • 12 datasets                     │ │
│ │ Used in: Card Services, Investment, Mobile  │ │
│ │                     [View] [Add to Project] │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ Functional Domains                              │
│ ┌─────────────────────────────────────────────┐ │
│ │ 💬 Customer Service                         │ │
│ │ Frameworks: ITIL, SLA Management            │ │
│ │ 34 agents • 15 datasets                     │ │
│ │ Used in: Card Services, Mobile, Helpdesk    │ │
│ │                     [View] [Add to Project] │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ Create Domain]* (Org Admin only)            │
└─────────────────────────────────────────────────┘
```

---

### 6. Teams

**Purpose**: Manage teams, assign to projects/domains

**Team List (Org Admin View)**:

```
┌─────────────────────────────────────────────────┐
│ CIBC Teams                                      │
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ 🛡️  Card Support Team          12 members   │ │
│ │ Lead: Alice Johnson                         │ │
│ │ Projects: 2 • Domains: 2                    │ │
│ │                     [Manage] [Edit Access]  │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ 🔒 Security Team                8 members   │ │
│ │ Lead: Bob Chen                              │ │
│ │ Projects: All • Domains: 3                  │ │
│ │                     [Manage] [Edit Access]  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ Create Team]                                 │
└─────────────────────────────────────────────────┘
```

**Team Detail (Tabs)**:

- **Overview**: Description, lead, stats
- **Members**: Add/remove team members
- **Projects**: Assign to projects, set permissions
- **Domains**: Assign to domains, set permissions

---

### 7. Playground

**Purpose**: Test agents with text and voice before deployment

**UI Layout**:

```
┌─────────────────────────────────────────────────┐
│ Playground                                      │
│ Agent: [fraud-detection-agent ▾]               │
├─────────────────────────────────────────────────┤
│ Chat History                                    │
│ ┌─────────────────────────────────────────────┐ │
│ │ User: Check transaction ID TXN-12345        │ │
│ │ Agent: Analyzing transaction...             │ │
│ │       Risk score: 85/100 (High)             │ │
│ │       Flagged patterns: velocity, location  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [Type message...] [🎤 Enable Voice]            │
│                                                 │
│ Session Info: banking-regulations-dataset      │
│ Response time: 850ms • Tokens: 234             │
└─────────────────────────────────────────────────┘
```

**Voice Mode (LiveKit Integration)**:

- Click "🎤 Enable Voice" → Connects to LiveKit room
- Real-time speech-to-text (Deepgram)
- Agent responds via text-to-speech (OpenAI)
- Visual waveform indicator during speech

---

### 8. Deployments

**Purpose**: Manage active agent deployments (project-scoped)

**UI Layout**:

```
┌─────────────────────────────────────────────────┐
│ Deployments - Card Services Project             │
├─────────────────────────────────────────────────┤
│ Active Deployments                              │
│ ┌─────────────────────────────────────────────┐ │
│ │ ● card-support-agent                        │ │
│ │ URL: cibc.com/card-support                  │ │
│ │ Status: Healthy • 42 sessions today         │ │
│ │ Uptime: 99.8% • Avg response: 650ms         │ │
│ │ [View Logs] [Configure] [Redeploy] [Stop]  │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ ⚠ fraud-detection-agent                     │ │
│ │ URL: Internal API                           │ │
│ │ Status: Warning • High latency (850ms)      │ │
│ │ Uptime: 98.2% • Errors: 3 in last hour      │ │
│ │ [View Logs] [Configure] [Redeploy] [Stop]  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ [+ Deploy Agent]                                │
└─────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Stack Overview

```
┌─────────────────────────────────────────────────┐
│ Frontend (Next.js 14 + TypeScript)              │
│ - React Server Components                       │
│ - LiveKit React SDK (@livekit/components-react) │
│ - TailwindCSS + shadcn/ui                       │
├─────────────────────────────────────────────────┤
│ Backend (FastAPI + Python 3.12)                 │
│ - LangChain 1.0.7 (agent framework)             │
│ - LangGraph 1.0.3 (orchestration)               │
│ - LiveKit Server SDK (voice integration)        │
│ - Anthropic Claude (LLM)                        │
│ - OpenAI (TTS), Deepgram (STT)                  │
├─────────────────────────────────────────────────┤
│ Services (Docker Compose)                       │
│ - foundry-frontend (Next.js)                    │
│ - foundry-backend (FastAPI)                     │
│ - foundry-compiler (DIS → YAML)                 │
│ - livekit-server (voice/video)                  │
│ - redis (state management)                      │
├─────────────────────────────────────────────────┤
│ Storage                                         │
│ - PostgreSQL (metadata, users, projects)        │
│ - Redis (session state, caching)                │
│ - Filesystem (agent YAML, datasets)             │
│ - Vector DB (Pinecone/Weaviate for RAG)         │
└─────────────────────────────────────────────────┘
```

### Agent Runtime Architecture

**Canonical Multi-Agent Pattern** (LangGraph-based):

```
User Input
   ↓
IOAgent (I/O Adapter)
   ↓
Supervisor Agent (LangGraph StateGraph)
   ├─→ PM Agent (project management domain)
   ├─→ Banking Agent (banking domain)
   ├─→ Support Agent (customer service domain)
   └─→ Tool Agent (executes MCP tools)
   ↓
IOAgent (formats response)
   ↓
User Output (text or voice via LiveKit)
```

**Key Principles**:

- ALL reasoning flows through LangGraph StateGraph
- NO direct LLM calls bypassing the graph
- NO collapsing into monolithic agents
- NO moving LangGraph logic into LiveKit callbacks

### LiveKit Voice Pipeline

```
User speaks → Deepgram STT → Text
   ↓
IOAgent receives text → LangGraph processes → Response text
   ↓
OpenAI TTS → Audio → LiveKit streams to user
```

---

## Database Schema (Simplified)

```sql
-- Tenant boundary
organizations
  - id, name, slug
  - subscription_tier
  - api_keys (encrypted jsonb)

-- Work boundary
projects
  - id, organization_id
  - name, slug, description
  - created_by_user_id

-- Knowledge boundary
domains
  - id, organization_id
  - name, slug, category
  - compliance_frameworks (jsonb)

-- Human grouping
teams
  - id, organization_id
  - name, description
  - lead_user_id

users
  - id, email, password_hash
  - default_organization_id
  - default_project_id
  - default_domain_id
  - global_role

-- Many-to-many relationships
team_memberships (users ↔ teams)
  - user_id, team_id, role

team_projects (teams ↔ projects)
  - team_id, project_id
  - permissions (jsonb)

team_domains (teams ↔ domains)
  - team_id, domain_id
  - permissions (jsonb)

project_domains (projects ↔ domains)
  - project_id, domain_id

-- Resources
agents
  - id, domain_id, organization_id
  - name, system_prompt, is_system
  - yaml_path

datasets
  - id, domain_id, organization_id
  - name, vector_store_id
  - is_shared

deployments
  - id, project_id, agent_id
  - url, status, health_check_url

-- Role assignments
organization_admins
  - user_id, organization_id

project_admins
  - user_id, project_id

domain_admins
  - user_id, domain_id
```

---

## MVP Implementation Timeline

### Week 1: Platform + LiveKit (12-15 hours)

**Status**: ✅ Complete per LIVEKIT_DOCKER_MIGRATION.md

**Completed**:

- LiveKit containerized (Docker Compose)
- Backend LiveKit integration (token generation, room management)
- Frontend voice UI components (LiveKit React SDK)
- All services healthy (livekit, redis, backend, compiler)

**Remaining**:

- End-to-end voice testing
- Frontend-to-backend-to-LiveKit flow validation

---

### Week 2: Core Platform Features (15-20 hours)

**Day 1-2: Organization/Project/Domain Structure**

- Database schema implementation
- Organization CRUD APIs
- Project CRUD APIs
- Domain CRUD APIs
- Context switching logic (org/project/domain in URL params)

**Day 3-4: Team & RBAC**

- Team CRUD APIs
- Team membership APIs
- Team-project assignment APIs
- Team-domain assignment APIs
- Permission checking middleware

**Day 5: Frontend Navigation**

- Header context selector (org/project/domain dropdowns)
- Primary navigation component
- Role-based nav visibility
- Dashboard layout (placeholder metrics)

---

### Week 3: Compiler & Agent Management (15-20 hours)

**Day 1-2: DIS Compiler**

- DIS 1.6.0 parser (JSON → dict)
- Agent YAML generator (Jinja2 templates)
- Compiler API endpoints (upload, status, download)
- Frontend Compiler page

**Day 3-4: Agent Registry**

- Agent CRUD APIs
- YAML file storage/loading
- Agent listing (domain-scoped)
- System agents vs user agents separation

**Day 5: Forge (Basic YAML Editor)**

- Monaco editor integration
- YAML validation
- Template gallery (3-5 starter templates)

---

### Week 4: Deployment & Monitoring (10-15 hours)

**Day 1-2: Deployment System**

- Deployment CRUD APIs
- Deploy agent to project
- Health check monitoring
- Demo URL generation

**Day 3-4: Playground**

- Agent testing UI (text mode)
- Voice mode integration (LiveKit)
- Session history

**Day 5: Monitoring**

- Logs aggregation (project/domain scoped)
- Basic metrics dashboard
- Agent health status

---

### Week 5: Polish & Production Ready (10-12 hours)

**Day 1-2: Frontend Polish**

- Domain Library page
- Project Overview page
- Teams management page
- Settings pages (domain/project/org/admin)

**Day 3-4: AWS Deployment**

- Terraform config (EC2, security groups, elastic IP)
- Docker Compose on EC2
- SSL setup (Let's Encrypt)
- DNS configuration (foundry.ravenhelm.ai)

**Day 5: Documentation & Testing**

- User documentation
- API documentation
- End-to-end workflow testing
- Performance validation

---

### Total Timeline: 5 weeks (62-82 hours)

**MVP Feature Checklist**:

- ✅ LiveKit voice integration
- ✅ Docker containerization
- 🔲 Organization/Project/Domain structure
- 🔲 Teams & RBAC
- 🔲 DIS Compiler (DIS → Agent YAML)
- 🔲 Agent Registry (domain-scoped)
- 🔲 Forge (YAML editor)
- 🔲 Playground (text + voice)
- 🔲 Deployments
- 🔲 Monitoring
- 🔲 AWS deployment
- 🔲 Production domain (foundry.ravenhelm.ai)

---

## Success Metrics

### MVP Complete When:

1. **Technical Validation**

   - ✅ foundry.ravenhelm.ai accessible via HTTPS
   - ✅ Can upload DIS dossier via UI
   - ✅ Compiler generates valid agent YAML
   - ✅ Agent appears in registry < 60 seconds
   - ✅ Voice conversation works with agent
   - ✅ Deployment succeeds, generates demo URL
   - ✅ Demo URL shareable with others

2. **User Validation**

   - ✅ Domain Expert can upload DIS → Get working agent (no code)
   - ✅ Developer can use Forge to build custom agent
   - ✅ Team can be assigned to project with limited permissions
   - ✅ Domain Admin can curate domain knowledge
   - ✅ Project Admin can deploy agents from multiple domains

3. **Operational Validation**
   - ✅ All services containerized (dev → prod parity)
   - ✅ GitLab CI/CD pipeline deploys updates
   - ✅ Monitoring shows agent health/performance
   - ✅ Logs accessible for debugging

---

## Post-MVP Roadmap

### Phase 2: Multi-Tenancy & Scale (Months 2-3)

**Subdomain Routing**:

- `cibc.foundry.ravenhelm.ai` → CIBC organization
- `acme.foundry.ravenhelm.ai` → Acme Corp organization

**Advanced RBAC**:

- Custom roles (beyond predefined admin/member)
- Fine-grained permissions (e.g., "can deploy to staging only")
- Audit logs (who did what, when)

**Marketplace**:

- Share domains across organizations
- Pre-built domain templates (ITSD, HR, Airlines, etc.)
- Community-contributed agents

---

### Phase 3: Enterprise Features (Months 4-6)

**Compliance & Governance**:

- Approval workflows (domain admin must approve agent changes)
- Compliance dashboards (PCI-DSS checklist for Banking domain)
- Audit trail (immutable log of all changes)

**Advanced Monitoring**:

- APM (Application Performance Monitoring)
- Distributed tracing (trace requests across agents)
- Anomaly detection (auto-flag unusual agent behavior)

**Auto-Scaling**:

- Agent instances scale based on load
- Load balancing across agent replicas
- Queue management for high-volume deployments

---

### Phase 4: AI Platform Features (Months 7-12)

**Agent Orchestration**:

- Multi-agent workflows (banking agent → fraud agent → approval agent)
- Conditional routing based on agent responses
- Human-in-the-loop approvals

**Advanced RAG**:

- Hybrid search (vector + keyword)
- Reranking models
- Citation tracking (which dataset chunk generated response)

**Agent Analytics**:

- Conversation analytics (common intents, failure patterns)
- A/B testing (deploy two versions, compare performance)
- User satisfaction scoring

---

## Risk Mitigation

### Technical Risks

**Risk**: LangGraph StateGraph complexity scales poorly  
**Mitigation**:

- Start with simple 3-agent architecture (IO, Supervisor, Worker)
- Extensive testing before adding more agents
- Document state transitions clearly

**Risk**: LiveKit voice quality/latency issues  
**Mitigation**:

- Use production-grade LiveKit Cloud for critical demos
- Optimize STT/TTS provider selection per use case
- Implement fallback to text-only mode

**Risk**: Domain knowledge modeling too complex for users  
**Mitigation**:

- DIS Designer (separate tool) abstracts complexity
- Provide domain templates for common industries
- Offer professional services for complex domains

---

### Business Risks

**Risk**: "Heroku for AI Agents" already exists (competitors)  
**Mitigation**:

- Emphasize domain-centric approach (unique differentiator)
- Focus on enterprise compliance needs (PCI-DSS, HIPAA)
- Leverage DIS as open standard

**Risk**: Enterprises resist uploading proprietary knowledge  
**Mitigation**:

- Self-hosted option (bring your own cloud)
- SOC 2 compliance
- Data residency controls (EU, US, etc.)

**Risk**: AI hype cycle peaks, funding dries up  
**Mitigation**:

- Focus on measurable ROI (cost per customer interaction)
- Target regulated industries (slow adopters, long contracts)
- Build sustainable unit economics early

---

## Conclusion

Agent Foundry represents a **paradigm shift** in how organizations deploy AI:

- **From**: Monolithic chatbots built by AI specialists
- **To**: Composable domain agents curated by subject matter experts

- **From**: Code-first agent development
- **To**: Declarative world modeling (DIS) → Automated deployment

- **From**: Siloed AI projects
- **To**: Reusable domain knowledge across the enterprise

The platform's **Organization > Project > Domain** architecture mirrors how
large enterprises actually structure knowledge and work, making it the natural
choice for regulated industries (banking, healthcare, aviation) where compliance
and auditability are non-negotiable.

With LiveKit containerization complete and core infrastructure validated,
**Agent Foundry is ready to build**.

---

## Appendix

### Key Files & References

- **LIVEKIT_DOCKER_MIGRATION.md**: LiveKit containerization status (complete)
- **afmvpimplementation.pdf**: Original MVP timeline (updated in this doc)
- **afmvparch.pdf**: Original architecture (superseded by this doc)
- **Project Root**: `/Users/nwalker/Development/Projects/agentfoundry`

### Technology Versions (LTS)

- Python: 3.12
- LangChain: 1.0.7
- LangGraph: 1.0.3
- Next.js: 14.x
- LiveKit: latest (Docker image)
- FastAPI: 0.115.x

### Contact & Ownership

- **Product Owner**: Nate Walker
- **Platform**: Agent Foundry (Ravenhelm Series A)
- **Domain**: foundry.ravenhelm.dev (staging), foundry.ravenhelm.ai (production)
- **Repository**: GitLab (private)

---

**End of Document**
