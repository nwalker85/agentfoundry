# Agent Foundry

**Enterprise-grade LangGraph platform with modern authorization, service discovery, and secrets management.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.3+-blue.svg)](https://www.typescriptlang.org/)

---

## Features

### 🎯 Core Platform
- **LangGraph Agents** - Visual designer (Forge) + YAML-driven workflows
- **Multi-Tenant** - Organization/domain/project hierarchy
- **Real-Time Voice** - LiveKit integration for voice agents
- **Visual Designer** - ReactFlow-based graph builder

### 🔐 Authorization & Secrets
- **OpenFGA** - Google Zanzibar-based authorization (ReBAC)
- **LocalStack** - Secure secret management with blind-write pattern
- **Zero .env Secrets** - All configuration in LocalStack

### 🏗️ Architecture
- **Service Discovery** - DNS-based, Kubernetes-ready
- **OpenTelemetry** - Distributed tracing and metrics
- **n8n Integration** - 100+ pre-built workflow connectors

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### 1. Clone & Start

```bash
git clone https://github.com/quant-eng/agent-foundry.git
cd agent-foundry

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 2. Initialize OpenFGA

```bash
# Load authorization model
python scripts/openfga_load_model_v2.py

# Set up initial relationships (users, teams, etc.)
python scripts/openfga_setup_initial_data.py

# Verify
python openfga/test_authorization_checks.py
# Should show: 12/12 tests passed ✅
```

### 3. Access

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **OpenFGA**: http://localhost:9080 (HTTP), http://localhost:8081 (gRPC)
- **LocalStack**: http://localhost:4566
- **n8n**: http://localhost:5678

---

## Architecture

### Service Discovery

All services use DNS-based discovery (no hardcoded URLs):

```python
from backend.config.services import SERVICES

backend_url = SERVICES.get_service_url("BACKEND")      # http://foundry-backend:8080
openfga_url = SERVICES.get_service_url("OPENFGA")      # http://openfga:8080
localstack_url = SERVICES.get_service_url("LOCALSTACK") # http://localstack:4566
```

**Benefits:**
- Works in Docker Compose AND Kubernetes (no code changes)
- No port configuration hell
- Consistent service naming

### Authorization (OpenFGA)

Fine-grained, relationship-based authorization:

```python
from backend.middleware.openfga_middleware import get_current_user

@app.post("/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    context: AuthContext = Depends(get_current_user)
):
    # Check: Can THIS user execute THIS agent?
    if not await context.can("can_execute", f"agent:{agent_id}"):
        raise HTTPException(403, "Cannot execute this agent")
    
    # Execute...
```

**Features:**
- Per-resource permissions ("alice can execute agent X")
- Team-based access
- Hierarchical inheritance (org → project → domain → agent)
- System agent protection (`but not is_system`)

### Secrets Management (LocalStack)

Blind-write pattern - frontend can write, never read:

```python
from backend.config.secrets import get_llm_api_key

# Backend retrieves org-specific API key
api_key = await get_llm_api_key(
    organization_id="acme-corp",
    provider="openai",
    domain_id="card-services"
)

# Use for agent execution
llm = ChatOpenAI(api_key=api_key)
```

**Security:**
- Frontend can update secrets, never retrieve them
- Organization-scoped (multi-tenant isolation)
- Encrypted at rest (LocalStack/AWS)
- Audit logged (WHO updated, not WHAT value)

---

## Authorization Model

### Hierarchy

```
platform:foundry (global admins)
  ↓
tenant:ravenhelm (billing, isolation)
  ↓
organization:cibc (business entity)
  ↓
project:card-services (initiative)
  ↓
domain:banking (knowledge vertical)
  ↓ (can nest: domain:banking-fraud)
  ↓
Assets: agent, report, config, dataset, tool, secret, session, graph
```

### Example Permissions

**Team-based access:**
```
user:bob → member of → team:card-support
  ↓
team:card-support → team_visibility → project:card-services
  ↓
Bob can view all project assets
```

**System agent protection:**
```
agent:marshal → is_system → platform:foundry
  ↓
can_delete: ... but not is_system
  ↓
Result: NOBODY can delete marshal (protected)
```

**Hierarchical cascading:**
```
user:nate → admin of → tenant:ravenhelm
  ↓
tenant:ravenhelm → tenant of → organization:cibc
  ↓
organization:cibc → organization of → project:card-services
  ↓
Nate can manage ALL projects in ALL orgs in his tenant
```

---

## Technology Stack

### Backend
- **FastAPI** - Python async web framework
- **LangGraph** - Stateful agent orchestration
- **OpenFGA** - Authorization (Zanzibar)
- **LocalStack** - AWS services emulation
- **PostgreSQL** - Primary database
- **Redis** - Caching & state

### Frontend
- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **ReactFlow** - Visual graph editor
- **Radix UI** - Component library
- **Tailwind CSS** - Styling

### Infrastructure
- **Docker Compose** - Local development
- **LiveKit** - Voice/video infrastructure
- **n8n** - Workflow automation
- **OpenTelemetry** - Observability
- **Prometheus/Grafana** - Metrics

---

## Development

### Running Locally

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f foundry-backend

# Rebuild after changes
docker-compose build foundry-backend
docker-compose restart foundry-backend
```

### Testing Authorization

```bash
# Run full test suite
python openfga/test_authorization_checks.py

# Should show: 12/12 tests passed
```

### Code Formatting

```bash
# Python (backend)
black backend/ agents/
isort backend/ agents/

# TypeScript (frontend)
npm run format
```

---

## Configuration

### Environment Variables

Agent Foundry uses **LocalStack for all secrets** - no API keys in `.env`!

```bash
# .env - Only service names and ports
ENVIRONMENT=development
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Service discovery (DNS names)
SVC_BACKEND_HOST=foundry-backend
SVC_OPENFGA_HOST=openfga
SVC_LOCALSTACK_HOST=localstack
```

### Secrets in LocalStack

```bash
# Store API key
python -c "
import asyncio
from backend.config.secrets import secrets_manager

asyncio.run(secrets_manager.upsert_secret(
    organization_id='acme-corp',
    secret_name='openai_api_key',
    secret_value='sk-...'
))
"
```

---

## Documentation

### Architecture
- Service Discovery - DNS-based service communication
- OpenFGA Authorization - Relationship-based access control
- LocalStack Secrets - Secure API key management
- OpenFGA + LocalStack Integration - How they work together

### Guides
- Quick Start - Get running in 10 minutes
- OpenFGA Setup - Authorization model setup
- Secret Management - API key storage
- Development Guide - Local development workflow

---

## Project Structure

```
agent-foundry/
├── backend/               # FastAPI backend
│   ├── config/           # Service discovery & secrets
│   ├── middleware/       # OpenFGA authorization
│   ├── routes/           # API endpoints
│   └── openfga_client.py # OpenFGA integration
│
├── app/                  # Next.js frontend
│   ├── app/             # Pages & layouts
│   ├── components/      # React components
│   └── lib/             # Utilities
│
├── agents/               # LangGraph agent implementations
├── openfga/             # Authorization model & tests
│   ├── authorization_model_v2.fga  # Enhanced model
│   ├── test_authorization_checks.py # Test suite
│   └── README.md        # Model documentation
│
├── scripts/             # Utility scripts
│   ├── openfga_load_model_v2.py    # Load auth model
│   ├── openfga_setup_initial_data.py # Initial relationships
│   └── openfga_setup_localstack.py  # Store config
│
└── docker-compose.yml    # All services
```

---

## Contributing

### Setup Development Environment

```bash
# Python virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
npm install
```

### Code Quality

- **Python**: black, isort, mypy, pytest
- **TypeScript**: eslint, prettier
- **Pre-commit hooks**: Run formatters automatically

---

## Testing

### Backend Tests

```bash
pytest tests/
```

### Authorization Tests

```bash
python openfga/test_authorization_checks.py
```

### Integration Tests

```bash
# Test full agent execution
curl -X POST http://localhost:8000/api/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent",
    "input": "Hello!",
    "session_id": "test-123"
  }'
```

---

## Production Deployment

### Environment Detection

Agent Foundry automatically detects environment:

**Development:**
- LocalStack (localhost:4566) for secrets
- OpenFGA (localhost:9080) for authorization

**Production:**
- AWS Secrets Manager for secrets
- OpenFGA (deployed) for authorization

**Zero code changes needed!**

### Kubernetes

```yaml
# All services use same DNS names
# No code changes from Docker Compose

apiVersion: v1
kind: Service
metadata:
  name: foundry-backend  # Same as Docker service name
spec:
  ports:
    - port: 8080
```

---

## Security

### Defense in Depth

| Layer | System | Protection |
|-------|--------|------------|
| **Authorization** | OpenFGA | WHO can access |
| **Storage** | LocalStack/AWS | Encrypted secrets |
| **Transport** | HTTPS | Data in transit |
| **Audit** | Backend | All operations logged |
| **Blind Write** | Frontend | Can't read secrets |

### Compliance

- **GDPR Ready** - User data isolation
- **SOC 2** - Audit logging
- **HIPAA** - Compliance officer roles
- **Multi-tenant** - Organization isolation

---

## Performance

- **Authorization checks**: 1-5ms (cached)
- **Secret retrieval**: <10ms (LocalStack)
- **Agent execution**: Depends on workflow
- **Horizontal scaling**: Kubernetes-ready

---

## License

MIT License - see LICENSE file for details

---

## Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **Examples**: `/openfga/test_authorization_checks.py`

---

## Acknowledgments

Built with:
- [OpenFGA](https://openfga.dev) - Authorization
- [LangGraph](https://www.langchain.com/langgraph) - Agent orchestration
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [Next.js](https://nextjs.org) - Frontend framework
- [LocalStack](https://localstack.cloud) - AWS emulation

---

**Agent Foundry** - Enterprise LangGraph Platform  
**Organization**: [Quant Engineering](https://github.com/quant-eng)  
**Repository**: https://github.com/quant-eng/agent-foundry  
**Architecture**: Zero-config, zero-secrets-in-env, production-ready  

🚀 **Built for scale. Designed for security. Ready for production.**

