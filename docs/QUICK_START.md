# Agent Foundry - Quick Start Guide

**Version:** 0.8.1-dev  
**Last Updated:** 2025-11-16

---

## 🚀 Starting the System

### Start All Services (Colima + Docker)

```bash
# Ensure Colima is running
colima status  # Check status
colima start   # Start if needed

# Start Agent Foundry services
cd /Users/nwalker/Development/Projects/agentfoundry
./start_foundry.sh

# Or manually with docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Stop All Services

```bash
docker-compose down

# Stop Colima (optional)
colima stop
```

---

## 🌐 Service URLs

| Service           | URL                        | Purpose                 |
| ----------------- | -------------------------- | ----------------------- |
| **Frontend UI**   | http://localhost:3000      | Main web interface      |
| **Backend API**   | http://localhost:8000      | REST API + MCP server   |
| **API Docs**      | http://localhost:8000/docs | Swagger/OpenAPI docs    |
| **Compiler**      | http://localhost:8002      | DIS to YAML compiler    |
| **Forge Service** | http://localhost:8003      | Agent configuration API |
| **n8n Workflows** | http://localhost:5678      | Workflow automation     |
| **MongoDB**       | mongodb://localhost:27017  | Dossier storage         |
| **PostgreSQL**    | localhost:5432             | Control plane DB        |
| **Redis**         | localhost:6379             | State/cache             |
| **LiveKit**       | ws://localhost:7880        | Voice/video             |

---

## 🧭 Navigation Structure

```
📊 Dashboard

CREATE
  📄 From DIS      - Import from Domain Intelligence Schema
  ➕ New Agent     - Visual agent designer (Forge)

MANAGE
  📚 Agents        - Agent registry and management
  🗄️ Datasets      - Data management
  🔧 Tools         - Tool library

LAUNCH
  🧪 Test          - Test agents before deployment
  🚀 Deploy        - Deployment management
  📈 Monitor       - System monitoring

CONFIGURE
  📁 Projects      - Project management
  🌍 Domains       - Domain configuration
  👥 Teams         - Team & permissions

🏪 Marketplace    - Agent marketplace
🛡️ Admin          - System administration
```

---

## 🎨 Key Features

### 1. Visual Agent Designer (New Agent)

**Location:** http://localhost:3000/app/forge

**Features:**

- Drag-and-drop node-based workflow design
- Real-time Python LangGraph code generation
- Edit node properties (label, model, parameters)
- Delete nodes with confirmation
- Undo/redo support
- Save and deploy agents

**Node Types:**

- 🟢 Entry Point - Workflow start
- 🔵 Process - LLM processing
- 🟡 Decision - Conditional routing
- 🟣 Tool Call - External tool integration
- 🔴 End - Workflow termination

### 2. DIS Compiler (From DIS)

**Location:** http://localhost:3000/app/compiler

**Features:**

- Import Domain Intelligence Schema definitions
- Validate DIS 1.6.0 compliance
- Generate agent configurations
- Upload DIS files

### 3. MongoDB Dossier Storage

**Connection:**

```bash
mongodb://foundry_dossier:foundry@localhost:27017/dossiers
```

**Collections:**

- `dossiers` - Main DIS dossier storage
- `dossier_versions` - Version history
- `dossier_operations` - Audit log
- `dossier_locks` - Concurrent editing locks

**Sample Data:**

- Pre-loaded sample banking domain dossier
- View with MongoDB Compass or mongosh

---

## 🔧 Common Operations

### Check Service Health

```bash
# Backend health
curl http://localhost:8000/health | jq .

# Compiler health
curl http://localhost:8002/health | jq .

# All containers
docker ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f foundry-backend
docker-compose logs -f agent-foundry-ui
docker-compose logs -f mongodb
```

### Restart Single Service

```bash
docker-compose restart foundry-backend
docker-compose restart agent-foundry-ui
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose build foundry-backend
docker-compose up -d foundry-backend

# Rebuild all
docker-compose build
docker-compose up -d
```

### Access MongoDB

```bash
# Using mongosh
docker exec -it agentfoundry-mongodb-1 mongosh \
  -u foundry_dossier -p foundry --authenticationDatabase dossiers

# List collections
use dossiers
show collections
db.dossiers.find().pretty()
```

### Access PostgreSQL

```bash
# Using psql
docker exec -it agentfoundry-postgres-1 psql \
  -U foundry -d foundry

# List tables
\dt
SELECT * FROM organizations;
```

---

## 🐛 Troubleshooting

### Docker Issues

**Problem:** "Cannot connect to Docker daemon"

```bash
# Solution: Start Colima
colima start
docker info
```

**Problem:** Port already in use

```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting process or change port in .env.local
```

### Service Issues

**Problem:** Backend not starting

```bash
# Check logs
docker logs agentfoundry-foundry-backend-1

# Restart service
docker-compose restart foundry-backend
```

**Problem:** UI not loading

```bash
# Check logs
docker logs agentfoundry-agent-foundry-ui-1

# Common fix: Clear Next.js cache
docker-compose exec agent-foundry-ui rm -rf .next
docker-compose restart agent-foundry-ui
```

### MongoDB Issues

**Problem:** Connection refused

```bash
# Check MongoDB is running
docker ps | grep mongodb

# Check health
docker exec agentfoundry-mongodb-1 mongosh --eval "db.adminCommand('ping')"
```

---

## 📦 Development Workflow

### Making Changes

1. **Edit Code** - Use your favorite editor
2. **Auto-reload** - Services watch for changes
3. **Test** - Changes reflected in seconds
4. **No Rebuild** - Hot reload for Python and TypeScript

### Committing Changes

```bash
# Check status
git status

# Stage changes
git add .

# Commit
git commit -m "Description of changes"

# Push
git push origin your-branch
```

---

## 📚 Documentation

### Core Docs

- `START_HERE.md` - Project overview
- `DOCKER_DEV_WORKFLOW.md` - Docker development guide
- `README.md` - General readme

### Architecture

- `docs/FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md`
- `docs/DOSSIER_SYSTEM_DESIGN.md`
- `docs/NAVIGATION_SYSTEM.md`

### Recent Changes

- `docs/NAVIGATION_RESTRUCTURE_COMPLETE.md`
- `docs/FORGE_PYTHON_CONVERSION_COMPLETE.md`
- `docs/SESSION_COMPLETE_SUMMARY.md`

---

## ✅ Health Checklist

Use this checklist to verify system health:

- [ ] Colima running (`colima status`)
- [ ] Docker daemon accessible (`docker info`)
- [ ] All containers running (`docker ps`)
- [ ] Backend healthy (`curl http://localhost:8000/health`)
- [ ] Frontend accessible (http://localhost:3000)
- [ ] MongoDB healthy
      (`docker exec ... mongosh --eval "db.adminCommand('ping')"`)
- [ ] Redis responsive (`docker exec ... redis-cli ping`)

**All Green?** 🟢 You're ready to build!

---

**Need Help?** Check the comprehensive documentation in `/docs` directory.

**Have Questions?** See the Admin chat panel at the bottom of the UI.

**Found a Bug?** Create an issue with details and logs.

---

Happy Building! 🏭
