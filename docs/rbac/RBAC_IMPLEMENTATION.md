# RBAC Implementation Guide

## Overview

Agent Foundry now implements a comprehensive Role-Based Access Control (RBAC)
system that provides:

- **Fine-grained permissions**: Atomic authorities like `agent:create`,
  `session:read:org`
- **Flexible roles**: Pre-defined roles (platform & org-level) with bundles of
  permissions
- **Multi-tenant isolation**: Organization-scoped permissions with Row-Level
  Security (RLS)
- **API key support**: Programmatic access with role-based scoping
- **Service accounts**: Non-human identities for backend services
- **Audit logging**: Complete trail of all privileged operations
- **LLM usage tracking**: Quota enforcement and billing

---

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         REQUEST FLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. JWT/API Key → Authentication                                 │
│  2. Load User Permissions (cached)                               │
│  3. Check Permission → Allow/Deny                                │
│  4. Set RLS Context (org_id, user_id, permissions)               │
│  5. Execute Query (RLS enforces tenant isolation)                │
│  6. Log Audit Entry                                              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema

**Core RBAC Tables:**

- `roles` - Role definitions (e.g., `org_admin`, `org_developer`)
- `permissions` - Atomic authorities (e.g., `agent:create`, `session:read:org`)
- `role_permissions` - Many-to-many mapping
- `user_roles` - User role assignments per org

**Supporting Tables:**

- `api_keys` - API keys for programmatic access
- `service_accounts` - Non-human identities
- `sessions` - Agent execution sessions
- `audit_logs` - Complete audit trail
- `llm_usage` - LLM usage tracking
- `llm_quotas` - Quota definitions per org

**Row-Level Security:**

- Postgres RLS policies enforce tenant isolation
- Session variables: `app.current_org`, `app.current_user`, `app.has_permission`

---

## Roles & Permissions

### Platform-Level Roles

These are **global roles** for platform administrators:

#### `platform_owner`

- Full access to all organizations and settings
- Manage users, quotas, and platform configuration
- **Use sparingly** - only for core platform team

#### `platform_support`

- Read-only access across organizations
- View agents, sessions, usage, audit logs
- No write access (except optional impersonation)

### Organization-Level Roles

These are **per-tenant roles** assigned to users within their organization:

#### `org_admin`

- Full control over organization resources and users
- Manage users, agents, domains, instances
- View and manage billing, quotas, audit logs
- **Default role for org owners**

#### `org_developer`

- Create and manage own agents
- Execute agents and run sessions
- View org-wide agents (read-only)
- Manage own API keys
- **Primary role for builders**

#### `org_viewer`

- Read-only access to org resources
- View agents, sessions, artifacts, quotas
- No create/update/delete capabilities
- **Good for stakeholders and analysts**

#### `org_operator`

- Execute agents and manage sessions
- Terminate sessions, view artifacts
- No agent authoring capabilities
- **Good for SRE/ops teams**

#### `api_client`

- Programmatic access for API keys
- Execute agents, read sessions
- Subject to LLM quotas
- **Used for CI/CD, automation**

### Service Roles (Internal)

These are for **service accounts** (non-human):

- `backend_service` - Backend API access to Redis, LiveKit, DB
- `compiler_service` - Compile agents, emit artifacts
- `job_runner_service` - Background jobs, cleanup, batch operations

---

## Permission Model

Permissions follow a **hierarchical naming convention**:

```
<resource>:<action>:<scope>
```

### Resource Types

- `org` - Organization management
- `user` - User management
- `agent` - Agent management
- `session` - Session management
- `artifact` - Artifact management
- `llm` / `llm_quota` - LLM usage and quotas
- `audit` - Audit logs
- `settings` - Configuration
- `api_key` - API key management
- `domain` / `instance` - Domain and instance management

### Actions

- `read` - View resource
- `create` - Create new resource
- `update` - Modify existing resource
- `delete` - Remove resource
- `execute` - Execute agent
- `terminate` - Terminate session
- `invoke` - Make LLM calls
- `revoke` - Revoke access
- `publish` - Publish to gallery
- `impersonate` - Impersonate user (dangerous)

### Scopes

- `self` - Own resources only
- `org` - Organization-wide
- `platform` - Platform-wide (admin only)

### Examples

```
agent:create           → Create agents in org
agent:read:self        → View own agents
agent:read:org         → View all agents in org
agent:update:org       → Update any agent in org
session:terminate:org  → Terminate any session in org
llm:quota:read:self    → View own LLM usage
audit:read:org         → View org audit logs
```

---

## Usage Guide

### 1. Protecting API Routes

#### Basic Permission Check

```python
from fastapi import Depends, APIRouter
from backend.rbac_middleware import get_current_user, RequirePermission, RequestContext

router = APIRouter()

@router.get("/api/agents")
async def list_agents(
    context: RequestContext = Depends(RequirePermission("agent:read:org"))
):
    """List all agents (requires agent:read:org permission)."""
    org_id = context.organization_id
    # ... fetch agents for org
    return {"agents": [...]}
```

#### Multiple Permissions (ALL required)

```python
@router.post("/api/agents")
async def create_agent(
    context: RequestContext = Depends(RequirePermission(["agent:create", "agent:execute"]))
):
    """Create and execute agent (requires both permissions)."""
    # ... create agent logic
```

#### Multiple Permissions (ANY required)

```python
@router.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    context: RequestContext = Depends(RequirePermission(
        ["session:read:self", "session:read:org"],
        require_all=False
    ))
):
    """Get session (requires either self or org read permission)."""
    # ... fetch session
```

#### Optional Authentication

```python
from backend.rbac_middleware import get_optional_user

@router.get("/api/public/agents")
async def list_public_agents(
    context: Optional[RequestContext] = Depends(get_optional_user)
):
    """List agents (different results based on auth status)."""
    if context:
        # Authenticated - show org agents
        return {"agents": [...], "authenticated": True}
    else:
        # Anonymous - show only public agents
        return {"agents": [...], "authenticated": False}
```

### 2. Manual Permission Checks

```python
from backend.rbac_service import rbac_service

# Check single permission
if rbac_service.has_permission(user_id, org_id, "agent:delete:org"):
    # User can delete any agent in org
    delete_agent(agent_id)

# Check multiple permissions (ANY)
if rbac_service.has_any_permission(user_id, org_id, ["agent:update:self", "agent:update:org"]):
    # User can update at least this category of agents
    update_agent(agent_id, updates)

# Get all permissions
permissions = rbac_service.get_user_permissions(user_id, org_id)
print(permissions)  # {'agent:create', 'agent:read:org', ...}
```

### 3. Using Request Context

```python
@router.post("/api/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    context: RequestContext = Depends(get_current_user)
):
    """Execute agent using context."""

    # Access user info
    user_id = context.user_id
    org_id = context.organization_id
    email = context.email

    # Check permissions manually
    if not context.has_permission("agent:execute"):
        raise HTTPException(status_code=403, detail="No execute permission")

    # Check if service account
    if context.is_service_account:
        logger.info(f"API key execution by {user_id}")

    # ... execute agent
```

### 4. Audit Logging

```python
from backend.rbac_middleware import log_request_audit

@router.post("/api/agents")
async def create_agent(
    request: Request,
    agent_data: AgentCreate,
    context: RequestContext = Depends(RequirePermission("agent:create"))
):
    """Create agent with audit logging."""

    # Create agent
    agent = create_agent_logic(agent_data, context.organization_id, context.user_id)

    # Log audit entry
    await log_request_audit(
        request=request,
        action="agent.create",
        resource_type="agent",
        resource_id=agent.id,
        result="success",
        metadata={"agent_name": agent.name}
    )

    return {"agent": agent}
```

### 5. Row-Level Security (RLS) Context

For advanced use cases where you need RLS enforcement:

```python
from backend.rbac_middleware import set_rls_context

@router.get("/api/agents")
async def list_agents(
    request: Request,
    context: RequestContext = Depends(get_current_user)
):
    """List agents with RLS enforcement."""

    # Set RLS context for this request
    await set_rls_context(request, context)

    # Now all queries will respect RLS policies
    # Postgres automatically filters by org_id and visibility
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM agents")  # RLS filters automatically
            agents = cur.fetchall()

    return {"agents": agents}
```

---

## Role Management

### Assigning Roles

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import UserRoleAssignmentCreate

# Assign developer role to user
assignment = UserRoleAssignmentCreate(
    user_id="user_123",
    role_name="org_developer",
    organization_id="org_456",
    granted_by="admin_user_id",
    expires_at=None  # Never expires
)

rbac_service.assign_role(assignment)
```

### Revoking Roles

```python
rbac_service.revoke_role(
    user_id="user_123",
    role_name="org_developer",
    org_id="org_456"
)
```

### Listing Available Roles

```python
# List all roles
roles = rbac_service.list_roles(include_system=True)

# List only org-level roles (exclude platform roles)
org_roles = rbac_service.list_roles(include_system=False)

for role in org_roles:
    print(f"{role.name}: {role.description}")
```

### Getting Role Details

```python
role = rbac_service.get_role_by_name("org_developer")
print(f"Role: {role.name}")
print(f"Permissions: {[p.code for p in role.permissions]}")
```

---

## API Key Management

### Creating API Keys

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import APIKeyCreate

# Create API key for CI/CD
api_key_create = APIKeyCreate(
    name="CI/CD Pipeline Key",
    user_id="user_123",
    organization_id="org_456",
    role_name="api_client",
    expires_at=datetime(2025, 12, 31)  # Optional expiration
)

api_key_response = rbac_service.create_api_key(api_key_create)

# IMPORTANT: Full key is only shown once!
print(f"API Key: {api_key_response.key}")  # ak_live_...
print(f"Key ID: {api_key_response.id}")
print(f"Prefix: {api_key_response.key_prefix}")  # For display
```

### Using API Keys

```bash
# API keys work like JWT tokens
curl -H "Authorization: Bearer ak_live_..." \
  https://api.agentfoundry.com/api/agents
```

### Revoking API Keys

```python
from uuid import UUID

rbac_service.revoke_api_key(UUID("api-key-id-here"))
```

---

## LLM Usage & Quotas

### Logging LLM Usage

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import LLMUsageCreate

# After making an LLM call
usage = LLMUsageCreate(
    organization_id="org_456",
    user_id="user_123",
    session_id=session_id,
    agent_id="agent_789",
    model="gpt-4",
    provider="openai",
    prompt_tokens=150,
    completion_tokens=300,
    total_tokens=450,
    cost_usd=0.0135  # Calculate based on provider pricing
)

rbac_service.log_llm_usage(usage)
```

### Checking Quotas

```python
# Query current usage
with rbac_service.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT SUM(total_tokens) as total
            FROM llm_usage
            WHERE organization_id = %s
              AND created_at >= %s
            """,
            (org_id, period_start)
        )
        current_usage = cur.fetchone()['total']

# Check against quota
with conn.cursor() as cur:
    cur.execute(
        """
        SELECT limit_value
        FROM llm_quotas
        WHERE organization_id = %s
          AND quota_type = 'monthly_tokens'
          AND is_active = TRUE
        """,
        (org_id,)
    )
    quota = cur.fetchone()

if current_usage >= quota['limit_value']:
    raise HTTPException(status_code=429, detail="Monthly token quota exceeded")
```

---

## Migration Guide

### Migrating from Simple Roles

The existing `users.role` field (TEXT: 'admin', 'user', 'viewer') needs to be
mapped to the new RBAC system:

```python
# Migration script (run once)
from backend.rbac_service import rbac_service
from backend.rbac_models import UserRoleAssignmentCreate
from backend.db import get_connection

# Map old roles to new roles
ROLE_MAPPING = {
    'admin': 'org_admin',
    'user': 'org_developer',
    'viewer': 'org_viewer'
}

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, organization_id, role FROM users")

        for user in cur.fetchall():
            new_role = ROLE_MAPPING.get(user['role'], 'org_developer')

            assignment = UserRoleAssignmentCreate(
                user_id=user['id'],
                role_name=new_role,
                organization_id=user['organization_id'],
                granted_by='system'
            )

            rbac_service.assign_role(assignment)

print("✅ Migration complete")
```

### Updating Existing Code

**Before:**

```python
# Old simple role check
if user.role == 'admin':
    # Do admin thing
```

**After:**

```python
# New permission check
if context.has_permission("org:update"):
    # Do admin thing
```

**Before:**

```python
@router.get("/api/agents")
async def list_agents(user: User = Depends(get_current_user)):
    if user.role not in ['admin', 'user']:
        raise HTTPException(403)
```

**After:**

```python
@router.get("/api/agents")
async def list_agents(
    context: RequestContext = Depends(RequirePermission("agent:read:org"))
):
    # Permission enforced automatically
```

---

## Security Best Practices

### 1. Least Privilege Principle

- Assign the **minimum permissions** needed for each user
- Use `org_developer` instead of `org_admin` unless truly needed
- Create custom roles for specialized use cases

### 2. API Key Rotation

- Set expiration dates on API keys
- Rotate keys regularly (every 90 days recommended)
- Revoke keys immediately when no longer needed

### 3. Audit Everything

- Log all privileged operations (create, update, delete)
- Review audit logs regularly
- Set up alerts for suspicious activity

### 4. Service Account Isolation

- Use separate service accounts for each service
- Don't share service credentials between services
- Rotate service credentials periodically

### 5. Permission Caching

- Permissions are cached for 5 minutes by default
- Invalidate cache when roles change:
  `rbac_service.invalidate_cache(user_id, org_id)`
- Don't cache permissions client-side

### 6. Row-Level Security

- Always use RLS for multi-tenant tables
- Set RLS context at the start of each transaction
- Never trust client-provided `org_id` without verification

---

## Testing RBAC

### Unit Tests

```python
import pytest
from backend.rbac_service import rbac_service

def test_permission_check():
    # Setup: Create user with developer role
    rbac_service.assign_role(UserRoleAssignmentCreate(
        user_id="test_user",
        role_name="org_developer",
        organization_id="test_org"
    ))

    # Test: Check permissions
    assert rbac_service.has_permission("test_user", "test_org", "agent:create")
    assert rbac_service.has_permission("test_user", "test_org", "agent:read:org")
    assert not rbac_service.has_permission("test_user", "test_org", "user:invite")
```

### Integration Tests

```python
from fastapi.testclient import TestClient

def test_protected_endpoint():
    client = TestClient(app)

    # Test without auth
    response = client.get("/api/agents")
    assert response.status_code == 401

    # Test with valid JWT
    token = create_jwt(user_id="user_123", org_id="org_456")
    response = client.get(
        "/api/agents",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

## Troubleshooting

### Permission Denied (403)

**Problem:** User gets 403 Forbidden on a route they should have access to.

**Solution:**

1. Check user's roles: `rbac_service.get_user_with_permissions(user_id, org_id)`
2. Verify role has the permission: `rbac_service.get_role_by_name(role_name)`
3. Check if role assignment expired:
   `SELECT * FROM user_roles WHERE user_id = '...'`
4. Invalidate cache: `rbac_service.invalidate_cache(user_id, org_id)`

### RLS Not Working

**Problem:** Users can see data from other organizations.

**Solution:**

1. Verify RLS is enabled:
   `SELECT tablename FROM pg_tables WHERE rowsecurity = true`
2. Check if RLS context is set: `SHOW app.current_org`
3. Ensure `set_rls_context()` is called at transaction start
4. Verify RLS policies are correct: `SELECT * FROM pg_policies`

### API Key Not Working

**Problem:** API key returns 401 Unauthorized.

**Solution:**

1. Check if key is active:
   `SELECT * FROM api_keys WHERE key_prefix = 'ak_live_...'`
2. Verify key hasn't expired: `expires_at IS NULL OR expires_at > NOW()`
3. Check if key was revoked: `revoked_at IS NULL`
4. Ensure Bearer prefix is correct: `Authorization: Bearer ak_live_...`

---

## Database Schema Reference

### Quick Reference

```sql
-- Get all permissions for a user
SELECT p.code
FROM user_roles ur
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE ur.user_id = 'user_123'
  AND ur.organization_id = 'org_456';

-- Get all users with a specific role
SELECT u.email, u.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE r.name = 'org_admin'
  AND ur.organization_id = 'org_456';

-- Get role details
SELECT r.name, COUNT(rp.permission_id) as permission_count
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id, r.name;

-- Audit recent actions
SELECT created_at, user_id, action, resource_type, resource_id, result
FROM audit_logs
WHERE organization_id = 'org_456'
ORDER BY created_at DESC
LIMIT 100;
```

---

## Next Steps

1. **Initialize RBAC** - Run `init_db()` to create tables and seed roles
2. **Migrate Users** - Run migration script to assign roles to existing users
3. **Update Routes** - Add `RequirePermission` dependencies to protected
   endpoints
4. **Add Audit Logging** - Call `log_request_audit()` for sensitive operations
5. **Test Thoroughly** - Verify permissions work as expected
6. **Monitor Usage** - Set up LLM usage tracking and quotas
7. **Review Regularly** - Audit role assignments and permission usage

---

## Additional Resources

- **Gap Analysis**: See `docs/FORGE_LANGGRAPH_GAP_ANALYSIS.md` for feature
  requirements
- **Platform Implications**: See `docs/PLATFORM_IMPLICATIONS.md` for
  architecture context
- **Database Schema**: See `backend/rbac_schema.sql` and
  `backend/rbac_seed_data.sql`
- **Python API**: See `backend/rbac_service.py` and `backend/rbac_middleware.py`

---

## Support

For questions or issues with RBAC implementation:

1. Check this documentation first
2. Review the troubleshooting section
3. Examine audit logs for permission denials
4. Check database for role assignments
5. Contact platform team if issue persists
