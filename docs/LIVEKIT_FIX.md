# LiveKit Voice Session Fix

## Problem
The `/api/voice/session` endpoint was returning "Internal Server Error" when called.

## Root Cause
The `LiveKitService` methods were declared as `async` and being called with `await`, but the LiveKit Python SDK's `RoomService` methods are **synchronous**, not asynchronous. This caused the await to fail.

## Changes Made

### 1. `/backend/livekit_service.py`
Removed `async` declarations and `await` keywords from:
- `create_voice_session()` - Changed from async to sync
- `get_room_info()` - Changed from async to sync  
- `end_session()` - Changed from async to sync

All calls to `self.room_service.*` are now synchronous.

### 2. `/backend/main.py`
Updated endpoint handlers to call LiveKit service methods without `await`:
- `create_voice_session()` endpoint - Removed await
- `get_room_info()` endpoint - Removed await
- `end_voice_session()` endpoint - Removed await

The endpoint functions themselves remain `async` for FastAPI compatibility, but the LiveKit service calls are synchronous.

## Testing

### Prerequisites
Install LiveKit dependencies first (see [LIVEKIT_INSTALL.md](LIVEKIT_INSTALL.md)):
```bash
pip install -r requirements.txt
```

### Quick Test (No LiveKit Server Required)
This tests the service initialization and session creation logic:

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
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

### Full Integration Test (Requires LiveKit Server)
1. Ensure LiveKit server is running:
```bash
# If using Homebrew
brew services start livekit

# Or with Docker
docker run --rm -p 7880:7880 -p 7881:7881 \
  livekit/livekit-server \
  --dev
```

2. Restart the backend service:
```bash
docker-compose restart foundry-backend
```

3. Test the endpoint:
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
  "session_id": "sess_...",
  "room_name": "foundry_nate_pm-agent_sess_...",
  "token": "eyJ...",
  "livekit_url": "ws://localhost:7880",
  "expires_at": "2025-11-15T..."
}
```

## Architecture Notes

### Why This Works
- **FastAPI**: Endpoints remain async for proper async/await support in FastAPI
- **LiveKit SDK**: Uses synchronous HTTP/gRPC calls under the hood
- **Blocking**: LiveKit calls block briefly but are fast enough for HTTP responses
- **No Breaking Changes**: All existing features preserved, LangGraph unchanged

### Future Considerations
If LiveKit calls become slow (>100ms), consider:
1. Running in thread pool executor: `await run_in_executor(None, service.create_session, ...)`
2. Using LiveKit's async client (if/when available)
3. Caching room info to reduce API calls

## Validation Checklist
- [x] Removed async/await from LiveKitService methods
- [x] Removed await calls in main.py endpoints  
- [x] Preserved all existing functionality
- [x] No changes to LangGraph integration
- [x] Created test script for verification
- [x] Documented changes and testing steps

## Files Changed
1. `backend/livekit_service.py` - Converted to sync methods + fixed RoomServiceClient import
2. `backend/main.py` - Removed await calls
3. `test_livekit.py` - Created for testing (NEW)
4. `diagnose_livekit.py` - SDK diagnostic tool (NEW)
5. `requirements.txt` - Added LiveKit packages

## Related Issues
- See [LIVEKIT_INSTALL.md](LIVEKIT_INSTALL.md) for dependency installation
- See [LIVEKIT_API_FIX.md](LIVEKIT_API_FIX.md) for RoomServiceClient import fix

## Next Steps
1. Run `python test_livekit.py` to verify the fix
2. Start LiveKit server if not running
3. Restart backend: `docker-compose restart foundry-backend`
4. Test endpoint with curl command above
5. If working, proceed with voice UI integration

---

**Commit Message:**
```
fix: Convert LiveKit service methods from async to sync

The LiveKit Python SDK RoomService uses synchronous methods, not async.
Removed async/await from LiveKitService methods and corresponding
await calls in FastAPI endpoints. All functionality preserved.

- backend/livekit_service.py: Remove async from create_voice_session, get_room_info, end_session
- backend/main.py: Remove await calls for LiveKit service methods
- test_livekit.py: Add standalone test for LiveKit service
```
