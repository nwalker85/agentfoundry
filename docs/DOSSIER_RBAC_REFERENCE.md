# Dossier RBAC Reference Guide

Quick reference for dossier-specific RBAC permissions and usage patterns in
Agent Foundry.

---

## Dossier Permission Hierarchy

### Core CRUD Permissions

| Permission Code         | Scope    | Description           | Who Has It                                             |
| ----------------------- | -------- | --------------------- | ------------------------------------------------------ |
| `dossier:create`        | org      | Create new dossiers   | domain_architect, org_admin, org_developer, api_client |
| `dossier:read:self`     | self     | View own dossiers     | org_developer                                          |
| `dossier:read:org`      | org      | View all org dossiers | All roles                                              |
| `dossier:read:platform` | platform | View all dossiers     | platform_owner                                         |
| `dossier:update:self`   | self     | Update own dossiers   | org_developer                                          |
| `dossier:update:org`    | org      | Update any dossier    | domain_architect, org_admin, api_client                |
| `dossier:delete:self`   | self     | Delete own dossiers   | org_developer                                          |
| `dossier:delete:org`    | org      | Delete any dossier    | domain_architect, org_admin                            |

### Versioning Permissions

| Permission Code            | Description                  | Who Has It                                             |
| -------------------------- | ---------------------------- | ------------------------------------------------------ |
| `dossier:version:create`   | Create new versions          | domain_architect, org_admin, org_developer, api_client |
| `dossier:version:read`     | View version history         | All roles                                              |
| `dossier:version:rollback` | Rollback to previous version | domain_architect, org_admin                            |

### Lifecycle & Governance

| Permission Code   | Description                        | Who Has It                  |
| ----------------- | ---------------------------------- | --------------------------- |
| `dossier:approve` | Approve changes (DRAFT → APPROVED) | domain_architect, org_admin |
| `dossier:lock`    | Lock/unlock for editing            | domain_architect, org_admin |
| `dossier:archive` | Archive dossiers                   | domain_architect, org_admin |
| `dossier:publish` | Publish to marketplace             | domain_architect, org_admin |

### Import/Export

| Permission Code           | Description        | Who Has It                                             |
| ------------------------- | ------------------ | ------------------------------------------------------ |
| `dossier:export`          | Export to JSON     | All roles                                              |
| `dossier:import`          | Import from JSON   | domain_architect, org_admin, org_developer, api_client |
| `dossier:import:platform` | Import across orgs | platform_owner                                         |

### Validation & Analysis

| Permission Code    | Description                     | Who Has It                                                           |
| ------------------ | ------------------------------- | -------------------------------------------------------------------- |
| `dossier:validate` | Validate against DIS schema     | All roles (except viewer)                                            |
| `dossier:analyze`  | Run analysis                    | All roles (except viewer)                                            |
| `dossier:generate` | Generate artifacts (code, docs) | domain_architect, org_admin, org_developer, org_operator, api_client |

### Component-Level Permissions

| Permission Code             | Description             | Who Has It                              |
| --------------------------- | ----------------------- | --------------------------------------- |
| `dossier:entity:read`       | Query entities          | All roles                               |
| `dossier:entity:update`     | Update entities         | domain_architect, org_admin, api_client |
| `dossier:triplet:read`      | Query triplet functions | All roles                               |
| `dossier:triplet:update`    | Update triplets         | domain_architect, org_admin, api_client |
| `dossier:workflow:read`     | View workflows          | All roles                               |
| `dossier:workflow:update`   | Update workflows        | domain_architect, org_admin, api_client |
| `dossier:governance:read`   | View access gates/rules | All roles                               |
| `dossier:governance:update` | Update governance       | domain_architect, org_admin             |

### Dossier Agent Operations

| Permission Code           | Description                      | Who Has It                                                           |
| ------------------------- | -------------------------------- | -------------------------------------------------------------------- |
| `dossier:agent:query`     | Query domain knowledge via agent | All roles                                                            |
| `dossier:agent:transform` | Transform dossiers via agent     | domain_architect, org_admin, org_operator, api_client                |
| `dossier:agent:generate`  | Generate artifacts via agent     | domain_architect, org_admin, org_developer, org_operator, api_client |

### Privacy & Sensitive Data

| Permission Code          | Description                     | Who Has It                                   |
| ------------------------ | ------------------------------- | -------------------------------------------- |
| `dossier:privacy:read`   | View privacy manifests          | All roles (except viewer has limited access) |
| `dossier:privacy:update` | Update privacy classifications  | domain_architect, org_admin                  |
| `dossier:sensitive:read` | Access encrypted sensitive data | domain_architect, org_admin                  |

---

## Role Permission Matrix

### domain_architect (Specialized Dossier Designer)

**Purpose:** Domain modeling expert who designs and manages DIS dossiers

**Dossier Permissions:** ✅ ALL (30+ permissions)

**Key Capabilities:**

- Full dossier lifecycle management
- Entity and workflow design
- Governance rule creation
- Sensitive data access
- Version control and rollback
- Marketplace publishing

**Use Case:** Enterprise architects, domain modelers, system designers

---

### org_admin (Organization Administrator)

**Dossier Permissions:** ✅ 27 permissions (all except platform-level)

**Key Capabilities:**

- Full org dossier management
- Approval workflows
- Governance enforcement
- Team collaboration
- Import/export

**Restrictions:**

- Cannot access other organization's dossiers

---

### org_developer (Builder/Developer)

**Dossier Permissions:** ✅ 16 permissions (create + own management)

**Key Capabilities:**

- Create and manage own dossiers
- View org dossiers (read-only others')
- Generate code from dossiers
- Use dossier agent for queries
- Export dossiers

**Restrictions:**

- Cannot update others' dossiers
- Cannot approve or publish
- Cannot modify governance rules
- Limited privacy manifest access

---

### org_operator (Operations/SRE)

**Dossier Permissions:** ✅ 12 permissions (read + execute)

**Key Capabilities:**

- Read all org dossiers
- Execute dossier agent operations
- Generate artifacts
- Validate and analyze
- Export for operations

**Restrictions:**

- Cannot create or modify dossiers
- Cannot approve or publish
- Read-only component access

---

### org_viewer (Stakeholder/Observer)

**Dossier Permissions:** ✅ 7 permissions (read-only)

**Key Capabilities:**

- View org dossiers
- View version history
- Export for review
- Query via dossier agent
- View entities, triplets, workflows

**Restrictions:**

- Cannot modify anything
- Cannot generate artifacts
- Cannot validate

---

### api_client (Automation/Integration)

**Dossier Permissions:** ✅ 23 permissions (programmatic access)

**Key Capabilities:**

- Full CRUD via API
- Versioning
- Import/export automation
- Generate artifacts
- All agent operations
- Component-level updates

**Restrictions:**

- Cannot approve dossiers (manual review required)
- Cannot publish to marketplace
- Cannot access platform-level operations

---

## Common Usage Patterns

### 1. Protect Dossier CRUD Endpoint

```python
from fastapi import Depends, APIRouter
from backend.rbac_middleware import RequirePermission, RequestContext

router = APIRouter()

@router.post("/api/dossiers")
async def create_dossier(
    dossier_data: dict,
    context: RequestContext = Depends(RequirePermission("dossier:create"))
):
    # User has dossier:create permission
    # context.organization_id available for isolation
    return {"dossierId": save_dossier(dossier_data, context.organization_id)}
```

### 2. Check Owner vs Org-Wide Access

```python
@router.put("/api/dossiers/{dossier_id}")
async def update_dossier(
    dossier_id: str,
    updates: dict,
    context: RequestContext = Depends(RequirePermission([
        "dossier:update:self",
        "dossier:update:org"
    ], require_all=False))  # Either permission works
):
    dossier = get_dossier(dossier_id)

    # Check if user owns it OR has org-wide permission
    if dossier.created_by == context.user_id:
        # User owns it, allowed by dossier:update:self
        pass
    elif context.has_permission("dossier:update:org"):
        # User has org-wide permission
        pass
    else:
        raise HTTPException(403, "Cannot update this dossier")

    return update_dossier_logic(dossier_id, updates)
```

### 3. Dossier Approval Workflow

```python
@router.post("/api/dossiers/{dossier_id}/approve")
async def approve_dossier(
    dossier_id: str,
    context: RequestContext = Depends(RequirePermission("dossier:approve"))
):
    dossier = get_dossier(dossier_id)

    if dossier.status != "DRAFT":
        raise HTTPException(400, "Only DRAFT dossiers can be approved")

    # Update status
    dossier.status = "APPROVED"
    dossier.approved_by = context.user_id
    dossier.approved_at = datetime.utcnow()

    save_dossier(dossier)

    # Audit log
    await log_request_audit(
        request=request,
        action="dossier.approve",
        resource_type="dossier",
        resource_id=dossier_id,
        result="success"
    )

    return {"status": "approved"}
```

### 4. Version Creation with Permission Check

```python
@router.post("/api/dossiers/{dossier_id}/versions")
async def create_version(
    dossier_id: str,
    version_data: dict,
    context: RequestContext = Depends(RequirePermission("dossier:version:create"))
):
    dossier = get_dossier(dossier_id)

    # Create snapshot
    new_version = {
        "dossierId": dossier_id,
        "version": increment_version(dossier.version),
        "snapshotDate": datetime.utcnow(),
        "dossierSnapshot": dossier.dict(),
        "changeManagement": {
            "changeType": version_data.get("changeType"),
            "changeDescription": version_data.get("description"),
            "changedBy": context.user_id
        }
    }

    save_version(new_version)
    return {"version": new_version["version"]}
```

### 5. Sensitive Data Access

```python
@router.get("/api/dossiers/{dossier_id}/sensitive")
async def get_sensitive_data(
    dossier_id: str,
    context: RequestContext = Depends(RequirePermission("dossier:sensitive:read"))
):
    # Only domain_architect and org_admin have this permission
    dossier = get_dossier(dossier_id)

    # Decrypt sensitive fields
    sensitive_data = decrypt_sensitive_fields(dossier)

    # Audit the access
    await log_request_audit(
        request=request,
        action="dossier.sensitive_access",
        resource_type="dossier",
        resource_id=dossier_id,
        result="success",
        metadata={"accessed_by": context.user_id}
    )

    return {"sensitive_data": sensitive_data}
```

### 6. Dossier Agent Query

```python
@router.post("/api/dossiers/{dossier_id}/agent/query")
async def dossier_agent_query(
    dossier_id: str,
    query: dict,
    context: RequestContext = Depends(RequirePermission("dossier:agent:query"))
):
    # All roles have this permission (even viewers)
    dossier = get_dossier(dossier_id)

    # Use dossier agent to answer questions
    agent_response = await dossier_agent.query(
        dossier=dossier,
        question=query["question"],
        user_id=context.user_id
    )

    return {"answer": agent_response}
```

### 7. Frontend Permission Checks

```tsx
import { usePermissions } from '@/app/lib/hooks/usePermissions';
import { PermissionGate } from '@/app/components/auth/PermissionGate';

function DossierActions({ dossier }) {
  const { hasPermission } = usePermissions();

  const canUpdate =
    hasPermission('dossier:update:org') ||
    (hasPermission('dossier:update:self') &&
      dossier.createdBy === currentUserId);

  return (
    <div>
      <PermissionGate permission="dossier:approve">
        <Button onClick={() => approveDossier(dossier.id)}>
          Approve Dossier
        </Button>
      </PermissionGate>

      {canUpdate && (
        <Button onClick={() => editDossier(dossier.id)}>Edit</Button>
      )}

      <PermissionGate permissions={['dossier:export']}>
        <Button onClick={() => exportDossier(dossier.id)}>Export</Button>
      </PermissionGate>
    </div>
  );
}
```

---

## Installation

### 1. Run RBAC Initialization (if not done)

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
./scripts/initialize_rbac.sh
```

### 2. Apply Dossier Extension

```bash
# Apply dossier permissions
psql $DATABASE_URL -f backend/rbac_dossier_extension.sql
```

### 3. Verify Installation

```sql
-- Count dossier permissions
SELECT COUNT(*) as dossier_permissions
FROM permissions
WHERE code LIKE 'dossier:%';
-- Expected: 30+

-- Check domain_architect role
SELECT p.code, p.description
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE r.name = 'domain_architect'
AND p.code LIKE 'dossier:%'
ORDER BY p.code;
-- Expected: 30+ permissions
```

---

## Best Practices

### 1. Use Scoped Permissions

Always use the most restrictive permission:

- Use `:self` permissions when user owns the resource
- Use `:org` permissions for team collaboration
- Only `:platform` permissions for system admins

### 2. Audit Sensitive Operations

Log all sensitive dossier operations:

```python
await log_request_audit(
    action="dossier.sensitive_access",
    resource_id=dossier_id,
    result="success"
)
```

### 3. Version Before Major Changes

Require version creation before approvals:

```python
if major_change and not has_recent_version(dossier_id):
    raise HTTPException(400, "Create version before approval")
```

### 4. Lock During Editing

Use locking to prevent concurrent edits:

```python
if not acquire_lock(dossier_id, context.user_id):
    raise HTTPException(409, "Dossier locked by another user")
```

### 5. Validate on Import

Always validate imported dossiers:

```python
validation_result = validate_dossier_schema(imported_data)
if not validation_result.is_valid:
    raise HTTPException(400, validation_result.errors)
```

---

## Migration Guide

### Adding Dossier Permissions to Existing User

```python
from backend.rbac_service import rbac_service

# Assign domain_architect role to user
rbac_service.assign_role({
    "user_id": "user123",
    "role_name": "domain_architect",
    "organization_id": "org456",
    "granted_by": "nate"
})
```

### Creating Custom Dossier Role

```sql
-- Create custom role
INSERT INTO roles (name, description, scope, is_system_role)
VALUES (
    'dossier_reviewer',
    'Reviews and approves dossiers',
    'org',
    false
);

-- Grant specific permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'dossier_reviewer'
AND p.code IN (
    'dossier:read:org',
    'dossier:approve',
    'dossier:version:read',
    'dossier:entity:read',
    'dossier:governance:read'
);
```

---

## Troubleshooting

### Permission Denied on Dossier Create

**Symptom:** 403 Forbidden when creating dossier

**Check:**

```sql
SELECT p.code
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.email = 'user@example.com'
AND p.code = 'dossier:create';
```

**Fix:** Assign appropriate role with `dossier:create` permission

### Cannot Access Sensitive Data

**Symptom:** Missing encrypted fields in response

**Check:**

```python
context.has_permission("dossier:sensitive:read")  # Should be True
```

**Fix:** Only `domain_architect` and `org_admin` can access sensitive data

### Version Rollback Fails

**Symptom:** Cannot rollback dossier version

**Check:**

```sql
SELECT p.code
FROM ... -- (same query as above)
WHERE p.code = 'dossier:version:rollback';
```

**Fix:** User needs `dossier:version:rollback` permission (admin-level only)

---

## Summary

**Total Dossier Permissions:** 30+

**New Role:** `domain_architect` (full dossier access)

**Integration:** Seamless with existing RBAC system

**Security:** Multi-level (self, org, platform) + sensitive data controls

**Ready to use** after running `rbac_dossier_extension.sql`

---

For full RBAC documentation, see:

- `RBAC_QUICKSTART.md`
- `docs/RBAC_IMPLEMENTATION.md`
- `docs/RBAC_QUICK_REFERENCE.md`
