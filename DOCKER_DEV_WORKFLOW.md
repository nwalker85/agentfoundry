## Local Development – Docker Workflow

**Purpose:** This doc is your **day‑to‑day local dev guide** for running the Agent Foundry stack with Docker + Next.js, including hot reload behavior and when you actually need to rebuild.

For a higher‑level overview and AWS deployment, see `START_HERE.md` and `DEPLOYMENT.md`.

---

## 1. What Runs Where

- **Docker Compose services**
  - `livekit` – LiveKit server (`http://localhost:7880`)
  - `redis` – state and checkpointing
  - `foundry-backend` – FastAPI backend (`http://localhost:8000`)
  - `foundry-compiler` – DIS compiler (`http://localhost:8002`)
- **Local Next.js dev server**
  - `npm run dev` – UI on `http://localhost:3000`

You normally start the stack via:

```bash
./start_foundry.sh
```

Under the hood, that:

- Ensures `.env` → `.env.local` symlink for Docker
- Uses `docker compose` (plus `docker-compose.dev.yml` if present) to start services
- Runs health checks for LiveKit, Redis, backend, compiler, and UI

---

## 2. Daily Dev Workflow

### Start Services (Once Per Day)

```bash
# Recommended
./start_foundry.sh

# Or, if you prefer direct Docker commands:
docker compose up -d
# or, with explicit dev overrides:
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Edit Code (No Rebuild Needed!)

```bash
# Edit any of these – changes auto‑reload:
backend/**/*.py          → uvicorn --reload
agent/**/*.py            → uvicorn --reload
compiler/**/*.py         → uvicorn --reload (if using dev override)
app/**/*.tsx             → Next.js Fast Refresh
app/components/**/*.tsx  → Next.js Fast Refresh
app/lib/**/*.ts          → Next.js Fast Refresh
```

**Watch the logs to see backend reload:**

```bash
docker compose logs -f foundry-backend
# You'll see: "Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)"
# On file change: "Detected file change, reloading..."
```

### View Logs

```bash
# Follow specific service
docker compose logs -f foundry-backend

# Last 50 lines
docker compose logs --tail=50 foundry-backend

# All services
docker compose logs -f

# Multiple services
docker compose logs -f foundry-backend livekit redis
```

---

## 3. When You DO Need Extra Actions

### Restart Single Service (Config Change, Not Code)

Use this when you:
- Change `.env` / `.env.local`
- Change non‑watched config files that aren’t hot‑reloaded

```bash
# Example: changed .env.local
docker compose restart foundry-backend

# Or restart multiple
docker compose restart foundry-backend livekit redis
```

### Rebuild (Dependency or Dockerfile Change Only)

Rebuild only when you:
- Change `requirements.txt`
- Change `backend/Dockerfile` / `compiler/Dockerfile`
- Change `Dockerfile.frontend` (if you’re using Docker for the UI)

```bash
# Backend Python deps changed
docker compose build foundry-backend
docker compose up -d foundry-backend

# Compiler Python deps changed
docker compose build foundry-compiler
docker compose up -d foundry-compiler
```

### Full Rebuild (Rare)

Use only when things are badly out of sync:

```bash
docker compose down
docker compose build
docker compose up -d
```

---

## 4. Troubleshooting

### “My changes aren’t showing up”

Check that hot reload is actually firing:

```bash
docker compose logs -f foundry-backend
```

If you don’t see reload messages:

1. Confirm you’re editing the right file under `backend/` or `agent/`.
2. Check the file is mounted into the container:

```bash
docker compose exec foundry-backend ls -la backend/main.py
```

3. Force a restart:

```bash
docker compose restart foundry-backend
```

### “Container won’t start after code change”

You likely introduced a syntax/runtime error:

```bash
docker compose logs foundry-backend
```

Fix the error and save – the container will auto‑restart when the code is valid again.

### “Backend still running old code”

Possible causes:

1. You’re editing the wrong file (check path)
2. File isn’t mounted (check `docker-compose.yml` volumes)
3. Service needs explicit restart:

```bash
docker compose restart foundry-backend
```

### “Frontend not hot‑reloading”

Sometimes Next.js needs polling when running in Docker‑heavy environments:

```bash
# In .env.local
WATCHPACK_POLLING=true

# Then restart frontend
docker compose restart agent-foundry-ui  # if using Docker UI
# or:
Ctrl+C && npm run dev                    # if using local Next.js
```

---

## 5. Service‑Specific Notes

### Backend (FastAPI + uvicorn)

- **Auto‑reload:** ✅ Enabled via `--reload` flag
- **Watch dirs:** `backend/`, `agent/`, `mcp/`
- **Restart time:** ~2–3 seconds

### Frontend (Next.js)

- **Auto‑reload:** ✅ Built into `npm run dev`
- **Watch dirs:** `app/`, `components/`, `lib/`, etc.
- **Restart time:** Instant (Fast Refresh)

### Compiler (FastAPI)

- **Auto‑reload:** ⚠️ Not in base `docker-compose.yml`
- **Fix:** Use `docker-compose.dev.yml` for auto‑reload
- **Or:** Manually restart when needed:

```bash
docker compose restart foundry-compiler
```

### Voice / LiveKit

- LiveKit runs as a Docker service (`livekit`)
- Health: `curl http://localhost:7880`
- If voice flows break, check:

```bash
docker compose logs -f livekit
```

For architecture and deeper troubleshooting, see `LIVEKIT_SETUP.md` and `INFRASTRUCTURE_STATUS.md`.

---

## 6. Performance Tips

### Faster Startup

```bash
# Only start what you need
docker compose up -d livekit redis foundry-backend

# Skip building if images already exist
docker compose up -d --no-build
```

### Faster Rebuilds (When Needed)

```bash
# Use build cache
docker compose build

# If things are really stuck
docker compose build --no-cache foundry-backend

# Parallel builds
docker compose build --parallel
```

### See What’s Running

```bash
# Service status
docker compose ps

# Resource usage
docker stats

# Services with health checks
docker compose ps | grep healthy
```

---

## 7. Summary

- **99% of the time**

```bash
./start_foundry.sh

# Edit code → hot reload

docker compose logs -f foundry-backend   # when debugging
```

- **1% of the time (dependency / Dockerfile change)**

```bash
docker compose build foundry-backend
docker compose up -d foundry-backend
```

- **Almost never**

```bash
# ❌ Don’t do this on every code change!
docker compose down
docker compose build
docker compose up -d
```

---

**Last Updated:** 2025‑11‑16  
**Version:** 0.8.x‑dev – Docker‑based LiveKit + backend + compiler stack
