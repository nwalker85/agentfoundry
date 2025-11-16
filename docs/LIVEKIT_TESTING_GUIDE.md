# LiveKit Voice Agent - Testing & Troubleshooting Guide

**Date:** November 16, 2025  
**Version:** 0.8.0-dev

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│ LiveKit Voice Agent Architecture                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  User (Browser) ←─── WebRTC ───→ LiveKit Server     │
│                                         │            │
│                                         │            │
│                                      WebRTC          │
│                                         │            │
│                                         ↓            │
│                              Voice Agent Worker      │
│                                    (Python)          │
│                                         │            │
│                                         │            │
│              ┌──────────────────────────┴──────┐    │
│              │                                  │    │
│              ↓                                  ↓    │
│        Agent (Instructions)          AgentSession   │
│         └── Tools                      ├── VAD      │
│             ├── get_project_status     ├── STT      │
│             ├── create_task            ├── LLM      │
│             └── search_docs            └── TTS      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Key Changes from Old Implementation

### BEFORE (Deprecated Pattern):
```python
# ❌ OLD - Using VoiceAssistant class
assistant = voice.VoiceAssistant(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=IOAgentLLMWrapper(...),  # Complex custom wrapper
    tts=openai.TTS(),
    chat_ctx=initial_ctx,
)
```

### AFTER (Modern Pattern):
```python
# ✅ NEW - Using Agent + AgentSession
agent = Agent(
    instructions="...",
    tools=[...],
)
session = AgentSession(
    agent=agent,
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=openai.TTS(voice="alloy"),
)
await session.start(ctx.room)
```

### Critical Fixes:
1. ✅ Added `await ctx.connect()` - Essential for WebRTC connection
2. ✅ Switched from `VoiceAssistant` to `Agent` + `AgentSession`
3. ✅ Simplified LLM integration - Using native `openai.LLM()` instead of custom wrapper
4. ✅ Added proper function tools using `@function_tool` decorator
5. ✅ Added `await asyncio.Future()` to keep worker running

## Prerequisites

1. **LiveKit Server Running**
   ```bash
   docker ps | grep livekit
   # Should show: livekit container HEALTHY
   ```

2. **Environment Variables Set**
   ```bash
   # In .env file:
   LIVEKIT_URL=ws://livekit:7880
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=secret
   OPENAI_API_KEY=sk-...
   DEEPGRAM_API_KEY=...
   ```

3. **Dependencies Installed**
   ```bash
   # Check requirements.txt has:
   livekit==1.0.19
   livekit-agents==1.2.18
   livekit-api==1.0.7
   livekit-plugins-deepgram
   livekit-plugins-openai
   livekit-plugins-silero
   ```

## Testing Steps

### Step 1: Verify LiveKit Server

```bash
# Check LiveKit is accessible
curl http://localhost:7880

# Should return HTML page or JSON with server info
```

### Step 2: Start Voice Agent Worker

```bash
# Option A: Via Docker Compose
cd /Users/nwalker/Development/Projects/agentfoundry
docker compose up voice-agent-worker -d

# Option B: Locally for debugging
cd /Users/nwalker/Development/Projects/agentfoundry
python backend/voice_agent_worker.py start

# Watch logs
docker compose logs -f voice-agent-worker
```

**Expected Output:**
```
🚀 Starting LiveKit Voice Agent Worker
INFO     livekit.agents.worker    Starting worker
INFO     livekit.agents.worker    Connected to LiveKit server: ws://livekit:7880
INFO     livekit.agents.worker    Worker ready, waiting for jobs...
```

### Step 3: Create Voice Session (Backend API)

```bash
# Test the FastAPI endpoint that creates LiveKit rooms
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test-user", "agent_id": "pm-agent"}'

# Expected response:
{
  "session_id": "sess_...",
  "room_name": "foundry_test-user_pm-agent_sess_...",
  "token": "eyJ...",  # JWT token for frontend
  "livekit_url": "ws://localhost:7880"
}
```

### Step 4: Connect Frontend

```javascript
// In your browser console (http://localhost:3000)
const response = await fetch('http://localhost:8000/api/voice/session', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({user_id: 'test-user', agent_id: 'pm-agent'})
});
const session = await response.json();
console.log('Session:', session);

// The LiveKit React component should then connect using session.token
```

### Step 5: Verify Agent Joins Room

**Worker logs should show:**
```
🎙️  Voice agent connected to room: foundry_test-user_pm-agent_sess_...
✅ Voice agent session active for room: foundry_test-user_pm-agent_sess_...
```

**LiveKit Server logs should show:**
```
INFO     Participant joined: voice-agent
INFO     Track published: audio from voice-agent
```

### Step 6: Test Voice Conversation

1. Click "Enable Voice" in the frontend
2. Grant microphone permissions
3. Say: "Hello, can you help me?"
4. **Expected flow:**
   - Your audio → Silero VAD detects speech
   - Speech → Deepgram STT → "Hello, can you help me?"
   - Text → OpenAI LLM → Response text
   - Response text → OpenAI TTS → Audio
   - Audio → Plays in your browser

## Troubleshooting

### Issue: Worker Not Connecting to LiveKit

**Symptoms:**
```
ERROR    livekit.agents.worker    Failed to connect to LiveKit server
ConnectionRefusedError: [Errno 111] Connection refused
```

**Solutions:**
1. Verify LiveKit is running:
   ```bash
   docker ps | grep livekit
   curl http://localhost:7880
   ```

2. Check network configuration:
   ```bash
   # Worker should use Docker network name
   LIVEKIT_URL=ws://livekit:7880  # ✅ Correct
   LIVEKIT_URL=ws://localhost:7880  # ❌ Wrong (from inside Docker)
   ```

3. Verify API keys match:
   ```bash
   # In .env
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=secret
   
   # In livekit-config.yaml
   keys:
     devkey: secret
   ```

### Issue: Agent Not Joining Room

**Symptoms:**
- Worker starts successfully
- Room is created
- User connects
- Agent never joins

**Solutions:**
1. Check worker logs for job assignments:
   ```bash
   docker compose logs voice-agent-worker | grep "Job assigned"
   ```

2. Verify worker is registered with LiveKit:
   ```bash
   # LiveKit should dispatch jobs to registered workers
   # Check if worker shows "ready" state
   ```

3. Try manual room connection:
   ```python
   # In voice_agent_worker.py, add debug logging
   logger.info(f"Job context: room={ctx.room.name}, participant={ctx.participant}")
   ```

### Issue: No Audio from Agent

**Symptoms:**
- Agent joins room
- User can see agent in participant list
- No audio plays

**Solutions:**
1. Check TTS is working:
   ```python
   # Test OpenAI TTS separately
   import openai
   client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   response = client.audio.speech.create(
       model="tts-1",
       voice="alloy",
       input="Testing TTS"
   )
   with open("/tmp/test.mp3", "wb") as f:
       f.write(response.content)
   ```

2. Verify audio track is published:
   ```bash
   # In LiveKit logs, should see:
   INFO     Track published: audio from voice-agent
   ```

3. Check browser audio permissions and playback

### Issue: Agent Not Responding to Speech

**Symptoms:**
- User speaks
- No response from agent
- No errors in logs

**Solutions:**
1. Check STT is receiving audio:
   ```python
   # Add debug logging in entrypoint
   logger.info("STT events: ...")
   ```

2. Verify VAD is detecting speech:
   ```python
   # Silero VAD should log speech detection
   ```

3. Test Deepgram API key:
   ```bash
   curl -X POST https://api.deepgram.com/v1/listen \
     -H "Authorization: Token $DEEPGRAM_API_KEY" \
     -H "Content-Type: audio/wav" \
     --data-binary @test.wav
   ```

### Issue: Tools Not Being Called

**Symptoms:**
- Agent responds to questions
- Never calls functions like `get_project_status`

**Solutions:**
1. Verify tool definitions are registered:
   ```python
   # In agent definition
   agent = Agent(
       instructions="Use tools when appropriate...",
       tools=[get_project_status, create_task],  # ✅ Include tools
   )
   ```

2. Update instructions to encourage tool use:
   ```python
   instructions="""
   When asked about project status, ALWAYS use the get_project_status tool.
   When asked to create a task, ALWAYS use the create_task tool.
   """
   ```

3. Check OpenAI model supports function calling:
   ```python
   # gpt-4o-mini ✅ Supports function calling
   # gpt-3.5-turbo ✅ Supports function calling
   ```

## Validation Checklist

Run through this checklist to verify everything is working:

- [ ] LiveKit server responding on `http://localhost:7880`
- [ ] Redis healthy: `docker compose ps redis`
- [ ] Backend API running: `curl http://localhost:8000/health`
- [ ] Worker container running: `docker compose ps voice-agent-worker`
- [ ] Worker logs show "Worker ready, waiting for jobs..."
- [ ] Can create voice session via API
- [ ] Frontend receives valid token
- [ ] Agent joins room when user connects
- [ ] Agent responds to speech
- [ ] Tools are called when appropriate
- [ ] Audio quality is acceptable

## Next Steps

Once basic voice is working:

1. **Integrate with IOAgent**: Replace mock tool responses with real LangGraph calls
2. **Add LangGraph Multi-Agent**: Connect to supervisor → worker pattern
3. **Session Persistence**: Store conversation state in Redis
4. **Advanced Features**:
   - Interruption handling
   - Multi-turn conversations
   - Context retention
   - User preferences

## Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LiveKit Quickstart](https://docs.livekit.io/agents/quickstarts/voice-agent/)
- [Agent Examples](https://github.com/livekit/agents/tree/main/examples/voice_agents)
- [LiveKit Discord](https://livekit.io/discord)

---

**Last Updated:** November 16, 2025  
**Status:** Ready for testing
