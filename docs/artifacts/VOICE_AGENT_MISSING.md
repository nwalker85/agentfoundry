# Voice Agent Not Joining Room - Diagnostic & Fix

**Date:** November 16, 2025  
**Issue:** User joins LiveKit room but only sees themselves, no agent
participant  
**Status:** 🔴 Critical - Voice functionality broken

## Symptoms

1. ✅ Frontend successfully creates LiveKit room
2. ✅ User successfully joins room
3. ✅ User can see their own audio level
4. ❌ No agent participant appears in "In this conversation"
5. ❌ "Connection lost. Reconnecting..." message appears
6. ❌ User cannot interact with agent via voice

**Screenshot Evidence:**

- Room created: `foundry_user_6g0a1ei2gwx_pm-agent_sess_ZCPqz4oJ3QmGLn9tWtdzmA`
- Participants: Only "User user_6g0a1ei2gwx (You)"
- Expected: Should show both User AND "pm-agent" (IO Agent)

## Root Cause

The **voice-agent-worker** service exists in `docker-compose.yml` but is **not
running**.

### Architecture Review

Per the multi-agent architecture, voice interactions require:

```
User (Frontend)
    ↓ (joins LiveKit room)
LiveKit Server
    ↓ (triggers)
Voice Agent Worker ← NOT RUNNING
    ↓ (joins room as agent)
    ↓ (listens to audio)
    ↓ (Deepgram STT)
IO Agent
    ↓
Supervisor Agent
    ↓
Worker Agents (pm_agent, etc.)
    ↓
Supervisor Agent
    ↓
IO Agent
    ↓ (OpenAI TTS)
Voice Agent Worker
    ↓ (streams audio)
LiveKit Server
    ↓
User (hears response)
```

**Current state:** The voice-agent-worker is not running, so the chain breaks at
step 3.

## Files Involved

### 1. Backend Implementation ✅

**File:** `backend/voice_agent_worker.py`  
**Status:** Code exists and looks correct

Key components:

- `IOAgentLLMWrapper`: Bridges LiveKit LLM interface to our IOAgent
- `entrypoint()`: Joins rooms when participants connect
- Configures STT (Deepgram), TTS (OpenAI), VAD (Silero)
- Routes messages through IOAgent → Supervisor → Workers

### 2. Docker Configuration ✅

**File:** `docker-compose.yml`  
**Status:** Service defined but not running

Service definition:

```yaml
voice-agent-worker:
  build:
    context: .
    dockerfile: backend/Dockerfile
  command: python backend/voice_agent_worker.py start
  volumes:
    - ./backend:/app/backend
    - ./agent:/app/agent
    - ./agents:/app/agents
    - ./data:/app/data
  environment:
    - LIVEKIT_URL=ws://livekit:7880
    - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
    - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}
  depends_on:
    livekit:
      condition: service_healthy
    foundry-backend:
      condition: service_started
  networks:
    - foundry
  restart: unless-stopped
```

## Solution Steps

### 1. Verify Environment Variables

Ensure `.env` contains all required keys:

```bash
# Check current .env
cat .env | grep -E "(LIVEKIT|DEEPGRAM)"
```

Required variables:

- `LIVEKIT_API_KEY` - Should match livekit-config.yaml
- `LIVEKIT_API_SECRET` - Should match livekit-config.yaml
- `DEEPGRAM_API_KEY` - For speech-to-text (get from Deepgram)

If `DEEPGRAM_API_KEY` is missing, you need to:

1. Sign up at https://deepgram.com
2. Get API key from dashboard
3. Add to `.env`:
   ```
   DEEPGRAM_API_KEY=your_key_here
   ```

### 2. Check Current Service Status

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
docker compose ps
```

Expected output should show:

- `livekit` - healthy
- `redis` - healthy
- `foundry-backend` - running
- `foundry-compiler` - running
- `voice-agent-worker` - **should be running but likely missing**

### 3. Start Voice Agent Worker

#### Option A: Start just the worker

```bash
docker compose up -d voice-agent-worker
```

#### Option B: Restart entire stack (safer)

```bash
# Stop everything
docker compose down

# Start everything including worker
docker compose up -d

# Verify all services running
docker compose ps
```

### 4. Check Worker Logs

Once started, verify the worker is connecting:

```bash
# Follow worker logs
docker compose logs -f voice-agent-worker

# Should see:
# - "Voice agent joining room: ..."
# - "Voice assistant active in room: ..."
```

### 5. Test Voice Interaction

1. **Open frontend**: http://localhost:3000/chat
2. **Select agent**: pm-agent
3. **Click voice icon** in chat UI
4. **Verify participants**:
   - Should see TWO participants now:
     - User (you)
     - pm-agent (IO Agent)
5. **Speak**: "Hello, can you hear me?"
6. **Agent should respond** via voice

## Debugging Common Issues

### Issue: Worker exits immediately

```bash
# Check logs for error
docker compose logs voice-agent-worker

# Common causes:
# 1. Missing DEEPGRAM_API_KEY
# 2. Wrong LIVEKIT_API_KEY/SECRET
# 3. Import errors (missing dependencies)
```

**Fix:** Ensure all environment variables are set and Python dependencies
installed

### Issue: Worker runs but doesn't join rooms

```bash
# Check LiveKit connection
docker compose logs voice-agent-worker | grep -i "livekit"

# Should see successful connection to ws://livekit:7880
```

**Fix:** Verify `LIVEKIT_URL` is correct and LiveKit service is healthy

### Issue: Agent joins but no audio

```bash
# Check for Deepgram/OpenAI errors
docker compose logs voice-agent-worker | grep -iE "(deepgram|openai)"

# Common causes:
# 1. Invalid Deepgram API key
# 2. Invalid OpenAI API key
# 3. Rate limits exceeded
```

**Fix:** Verify API keys and check quotas

### Issue: Agent joins but doesn't respond

```bash
# Check if IOAgent is receiving messages
docker compose logs foundry-backend | grep -i "ioagent"

# Check if supervisor is routing
docker compose logs foundry-backend | grep -i "supervisor"
```

**Fix:** Verify full agent chain (IOAgent → Supervisor → Workers) is functioning

## Validation Checklist

After fix, verify:

- [ ] `docker compose ps` shows voice-agent-worker running
- [ ] Worker logs show "Voice agent joining room"
- [ ] Frontend shows 2 participants (User + pm-agent)
- [ ] User can speak and hear audio input level
- [ ] Agent responds with synthesized voice
- [ ] Conversation flows through multi-agent system
- [ ] No "Connection lost" errors

## Architecture Compliance

This fix ensures compliance with the mandatory multi-agent architecture:

1. **IO Agent** (voice_agent_worker.py): Pure I/O adapter for LiveKit
2. **Supervisor Agent**: Routes messages through LangGraph
3. **Worker Agents**: Handle domain logic (pm_agent, etc.)

The voice-agent-worker is the **critical bridge** between LiveKit's voice
streams and the LangGraph multi-agent system. Without it, voice functionality is
completely broken.

## Next Steps After Fix

Once voice is working:

1. **Test multi-turn conversations**:

   - "Create a new user story for login feature"
   - "Add it to the current sprint"
   - "What's in the backlog?"

2. **Validate agent routing**:

   - Check logs to confirm IOAgent → Supervisor → PM Agent flow
   - Verify Notion integration works from voice commands

3. **Production readiness**:
   - Add health checks for voice-agent-worker
   - Implement graceful shutdown
   - Add metrics/monitoring
   - Test WebRTC connectivity in cloud (AWS EC2)

## References

- Implementation Plan: `docs/afmvpimplementation.pdf` (Week 1, Days 1-2)
- Architecture Doc: `docs/afmvparch.pdf`
- Migration Guide: `LIVEKIT_DOCKER_MIGRATION.md`
- LiveKit Agent SDK: https://docs.livekit.io/agents/
- Deepgram STT: https://deepgram.com/docs
- OpenAI TTS: https://platform.openai.com/docs/guides/text-to-speech

---

**Priority:** P0 - Voice is core MVP feature  
**Effort:** 15 minutes (environment setup + service start)  
**Risk:** Low - Service code exists, just needs to run  
**Blocker:** Missing Deepgram API key (if not in .env)
