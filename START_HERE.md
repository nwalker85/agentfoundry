# 🏗️ Agent Foundry - Setup Complete

**Status:** ✅ **READY TO START**  
**Date:** November 15, 2025  
**LiveKit:** Homebrew (native), running with `livekit-server --dev`

---

## 🚀 Quick Start (2 Steps)

### Step 1: Start LiveKit

```bash
livekit-server --dev
```

Keep this running in Terminal 1.

### Step 2: Start Agent Foundry

```bash
# New terminal
cd /Users/nwalker/Development/Projects/agentfoundry
chmod +x start_foundry.sh
./start_foundry.sh
```

**Done!** Services starting on:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Compiler: http://localhost:8002
- LiveKit: ws://localhost:7880

---

## ✅ What's Built

### Infrastructure
- ✅ **LiveKit** - Native Homebrew install (`devkey` / `secret`)
- ✅ **Redis** - Docker container for state persistence
- ✅ **Backend** - FastAPI with voice + agent endpoints
- ✅ **Compiler** - DIS 1.6.0 → Agent YAML transformation
- ✅ **Frontend** - Next.js (existing Engineering Department)

### Backend Features
- ✅ Voice session creation (`POST /api/voice/session`)
- ✅ LiveKit token generation
- ✅ Room management
- ✅ Agent registry (stub)
- ✅ WebSocket endpoint for text chat (stub)

### Compiler Features
- ✅ DIS JSON parsing (all 23 schemas)
- ✅ Agent YAML generation
- ✅ Triplet → LangGraph workflow conversion
- ✅ Upload endpoint (`POST /api/compile/upload`)
- ✅ Save to agent registry

### Configuration
- ✅ `.env.local` with LiveKit credentials
- ✅ `docker-compose.yml` using host LiveKit
- ✅ `start_foundry.sh` startup script
- ✅ `LIVEKIT_SETUP.md` guide

---

## 🧪 Test It Now

### 1. Verify Services

```bash
# LiveKit (native)
curl http://localhost:7880

# Backend
curl http://localhost:8000/health

# Compiler
curl http://localhost:8002/health
```

### 2. Create Voice Session

```bash
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "nate",
    "agent_id": "pm-agent"
  }'
```

**Expected response:**
```json
{
  "session_id": "sess_abc123...",
  "room_name": "foundry_nate_pm-agent_abc123",
  "token": "eyJhbGci...",
  "livekit_url": "ws://localhost:7880",
  "expires_at": "2025-11-15T14:00:00.000Z"
}
```

### 3. Compile DIS Dossier

```bash
# Upload the CIBC dossier
curl -X POST http://localhost:8002/api/compile/upload \
  -F "file=@/path/to/cibc_consumer_banking_cards_future_v2_2_0_complete.json"
```

---

## 📁 Project Structure

```
agentfoundry/
├── backend/                    # FastAPI backend service
│   ├── main.py                # Voice + agent endpoints
│   ├── livekit_service.py     # Session management
│   └── Dockerfile
├── compiler/                   # DIS compiler service
│   ├── dis_compiler.py        # Core compilation logic
│   ├── main.py                # Upload + compile endpoints
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   └── Dockerfile
├── app/                        # Next.js pages (from Engineering Dept)
├── agent/                      # LangGraph agents
│   └── pm_graph.py            # PM Agent
├── mcp/                        # MCP server (existing)
├── agents/                     # Agent YAML registry
├── data/                       # SQLite database
├── docker-compose.yml         # Services (no LiveKit)
├── .env.local                 # Environment variables
├── start_foundry.sh           # Startup script
├── LIVEKIT_SETUP.md          # Homebrew setup guide
└── INFRASTRUCTURE_STATUS.md   # Current status
```

---

## 🎯 Next: Build Voice UI

### Install LiveKit React SDK

```bash
npm install @livekit/components-react livekit-client
```

### Create Voice Component

`app/voice/page.tsx`:
```typescript
'use client';

import { useState } from 'react';
import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';

export default function VoicePage() {
  const [token, setToken] = useState('');
  const [roomUrl, setRoomUrl] = useState('');

  const createSession = async () => {
    const response = await fetch('http://localhost:8000/api/voice/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'nate',
        agent_id: 'pm-agent'
      })
    });
    
    const session = await response.json();
    setToken(session.token);
    setRoomUrl(session.livekit_url);
  };

  if (!token) {
    return <button onClick={createSession}>Start Voice Session</button>;
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={roomUrl}
      connect={true}
    >
      <RoomAudioRenderer />
      <div>Connected to voice session</div>
    </LiveKitRoom>
  );
}
```

---

## 🚧 What's Stubbed (Week 1 Tasks)

### Backend
- [ ] Voice I/O Agent (handles audio from LiveKit)
- [ ] LangGraph state checkpointing (Redis)
- [ ] User authentication (JWT)
- [ ] Agent registry hot-reload (file watcher)

### Frontend
- [ ] Voice UI component (above example)
- [ ] Voice controls (mute, disconnect)
- [ ] Agent selector
- [ ] DIS upload interface

### Integration
- [ ] Voice → LangGraph agent flow
- [ ] Text chat WebSocket implementation
- [ ] Session persistence across voice/text

---

## 📚 Documentation

- **[LIVEKIT_SETUP.md](./LIVEKIT_SETUP.md)** - Complete setup guide
- **[INFRASTRUCTURE_STATUS.md](./INFRASTRUCTURE_STATUS.md)** - Detailed status
- **[README.md](./README.md)** - Engineering Department (original)

---

## 🛠️ Development Workflow

### Terminal 1: LiveKit
```bash
livekit-server --dev
```

### Terminal 2: Services
```bash
./start_foundry.sh
```

### Terminal 3: Logs
```bash
docker-compose logs -f foundry-backend
```

### Terminal 4: Testing
```bash
# Test voice session
curl -X POST http://localhost:8000/api/voice/session \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"nate","agent_id":"pm-agent"}'

# List agents
curl http://localhost:8000/api/agents

# Compile DIS
curl -X POST http://localhost:8002/api/compile/upload \
  -F "file=@dossier.json"
```

---

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker
docker ps

# Rebuild
docker-compose down
docker-compose up --build
```

### LiveKit not accessible
```bash
# Check it's running
lsof -i :7880

# Restart
pkill livekit-server
livekit-server --dev
```

### Backend can't reach LiveKit
```bash
# Check logs
docker-compose logs foundry-backend

# Verify host.docker.internal
docker-compose exec foundry-backend ping host.docker.internal
```

---

## ✨ You're Ready

**Everything is configured. Next command:**

```bash
# Terminal 1
livekit-server --dev

# Terminal 2
./start_foundry.sh
```

Then test voice session creation and start building the Voice UI.

**Let's build agents that can talk.**
