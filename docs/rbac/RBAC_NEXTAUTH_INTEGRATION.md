# RBAC + NextAuth Integration Guide

This document explains how RBAC is integrated with NextAuth.js (Google OAuth) in
Agent Foundry.

---

## Overview

The platform now has a complete RBAC system integrated with NextAuth.js for
authentication. When users sign in via Google OAuth, their permissions are
automatically loaded from the database and included in their session.

**Admin User:** `nate@ravenhelm.co` has been configured with `platform_owner`
role with full platform access.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. User clicks "Sign in with Google"                            │
│  2. Google OAuth flow → NextAuth                                 │
│  3. NextAuth signIn callback:                                    │
│     ├─ Calls backend: POST /api/auth/user-permissions           │
│     ├─ Backend looks up user by email                            │
│     └─ Returns: user_id, org_id, permissions[], roles[]          │
│  4. NextAuth jwt callback:                                       │
│     └─ Stores RBAC data in JWT token                             │
│  5. NextAuth session callback:                                   │
│     └─ Includes RBAC data in session object                      │
│  6. Frontend:                                                    │
│     ├─ usePermissions() hook reads session                       │
│     ├─ PermissionGate component shows/hides UI                   │
│     └─ Can check permissions before API calls                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### 1. Initialize RBAC System

Run the initialization script to set up the database and admin user:

```bash
./scripts/initialize_rbac.sh
```

This will:

- Create all RBAC tables (roles, permissions, user_roles, etc.)
- Seed 60+ permissions
- Create 7 org-level and 2 platform-level roles
- Set up `nate@ravenhelm.co` as `platform_owner`

### 2. Environment Variables

Ensure these are set in your `.env.local`:

```bash
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-here

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Backend URL (for NextAuth to fetch permissions)
BACKEND_URL=http://backend:8000

# Database
DATABASE_URL=postgresql://foundry:foundry@postgres:5432/foundry
```

### 3. Restart Services

After running the initialization script:

```bash
# Restart backend
docker-compose restart backend

# Or if running locally
cd backend && uvicorn main:app --reload
```

### 4. Sign In

1. Navigate to `http://localhost:3000`
2. Sign in with Google using `nate@ravenhelm.co`
3. You'll be authenticated with full `platform_owner` permissions

---

## Frontend Usage

### Check Permissions in Components

```tsx
import { usePermissions } from '@/app/lib/hooks/usePermissions';

function MyComponent() {
  const { hasPermission, isPlatformAdmin, canCreateAgents } = usePermissions();

  if (isPlatformAdmin) {
    return <AdminPanel />;
  }

  if (canCreateAgents) {
    return <CreateAgentButton />;
  }

  return <ReadOnlyView />;
}
```

### Conditional Rendering with PermissionGate

```tsx
import {
  PermissionGate,
  PlatformAdminOnly,
} from '@/app/components/auth/PermissionGate';

function Dashboard() {
  return (
    <>
      {/* Show only if user can create agents */}
      <PermissionGate permission="agent:create">
        <CreateAgentButton />
      </PermissionGate>

      {/* Show if user has ANY of these permissions */}
      <PermissionGate
        permissions={['agent:update:self', 'agent:update:org']}
        requireAll={false}
      >
        <EditButton />
      </PermissionGate>

      {/* Show only to platform admins */}
      <PlatformAdminOnly>
        <SystemSettingsLink />
      </PlatformAdminOnly>
    </>
  );
}
```

### Check Before API Calls

```tsx
import { usePermissions } from '@/app/lib/hooks/usePermissions';

function AgentList() {
  const { hasPermission, session } = usePermissions();

  async function deleteAgent(agentId: string) {
    if (!hasPermission('agent:delete:org')) {
      alert("You don't have permission to delete agents");
      return;
    }

    // Make API call with session
    await fetch(`/api/agents/${agentId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${session?.user?.id}`, // Or use proper JWT
      },
    });
  }
}
```

---

## Backend Integration

### Access User Info from Session

In your backend routes, you can validate the NextAuth session:

```python
from fastapi import Header, HTTPException

async def get_current_user_from_nextauth(authorization: str = Header(None)):
    """
    Extract user info from NextAuth session.
    In production, you'd validate the JWT properly.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")

    # Parse token (implement proper JWT validation in production)
    token = authorization.replace("Bearer ", "")

    # Verify and extract user info
    # ...

    return user_info
```

### Protected Endpoints

```python
from backend.rbac_middleware import RequirePermission, RequestContext

@app.post("/api/agents")
async def create_agent(
    context: RequestContext = Depends(RequirePermission("agent:create"))
):
    """
    Create agent (requires agent:create permission).
    The RequirePermission dependency automatically checks permissions.
    """
    agent = create_agent_logic(
        organization_id=context.organization_id,
        user_id=context.user_id
    )
    return {"agent": agent}
```

---

## Session Structure

After signing in, the session object contains:

```typescript
{
  user: {
    id: "nate",                    // User ID from database
    email: "nate@ravenhelm.co",    // Email from Google
    name: "Nate Walker",           // Name from Google
    image: "...",                  // Profile picture from Google
    organizationId: "platform",    // Organization ID
    permissions: [                 // Array of permission codes
      "org:read:platform",
      "org:update:platform",
      "user:read:platform",
      "agent:read:org",
      // ... all platform_owner permissions
    ],
    roles: [                       // Array of roles
      {
        name: "platform_owner",
        description: "Platform administrator with full access..."
      }
    ]
  }
}
```

---

## Adding More Users

### Via Database

```sql
-- 1. Create user
INSERT INTO users (id, organization_id, email, name)
VALUES ('user_id', 'org_id', 'user@example.com', 'User Name');

-- 2. Assign role
INSERT INTO user_roles (user_id, role_id, organization_id)
SELECT 'user_id', r.id, 'org_id'
FROM roles r
WHERE r.name = 'org_developer';  -- or org_admin, org_viewer, etc.
```

### Via Python Script

```python
from backend.rbac_service import rbac_service
from backend.rbac_models import UserRoleAssignmentCreate
from backend.db import get_connection

# Create user
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, organization_id, email, name) VALUES (%s, %s, %s, %s)",
            ("john", "quant", "john@example.com", "John Doe")
        )
    conn.commit()

# Assign role
rbac_service.assign_role(UserRoleAssignmentCreate(
    user_id="john",
    role_name="org_developer",
    organization_id="quant",
    granted_by="nate"
))
```

---

## Permissions Reference

### Platform Owner Permissions

As `platform_owner`, `nate@ravenhelm.co` has access to:

**Organization Management:**

- `org:read:platform` - View all organizations
- `org:update:platform` - Update any organization

**User Management:**

- `user:read:platform` - View all users

**Agent Management:**

- `agent:read:org` - View agents
- `agent:update:org` - Update any agent
- `agent:delete:org` - Delete any agent

**Sessions:**

- `session:read:org` - View all sessions
- `session:terminate:org` - Terminate any session

**Artifacts:**

- `artifact:read:org` - View all artifacts
- `artifact:delete:org` - Delete artifacts

**LLM & Quotas:**

- `llm:quota:read:org` - View LLM usage
- `llm:quota:update:org` - Update quotas

**Audit:**

- `audit:read:platform` - View all audit logs

**Settings:**

- `settings:read:platform` - View platform settings
- `settings:update:platform` - Update platform settings

**And more...** (see `docs/RBAC_QUICK_REFERENCE.md` for complete list)

---

## Troubleshooting

### User Not Found Error

**Problem:** After signing in, you get "User not found" error.

**Solution:** Make sure the user exists in the database and has been assigned a
role:

```bash
# Run the setup script
./scripts/initialize_rbac.sh

# Or manually check
psql $DATABASE_URL -c "SELECT * FROM users WHERE email = 'nate@ravenhelm.co';"
```

### No Permissions in Session

**Problem:** Session exists but permissions array is empty.

**Solution:**

1. Verify user has roles assigned:

```sql
SELECT u.email, r.name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
WHERE u.email = 'nate@ravenhelm.co';
```

2. Check if roles have permissions:

```sql
SELECT r.name, COUNT(rp.permission_id)
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
WHERE r.name = 'platform_owner'
GROUP BY r.name;
```

3. Clear NextAuth session and sign in again

### Backend Connection Error

**Problem:** NextAuth can't reach backend to fetch permissions.

**Solution:**

1. Verify `BACKEND_URL` is set correctly in `.env.local`
2. Ensure backend is running: `docker-compose ps backend`
3. Check backend logs: `docker-compose logs backend`
4. Test endpoint manually:

```bash
curl -X POST http://localhost:8000/api/auth/user-permissions \
  -H "Content-Type: application/json" \
  -d '{"email": "nate@ravenhelm.co"}'
```

---

## Security Considerations

### JWT Token Security

Currently, the integration uses a simple base64-encoded token for demo purposes.
**In production:**

1. Generate proper JWT tokens with signing:

```typescript
import jwt from 'jsonwebtoken';

const token = jwt.sign(
  {
    sub: session.user.id,
    email: session.user.email,
    org_id: session.user.organizationId,
  },
  process.env.JWT_SECRET!,
  { expiresIn: '1d' }
);
```

2. Validate JWTs in backend:

```python
import jwt

def validate_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### Permission Caching

Permissions are cached in the NextAuth session (JWT) for 30 days by default. If
you change a user's roles/permissions:

1. **Option A:** User signs out and back in
2. **Option B:** Implement session refresh:

```typescript
import { useSession } from 'next-auth/react';

const { update } = useSession();
await update(); // Triggers jwt callback to reload permissions
```

### Row-Level Security

The backend has RLS (Row-Level Security) policies that automatically filter
queries by organization. This provides defense-in-depth even if permission
checks fail.

---

## Testing

### Test Sign In

```bash
# 1. Start services
docker-compose up

# 2. Open browser
open http://localhost:3000

# 3. Sign in with nate@ravenhelm.co via Google

# 4. Check session in browser console
// In browser DevTools console:
import { useSession } from "next-auth/react"
const { data: session } = useSession()
console.log(session.user.permissions)
```

### Test Permissions

```typescript
// In a React component:
import { usePermissions } from "@/app/lib/hooks/usePermissions"

function TestComponent() {
  const perms = usePermissions()

  console.log('All permissions:', perms.permissions)
  console.log('Is platform admin?', perms.isPlatformAdmin)
  console.log('Can create agents?', perms.canCreateAgents)

  return <pre>{JSON.stringify(perms, null, 2)}</pre>
}
```

---

## Next Steps

1. ✅ **Setup Complete** - RBAC integrated with NextAuth
2. 📝 **Add More Users** - Invite team members and assign roles
3. 🔒 **Protect Backend Routes** - Add `RequirePermission` to all sensitive
   endpoints
4. 🎨 **Update UI** - Use `PermissionGate` to show/hide features based on
   permissions
5. 📊 **Audit Logging** - Add `log_request_audit()` calls to track privileged
   operations
6. 🔑 **API Keys** - Create API keys for programmatic access
7. 📈 **LLM Quotas** - Set up usage tracking and quota enforcement

---

## Additional Resources

- **RBAC Implementation Guide**: `docs/RBAC_IMPLEMENTATION.md`
- **Quick Reference**: `docs/RBAC_QUICK_REFERENCE.md`
- **Example Routes**: `backend/example_rbac_routes.py`
- **Frontend Hooks**: `app/lib/hooks/usePermissions.ts`
- **Permission Components**: `app/components/auth/PermissionGate.tsx`

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs backend`
2. Verify database: `psql $DATABASE_URL`
3. Test endpoint:
   `curl http://localhost:8000/api/auth/user-permissions -X POST -H "Content-Type: application/json" -d '{"email":"nate@ravenhelm.co"}'`
4. Review this documentation
5. Check `docs/RBAC_IMPLEMENTATION.md` for detailed troubleshooting

---

**Status:** ✅ Ready for use  
**Admin User:** nate@ravenhelm.co (platform_owner)  
**Last Updated:** November 17, 2025
