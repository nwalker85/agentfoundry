# Service Discovery Quick Reference

## Quick Start

### Python/Backend

```python
from backend.config.services import SERVICES

# Get service URL
url = SERVICES.get_service_url("BACKEND")  # http://foundry-backend:8080

# Call another service
response = await httpx.get(f"{url}/api/health")
```

### TypeScript/Frontend

```typescript
import { getServiceUrl, buildServiceUrl, API } from '@/lib/config/services';

// Auto context-aware (client vs server)
const url = getServiceUrl('backend');

// With query params
const url = buildServiceUrl('backend', '/api/agents', { status: 'active' });

// Pre-built helpers
const agentsUrl = API.backend.agents();
```

## Service Names

### Application Services (port 8080)

| Service         | DNS Name           | Port | Usage        |
| --------------- | ------------------ | ---- | ------------ |
| Backend         | `foundry-backend`  | 8080 | Main API     |
| Compiler        | `foundry-compiler` | 8080 | DIS → YAML   |
| MCP Integration | `mcp-integration`  | 8080 | Tool gateway |

### Infrastructure Services

| Service    | DNS Name     | Port | Usage                   |
| ---------- | ------------ | ---- | ----------------------- |
| LiveKit    | `livekit`    | 7880 | Voice/RTC               |
| Redis      | `redis`      | 6379 | Cache/state             |
| PostgreSQL | `postgres`   | 5432 | Database                |
| n8n        | `n8n`        | 5678 | Workflows               |
| LocalStack | `localstack` | 4566 | AWS emulation (Secrets) |
| OpenFGA    | `openfga`    | 8081 | Authorization (ReBAC)   |

### Observability Services

| Service    | DNS Name     | Port      | Usage                            |
| ---------- | ------------ | --------- | -------------------------------- |
| Prometheus | `prometheus` | 9090      | Metrics collection               |
| Grafana    | `grafana`    | 3000      | Dashboards                       |
| Tempo      | `tempo`      | 4318/3200 | Distributed tracing (OTLP/Query) |

## Common Patterns

### Backend to Backend

```python
from backend.config.services import SERVICES

# Call compiler from backend
compiler_url = SERVICES.get_service_url("COMPILER")
response = await client.post(f"{compiler_url}/api/compile", json=payload)
```

### Frontend to Backend (Browser)

```typescript
import { getServiceUrl } from '@/lib/config/services';

// Automatically uses http://localhost:8000 in browser
const response = await fetch(`${getServiceUrl('backend')}/api/agents`);
```

### Frontend to Backend (Server-Side)

```typescript
// In Next.js API route or server component
import { getServiceUrl } from '@/lib/config/services';

// Automatically uses http://foundry-backend:8080 server-side
const response = await fetch(`${getServiceUrl('backend')}/api/agents`);
```

### WebSocket Connection

```typescript
import { API } from '@/lib/config/services';

const ws = new WebSocket(API.websocket.events());
```

## Environment Variables

### Required (External Access)

```bash
# For localhost development - maps external → internal
BACKEND_PORT=8000        # localhost:8000 → foundry-backend:8080
COMPILER_PORT=8002       # localhost:8002 → foundry-compiler:8080
FRONTEND_PORT=3000       # localhost:3000 (frontend)
```

### Optional (Service Overrides)

```bash
# Only set these to override default DNS names
SVC_BACKEND_HOST=foundry-backend
SVC_COMPILER_HOST=foundry-compiler
SVC_LIVEKIT_HOST=livekit
```

## Troubleshooting

### Service Not Found

```bash
# Check service is running
docker-compose ps | grep foundry-backend

# Test connectivity
docker-compose exec foundry-backend curl http://foundry-compiler:8080/health
```

### Wrong URL

```bash
# Python: Check what SERVICES resolves to
docker-compose exec foundry-backend python -c "
from backend.config.services import SERVICES
print(SERVICES.get_service_url('COMPILER'))
"
```

### Port Conflict

```bash
# Change EXTERNAL port only (internal stays 8080)
export BACKEND_PORT=8001
docker-compose up -d
```

## Migration Checklist

- [ ] Remove old `*_URL` env vars from .env
- [ ] Update code to use `SERVICES` config
- [ ] Rebuild: `docker-compose build`
- [ ] Restart: `docker-compose up -d`
- [ ] Test: `curl localhost:8000/health`

## Full Documentation

- **Architecture:** [SERVICE_DISCOVERY.md](./architecture/SERVICE_DISCOVERY.md)
- **Migration:**
  [MIGRATION_SERVICE_DISCOVERY.md](./MIGRATION_SERVICE_DISCOVERY.md)
- **Summary:**
  [SERVICE_DISCOVERY_IMPLEMENTATION_SUMMARY.md](./SERVICE_DISCOVERY_IMPLEMENTATION_SUMMARY.md)
