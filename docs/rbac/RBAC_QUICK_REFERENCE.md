# RBAC Quick Reference

Quick reference guide for using RBAC in Agent Foundry.

---

## Common Patterns

### 1. Protect a Route

```python
from fastapi import Depends, APIRouter
from backend.rbac_middleware import RequirePermission, RequestContext

router = APIRouter()

@router.post("/api/agents")
async def create_agent(
    context: RequestContext = Depends(RequirePermission("agent:create"))
):
    return {"status": "created"}
```

### 2. Get Current User Info

```python
from backend.rbac_middleware import get_current_user, RequestContext

@router.get("/api/me")
async def get_me(context: RequestContext = Depends(get_current_user)):
    return {
        "user_id": context.user_id,
        "organization_id": context.organization_id,
        "email": context.email,
        "permissions": list(context.permissions)
    }
```

### 3. Manual Permission Check

```python
@router.post("/api/agents/{agent_id}/delete")
async def delete_agent(
    agent_id: str,
    context: RequestContext = Depends(get_current_user)
):
    # Check if user owns the agent OR has org-wide delete permission
    if not context.has_any_permission(["agent:delete:self", "agent:delete:org"]):
        raise HTTPException(403, "Cannot delete agent")

    # ... delete logic
```

### 4. Check Multiple Permissions (ALL required)

```python
@router.post("/api/deployments")
async def create_deployment(
    context: RequestContext = Depends(RequirePermission([
        "agent:read:org",
        "instance:update"
    ]))
):
    return {"status": "deployed"}
```

### 5. Check Multiple Permissions (ANY required)

```python
@router.get("/api/sessions/{session_id}")
async def get_session(
    session_id: str,
    context: RequestContext = Depends(RequirePermission(
        ["session:read:self", "session:read:org"],
        require_all=False  # ANY permission is sufficient
    ))
):
    return {"session": {...}}
```

### 6. Optional Authentication

```python
from backend.rbac_middleware import get_optional_user

@router.get("/api/agents/gallery")
async def list_gallery_agents(
    context: Optional[RequestContext] = Depends(get_optional_user)
):
    if context:
        # Authenticated user
        return {"agents": all_agents, "can_publish": context.has_permission("agent:publish")}
    else:
        # Anonymous user
        return {"agents": public_agents, "can_publish": False}
```

### 7. Audit Logging

```python
from backend.rbac_middleware import log_request_audit

@router.delete("/api/agents/{agent_id}")
async def delete_agent(
    request: Request,
    agent_id: str,
    context: RequestContext = Depends(RequirePermission("agent:delete:org"))
):
    delete_agent_logic(agent_id)

    await log_request_audit(
        request=request,
        action="agent.delete",
        resource_type="agent",
        resource_id=agent_id,
        result="success"
    )

    return {"status": "deleted"}
```

---

## Permission Codes Cheat Sheet

### Agent Permissions

| Code                | Description         |
| ------------------- | ------------------- |
| `agent:create`      | Create new agents   |
| `agent:read:self`   | View own agents     |
| `agent:read:org`    | View all org agents |
| `agent:update:self` | Update own agents   |
| `agent:update:org`  | Update any agent    |
| `agent:delete:self` | Delete own agents   |
| `agent:delete:org`  | Delete any agent    |
| `agent:execute`     | Execute agents      |
| `agent:publish`     | Publish to gallery  |

### Session Permissions

| Code                     | Description            |
| ------------------------ | ---------------------- |
| `session:read:self`      | View own sessions      |
| `session:read:org`       | View all org sessions  |
| `session:terminate:self` | Terminate own sessions |
| `session:terminate:org`  | Terminate any session  |

### User Management

| Code          | Description         |
| ------------- | ------------------- |
| `user:read`   | View users in org   |
| `user:invite` | Invite new users    |
| `user:update` | Update user details |
| `user:revoke` | Remove users        |

### Organization

| Code         | Description         |
| ------------ | ------------------- |
| `org:read`   | View org details    |
| `org:update` | Update org settings |

### API Keys

| Code                  | Description         |
| --------------------- | ------------------- |
| `api_key:create:self` | Create own API keys |
| `api_key:read:self`   | View own API keys   |
| `api_key:revoke:self` | Revoke own API keys |
| `api_key:create:org`  | Create org API keys |
| `api_key:revoke:org`  | Revoke any API key  |

### LLM & Quotas

| Code                   | Description        |
| ---------------------- | ------------------ |
| `llm:invoke`           | Make LLM API calls |
| `llm:quota:read:self`  | View own usage     |
| `llm:quota:read:org`   | View org usage     |
| `llm:quota:update:org` | Update org quotas  |

### Audit Logs

| Code              | Description         |
| ----------------- | ------------------- |
| `audit:read:self` | View own audit logs |
| `audit:read:org`  | View org audit logs |

---

## Role Comparison

| Feature            | `org_admin` | `org_developer` | `org_operator` | `org_viewer` | `api_client` |
| ------------------ | ----------- | --------------- | -------------- | ------------ | ------------ |
| **Agents**         |
| Create agents      | ✅          | ✅              | ❌             | ❌           | ❌           |
| View all agents    | ✅          | ✅              | ✅             | ✅           | ✅           |
| Update own agents  | ✅          | ✅              | ❌             | ❌           | ❌           |
| Update any agent   | ✅          | ❌              | ❌             | ❌           | ❌           |
| Delete agents      | ✅          | Own only        | ❌             | ❌           | ❌           |
| Execute agents     | ✅          | ✅              | ✅             | ❌           | ✅           |
| Publish agents     | ✅          | ❌              | ❌             | ❌           | ❌           |
| **Sessions**       |
| View all sessions  | ✅          | Own only        | ✅             | ✅           | Own only     |
| Terminate sessions | ✅          | Own only        | ✅             | ❌           | ❌           |
| **Users**          |
| View users         | ✅          | ❌              | ❌             | ❌           | ❌           |
| Invite users       | ✅          | ❌              | ❌             | ❌           | ❌           |
| Update users       | ✅          | ❌              | ❌             | ❌           | ❌           |
| **LLM**            |
| Make LLM calls     | ✅          | ✅              | ❌             | ❌           | ✅           |
| View org usage     | ✅          | Own only        | ✅             | ✅           | Own only     |
| Update quotas      | ✅          | ❌              | ❌             | ❌           | ❌           |
| **Audit Logs**     |
| View audit logs    | ✅          | ❌              | ❌             | ❌           | ❌           |

---

## RBAC Service API

### Permission Checking

```python
from backend.rbac_service import rbac_service

# Check single permission
has_perm = rbac_service.has_permission(user_id, org_id, "agent:create")

# Check any permission
has_any = rbac_service.has_any_permission(user_id, org_id, ["agent:read:self", "agent:read:org"])

# Check all permissions
has_all = rbac_service.has_all_permissions(user_id, org_id, ["agent:create", "agent:execute"])

# Get all permissions
permissions = rbac_service.get_user_permissions(user_id, org_id)
# Returns: {'agent:create', 'agent:read:org', 'session:read:self', ...}

# Get user with roles and permissions
user_perms = rbac_service.get_user_with_permissions(user_id, org_id)
print(user_perms.email, user_perms.roles, user_perms.permissions)
```

### Role Management

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import UserRoleAssignmentCreate

# Assign role
rbac_service.assign_role(UserRoleAssignmentCreate(
    user_id="user_123",
    role_name="org_developer",
    organization_id="org_456",
    granted_by="admin_user"
))

# Revoke role
rbac_service.revoke_role("user_123", "org_developer", "org_456")

# List available roles
roles = rbac_service.list_roles(include_system=False)

# Get role details
role = rbac_service.get_role_by_name("org_developer")
print(f"Permissions: {[p.code for p in role.permissions]}")

# Invalidate permission cache
rbac_service.invalidate_cache(user_id, org_id)
```

### API Key Management

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import APIKeyCreate

# Create API key
api_key = rbac_service.create_api_key(APIKeyCreate(
    name="Production API Key",
    user_id="user_123",
    organization_id="org_456",
    role_name="api_client"
))
print(f"Key (save this!): {api_key.key}")
print(f"Prefix (for display): {api_key.key_prefix}")

# Verify API key
key_info = rbac_service.verify_api_key("ak_live_...")
if key_info:
    print(f"Valid key for user {key_info['user_id']}")

# Revoke API key
rbac_service.revoke_api_key(api_key.id)
```

### Audit Logging

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import AuditLogCreate

rbac_service.log_audit(AuditLogCreate(
    organization_id="org_456",
    user_id="user_123",
    action="agent.create",
    resource_type="agent",
    resource_id="agent_789",
    result="success",
    metadata={"agent_name": "My Agent"}
))
```

---

## Testing Snippets

### Test Permission Check

```python
def test_permission_enforcement(client, test_user_token):
    # Should succeed with valid permission
    response = client.get(
        "/api/agents",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200

    # Should fail without permission
    response = client.delete("/api/agents/123")
    assert response.status_code == 403
```

### Mock RequestContext

```python
from backend.rbac_middleware import RequestContext

def test_function_with_context():
    context = RequestContext(
        user_id="test_user",
        organization_id="test_org",
        email="test@example.com",
        name="Test User",
        permissions=["agent:create", "agent:read:org"]
    )

    assert context.has_permission("agent:create")
    assert not context.has_permission("user:invite")
```

---

## SQL Queries

### Check User Permissions

```sql
SELECT p.code, p.description
FROM user_roles ur
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE ur.user_id = 'user_123'
  AND ur.organization_id = 'org_456'
ORDER BY p.code;
```

### List Users by Role

```sql
SELECT u.email, r.name as role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.organization_id = 'org_456'
ORDER BY u.email;
```

### View Recent Audit Logs

```sql
SELECT
    created_at,
    u.email,
    action,
    resource_type,
    resource_id,
    result
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
WHERE al.organization_id = 'org_456'
ORDER BY created_at DESC
LIMIT 50;
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://foundry:foundry@postgres:5432/foundry

# JWT (for user authentication)
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
```

---

## Common Errors & Solutions

| Error                        | Cause                    | Solution                                  |
| ---------------------------- | ------------------------ | ----------------------------------------- |
| `401 Unauthorized`           | Missing/invalid token    | Check Authorization header                |
| `403 Forbidden`              | Insufficient permissions | Verify user has required role/permission  |
| `Permission denied for user` | Wrong org context        | Check user is in correct organization     |
| `Role not found`             | Invalid role name        | Use `list_roles()` to see available roles |
| `Cache not invalidated`      | Stale permissions        | Call `invalidate_cache(user_id, org_id)`  |

---

## Migration Checklist

- [ ] Run `init_db()` to create RBAC tables
- [ ] Run migration script to assign roles to existing users
- [ ] Update route handlers to use `RequirePermission`
- [ ] Replace manual role checks with permission checks
- [ ] Add audit logging to sensitive operations
- [ ] Test permission enforcement
- [ ] Update frontend to hide/disable UI based on permissions
- [ ] Document custom roles/permissions for your team
- [ ] Set up API keys for programmatic access
- [ ] Configure LLM usage tracking

---

## Next Steps

1. Read `docs/RBAC_IMPLEMENTATION.md` for full documentation
2. Review `backend/rbac_schema.sql` for schema details
3. See `backend/rbac_service.py` for complete API
4. Check `backend/rbac_middleware.py` for FastAPI integration
5. Test with your existing endpoints
