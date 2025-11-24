# Agent Foundry - Local Setup Quick Start

**Time to first run: ~15 minutes**

This guide gets you from zero to a fully running Agent Foundry instance with all services configured.

---

## Prerequisites

- **Docker Desktop** (or Colima on macOS)
- **Python 3.11+**
- **Node.js 20+**
- **OpenAI API Key** (or Anthropic)

---

## Step 1: Clone and Configure Environment

```bash
cd /path/to/agentfoundry

# Copy environment template
cp .env.example .env.local
```

### Required Environment Variables

Edit `.env.local` and set these **required** values:

```bash
# REQUIRED - LLM Provider (at minimum)
OPENAI_API_KEY=sk-...

# REQUIRED - NextAuth (generate with: openssl rand -base64 32)
NEXTAUTH_SECRET=your-random-32-char-string
NEXTAUTH_URL=http://localhost:3000
```

The rest have sensible defaults for local development.

---

## Step 2: Start Docker Services

```bash
# Start all services (16+ containers)
docker-compose up -d

# Wait for services to initialize (~60-90 seconds for Zitadel)
docker-compose ps
```

### Verify Core Services

```bash
# Backend API
curl http://localhost:8000/health

# PostgreSQL
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping

# OpenFGA
curl http://localhost:9080/healthz

# Zitadel (may take 60-90 seconds)
curl http://localhost:8082/debug/healthz
```

---

## Step 3: Initialize PostgreSQL Database

```bash
# From Docker (recommended)
docker-compose exec foundry-backend python scripts/init-postgres.py

# Or locally (if you have the Python env set up)
python scripts/init-postgres.py
```

This creates:
- Tables with Row-Level Security (RLS)
- RBAC roles and permissions
- Initial seed data (test organizations, domains)

---

## Step 4: Setup Zitadel (Authentication)

Zitadel is the identity provider. **Manual setup required.**

### 4.1 Access Zitadel Console

Open: **http://localhost:8082**

Login:
- Username: `admin`
- Password: `AgentFoundry2024!`

### 4.2 Create Project

1. Click **"Projects"** in left menu
2. Click **"+ New"**
3. Name: `AgentFoundry`
4. Click **"Continue"**

### 4.3 Create Application

1. In the project, click **"Applications"** tab
2. Click **"+ New"**
3. Name: `foundry-web`
4. Type: **Web**
5. Click **"Continue"**

### 4.4 Configure Application

1. Auth Method: **PKCE** (recommended)
2. Redirect URIs: `http://localhost:3000/api/auth/callback/zitadel`
3. Post Logout URIs: `http://localhost:3000`
4. Click **"Create"**

### 4.5 Copy Credentials

Copy the **Client ID** shown (looks like `123456789012345678@agentfoundry`).

If using Basic auth (not PKCE), also copy the **Client Secret**.

### 4.6 Store in LocalStack

```bash
# For PKCE (no secret needed, use empty string)
python scripts/zitadel_setup_localstack.py "YOUR_CLIENT_ID" "" --issuer http://localhost:8082

# For Basic auth (with secret)
python scripts/zitadel_setup_localstack.py "YOUR_CLIENT_ID" "YOUR_SECRET" --issuer http://localhost:8082
```

---

## Step 5: Initialize OpenFGA (Authorization)

OpenFGA provides fine-grained authorization (Google Zanzibar-style).

```bash
# Initialize store and load authorization model
python scripts/openfga_init.py
```

**Copy the output values:**
```
OPENFGA_STORE_ID=xxxxx
OPENFGA_AUTH_MODEL_ID=xxxxx
```

### Store in LocalStack

```bash
python scripts/openfga_setup_localstack.py <store_id> <model_id>
```

---

## Step 6: Create Admin User

```bash
# Creates platform admin user with full permissions
python scripts/setup_admin_user.py
```

Default admin:
- Email: `nate@ravenhelm.co`
- Role: `platform_owner`

---

## Step 7: Restart Backend

After all configuration:

```bash
docker-compose restart foundry-backend
```

---

## Step 8: Start Frontend (Development)

The frontend can run in Docker or locally:

### Option A: Use Docker (Already Running)
Frontend is already running at **http://localhost:3000**

### Option B: Local Development (Hot Reload)
```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## Verification Checklist

| Service | URL | Expected |
|---------|-----|----------|
| Frontend | http://localhost:3000 | App loads |
| Backend API | http://localhost:8000/docs | Swagger UI |
| Zitadel | http://localhost:8082 | Login page |
| n8n | http://localhost:5678 | Workflow UI |
| Grafana | http://localhost:3001 | Dashboards (admin/foundry) |
| Mailpit | http://localhost:8025 | Email inbox |

### Health Check Script

```bash
./scripts/monitor_local_health.sh
```

---

## Quick Reference: All Services

| Service | Port | Purpose |
|---------|------|---------|
| **Frontend** | 3000 | Next.js UI |
| **Backend API** | 8000 | FastAPI + MCP |
| **PostgreSQL** | 5432 | Primary database |
| **Redis** | 6379 | State/cache |
| **MongoDB** | 27017 | Dossier storage |
| **Zitadel** | 8082 | Identity provider |
| **OpenFGA** | 9080 (HTTP), 8081 (gRPC) | Authorization |
| **LocalStack** | 4566 | AWS emulation (Secrets Manager) |
| **LiveKit** | 7880 | Voice/video |
| **n8n** | 5678 | Workflow automation |
| **Grafana** | 3001 | Metrics dashboards |
| **Prometheus** | 9090 | Metrics collection |
| **Tempo** | 4317, 3200 | Distributed tracing |
| **Mailpit** | 8025 | Email testing |

---

## Troubleshooting

### "Cannot connect to Docker daemon"
```bash
# macOS with Colima
colima start

# Or start Docker Desktop
```

### Zitadel not accessible
Wait 60-90 seconds after startup. Check logs:
```bash
docker-compose logs zitadel
```

### Backend crashes on startup
```bash
# Check logs
docker-compose logs foundry-backend

# Common fix: ensure PostgreSQL is ready
docker-compose restart foundry-backend
```

### Port already in use
```bash
lsof -i :8000  # Find process
kill <PID>     # Or change port in .env.local
```

### Database connection refused
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres
```

---

## Optional: Additional API Keys

For full functionality, add these to `.env.local`:

```bash
# Voice (Text-to-Speech)
ELEVENLABS_API_KEY=sk_...

# Agent Tracing
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=agent-foundry

# Integrations
NOTION_API_TOKEN=secret_...
GITHUB_TOKEN=ghp_...
```

---

## Next Steps

1. **Explore the UI**: http://localhost:3000
2. **Read the docs**: `START_HERE.md` for project overview
3. **Try an agent**: Use the Test page to run built-in agents
4. **Build your own**: Use Forge to create visual agent workflows

---

## Common Commands

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f foundry-backend

# Restart everything
docker-compose down && docker-compose up -d

# Rebuild after code changes
docker-compose build foundry-backend && docker-compose up -d foundry-backend

# Access PostgreSQL
docker-compose exec postgres psql -U foundry -d foundry

# Access MongoDB
docker-compose exec mongodb mongosh -u foundry -p foundry --authenticationDatabase admin

# Run backend tests
docker-compose exec foundry-backend pytest
```

---

## TL;DR - Complete Setup Script

For the impatient, here's everything in order:

```bash
# 1. Environment
cp .env.example .env.local
# Edit .env.local with OPENAI_API_KEY and NEXTAUTH_SECRET

# 2. Start services
docker-compose up -d
sleep 90  # Wait for Zitadel

# 3. Initialize database
docker-compose exec foundry-backend python scripts/init-postgres.py

# 4. Setup Zitadel (MANUAL - see Step 4 above)
# Then run:
# python scripts/zitadel_setup_localstack.py "<client_id>" "" --issuer http://localhost:8082

# 5. Initialize OpenFGA
python scripts/openfga_init.py
# python scripts/openfga_setup_localstack.py <store_id> <model_id>

# 6. Create admin user
python scripts/setup_admin_user.py

# 7. Restart backend
docker-compose restart foundry-backend

# 8. Access at http://localhost:3000
```

---

**Questions?** Check the full documentation in `/docs` or the admin chat panel in the UI.
