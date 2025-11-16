# Docker Development Workflow - Quick Reference

## TL;DR: Stop Rebuilding on Every Change!

**Your services are already configured for hot reload.** Just edit files and save.

---

## Daily Dev Workflow

### Start Services (Once Per Day)

```bash
# Standard mode (already dev-configured)
docker-compose up -d

# OR with explicit dev overrides
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Edit Code (No Rebuild Needed!)

```bash
# Edit any of these - changes auto-reload:
backend/**/*.py          → uvicorn --reload
agent/**/*.py            → uvicorn --reload  
app/**/*.tsx             → Next.js hot reload
components/**/*.tsx      → Next.js hot reload
compiler/**/*.py         → uvicorn --reload (if using dev override)
```

**Watch the logs to see reload happen:**
```bash
docker-compose logs -f foundry-backend
# You'll see: "Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)"
# On file change: "Detected file change, reloading..."
```

### View Logs

```bash
# Follow specific service
docker-compose logs -f foundry-backend

# Last 50 lines
docker-compose logs --tail=50 agent-foundry-ui

# All services
docker-compose logs -f

# Multiple services
docker-compose logs -f foundry-backend voice-agent-worker
```

---

## When You DO Need Actions

### Restart Single Service (Config Change, Not Code)

```bash
# Example: Changed .env file
docker-compose restart foundry-backend

# Or restart multiple
docker-compose restart foundry-backend voice-agent-worker
```

### Rebuild (Dependency or Dockerfile Change Only)

```bash
# Changed requirements.txt?
docker-compose build foundry-backend
docker-compose up -d foundry-backend

# Changed package.json?
docker-compose build agent-foundry-ui  
docker-compose up -d agent-foundry-ui

# Changed Dockerfile?
docker-compose build foundry-backend
docker-compose up -d foundry-backend

# Changed docker-compose.yml?
docker-compose up -d  # Recreates changed services
```

### Full Rebuild (Rare)

```bash
# Nuclear option - only if something is broken
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Troubleshooting

### "My changes aren't showing up!"

**Check if hot reload is working:**
```bash
# Look for reload messages
docker-compose logs -f foundry-backend

# Force restart the specific service
docker-compose restart foundry-backend

# If that doesn't work, check if file is mounted:
docker-compose exec foundry-backend ls -la backend/main.py
```

### "Container won't start after code change"

**You probably have a syntax error:**
```bash
# Check the logs
docker-compose logs foundry-backend

# Fix the syntax error
# Container will auto-restart when you save the fix
```

### "Backend still running old code"

**Possible causes:**
1. You're editing the wrong file (check path)
2. File isn't mounted (check docker-compose.yml volumes)
3. Service needs explicit restart:
   ```bash
   docker-compose restart foundry-backend
   ```

### "Frontend not hot-reloading"

**Next.js sometimes needs explicit permission:**
```bash
# Add to .env.local if needed
WATCHPACK_POLLING=true

# Then restart frontend
docker-compose restart agent-foundry-ui
```

---

## Service-Specific Notes

### Backend (FastAPI + uvicorn)
- **Auto-reload:** ✅ Enabled via `--reload` flag
- **Watch dirs:** `backend/`, `agent/`, `mcp/`
- **Restart time:** ~2-3 seconds

### Frontend (Next.js)
- **Auto-reload:** ✅ Built into `npm run dev`
- **Watch dirs:** `app/`, `components/`, `lib/`, etc.
- **Restart time:** Instant (Fast Refresh)

### Compiler (FastAPI)
- **Auto-reload:** ⚠️ Not in base docker-compose.yml
- **Fix:** Use `docker-compose.dev.yml` for auto-reload
- **Or:** Manually restart when needed

### Voice Agent Worker
- **Auto-reload:** ⚠️ Not enabled (runs via `start` command)
- **Restart:** Manual via `docker-compose restart voice-agent-worker`
- **Consider:** Adding `--reload` if you're actively developing it

---

## Performance Tips

### Faster Startup

```bash
# Only start what you need
docker-compose up -d livekit redis foundry-backend

# Skip building if images exist
docker-compose up -d --no-build
```

### Faster Rebuilds (When Needed)

```bash
# Use build cache
docker-compose build

# Skip cache if something weird
docker-compose build --no-cache foundry-backend

# Parallel builds
docker-compose build --parallel
```

### Check What's Running

```bash
# Service status
docker-compose ps

# Resource usage
docker stats

# Service health
docker-compose ps | grep healthy
```

---

## Summary

**99% of the time:**
```bash
# Start once
docker-compose up -d

# Edit files, save
# Changes auto-reload

# View logs if needed
docker-compose logs -f foundry-backend
```

**1% of the time (dependencies changed):**
```bash
docker-compose build foundry-backend
docker-compose up -d foundry-backend
```

**Never:**
```bash
# ❌ Don't do this on every code change!
docker-compose down
docker-compose build  
docker-compose up -d
```

---

## Created: 2025-11-16
## Version: 0.8.0-dev
