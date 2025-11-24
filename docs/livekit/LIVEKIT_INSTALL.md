# LiveKit Installation & Testing

## Quick Install (Local Development)

### Option 1: Install directly

```bash
pip install livekit livekit-api livekit-agents
```

### Option 2: Use requirements.txt (Recommended)

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
pip install -r requirements.txt
```

### Option 3: Use virtual environment (Best Practice)

```bash
cd /Users/nwalker/Development/Projects/agentfoundry

# Create venv if not exists
python -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Verify Installation

```bash
python -c "import livekit; print('✓ LiveKit installed:', livekit.__version__)"
```

Expected output:

```
✓ LiveKit installed: 0.17.4
```

## Run Test

```bash
python test_livekit.py
```

Expected output:

```
✓ Imports successful
✓ LiveKitService initialized
  - URL: ws://localhost:7880
  - API Key: devkey...

Creating test session...
✓ Session created:
  - Session ID: sess_...
  - Room Name: foundry_test_user_test_agent_sess_...
  - Token: eyJ...
  - Expires: 2025-11-15 XX:XX:XX

✅ All tests passed!
```

## Troubleshooting

### Error: "No module named 'livekit'"

**Solution:** Install LiveKit packages (see above)

### Error: "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set"

**Solution:** The test script sets these automatically. If you see this error,
the environment variables in the test script aren't being applied correctly.

### Error: Connection to LiveKit server failed

**Cause:** This test doesn't actually connect to LiveKit - it only tests token
generation. **Action:** This is expected and won't prevent the fix from working.

## Full Integration Test (With LiveKit Server)

1. **Start LiveKit server:**

```bash
# Using Homebrew
brew services start livekit

# OR using Docker
docker run --rm -p 7880:7880 -p 7881:7881 \
  livekit/livekit-server --dev
```

2. **Restart backend:**

```bash
docker-compose restart foundry-backend
```

3. **Test the endpoint:**

```bash
curl -X POST http://localhost:8000/api/voice/session \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "nate",
    "agent_id": "pm-agent",
    "session_duration_hours": 2
  }'
```

Expected response:

```json
{
  "session_id": "sess_abc123...",
  "room_name": "foundry_nate_pm-agent_sess_abc123...",
  "token": "eyJhbGc...",
  "livekit_url": "ws://localhost:7880",
  "expires_at": "2025-11-15T18:30:00.123456"
}
```

## Dependencies Added

The following packages were added to `requirements.txt`:

- `livekit==0.17.4` - Core LiveKit Python SDK
- `livekit-api==0.7.2` - LiveKit API client
- `livekit-agents==0.10.3` - LiveKit agent framework

## Next Steps

Once the test passes:

1. ✅ LiveKit service is working locally
2. → Rebuild Docker image: `docker-compose build foundry-backend`
3. → Restart services: `docker-compose up -d`
4. → Test endpoint with curl
5. → Integrate with frontend voice UI
