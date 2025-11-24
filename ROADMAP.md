# Agent Foundry Roadmap

**Version:** 0.9.0 → 1.0.0
**Last Updated:** 2025-11-24

---

## Current State (v0.9)

### Complete
- [x] Forge visual graph editor with version control
- [x] LangGraph agent orchestration (7 system agents)
- [x] Basic RBAC with Zitadel SSO
- [x] Voice pipeline (LiveKit + Deepgram + ElevenLabs)
- [x] MCP tool integration gateway
- [x] PostgreSQL control plane with RLS
- [x] Docker Compose local development
- [x] Basic AWS ECS/Fargate deployment

---

## Backlog (Prioritized)

### 🔐 P0: Security & Authentication

| Item | Description | Status |
|------|-------------|--------|
| **API Endpoint Auth** | Secure all API endpoints with JWT/API key validation | Not Started |
| **API Key Management** | Per-scope API keys (org/domain/environment) | Not Started |
| **Complete Multi-Tenancy** | Full tenant isolation, data segregation, RLS everywhere | In Progress |
| **Secrets Rotation** | Automated secrets rotation and audit logging | Not Started |
| **Inter-Service mTLS** | SSL certificates for all service-to-service communication | Not Started |
| **Certificate Management** | Automated cert provisioning and rotation (Let's Encrypt / ACM) | Not Started |

### 🌐 P0: Multi-Tenant Routing (Virtual Hosts)

| Item | Description | Status |
|------|-------------|--------|
| **Subdomain Tenant Routing** | `{tenant}.platform.quant.ai` → correct tenant context | Not Started |
| **Wildcard SSL Certs** | `*.platform.quant.ai` certificate provisioning | Not Started |
| **Tenant DNS Management** | Self-service custom domain mapping | Not Started |
| **Request Context Injection** | Extract tenant from hostname, inject into request context | Not Started |
| **Tenant-Aware Load Balancing** | Route to correct tenant data while sharing infrastructure | Not Started |
| **White-Label Support** | Custom branding per tenant subdomain | Not Started |

### 📊 P0: Observability & Telemetry

| Item | Description | Status |
|------|-------------|--------|
| **Agent Telemetry View** | Real-time agent metrics dashboard (latency, tokens, errors) | Not Started |
| **Execution Traces** | End-to-end request tracing with OpenTelemetry | Partial |
| **Cost Tracking** | Token usage and cost attribution per org/domain | Not Started |
| **Alerting** | Threshold-based alerts for agent health | Not Started |

### 🤖 P0: Agent Execution

| Item | Description | Status |
|------|-------------|--------|
| **Deep Agent Usage** | Goal planning and autonomous agent execution | Not Started |
| **Multi-Agent Execution** | Parallel agent orchestration and result aggregation | Not Started |
| **Tool Use Integration** | Complete MCP tool binding and execution UI | Partial |
| **Agent Checkpointing** | Long-running session state persistence | Partial |

### 🎙️ P1: Voice & Channels

| Item | Description | Status |
|------|-------------|--------|
| **Voice Provider Config** | UI for selecting/configuring STT/TTS providers | Not Started |
| **Greeting Configuration** | Customizable agent greetings per channel/domain | Not Started |
| **Channel Routing** | Route requests to appropriate channel workflows | Partial |
| **Voice Quality Metrics** | Latency, accuracy, and quality monitoring | Not Started |

### 📦 P1: Deployment & Distribution

| Item | Description | Status |
|------|-------------|--------|
| **Deployment Packages** | Collect agents, settings → standalone Docker image | Not Started |
| **Terraform Scripts** | Complete AWS deployment automation | Partial |
| **Blue-Green Deployments** | Zero-downtime deployment strategy | Not Started |
| **Environment Promotion** | Dev → Staging → Prod workflow | Not Started |

### 🔧 P1: Integrations

| Item | Description | Status |
|------|-------------|--------|
| **GitLab Integration** | GitLab repos, issues, MRs via MCP | Not Started |
| **GitHub Enhancement** | Complete GitHub integration (Actions, Releases) | Partial |
| **Slack Integration** | Notifications and agent interaction via Slack | Not Started |
| **Webhook System** | Outbound webhooks for events | Not Started |

### 🏗️ P2: Architecture & Refactoring

| Item | Description | Status |
|------|-------------|--------|
| **FastAPI vs Node.js** | Consolidate or clearly separate backend responsibilities | Not Started |
| **API Gateway** | Centralized API gateway with rate limiting | Not Started |
| **Event Bus** | Async event system for decoupled services | Partial |
| **Plugin Architecture** | Extensible plugin system for agents/tools | Not Started |

### 🎨 P2: UI/UX Enhancements

| Item | Description | Status |
|------|-------------|--------|
| **Monitoring Dashboard** | Complete monitoring page with metrics/logs | Not Started |
| **Deployment UI** | Visual deployment workflow and status | Not Started |
| **Tool Configuration UI** | Per-tool settings and credentials management | Partial |
| **Agent Testing UI** | Interactive agent testing playground | Partial |

### 📋 P3: Platform Features

| Item | Description | Status |
|------|-------------|--------|
| **Marketplace** | Agent and tool marketplace | Not Started |
| **Templates** | Pre-built agent templates | Not Started |
| **Versioned Rollback** | One-click rollback to previous versions | Not Started |
| **Audit Logging** | Complete audit trail for compliance | Partial |

---

## Detailed Feature Specifications

### Inter-Service mTLS (Service Mesh Security)

**Current State:** Services communicate over unencrypted Docker network

**Requirements:**
- [ ] Generate CA and service certificates
- [ ] Configure mTLS for all service-to-service communication:
  - Frontend → Backend API
  - Backend → PostgreSQL
  - Backend → Redis
  - Backend → LiveKit
  - Backend → LocalStack/AWS
- [ ] Certificate rotation automation (90-day cycle)
- [ ] Service identity verification
- [ ] Options:
  - **Simple**: Traefik with auto-cert
  - **Enterprise**: Istio service mesh or Linkerd
  - **AWS**: AWS App Mesh with ACM

### Subdomain Multi-Tenant Routing (Virtual Hosts)

**Current State:** Single tenant, no subdomain routing

**Architecture:**
```
                    *.platform.quant.ai
                           │
                           ▼
              ┌────────────────────────┐
              │   Load Balancer/CDN    │
              │   (Wildcard SSL Cert)  │
              └────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    companyx.platform.quant.ai    companyy.platform.quant.ai
              │                         │
              └──────────┬──────────────┘
                         ▼
              ┌────────────────────────┐
              │    Tenant Router       │
              │  (Extract subdomain)   │
              └────────────────────────┘
                         │
                         ▼
              ┌────────────────────────┐
              │   Shared SaaS Cluster  │
              │  ┌──────────────────┐  │
              │  │ Tenant Context:  │  │
              │  │ org_id = companyx│  │
              │  └──────────────────┘  │
              └────────────────────────┘
```

**Requirements:**
- [ ] Wildcard SSL certificate (`*.platform.quant.ai`)
- [ ] DNS configuration (Route53 wildcard A record)
- [ ] Tenant router middleware:
  ```python
  # Extract tenant from subdomain
  def get_tenant_from_host(request):
      host = request.headers.get("host")  # companyx.platform.quant.ai
      subdomain = host.split(".")[0]      # companyx
      return lookup_tenant_by_subdomain(subdomain)
  ```
- [ ] Tenant → Organization mapping table
- [ ] Request context injection (all queries scoped to tenant)
- [ ] Tenant-specific:
  - Branding (logo, colors, name)
  - Feature flags
  - Rate limits
  - Data isolation (RLS)
- [ ] Custom domain support (`agents.companyx.com` → `companyx.platform.quant.ai`)
- [ ] SSL cert provisioning for custom domains (Let's Encrypt)

**Implementation Options:**

| Option | Pros | Cons |
|--------|------|------|
| **ALB + Lambda@Edge** | AWS-native, scalable | Vendor lock-in |
| **Traefik** | Docker-native, auto-cert | Self-managed |
| **Nginx + Lua** | Flexible, proven | Complex config |
| **Cloudflare** | Global CDN, easy SSL | External dependency |

### Complete Multi-Tenancy

**Current State:** Basic org/domain structure with RLS on some tables

**Requirements:**
- [ ] RLS policies on ALL tables (agents, versions, tools, configs, etc.)
- [ ] Tenant context propagation through all API calls
- [ ] Cross-tenant query prevention
- [ ] Tenant-specific Redis namespacing
- [ ] Tenant data export/import
- [ ] Tenant deletion with cascade cleanup
- [ ] Subdomain → Tenant mapping
- [ ] Tenant provisioning workflow (create subdomain, org, admin user)
- [ ] Tenant suspension/reactivation

### API Key Management Per Scope

**Current State:** No API key system

**Requirements:**
- [ ] API key generation UI (org admin, domain admin)
- [ ] Scope levels: Organization, Domain, Environment, Agent
- [ ] Key rotation with grace period
- [ ] Usage tracking per key
- [ ] Rate limiting per key
- [ ] Key revocation with audit log

### Agent Telemetry View

**Current State:** Basic metrics endpoint, no UI

**Requirements:**
- [ ] Real-time metrics dashboard
  - Requests per minute
  - Latency percentiles (p50, p95, p99)
  - Token usage (input/output)
  - Error rate and types
  - Active sessions
- [ ] Historical trends (1h, 24h, 7d, 30d)
- [ ] Per-agent breakdown
- [ ] Cost attribution

### Deep Agent Usage (Goal Planning)

**Current State:** Single-turn agent execution

**Requirements:**
- [ ] Goal decomposition (break complex goals into subtasks)
- [ ] Plan generation and validation
- [ ] Autonomous execution with checkpoints
- [ ] Human-in-the-loop approval gates
- [ ] Progress tracking and reporting
- [ ] Failure recovery and retry logic

### Multi-Agent Execution

**Current State:** Sequential agent execution via Supervisor

**Requirements:**
- [ ] Parallel agent invocation
- [ ] Result aggregation strategies (first, all, majority)
- [ ] Agent coordination protocol
- [ ] Shared state management
- [ ] Conflict resolution
- [ ] Execution graph visualization

### Deployment Package Generation

**Current State:** Manual Docker builds

**Requirements:**
- [ ] UI to select agents for deployment
- [ ] Configuration bundling (env vars, secrets references)
- [ ] Dockerfile generation
- [ ] Docker image build and push to registry
- [ ] Deployment manifest generation (k8s, ECS)
- [ ] One-click deploy to target environment

### Terraform AWS Deployment

**Current State:** Partial Terraform in `infra/`

**Requirements:**
- [ ] Complete VPC setup with proper security groups
- [ ] ECS Fargate task definitions for all services
- [ ] RDS PostgreSQL with automated backups
- [ ] ElastiCache Redis cluster
- [ ] ALB with SSL termination
- [ ] Route53 DNS management
- [ ] Secrets Manager integration
- [ ] CloudWatch logging and alarms
- [ ] Auto-scaling policies

### FastAPI vs Node.js Refactor

**Current State:** FastAPI backend + Next.js frontend with some API routes

**Requirements:**
- [ ] Audit all API routes (FastAPI vs Next.js API routes)
- [ ] Define clear boundaries:
  - FastAPI: Agent execution, tools, database, voice
  - Next.js: Auth, session, UI-specific APIs
- [ ] Consolidate duplicate endpoints
- [ ] Document API ownership
- [ ] Consider BFF (Backend for Frontend) pattern

### Voice Provider Configuration

**Current State:** Hardcoded provider selection

**Requirements:**
- [ ] Provider selection UI (Deepgram, Whisper, Azure, Google)
- [ ] Per-provider configuration (API keys, models, languages)
- [ ] TTS provider selection (ElevenLabs, OpenAI, Azure, Google)
- [ ] Voice/model selection per agent
- [ ] Cost tracking per provider
- [ ] Fallback provider configuration

### Greeting Configuration

**Current State:** No greeting system

**Requirements:**
- [ ] Default greeting per organization
- [ ] Override greeting per domain/agent
- [ ] Dynamic greeting with context (time of day, user info)
- [ ] Multi-language greeting support
- [ ] A/B testing for greetings

---

## Release Plan

### v0.9.1 (Next)
- API Endpoint Auth
- API Key Management (basic)
- Agent Telemetry View (basic)

### v0.9.2
- Complete Multi-Tenancy
- Tool Use Integration (complete)
- Voice Provider Config UI

### v0.10.0
- Deep Agent Usage
- Multi-Agent Execution
- Deployment Package Generation

### v1.0.0
- Complete Terraform AWS
- Production hardening
- Performance optimization
- Security audit

---

## Contributing

When working on backlog items:

1. Create a branch: `feature/{item-name}`
2. Update this roadmap with status changes
3. Add documentation in `docs/`
4. Include tests
5. Update CHANGELOG.md

---

## Notes

- Priority levels: P0 (critical), P1 (high), P2 (medium), P3 (low)
- Status: Not Started, In Progress, Partial, Complete
- This roadmap is a living document - update as work progresses
