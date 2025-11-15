# Docker Build Fixes

## Issues Fixed

### 1. Missing `/public/` directory
**Problem:** Frontend Dockerfile tried to copy `/public/` from project root  
**Cause:** Next.js App Router has `/app/public/` not root `/public/`  
**Fix:** Removed frontend from Docker (runs locally with `npm run dev`)

### 2. Missing `/agents/` directory
**Problem:** Backend volume mount referenced non-existent directory  
**Fix:** Created `/agents/` and added `pm-agent.agent.yaml`

### 3. Missing `/data/` directory
**Problem:** Volume mount referenced non-existent directory  
**Fix:** Created `/data/` with `.gitkeep`

### 4. Docker Compose reading wrong env file
**Problem:** Compose reads `.env` but we have `.env.local`  
**Fix:** Start script creates symlink: `.env` → `.env.local`

---

## Updated Architecture

### Services in Docker
- ✅ **Redis** - State persistence (port 6379)
- ✅ **Backend** - FastAPI + LiveKit (ports 8000, 8001)
- ✅ **Compiler** - DIS → YAML (port 8002)

### Services Running Locally
- ✅ **LiveKit** - Homebrew (`livekit-server --dev` on port 7880)
- ✅ **Frontend** - Next.js (`npm run dev` on port 3000)

---

## Updated Startup Sequence

### Terminal 1: LiveKit
```bash
livekit-server --dev
```

### Terminal 2: Docker Services
```bash
./start_foundry.sh
```

### Terminal 3: Frontend
```bash
npm run dev
```

---

## Files Changed

### Created
- `/agents/` - Agent YAML registry
- `/agents/pm-agent.agent.yaml` - PM Agent manifest
- `/data/` - SQLite database location
- `/data/.gitkeep` - Keep directory in git
- `/backend/__init__.py` - Python package
- `/compiler/__init__.py` - Python package

### Updated
- `/backend/Dockerfile` - Fixed paths, added health check
- `/compiler/Dockerfile` - Fixed paths, added health check
- `/docker-compose.yml` - Removed frontend, added health checks
- `/start_foundry.sh` - Creates `.env` symlink, updated instructions

### Removed
- Frontend service from docker-compose (runs locally)

---

## Directory Structure

```
agentfoundry/
├── backend/           # FastAPI backend (Docker)
│   ├── __init__.py
│   ├── main.py
│   ├── livekit_service.py
│   └── Dockerfile
├── compiler/          # DIS compiler (Docker)
│   ├── __init__.py
│   ├── dis_compiler.py
│   ├── main.py
│   └── Dockerfile
├── agents/            # Agent YAML registry (NEW)
│   └── pm-agent.agent.yaml
├── data/              # SQLite database (NEW)
│   └── .gitkeep
├── app/               # Next.js pages (local)
│   ├── api/
│   ├── chat/
│   ├── public/        # This is where public assets live!
│   └── ...
├── agent/             # LangGraph agents
│   └── pm_graph.py
├── mcp/               # MCP server
│   └── ...
├── .env               # Symlink to .env.local (created by script)
├── .env.local         # Actual environment variables
├── docker-compose.yml # Backend + Compiler + Redis only
└── start_foundry.sh   # Startup script
```

---

## Next Steps

Run the startup script again:

```bash
./start_foundry.sh
```

Should now build successfully! ✅
