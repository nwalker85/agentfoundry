## STATUS SNAPSHOT (LEGACY) – Infrastructure as of 2025‑11‑15

> **Note:** This file captures a point‑in‑time status of the infrastructure during the LiveKit + Docker bring‑up.  
> For the **current deployment workflow**, see:
> - `docs/AWS_DEPLOYMENT_ECS.md` – ECS/Fargate deployment guide  
> - `DEPLOYMENT.md` – legacy EC2 deployment overview (archive)  
> - `DOCKER_DEV_WORKFLOW.md` – local Docker development workflow

# Agent Foundry - Infrastructure Status

**Date:** November 15, 2025  
**Status:** ✅ **FULLY OPERATIONAL**  
**LiveKit:** ✅ Running (Homebrew)  
**Docker:**  
  - ✅ Redis: Healthy  
  - ✅ Backend: Healthy  
  - ✅ Compiler: Healthy

---

## ✅ What's Complete

### Docker Infrastructure
- [x] `docker-compose.yml` with 5 services
- [x] LiveKit server configured
- [x] Redis for state management
- [x] Network bridge (`foundry`)
- [x] Volume persistence

### Backend Service
- [x] `backend/main.py` - FastAPI with voice endpoints
- [x] `backend/livekit_service.py` - Session management
- [x] `backend/Dockerfile` - Containerized
- [x] Voice session creation API
- [x] Room management API
- [x] WebSocket stub for text chat
- [x] Agent registry endpoints (stub)

### Compiler Service
- [x] `compiler/dis_compiler.py` - Full DIS → YAML compiler
- [x] `compiler/main.py` - FastAPI endpoints
- [x] `compiler/Dockerfile` - Containerized
- [x] Upload endpoint for DIS files
- [x] Compile + save to agent registry

### Configuration
- [x] `livekit-config.yaml` - Server config
- [x] `.env.example` - All environment variables
- [x] `generate_livekit_keys.sh` - Key generation
- [x] `LIVEKIT_SETUP.md` - Complete guide

### Existing Assets (from Engineering Department)
- [x] MCP server (`mcp_server.py`)
- [x] PM Agent LangGraph (`agent/pm_graph.py`)
- [x] Next.js frontend (`/app`)
- [x] Notion/GitHub integrations
- [x] Audit logging

---

## 🚧 What's Stubbed (Needs Implementation)

### Backend
- [ ] **Voice I/O Agent** - Handles LiveKit audio events
- [ ] **LangGraph integration** - Connect agents to voice/text
- [ ] **State persistence** - Redis checkpointing for sessions
- [ ] **User authentication** - JWT or session cookies
- [ ] **Agent registry hot-reload** - File watcher on `/agents/*.yaml`

### Frontend
- [ ] **Voice UI component** - LiveKit React SDK integration
- [ ] **Voice controls** - Mute, disconnect, status
- [ ] **DIS upload UI** - Compiler interface
- [ ] **Agent selector** - Choose which agent to talk to
- [ ] **Session management** - Create/end voice sessions

### Compiler
- [ ] **Enhanced triplet → workflow** - Better node generation
- [ ] **Function binding logic** - Parse TripletFunctionMatrixEntries
- [ ] **Mock API generation** - Create test endpoints from Functions
- [ ] **Validation** - Schema compliance checking

---

## 🎯 Immediate Next Actions

### Today (Nov 15)

**1. Test the stack:**
```bash
# Generate keys
./generate_livekit_keys.sh

# Copy to .env.local
cp .env.example .env.local
# Edit with generated keys

# Start everything
docker-compose up --build
```

**2. Verify services:**
```bash
# All should return healthy
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:7880
```

**3. Test voice session creation:**
```bash
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "nate", "agent_id": "pm-agent"}'
```

**4. Test DIS compiler:**
```bash
# Use uploaded CIBC dossier
curl -X POST http://localhost:8002/api/compile/upload \
  -F "file=@/path/to/cibc_dossier.json"
```

---

## 📋 Week 1 Plan (Revised)

### Day 1 (Today) - Infrastructure Validation
- [x] Docker stack complete
- [x] LiveKit configured
- [x] Backend skeleton ready
- [x] **Fixed:** Docker build (removed invalid LiveKit versions)
- [x] **Fixed:** Compiler startup (added python-multipart)
- [x] **Verified:** All services healthy (Redis, Backend, Compiler)
- [ ] **Test:** Voice session creation works
- [ ] **Test:** Room appears in LiveKit

### Day 2 - Frontend Voice UI
- [ ] Install LiveKit React SDK
- [ ] Create `<VoiceInterface>` component
- [ ] Create `<VoiceControls>` component
- [ ] Wire up session creation
- [ ] Test: Click → Join room → See participant

### Day 3 - Voice I/O Agent
- [ ] Create `VoiceIOAgent` class
- [ ] Handle LiveKit room events
- [ ] Transcribe audio → text
- [ ] Text → TTS → audio out
- [ ] Test: Speak → Agent hears

### Day 4 - LangGraph Integration
- [ ] Connect Voice I/O Agent → PM Agent
- [ ] Redis checkpointing for sessions
- [ ] Session persistence across reconnects
- [ ] Test: Conversation continuity

### Day 5 - End-to-End Voice Loop
- [ ] User authentication (simple JWT)
- [ ] Session ID → user_id mapping
- [ ] Full voice conversation test
- [ ] Demo: DIS upload → Agent live → Voice chat

---

## 🔧 Known Gaps

### Authentication
Current: None (all endpoints open)  
Needed: JWT tokens or session cookies  
Priority: High (required for state persistence)

### Agent Registry
Current: Hardcoded PM agent  
Needed: File watcher on `/agents/*.yaml`  
Priority: Medium (can manually restart for now)

### Error Handling
Current: Basic try/catch  
Needed: Proper error types, retry logic  
Priority: Medium

### Monitoring
Current: Console logs  
Needed: Structured logging, metrics  
Priority: Low (post-MVP)

---

## 💡 Architecture Decisions

### Why self-hosted LiveKit?
- Full control over infrastructure
- No usage costs (vs $50-500/mo cloud)
- Same APIs (portable to cloud later)
- ~500MB RAM footprint (fits on t3.small)

### Why Redis?
- LangGraph checkpointing requires it
- LiveKit uses it for multi-node scaling
- Single dependency for both needs

### Why separate Compiler service?
- Isolates DIS logic from runtime
- Can scale independently
- Clean separation of concerns

### Why WebSocket + LiveKit (dual transport)?
- WebSocket: Text chat, notifications, UI updates
- LiveKit: Voice/video only
- Unified state via shared session ID

---

## 📊 Resource Usage (Estimated)

**Single t3.small EC2 (2GB RAM):**
- LiveKit: ~500MB
- Redis: ~50MB
- Backend: ~300MB
- Compiler: ~200MB
- Frontend: ~200MB
- **Total:** ~1.25GB (leaves 750MB buffer)

**Disk:**
- Docker images: ~2GB
- SQLite DB: <100MB
- Agent YAML files: <10MB
- Logs: ~100MB/day

---

## 🚀 Ready to Start

**Everything you need is in place:**

1. ✅ Docker infrastructure configured
2. ✅ LiveKit self-hosted and ready
3. ✅ Backend service skeleton complete
4. ✅ Compiler service functional
5. ✅ DIS schema integration ready
6. ✅ Environment configuration documented

**Next command:**
```bash
./generate_livekit_keys.sh
# Then edit .env.local with the keys
docker-compose up --build
```

**First test:**
```bash
# Should return session details
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "nate", "agent_id": "pm-agent"}'
```

**You're locked and loaded. Time to build.**

---

## 📖 Documentation

- [LIVEKIT_SETUP.md](./LIVEKIT_SETUP.md) - Complete LiveKit guide
- [MVP Implementation Plan](./Agent%20Foundry%20MVP%20-%20Implementation%20Plan.md) - Original plan
- [Engineering Department README](./README.md) - Current state

---

## 🔧 Recent Fixes

### Docker Build Fix (Nov 15, 2025 - Part 1)
**Issue:** Build failing with `ERROR: No matching distribution found for livekit-api==0.7.2`

**Root Cause:**
- `requirements.txt` had pinned LiveKit versions
- `livekit-api==0.7.2` doesn't exist in PyPI
- Packages were redundant (Dockerfile installs them separately)

**Fix Applied:**
- Removed LiveKit packages from `requirements.txt`
- Backend Dockerfile installs without version pins
- Removed obsolete `version: '3.8'` from docker-compose.yml

**Status:** ✅ Fixed

---

### Compiler Startup Fix (Nov 15, 2025 - Part 2)
**Issue:** Compiler container failing with:
```
RuntimeError: Form data requires "python-multipart" to be installed.
```

**Root Cause:**
- `/api/compile/upload` endpoint uses `UploadFile`
- FastAPI requires `python-multipart` for file upload handling
- Compiler Dockerfile didn't install this dependency

**Fix Applied:**
- Added `python-multipart` to compiler Dockerfile
```dockerfile
RUN pip install --no-cache-dir \
    pyyaml \
    pydantic \
    python-multipart
```

**Rebuild Instructions:**
```bash
docker-compose build foundry-compiler
docker-compose up -d foundry-compiler
curl http://localhost:8002/health  # Should return healthy
```

**Status:** ✅ **VERIFIED - WORKING**

```bash
$ curl http://localhost:8002/health
{"status":"healthy","compiler":"operational","dis_schema_url":"..."}
```

**All Services Now Operational:**
- ✅ Redis: Healthy
- ✅ Backend: Healthy (LiveKit + Redis configured)
- ✅ Compiler: Healthy (DIS parsing ready)

---

**Last Updated:** November 15, 2025  
**Next Review:** After Day 1 testing complete
