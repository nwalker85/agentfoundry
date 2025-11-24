# OpenFGA Quick Start Guide

## What is OpenFGA?

**OpenFGA** (Open Fine-Grained Authorization) is an open-source implementation
of Google's Zanzibar authorization system. It provides relationship-based access
control (ReBAC) that naturally models hierarchical permissions.

### Why We're Using It

**Traditional RBAC:**

```
User → Role → Permissions (flat)
```

- ❌ Can't model "User A owns Agent X"
- ❌ Hard to delegate access
- ❌ Complex hierarchical queries

**OpenFGA (ReBAC):**

```
User → Relationship → Resource (graph)
```

- ✅ Models real-world relationships
- ✅ Easy delegation ("share this agent with Bob")
- ✅ Hierarchical: org → domain → agent
- ✅ Scalable (Google Zanzibar proven at billions of checks/sec)

## 10-Minute Setup

### Step 1: Start OpenFGA

```bash
# Start all services (includes OpenFGA)
docker-compose up -d

# Verify OpenFGA is running
curl http://localhost:8081/healthz
```

### Step 2: Initialize Store & Model

```bash
# Run initialization script
python scripts/openfga_init.py

# Output will show:
# ✓ Store created: 01HXXX...
# ✓ Authorization model loaded: 01HYYY...
#
# Add these to your .env:
# OPENFGA_STORE_ID=01HXXX...
# OPENFGA_AUTH_MODEL_ID=01HYYY...
```

### Step 3: Add to .env

```bash
# Add these lines to .env
OPENFGA_STORE_ID=01HXXX...  # From step 2
OPENFGA_AUTH_MODEL_ID=01HYYY...  # From step 2
```

### Step 4: Restart Backend

```bash
# Apply new configuration
docker-compose restart foundry-backend

# Verify it's working
curl -H "Authorization: Bearer YOUR_JWT" \
  http://localhost:8000/api/openfga-examples/agents
```

## Usage Patterns

### Pattern 1: Check Permission

```python
from backend.middleware.openfga_middleware import get_current_user, AuthContext

@app.get("/api/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    context: AuthContext = Depends(get_current_user)
):
    # Manual check
    if not await context.can("can_read", f"agent:{agent_id}"):
        raise HTTPException(403, "Cannot read this agent")

    # Fetch and return agent...
```

### Pattern 2: List Accessible Resources

```python
@app.get("/api/agents")
async def list_agents(
    context: AuthContext = Depends(get_current_user)
):
    # Get agents user can execute
    agent_ids = await context.list_accessible("agent", "can_execute")

    # Fetch from database
    agents = db.get_agents(agent_ids)
    return {"agents": agents}
```

### Pattern 3: Create Resource (Set Owner)

```python
from backend.openfga_client import fga_client

@app.post("/api/agents")
async def create_agent(
    agent_data: AgentCreate,
    context: AuthContext = Depends(get_current_user)
):
    # Create agent in database
    agent_id = db.create_agent(agent_data)

    # Set up relationships in OpenFGA
    await fga_client.write([
        # Link to domain
        {
            "user": f"domain:{agent_data.domain_id}",
            "relation": "parent_domain",
            "object": f"agent:{agent_id}"
        },
        # Set owner
        {
            "user": context.get_fga_user(),
            "relation": "owner",
            "object": f"agent:{agent_id}"
        }
    ])

    return {"id": agent_id}
```

### Pattern 4: Share Resource

```python
@app.post("/api/agents/{agent_id}/share")
async def share_agent(
    agent_id: str,
    target_user_id: str,
    context: AuthContext = Depends(get_current_user)
):
    # Check if user can share
    if not await context.can("can_share", f"agent:{agent_id}"):
        raise HTTPException(403, "Cannot share this agent")

    # Grant viewer access
    await fga_client.grant_access(
        user_id=target_user_id,
        resource_type="agent",
        resource_id=agent_id,
        relation="viewer"
    )

    return {"status": "shared"}
```

## Authorization Model

### Entity Hierarchy

```
Organization (tenant)
  ↓ owns
Domain (business unit)
  ↓ owns
Agent (executable)
```

### Relationships

| Entity           | Relations                                      | Computed Permissions                                     |
| ---------------- | ---------------------------------------------- | -------------------------------------------------------- |
| **Organization** | owner, admin, member, viewer                   | can_create_domain, can_manage_secrets                    |
| **Domain**       | parent_org, owner, editor, viewer              | can_create_agent, can_read                               |
| **Agent**        | parent_domain, owner, executor, editor, viewer | can_execute, can_read, can_update, can_delete, can_share |
| **Secret**       | parent_org, owner, viewer                      | can_read_status, can_update, can_delete                  |

### Permission Inheritance

```
User: alice
  ↓ admin of
Organization: acme-corp
  ↓ parent_org of
Domain: card-services
  ↓ parent_domain of
Agent: cibc-activation
  ↓ alice can:
     - can_create_agent (via org admin)
     - can_execute (via domain inheritance)
     - can_update (via domain inheritance)
```

## Common Operations

### Check Permission

```bash
curl -X POST http://localhost:8081/stores/${STORE_ID}/check \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_model_id": "'${MODEL_ID}'",
    "tuple_key": {
      "user": "user:alice",
      "relation": "can_execute",
      "object": "agent:my-agent"
    }
  }'
```

### Grant Access

```bash
curl -X POST http://localhost:8081/stores/${STORE_ID}/write \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_model_id": "'${MODEL_ID}'",
    "writes": {
      "tuple_keys": [{
        "user": "user:bob",
        "relation": "viewer",
        "object": "agent:my-agent"
      }]
    }
  }'
```

### List Accessible Resources

```bash
curl -X POST http://localhost:8081/stores/${STORE_ID}/list-objects \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_model_id": "'${MODEL_ID}'",
    "user": "user:alice",
    "relation": "can_execute",
    "type": "agent"
  }'
```

## Migration from RBAC

### Step 1: Run Migration Script

```bash
# Make sure OpenFGA is initialized first
python scripts/openfga_init.py

# Then migrate existing RBAC data
python scripts/rbac_to_openfga_migration.py
```

### Step 2: Update Route Dependencies

**Before (RBAC):**

```python
from backend.rbac_middleware import RequirePermission

@app.get("/api/agents")
async def list_agents(
    context: RequestContext = Depends(RequirePermission("agent:read:org"))
):
    ...
```

**After (OpenFGA):**

```python
from backend.middleware.openfga_middleware import get_current_user, AuthContext

@app.get("/api/agents")
async def list_agents(
    context: AuthContext = Depends(get_current_user)
):
    # List agents user can access
    agent_ids = await context.list_accessible("agent", "can_execute")
    ...
```

### Step 3: Test Authorization

```bash
# Create test JWT token
python -c "
import jwt
token = jwt.encode({
    'sub': 'test-user',
    'org_id': 'test-org',
    'email': 'test@example.com'
}, 'your-secret-key', algorithm='HS256')
print(token)
"

# Use token to test
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/openfga-examples/agents
```

## Environment Variables

```bash
# OpenFGA Configuration
OPENFGA_STORE_ID=01HXXX...          # From openfga_init.py
OPENFGA_AUTH_MODEL_ID=01HYYY...     # From openfga_init.py
OPENFGA_HTTP_PORT=8081              # Default HTTP API port
OPENFGA_GRPC_PORT=8080              # Default gRPC port

# Service Discovery (automatic)
SVC_OPENFGA_HOST=openfga            # DNS name in Docker

# JWT Authentication
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
```

## Troubleshooting

### OpenFGA Not Starting

```bash
docker-compose logs openfga
docker-compose ps openfga
docker-compose restart openfga
```

### Store/Model Not Created

```bash
# Check OpenFGA is reachable
curl http://localhost:8081/healthz

# List stores
curl http://localhost:8081/stores

# Re-run initialization
python scripts/openfga_init.py
```

### Authorization Always Fails

```bash
# Verify relationship exists
curl -X POST http://localhost:8081/stores/${STORE_ID}/read \
  -H "Content-Type: application/json" \
  -d '{
    "authorization_model_id": "'${MODEL_ID}'",
    "tuple_key": {
      "user": "user:alice",
      "object": "agent:my-agent"
    }
  }'
```

### Performance Issues

```bash
# Enable caching (already enabled by default)
OPENFGA_CACHE_TTL=60  # seconds

# Check OpenFGA logs for slow queries
docker-compose logs openfga | grep -i "slow"
```

## Next Steps

1. **Migrate Routes**: Update all routes to use OpenFGA middleware
2. **Create Relationships**: Set up org/domain/agent relationships
3. **Test Access**: Verify permissions work correctly
4. **Monitor**: Watch OpenFGA logs and metrics
5. **Optimize**: Add caching, batch checks

## Resources

- **OpenFGA Docs**: https://openfga.dev/docs
- **Zanzibar Paper**: https://research.google/pubs/pub48190/
- **Authorization Model**: `/openfga/authorization_model.fga`
- **Example Routes**: `/backend/routes/openfga_example_routes.py`
- **Architecture**: `/docs/OPENFGA_ARCHITECTURE.md`

---

**Status:** ✅ Ready for Development  
**Migration:** Use `rbac_to_openfga_migration.py`  
**Pattern:** Relationship-Based Access Control (ReBAC)
