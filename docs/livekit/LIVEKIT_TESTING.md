# LiveKit Voice Session - Testing Guide

## Quick Test (Token Generation Only)

No LiveKit server required:

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
source venv/bin/activate
python test_livekit_async.py
```

**Expected Output:**

```
=== Testing Token Generation (Standalone) ===
✅ Token generated successfully
  JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Full Test (With LiveKit Server)

### 1. Start LiveKit Server

```bash
# Option A: Homebrew (recommended)
brew services start livekit

# Option B: Docker
docker run -p 7880:7880 livekit/livekit-server --dev

# Verify it's running
curl http://localhost:7880
# Should return: {"version":"...","region":"..."}
```

### 2. Run Test Suite

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
source venv/bin/activate
python test_livekit_async.py
```

**Expected Output:**

```
=== Testing Token Generation (Standalone) ===
✅ Token generated successfully

=== Testing LiveKit Voice Session Creation ===
[Test 1] Creating voice session...
✅ Voice session created successfully
  Session ID: sess_abc123...
  Room: foundry_test-user_pm-agent_abc123...
  Token: eyJhbGci...
  Expires: 2025-11-15T15:00:00

[Test 2] Getting room info...
✅ Room info retrieved
  Participants: 0

[Test 3] Ending session...
✅ Room deleted successfully

✅ All tests passed!

🎉 All tests PASSED
```

### 3. Test FastAPI Endpoint

```bash
# Terminal 1: Start backend
cd /Users/nwalker/Development/Projects/agentfoundry/backend
source ../venv/bin/activate
uvicorn main:app --reload

# Terminal 2: Test endpoint
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "nate",
    "agent_id": "pm-agent",
    "session_duration_hours": 1
  }'
```

**Expected Response:**

```json
{
  "session_id": "sess_XYZ123...",
  "room_name": "foundry_nate_pm-agent_XYZ123...",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "livekit_url": "ws://localhost:7880",
  "expires_at": "2025-11-15T15:00:00"
}
```

## Docker Testing

After local validation passes:

```bash
cd /Users/nwalker/Development/Projects/agentfoundry

# Rebuild backend with new code
docker-compose build foundry-backend

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f foundry-backend

# Test endpoint through Docker
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "docker-test",
    "agent_id": "pm-agent",
    "session_duration_hours": 1
  }'
```

**Note:** Docker backend will try to connect to LiveKit at
`ws://host.docker.internal:7880`. Make sure LiveKit is running on your host
machine.

## Troubleshooting

### "Connection refused" errors

**Problem:** LiveKit server not running

**Solution:**

```bash
brew services list | grep livekit
# If not running:
brew services start livekit
```

### "No module named 'livekit'"

**Problem:** Virtual environment not activated or packages not installed

**Solution:**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Room creation failed"

**Problem:** May be expected if LiveKit server is not running

**Solution:**

- Token generation test will still pass ✅
- Full session test requires LiveKit server running

### Import errors in test

**Problem:** Backend module not in Python path

**Solution:**

```bash
# Run from project root
cd /Users/nwalker/Development/Projects/agentfoundry
python test_livekit_async.py
```

## Success Criteria

✅ Token generation test passes  
✅ Session creation test passes (with LiveKit server)  
✅ Room info retrieval works  
✅ Room deletion works  
✅ FastAPI endpoint returns valid JSON  
✅ Docker tests pass

## Next Steps

After all tests pass:

1. Integrate frontend LiveKit React components
2. Connect to LangGraph agent for voice I/O
3. Add persistence and session management
4. Deploy to AWS EC2

## Reference

- Implementation: `backend/livekit_service.py`
- Endpoints: `backend/main.py`
- Tests: `test_livekit_async.py`
- Docs: `docs/LIVEKIT_TROUBLESHOOTING_SNAPSHOT.md`
