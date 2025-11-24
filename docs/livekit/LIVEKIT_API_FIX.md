# LiveKit API Import Fix

## Problem

After fixing the async issue, got a new error:

```
❌ Error: module 'livekit.api' has no attribute 'RoomService'
```

## Root Cause

The class is named `RoomServiceClient`, not `RoomService` in the current LiveKit
Python SDK.

## Fix Applied

### Updated `backend/livekit_service.py`

**Before:**

```python
from livekit import api
from livekit.api import AccessToken, VideoGrants

# Later...
self.room_service = api.RoomService(
    url=self.url,
    api_key=self.api_key,
    api_secret=self.api_secret
)
```

**After:**

```python
from livekit import api
from livekit.api import AccessToken, VideoGrants, RoomServiceClient

# Later...
self.room_service = RoomServiceClient(
    self.url,
    self.api_key,
    self.api_secret
)
```

**Changes:**

1. Added `RoomServiceClient` to imports
2. Changed `api.RoomService` → `RoomServiceClient`
3. Updated constructor parameter order (URL first, then key, then secret)

## Diagnostic Tools

### Check LiveKit SDK Structure

```bash
python diagnose_livekit.py
```

This will show:

- LiveKit version installed
- Available classes and methods
- Whether `RoomServiceClient` can be instantiated
- All available methods on the client

### Test the Service

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

## If Still Failing

### Potential Issues

1. **Wrong LiveKit version installed**

   ```bash
   pip show livekit
   ```

   Should show version ~0.17.x

2. **Missing livekit-api package**

   ```bash
   pip install livekit-api
   ```

3. **Method names might differ**

   Run diagnostic to see actual method names:

   ```bash
   python diagnose_livekit.py
   ```

   Look for methods like:

   - `create_room` or `createRoom`
   - `get_room` or `getRoom`
   - `list_participants` or `listParticipants`
   - `delete_room` or `deleteRoom`

## Next Steps

1. Run `python diagnose_livekit.py` to verify SDK structure
2. Run `python test_livekit.py` to test the service
3. If test passes, rebuild Docker: `docker-compose build foundry-backend`
4. Restart: `docker-compose up -d`
5. Test endpoint: `curl -X POST http://localhost:8000/api/voice/session ...`

## Files Changed

- `backend/livekit_service.py` - Updated import and class name
- `diagnose_livekit.py` - Created for SDK inspection

## Commit Message

```
fix: Use RoomServiceClient instead of RoomService

The LiveKit Python SDK uses RoomServiceClient, not RoomService.
Updated import and constructor call.

- backend/livekit_service.py: Import RoomServiceClient, update instantiation
- diagnose_livekit.py: Add SDK structure diagnostic tool
```
