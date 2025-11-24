## LiveKit & Voice – Local Setup

This document explains how LiveKit fits into Agent Foundry and how to run and
test the **local voice stack**.

- **Current default:** LiveKit runs as a **Docker service** alongside the
  backend and compiler.
- **Legacy option:** Homebrew/native LiveKit is still documented below but is no
  longer the default.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                    │
│                   Port 3000                             │
└───────────┬─────────────────────────┬───────────────────┘
            │                         │
            │ HTTP/REST              │ WebRTC
            ↓                         ↓
┌───────────────────────┐   ┌──────────────────────────┐
│  Backend (FastAPI)    │   │   LiveKit Server         │
│  Port 8000 (HTTP)     │   │   Port 7880 (WebRTC)     │
│  Port 8001 (WS)       │   │   (Homebrew)             │
│  (Docker)             │   │   (Native)               │
└───────┬───────────────┘   └──────────┬───────────────┘
        │                              │
        │  ┌──────────────────────────┘
        │  │
        ↓  ↓
    ┌────────────┐
    │   Redis    │
    │  Port 6379 │
    │  (Docker)  │
    └────────────┘
```

In the current Docker‑based setup:

- LiveKit runs as a container (`livekit` service in `docker-compose.yml`)
- Backend connects to LiveKit via `ws://livekit:7880` on the Docker network
- The browser connects to LiveKit via `ws://localhost:7880` (port mapping)

---

## Environment Variables (Docker LiveKit)

In `.env.local`:

```bash
# LiveKit (Docker local instance)
LIVEKIT_URL=ws://livekit:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Browser / frontend
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
```

---

## Testing

### 1. Verify LiveKit is Running

```bash
# Should return LiveKit info
curl http://localhost:7880

# Or check status
livekit-cli list-rooms
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

Expected response:

```json
{
  "session_id": "sess_...",
  "room_name": "foundry_nate_pm-agent_...",
  "token": "eyJhbGci...",
  "livekit_url": "ws://localhost:7880",
  "expires_at": "2025-11-15T14:00:00.000Z"
}
```

### 3. Test Voice Client

Create `test-voice.html`:

```html
<!doctype html>
<html>
  <head>
    <script src="https://unpkg.com/livekit-client/dist/livekit-client.umd.min.js"></script>
  </head>
  <body>
    <h1>Agent Foundry Voice Test</h1>
    <button onclick="joinRoom()">Join Voice Session</button>
    <div id="status"></div>

    <script>
      async function joinRoom() {
        // Get session from backend
        const response = await fetch(
          'http://localhost:8000/api/voice/session',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_id: 'test-user',
              agent_id: 'pm-agent',
            }),
          }
        );

        const session = await response.json();
        console.log('Session:', session);

        // Connect to LiveKit
        const room = new LivekitClient.Room();
        await room.connect(session.livekit_url, session.token);

        document.getElementById('status').innerHTML =
          `✅ Connected to room: ${session.room_name}`;

        // Enable microphone
        await room.localParticipant.setMicrophoneEnabled(true);
      }
    </script>
  </body>
</html>
```

Open in browser, click button, grant mic access.

---

## Troubleshooting

### LiveKit not starting

```bash
# Check if port is in use
lsof -i :7880

# Kill existing process
kill -9 $(lsof -t -i:7880)

# Restart LiveKit
livekit-server --dev
```

### Backend can't connect to LiveKit

Check docker logs:

```bash
docker-compose logs foundry-backend
```

Common issue: `host.docker.internal` not resolving

- **Mac/Windows:** Works automatically
- **Linux:** Need to add `--add-host=host.docker.internal:host-gateway`

### Redis connection failed

```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test connection
docker-compose exec redis redis-cli ping
```

---

## Development Workflow

### Terminal 1: LiveKit

```bash
livekit-server --dev
```

### Terminal 2: Agent Foundry

```bash
./start_foundry.sh
```

### Terminal 3: Logs

```bash
# Watch all services
docker-compose logs -f

# Watch specific service
docker-compose logs -f foundry-backend
```

### Terminal 4: Testing

```bash
# Create voice session
curl -X POST http://localhost:8000/api/voice/session \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"nate","agent_id":"pm-agent"}'

# List agents
curl http://localhost:8000/api/agents
```

---

## Stopping Services

```bash
# Stop Docker services
docker-compose down

# Stop LiveKit (Ctrl+C in Terminal 1)
# Or kill process:
pkill livekit-server
```

---

## Next Steps

**Today:**

- [x] LiveKit running locally
- [x] Backend connecting to LiveKit
- [x] Voice session API working
- [ ] Test voice session creation
- [ ] Test room creation in LiveKit

**Tomorrow:**

- [ ] Frontend: Install LiveKit React SDK
- [ ] Frontend: Voice UI component
- [ ] Frontend: Join room from UI

**Week 1:**

- [ ] Voice I/O Agent (audio handling)
- [ ] LangGraph integration
- [ ] State persistence (Redis)

---

## Resources

- **LiveKit Homebrew:** `brew info livekit`
- **LiveKit Docs:** https://docs.livekit.io
- **LiveKit CLI:** `livekit-cli --help`
- **React SDK:** https://docs.livekit.io/client-sdk-js/

---

**Status:** ✅ Ready to test voice sessions
