# OpenFGA Architecture for Agent Foundry

## Overview

Agent Foundry uses **OpenFGA** (Open Fine-Grained Authorization) for
relationship-based access control. This provides flexible, scalable
authorization that models the natural hierarchy of organizations, domains, and
agents.

## Why OpenFGA?

### Traditional RBAC Problems

```
User → Role → Permissions
```

- ❌ Can't model resource ownership
- ❌ Hard to delegate access ("share this agent with User X")
- ❌ Complex hierarchical checks (org → domain → agent)
- ❌ Difficult to scale

### OpenFGA Solution (ReBAC)

```
User → Relationship → Resource
```

- ✅ Models real-world relationships
- ✅ Natural delegation ("user X is viewer of agent Y")
- ✅ Hierarchical permissions via relationships
- ✅ Billions of checks/sec (Google Zanzibar)

## Authorization Model

### Entity Hierarchy

```
Platform
  ├─ Organization (multi-tenant)
  │   ├─ Domain (business unit)
  │   │   ├─ Agent (executable)
  │   │   ├─ Secret (API keys)
  │   │   └─ Session (runtime)
  │   └─ Team (group of users)
  └─ User
```

### OpenFGA Type Definitions

```typescript
// authorization_model.fga
model
  schema 1.1

// ============================================================================
// CORE TYPES
// ============================================================================

type user

type organization
  relations
    define owner: [user]
    define admin: [user, organization#member]
    define member: [user, team#member]
    define viewer: [user, team#member]

    // Computed permissions
    define can_create_domain: owner or admin
    define can_read: viewer or member or admin or owner
    define can_update: admin or owner
    define can_delete: owner
    define can_manage_users: admin or owner

type team
  relations
    define parent_org: [organization]
    define owner: [user]
    define member: [user, team#member]

    // Inherit org permissions
    define can_read: member or owner or parent_org->admin

type domain
  relations
    define parent_org: [organization]
    define owner: [user]
    define editor: [user, team#member]
    define viewer: [user, team#member]

    // Computed permissions
    define can_create_agent: owner or editor or parent_org->admin
    define can_read: viewer or editor or owner or parent_org->member
    define can_update: editor or owner or parent_org->admin
    define can_delete: owner or parent_org->owner

type agent
  relations
    define parent_domain: [domain]
    define owner: [user]
    define executor: [user, team#member]
    define editor: [user, team#member]
    define viewer: [user, team#member]

    // Computed permissions (inherit from domain)
    define can_execute: executor or editor or owner or parent_domain->editor
    define can_read: viewer or executor or editor or owner or parent_domain->viewer
    define can_update: editor or owner or parent_domain->editor
    define can_delete: owner or parent_domain->owner
    define can_share: owner or parent_domain->admin

type secret
  relations
    define parent_org: [organization]
    define parent_domain: [domain]
    define owner: [user]
    define viewer: [user]  // Can see "configured" status only

    // Computed permissions
    define can_create: owner or parent_org->admin or parent_domain->owner
    define can_read_status: viewer or owner or parent_org->member
    define can_update: owner or parent_org->admin or parent_domain->owner
    define can_delete: owner or parent_org->admin

type session
  relations
    define parent_org: [organization]
    define agent_used: [agent]
    define owner: [user]
    define viewer: [user, team#member]

    // Computed permissions
    define can_read: owner or viewer or parent_org->admin or agent_used->viewer
    define can_terminate: owner or parent_org->admin

// ============================================================================
// PLATFORM ADMIN
// ============================================================================

type platform
  relations
    define admin: [user]

    define can_manage_all: admin
```

## Relationship Tuples

### Example: ACME Corp with Card Services Domain

```typescript
// Organization
{
  user: "user:alice",
  relation: "owner",
  object: "organization:acme-corp"
}
{
  user: "user:bob",
  relation: "admin",
  object: "organization:acme-corp"
}
{
  user: "user:charlie",
  relation: "member",
  object: "organization:acme-corp"
}

// Domain
{
  user: "organization:acme-corp",
  relation: "parent_org",
  object: "domain:card-services"
}
{
  user: "user:bob",
  relation: "owner",
  object: "domain:card-services"
}

// Agent
{
  user: "domain:card-services",
  relation: "parent_domain",
  object: "agent:cibc-card-activation"
}
{
  user: "user:bob",
  relation: "owner",
  object: "agent:cibc-card-activation"
}
{
  user: "user:charlie",
  relation: "executor",
  object: "agent:cibc-card-activation"
}

// Secret
{
  user: "organization:acme-corp",
  relation: "parent_org",
  object: "secret:acme-corp/shared/openai_api_key"
}
{
  user: "user:alice",
  relation: "owner",
  object: "secret:acme-corp/shared/openai_api_key"
}

// Team
{
  user: "organization:acme-corp",
  relation: "parent_org",
  object: "team:card-services-team"
}
{
  user: "user:charlie",
  relation: "member",
  object: "team:card-services-team"
}
{
  user: "team:card-services-team#member",
  relation: "executor",
  object: "agent:cibc-card-activation"
}
```

## Authorization Checks

### Check Examples

#### Can user execute an agent?

```typescript
// Check: can:execute on agent
const allowed = await fgaClient.check({
  user: 'user:charlie',
  relation: 'can_execute',
  object: 'agent:cibc-card-activation',
});

// OpenFGA evaluates:
// 1. charlie is executor? → YES
// 2. Result: ALLOWED
```

#### Can user update a secret?

```typescript
const allowed = await fgaClient.check({
  user: 'user:bob',
  relation: 'can_update',
  object: 'secret:acme-corp/shared/openai_api_key',
});

// OpenFGA evaluates:
// 1. bob is owner? → NO
// 2. bob is admin of parent_org (acme-corp)? → YES
// 3. Result: ALLOWED
```

#### List all agents user can execute

```typescript
const agents = await fgaClient.listObjects({
  user: 'user:charlie',
  relation: 'can_execute',
  type: 'agent',
});

// Returns: [agent:cibc-card-activation, ...]
```

### Permission Inheritance

```
User: charlie
Organization: acme-corp (member)
  ↓ inherits
Domain: card-services (viewer)
  ↓ inherits
Agent: cibc-card-activation (can_read)
```

Charlie can read the agent because:

1. charlie is member of acme-corp
2. Domain inherits: `can_read: ... or parent_org->member`
3. Agent inherits: `can_read: ... or parent_domain->viewer`

## Common Authorization Patterns

### Pattern 1: Resource Creation

```python
# User creates an agent in a domain
await fga_client.write([
    {
        "user": f"user:{user_id}",
        "relation": "owner",
        "object": f"agent:{agent_id}"
    },
    {
        "user": f"domain:{domain_id}",
        "relation": "parent_domain",
        "object": f"agent:{agent_id}"
    }
])
```

### Pattern 2: Delegated Access (Share)

```python
# User shares agent with another user
await fga_client.write([
    {
        "user": f"user:{recipient_id}",
        "relation": "viewer",
        "object": f"agent:{agent_id}"
    }
])
```

### Pattern 3: Team-Based Access

```python
# Grant team access to agent
await fga_client.write([
    {
        "user": f"team:{team_id}#member",
        "relation": "executor",
        "object": f"agent:{agent_id}"
    }
])
```

### Pattern 4: Hierarchical Setup

```python
# Create organization structure
await fga_client.write([
    # User is org owner
    {"user": f"user:{user_id}", "relation": "owner", "object": f"organization:{org_id}"},

    # Domain belongs to org
    {"user": f"organization:{org_id}", "relation": "parent_org", "object": f"domain:{domain_id}"},

    # User owns domain
    {"user": f"user:{user_id}", "relation": "owner", "object": f"domain:{domain_id}"},
])
```

## Migration from RBAC

### RBAC → OpenFGA Mapping

| RBAC Concept                | OpenFGA Equivalent                       |
| --------------------------- | ---------------------------------------- |
| Role: `org_admin`           | Relation: `admin` on `organization`      |
| Role: `agent_creator`       | Computed: `can_create_agent` on `domain` |
| Permission: `agent:execute` | Relation: `executor` on `agent`          |
| Permission: `secret:update` | Computed: `can_update` on `secret`       |
| User-Role Assignment        | Relationship tuple                       |

### Example Migration

**RBAC:**

```sql
-- User has role
INSERT INTO user_roles (user_id, role_id, organization_id)
VALUES ('alice', 'org_admin', 'acme-corp');

-- Role has permissions
INSERT INTO role_permissions (role_id, permission_id)
VALUES ('org_admin', 'agent:create');
```

**OpenFGA:**

```typescript
// User is admin of organization
await fgaClient.write([
  {
    user: 'user:alice',
    relation: 'admin',
    object: 'organization:acme-corp',
  },
]);

// Permission computed automatically:
// organization#admin → can_create_domain → can_create_agent
```

## Integration Points

### Backend Middleware

```python
# backend/middleware/openfga_middleware.py
async def check_permission(
    user_id: str,
    resource: str,
    permission: str
) -> bool:
    """
    Check if user has permission on resource.

    Examples:
        check_permission("alice", "agent:my-agent", "can_execute")
        check_permission("bob", "secret:openai_key", "can_update")
    """
    return await fga_client.check(
        user=f"user:{user_id}",
        relation=permission,
        object=resource
    )
```

### Frontend Components

```typescript
// app/hooks/usePermission.ts
export function usePermission(resource: string, permission: string): boolean {
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    fetch('/api/auth/check', {
      method: 'POST',
      body: JSON.stringify({ resource, permission }),
    })
      .then((res) => res.json())
      .then((data) => setAllowed(data.allowed));
  }, [resource, permission]);

  return allowed;
}
```

## Performance Considerations

### Caching Strategy

```python
# Cache authorization checks with short TTL
@cache(ttl=60)  # 60 seconds
async def check_cached(user: str, relation: str, object: str) -> bool:
    return await fga_client.check(user, relation, object)
```

### Batch Checks

```python
# Check multiple permissions at once
results = await fga_client.batch_check([
    {"user": user_id, "relation": "can_read", "object": "agent:1"},
    {"user": user_id, "relation": "can_read", "object": "agent:2"},
    {"user": user_id, "relation": "can_read", "object": "agent:3"},
])
```

### List Objects Optimization

```python
# Efficient: Let OpenFGA filter
agents = await fga_client.list_objects(
    user=user_id,
    relation="can_execute",
    type="agent"
)

# Inefficient: Don't do this
all_agents = await db.get_all_agents()
filtered = [a for a in all_agents if await check_permission(user_id, a.id, "can_execute")]
```

## Deployment

### Docker Compose

```yaml
openfga:
  image: openfga/openfga:latest
  command: run
  environment:
    - OPENFGA_DATASTORE_ENGINE=postgres
    - OPENFGA_DATASTORE_URI=postgres://user:pass@postgres:5432/openfga
  ports:
    - '8080:8080' # gRPC
    - '8081:8081' # HTTP
  depends_on:
    - postgres
```

### Service Discovery

```python
# backend/config/services.py
OPENFGA = os.getenv("SVC_OPENFGA_HOST", "openfga")
OPENFGA_HTTP_PORT = int(os.getenv("OPENFGA_HTTP_PORT", "8081"))

@classmethod
def get_service_url(cls, service_name: str) -> str:
    if service_name == "OPENFGA":
        return f"http://{cls.OPENFGA}:{cls.OPENFGA_HTTP_PORT}"
```

## Security Benefits

1. **Least Privilege**: Users only get access they need
2. **Audit Trail**: All relationship changes logged
3. **Delegation**: Easy to grant/revoke specific access
4. **Hierarchical**: Org admins automatically have domain access
5. **Scalable**: Authorization check ≈ 1-5ms (Zanzibar proven)

## Summary

OpenFGA provides Agent Foundry with:

✅ **Flexible authorization** - models real-world relationships  
✅ **Fine-grained control** - per-resource permissions  
✅ **Scalable checks** - Google Zanzibar architecture  
✅ **Easy delegation** - share resources naturally  
✅ **Hierarchical** - org → domain → agent inheritance  
✅ **Team support** - group-based access  
✅ **Production-ready** - battle-tested at scale

This replaces the flat RBAC model with a powerful, flexible ReBAC system perfect
for multi-tenant SaaS.
