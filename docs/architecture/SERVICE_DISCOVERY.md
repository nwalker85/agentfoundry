# Service Discovery & Port Management

## Overview

Agent Foundry uses the **Infrastructure as Registry** pattern for service
discovery. This eliminates the need for complex port configuration and makes the
system portable between Docker Compose and Kubernetes.

## Philosophy

### Before: Port Configuration Hell ❌

```yaml
# .env file with 28+ port variables
BACKEND_PORT=8000 BACKEND_WS_PORT=8001 COMPILER_PORT=8002 FORGE_PORT=8003
LIVEKIT_HTTP_PORT=7880 REDIS_PORT=6379
---
# Services referencing each other with variable ports
environment:
  - BACKEND_URL=http://foundry-backend:${BACKEND_PORT:-8000}
  - MCP_URL=http://mcp-integration:${MCP_PORT:-8100}
```

**Problems:**

- Hardcoded port numbers scattered across codebase
- Inter-service URLs require port configuration
- Difficult to track which service is on which port
- Doesn't scale to Kubernetes (requires code changes)

### After: Infrastructure as Registry ✅

```yaml
# Clean, simple configuration
environment:
  # Services use DNS names, no port variables
  - SVC_BACKEND_HOST=foundry-backend
  - SVC_COMPILER_HOST=foundry-compiler
  - SVC_LIVEKIT_HOST=livekit
# All internal services listen on standard port 8080
# Infrastructure handles routing via DNS
```

**Benefits:**

- **Zero Config**: No port variables for inter-service communication
- **Consistency**: All services use port 8080 (except infrastructure)
- **Portability**: Works in Docker Compose AND Kubernetes without code changes
- **Observability**: Clear service names in traces (e.g., `foundry-backend` →
  `mcp-integration`)

## Architecture

### Port Standards

| Service Type                | Internal Port | External Port (Dev) | Notes                              |
| --------------------------- | ------------- | ------------------- | ---------------------------------- |
| **Application Services**    | **8080**      | **Variable**        | Backend, Compiler, MCP Integration |
| **Infrastructure Services** |               |                     | Standard ports maintained          |
| - LiveKit                   | 7880          | 7880                | Voice/RTC server                   |
| - Redis                     | 6379          | 6379                | Cache/state store                  |
| - PostgreSQL                | 5432          | 5432                | Control plane DB                   |
| - n8n                       | 5678          | 5678                | Workflow automation                |
| - LocalStack                | 4566          | 4566                | AWS emulation (Secrets)            |
| - OpenFGA                   | 8081          | 8081                | Authorization (ReBAC)              |
| **Observability Services**  |               |                     |                                    |
| - Prometheus                | 9090          | 9090                | Metrics collection                 |
| - Grafana                   | 3000          | 3001                | Dashboards                         |
| - Tempo                     | 4318/3200     | 4318/3200           | Tracing (OTLP/Query)               |

### Service Communication Patterns

#### 1. Backend Service Discovery (Python)

**Configuration File:** `backend/config/services.py`

```python
from backend.config.services import SERVICES

# Internal service-to-service call
url = f"http://{SERVICES.COMPILER}:{SERVICES.PORT}/api/compile"
# Resolves to: http://foundry-compiler:8080/api/compile

# Or use helper
url = SERVICES.get_service_url("MCP_INTEGRATION")
# Returns: http://mcp-integration:8080
```

**Available Services:**

- `SERVICES.BACKEND` → foundry-backend:8080
- `SERVICES.COMPILER` → foundry-compiler:8080
- `SERVICES.MCP_INTEGRATION` → mcp-integration:8080
- `SERVICES.N8N` → n8n:5678
- `SERVICES.REDIS` → redis:6379
- `SERVICES.POSTGRES` → postgres:5432
- `SERVICES.LIVEKIT` → livekit:7880
- `SERVICES.LOCALSTACK` → localstack:4566
- `SERVICES.OPENFGA` → openfga:8081
- `SERVICES.PROMETHEUS` → prometheus:9090
- `SERVICES.GRAFANA` → grafana:3000
- `SERVICES.TEMPO` → tempo:4318 (OTLP endpoint)

#### 2. Frontend Service Discovery (TypeScript)

**Configuration File:** `app/lib/config/services.ts`

```typescript
import { getServiceUrl, buildServiceUrl, API } from '@/lib/config/services';

// Automatically uses correct URL based on context
// Client-side: http://localhost:8000
// Server-side: http://foundry-backend:8080
const url = getServiceUrl('backend');

// Build complete URL with query params
const url = buildServiceUrl('backend', '/api/agents', { status: 'active' });

// Use pre-built helpers
const agentsUrl = API.backend.agents();
const wsUrl = API.websocket.events();
```

**Context-Aware URLs:**

| Context                         | Backend URL                   | Usage                             |
| ------------------------------- | ----------------------------- | --------------------------------- |
| Browser (client-side)           | `http://localhost:8000`       | API calls from user's browser     |
| Next.js Server (SSR/API routes) | `http://foundry-backend:8080` | Server-side rendering, API routes |

### Docker Compose Configuration

#### Application Service Example

```yaml
foundry-backend:
  ports:
    - '${BACKEND_PORT:-8000}:8080' # External:Internal mapping
  environment:
    # Service always listens on 8080
    - PORT=8080

    # Service discovery - DNS names only, no port config
    - SVC_LIVEKIT_HOST=livekit
    - SVC_REDIS_HOST=redis
    - SVC_MCP_HOST=mcp-integration

    # Infrastructure ports (non-standard)
    - LIVEKIT_HTTP_PORT=7880
    - REDIS_PORT=6379
```

**Key Points:**

1. **Internal Port**: Always 8080 for application services
2. **External Mapping**: `${EXTERNAL_PORT}:8080` for localhost development
3. **DNS Names**: Use service names (e.g., `foundry-backend`, not `localhost`)
4. **No Port Variables**: Inter-service URLs don't include port variables

#### Frontend Service Example

```yaml
agent-foundry-ui:
  ports:
    - '3000:3000' # Next.js standard port
  environment:
    # Public URLs - For browser access (localhost in dev)
    - NEXT_PUBLIC_API_URL=http://localhost:8000
    - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    - NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880

    # Internal URLs - For Next.js server-side code
    - BACKEND_URL=http://foundry-backend:8080
    - SVC_COMPILER_URL=http://foundry-compiler:8080
```

## Migration Guide

### Updating Existing Code

#### Python/Backend Services

**Before:**

```python
backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
response = await fetch(f"{backend_url}/api/agents")
```

**After:**

```python
from backend.config.services import SERVICES

backend_url = SERVICES.get_service_url("BACKEND")
response = await fetch(f"{backend_url}/api/agents")
```

#### TypeScript/Frontend

**Before:**

```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const response = await fetch(`${apiUrl}/api/agents`);
```

**After:**

```typescript
import { getServiceUrl } from '@/lib/config/services';

const apiUrl = getServiceUrl('backend');
const response = await fetch(`${apiUrl}/api/agents`);
```

### Updating Environment Variables

**Remove these from `.env`:**

```bash
# ❌ OLD - Delete these
BACKEND_URL=http://foundry-backend:8000
MCP_INTEGRATION_URL=http://mcp-integration:8100
COMPILER_URL=http://foundry-compiler:8002
```

**Replace with (if customization needed):**

```bash
# ✅ NEW - Only if overriding defaults
SVC_BACKEND_HOST=foundry-backend
SVC_MCP_HOST=mcp-integration
SVC_COMPILER_HOST=foundry-compiler
```

## Production Deployment (Kubernetes)

### Zero Code Changes Required

The same service names work in Kubernetes via Service discovery:

```yaml
# Kubernetes Service (k8s/backend-service.yaml)
apiVersion: v1
kind: Service
metadata:
  name: foundry-backend # ← Matches SERVICES.BACKEND
spec:
  selector:
    app: backend
  ports:
    - protocol: TCP
      port: 8080 # Internal cluster port
      targetPort: 8080 # Container port
```

**Application code remains identical:**

```python
# Works in both Docker Compose AND Kubernetes
url = SERVICES.get_service_url("BACKEND")
# Resolves to: http://foundry-backend:8080
```

## Observability Benefits

### Consistent Service Naming

Using standardized service names provides clear distributed tracing:

```
🔍 Trace: User Request → foundry-backend:8080
  ↳ foundry-backend calls mcp-integration:8080
    ↳ mcp-integration calls n8n:5678
      ↳ n8n webhook → external API
```

**OpenTelemetry Integration:**

```python
from backend.config.services import get_otel_service_name

# Service name automatically matches DNS name
service_name = get_otel_service_name()  # "foundry-backend"
```

### Prometheus Metrics

Service names are consistent across metrics:

```promql
# HTTP request rate by service
rate(http_requests_total{service="foundry-backend"}[5m])

# Service-to-service call duration
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{
    source="foundry-backend",
    target="mcp-integration"
  }[5m])
)
```

## Troubleshooting

### Service Not Found

**Error:** `Could not connect to foundry-backend:8080`

**Solution:**

1. Verify service is running: `docker ps | grep foundry-backend`
2. Check service name in docker-compose.yml matches SERVICES config
3. Ensure services are on same Docker network

### Port Already in Use

**Error:** `port 8000 is already allocated`

**Solution:**

```bash
# Change EXTERNAL port only (internal stays 8080)
export BACKEND_PORT=8001
docker-compose up
```

### Wrong Port in Logs

**Error:** Service logs show `Starting on port 8000` but expects 8080

**Solution:**

```yaml
# Ensure environment variable is set correctly
environment:
  - PORT=8080 # Not ${BACKEND_PORT}
```

## Best Practices

### ✅ DO

- Use `SERVICES.get_service_url()` for all inter-service calls
- Keep internal port at 8080 for new services
- Use DNS service names in configuration
- Override with env vars only when necessary
- Document non-standard ports clearly

### ❌ DON'T

- Hardcode `localhost:8000` in application code
- Create new `*_PORT` environment variables
- Reference services by IP address
- Mix port variables with DNS names
- Use different ports for each service arbitrarily

## Summary

### Key Takeaways

1. **All internal services use port 8080** (except infrastructure)
2. **Service names are DNS-resolvable** (e.g., `foundry-backend`)
3. **No port configuration in inter-service calls**
4. **Works in Docker Compose AND Kubernetes** without code changes
5. **Centralized configuration** via `SERVICES` singleton

### Configuration Hierarchy

```
Infrastructure (Docker/K8s)
  ↓
Service Discovery (DNS)
  ↓
Application Config (SERVICES)
  ↓
Application Code
```

This architecture ensures your services are:

- **Portable** between environments
- **Observable** with consistent naming
- **Maintainable** with centralized configuration
- **Scalable** to Kubernetes without refactoring
