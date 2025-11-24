# Migration Guide: Infrastructure as Registry

## Overview

This guide walks you through migrating from the old port-heavy configuration to
the new Infrastructure as Registry pattern.

**Time Required:** ~15 minutes  
**Risk Level:** Low (backwards compatible)  
**Recommended:** Test in development first

## What's Changing

### Before (Old Pattern)

```yaml
# .env - 28+ port/URL variables
BACKEND_PORT=8000 BACKEND_WS_PORT=8001 BACKEND_URL=http://foundry-backend:8000
BACKEND_API_URL=http://foundry-backend:8000
MCP_INTEGRATION_URL=http://mcp-integration:8100
---
# Code - Hardcoded URLs everywhere
backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000") api_url =
process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

### After (New Pattern)

```yaml
# .env - Clean, minimal configuration
BACKEND_PORT=8000  # External access only

# Code - Centralized service discovery
from backend.config.services import SERVICES
url = SERVICES.get_service_url("BACKEND")  # http://foundry-backend:8080
```

## Migration Steps

### Step 1: Update Your Environment Files (5 min)

#### 1.1 Backup Current .env

```bash
cp .env .env.backup
```

#### 1.2 Remove Deprecated Variables

Delete these from your `.env`:

```bash
# ❌ Remove these lines
BACKEND_URL=...
BACKEND_WS_PORT=...
BACKEND_API_URL=...
MCP_BASE_URL=...
MCP_INTEGRATION_URL=...
COMPILER_URL=...
LIVEKIT_URL=...
N8N_BASE_URL=...
```

#### 1.3 Update Port Variables (Optional)

The following are now ONLY for external localhost access:

```bash
# ✅ Keep these (they map external → internal ports)
FRONTEND_PORT=3000
BACKEND_PORT=8000
COMPILER_PORT=8002
LIVEKIT_HTTP_PORT=7880
```

#### 1.4 Copy New Template

```bash
# Use the new .env.example as reference
cp .env.example .env.new
# Merge your API keys into .env.new
```

### Step 2: Verify Docker Compose (2 min)

No action needed! The updated `docker-compose.yml` already uses the new pattern.

**Verify it looks like this:**

```yaml
foundry-backend:
  ports:
    - '${BACKEND_PORT:-8000}:8080' # External:Internal
  environment:
    - PORT=8080 # Internal listening port
    - SVC_LIVEKIT_HOST=livekit # DNS service name
```

### Step 3: Test the Migration (5 min)

#### 3.1 Rebuild Services

```bash
# Rebuild with new configuration
docker-compose down
docker-compose build
docker-compose up -d
```

#### 3.2 Verify Services Started

```bash
# Check all services are healthy
docker-compose ps

# Expected output:
# NAME                  STATUS
# foundry-backend       healthy
# foundry-compiler      running
# agent-foundry-ui      running
# livekit              running
# redis                healthy
```

#### 3.3 Test Inter-Service Communication

```bash
# Test backend can reach compiler
docker-compose exec foundry-backend curl http://foundry-compiler:8080/health

# Should return: {"service":"agent-foundry-compiler","status":"operational",...}
```

#### 3.4 Test External Access

```bash
# Test localhost access still works
curl http://localhost:8000/health

# Open browser
open http://localhost:3000
```

### Step 4: Update Custom Code (If Any)

#### Python/Backend Services

**If you have custom services using the old pattern:**

```python
# ❌ OLD
backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# ✅ NEW
from backend.config.services import SERVICES
backend_url = SERVICES.get_service_url("BACKEND")
```

#### TypeScript/Frontend

**If you have custom components:**

```typescript
// ❌ OLD
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ✅ NEW
import { getServiceUrl } from '@/lib/config/services';
const apiUrl = getServiceUrl('backend');
```

## Verification Checklist

### ✅ Basic Checks

- [ ] All services start without errors (`docker-compose ps`)
- [ ] Backend health check passes (`curl localhost:8000/health`)
- [ ] Frontend loads in browser (`http://localhost:3000`)
- [ ] No DNS resolution errors in logs (`docker-compose logs`)

### ✅ Integration Checks

- [ ] Backend can call MCP integration
- [ ] Backend can call n8n
- [ ] Voice worker can connect to LiveKit
- [ ] Frontend can fetch agents list
- [ ] WebSocket connections work

### ✅ Development Workflow

- [ ] Hot reload still works for backend
- [ ] Hot reload still works for frontend
- [ ] New agents are discovered automatically
- [ ] Logs are visible and formatted correctly

## Rollback Procedure

If you encounter issues:

### Quick Rollback

```bash
# Stop services
docker-compose down

# Restore old environment
cp .env.backup .env

# Restore old docker-compose (if modified)
git checkout docker-compose.yml

# Restart with old config
docker-compose up -d
```

### Incremental Rollback

```bash
# Keep new docker-compose, just add back old env vars
echo "BACKEND_API_URL=http://foundry-backend:8000" >> .env
echo "MCP_INTEGRATION_URL=http://mcp-integration:8100" >> .env

# Restart
docker-compose restart
```

## Common Issues & Solutions

### Issue: Service Not Found

**Error:** `Could not connect to foundry-backend:8080`

**Solution:**

```bash
# Check service name matches docker-compose.yml
docker-compose config | grep -A5 foundry-backend

# Verify service is on correct network
docker network inspect agentfoundry_foundry
```

### Issue: Port Already in Use

**Error:** `port 8000 is already allocated`

**Solution:**

```bash
# Change external port only
export BACKEND_PORT=8001
docker-compose up -d

# Or kill process using port
lsof -ti:8000 | xargs kill -9
```

### Issue: Old Environment Variables Still Referenced

**Error:** `BACKEND_URL is deprecated`

**Solution:**

```bash
# Find where old vars are still used
grep -r "BACKEND_URL" backend/
grep -r "BACKEND_API_URL" backend/

# Update to use SERVICES config
# See Step 4 above
```

### Issue: Frontend Can't Connect

**Error:** `Failed to fetch http://undefined/api/agents`

**Solution:**

```bash
# Verify NEXT_PUBLIC_API_URL is set for browser
echo $NEXT_PUBLIC_API_URL  # Should be http://localhost:8000

# Or check docker-compose environment
docker-compose config | grep NEXT_PUBLIC
```

## Benefits Verification

After successful migration, you should notice:

1. **Cleaner Configuration**

   - `.env` file is 50% smaller
   - No duplicate port variables
   - Clear separation: external vs internal

2. **Easier Development**

   - Add new services without port coordination
   - No port conflicts between services
   - Clear error messages with service names

3. **Better Observability**

   - Service names in logs: `foundry-backend` instead of `localhost:8000`
   - Distributed traces show clear service flow
   - Prometheus metrics use consistent service labels

4. **Production Ready**
   - Same configuration works in Kubernetes
   - No code changes needed for deployment
   - Infrastructure handles all routing

## Next Steps

### 1. Update Team Documentation

```bash
# Share the new pattern with your team
cat docs/architecture/SERVICE_DISCOVERY.md

# Update your team wiki/notion with migration guide
```

### 2. Clean Up Old References

```bash
# Find remaining old patterns in codebase
grep -r "process.env.NEXT_PUBLIC_API_URL" app/
grep -r "os.getenv.*URL" backend/

# Update or document these occurrences
```

### 3. Test Production-Like Environment

```bash
# Test with Kubernetes locally (optional)
kind create cluster
kubectl apply -f k8s/

# Verify services discover each other
kubectl logs foundry-backend | grep "http://foundry-compiler:8080"
```

### 4. Enable Observability

```bash
# Verify consistent service naming in traces
curl localhost:16686  # Jaeger UI
# Look for spans with service.name = "foundry-backend"

# Check Prometheus metrics
curl localhost:9090  # Prometheus UI
# Query: rate(http_requests_total{service="foundry-backend"}[5m])
```

## Support

### Documentation

- [Service Discovery Architecture](./architecture/SERVICE_DISCOVERY.md)
- [Docker Compose Reference](../docker-compose.yml)
- [Environment Variables](./.env.example)

### Troubleshooting

1. Check logs: `docker-compose logs -f [service-name]`
2. Verify network: `docker network inspect agentfoundry_foundry`
3. Test connectivity: `docker-compose exec [service] curl http://[target]:8080`

### Questions?

Open an issue with:

- Error messages from `docker-compose logs`
- Output of `docker-compose ps`
- Your `.env` configuration (redacted)
- Steps to reproduce the issue

## Summary

**What Changed:**

- ❌ Removed 20+ port/URL environment variables
- ✅ Added centralized service configuration
- ✅ Standardized internal port to 8080
- ✅ Use DNS for service discovery

**What Stayed the Same:**

- External localhost access (http://localhost:8000)
- Development workflow (hot reload, logs)
- API routes and contracts
- Database connections

**Migration Time:**

- Small projects: ~15 minutes
- Large projects: ~30 minutes (more custom code)

**Risk Level:** ✅ Low

- Backwards compatible during transition
- Easy rollback procedure
- No database migrations required
- No breaking API changes

🎉 **You're done!** Your services now use Infrastructure as Registry for clean,
portable, observable service discovery.
