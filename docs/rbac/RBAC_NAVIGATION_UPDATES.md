# RBAC Updates for Navigation Restructure

**Date:** 2025-11-16  
**Status:** 📝 Proposed Updates

## Overview

This document outlines the RBAC permission updates required for the new
navigation structure implemented in the Agent Foundry UI.

---

## New Pages & Required Permissions

### 1. Teams Page (`/app/teams`)

**Purpose:** Team member management, role assignment, and collaboration

**New Permissions:**

```sql
-- View team members
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('teams:read:org', 'View Team Members', 'View all team members in organization', 'team', 'org'),
('teams:read:self', 'View Own Profile', 'View own team profile', 'team', 'self');

-- Manage team members
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('teams:invite', 'Invite Members', 'Send invitations to new team members', 'team', 'org'),
('teams:remove', 'Remove Members', 'Remove team members from organization', 'team', 'org'),
('teams:update:roles', 'Update Member Roles', 'Change roles of team members', 'team', 'org');

-- Team settings
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('teams:settings:read', 'View Team Settings', 'View organization team settings', 'team', 'org'),
('teams:settings:update', 'Update Team Settings', 'Modify organization team settings', 'team', 'org');
```

**Role Assignments:**

| Role             | Permissions                                         |
| ---------------- | --------------------------------------------------- |
| `platform_owner` | All teams permissions                               |
| `org_admin`      | All teams permissions except platform-level         |
| `org_developer`  | `teams:read:org`, `teams:read:self`, `teams:invite` |
| `org_operator`   | `teams:read:org`, `teams:read:self`                 |
| `org_viewer`     | `teams:read:org`, `teams:read:self`                 |
| `api_client`     | `teams:read:org` (read-only)                        |

### 2. Compiler/From DIS Page (`/app/compiler`)

**Purpose:** Import and compile agents from DIS (Domain Intelligence Schema)
definitions

**New Permissions:**

```sql
-- Compile operations
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('compiler:use', 'Use Compiler', 'Access the DIS compiler tool', 'compiler', 'org'),
('compiler:validate', 'Validate DIS', 'Validate DIS schemas', 'compiler', 'org'),
('compiler:import', 'Import DIS', 'Import DIS definitions and create agents', 'compiler', 'org'),
('compiler:export', 'Export to DIS', 'Export agents to DIS format', 'compiler', 'org');

-- Advanced operations
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('compiler:schema:manage', 'Manage DIS Schemas', 'Manage custom DIS schema definitions', 'compiler', 'org');
```

**Role Assignments:**

| Role               | Permissions                                            |
| ------------------ | ------------------------------------------------------ |
| `domain_architect` | All compiler permissions                               |
| `org_admin`        | All compiler permissions                               |
| `org_developer`    | `compiler:use`, `compiler:validate`, `compiler:import` |
| `org_operator`     | `compiler:use`, `compiler:validate` (read-only)        |
| `org_viewer`       | None                                                   |
| `api_client`       | `compiler:use`, `compiler:import`, `compiler:export`   |

---

## Updated Page Permission Mappings

### Page-to-Permission Matrix

```typescript
export const PAGE_PERMISSIONS: Record<string, string[]> = {
  // Dashboard
  '/': ['dashboard:view'],

  // CREATE section
  '/compiler': ['compiler:use'],
  '/forge': ['forge:use'],

  // MANAGE section
  '/agents': ['agents:read'],
  '/datasets': ['datasets:read'],
  '/tools': ['tools:read'],

  // LAUNCH section
  '/chat': ['playground:use'],
  '/deployments': ['deploy:view'],
  '/monitoring': ['monitoring:view'],

  // CONFIGURE section
  '/projects': ['projects:read'],
  '/domains': ['domains:read'],
  '/teams': ['teams:read:org'],

  // Bottom nav
  '/marketplace': ['marketplace:browse'],
  '/admin': ['admin:access'],
};
```

### Navigation Visibility Rules

```typescript
// app/components/layout/LeftNav.tsx - Add permission checks

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  section?: string;
  isSeparator?: boolean;
  requiredPermission?: string | string[]; // NEW
}

const navItems: NavItem[] = [
  {
    icon: LayoutDashboard,
    label: 'Dashboard',
    href: `${APP_BASE}`,
    requiredPermission: 'dashboard:view',
  },
  { icon: LayoutDashboard, label: '', href: '', isSeparator: true },

  // CREATE section
  { icon: FileCode, label: 'CREATE', href: '', section: 'CREATE' },
  {
    icon: FileCode,
    label: 'From DIS',
    href: `${APP_BASE}/compiler`,
    requiredPermission: 'compiler:use',
  },
  {
    icon: Plus,
    label: 'New Agent',
    href: `${APP_BASE}/forge`,
    requiredPermission: 'forge:use',
  },

  // MANAGE section
  { icon: Layers, label: 'MANAGE', href: '', section: 'MANAGE' },
  {
    icon: Layers,
    label: 'Agents',
    href: `${APP_BASE}/agents`,
    requiredPermission: 'agents:read',
  },
  {
    icon: Database,
    label: 'Datasets',
    href: `${APP_BASE}/datasets`,
    requiredPermission: 'datasets:read',
  },
  {
    icon: Wrench,
    label: 'Tools',
    href: `${APP_BASE}/tools`,
    requiredPermission: 'tools:read',
  },

  // LAUNCH section
  { icon: Rocket, label: 'LAUNCH', href: '', section: 'LAUNCH' },
  {
    icon: MessageSquare,
    label: 'Test',
    href: `${APP_BASE}/chat`,
    requiredPermission: 'playground:use',
  },
  {
    icon: Rocket,
    label: 'Deploy',
    href: `${APP_BASE}/deployments`,
    requiredPermission: 'deploy:view',
  },
  {
    icon: Activity,
    label: 'Monitor',
    href: `${APP_BASE}/monitoring`,
    requiredPermission: 'monitoring:view',
  },

  // CONFIGURE section
  { icon: FolderKanban, label: 'CONFIGURE', href: '', section: 'CONFIGURE' },
  {
    icon: FolderKanban,
    label: 'Projects',
    href: `${APP_BASE}/projects`,
    requiredPermission: 'projects:read',
  },
  {
    icon: Globe,
    label: 'Domains',
    href: `${APP_BASE}/domains`,
    requiredPermission: 'domains:read',
  },
  {
    icon: Users,
    label: 'Teams',
    href: `${APP_BASE}/teams`,
    requiredPermission: 'teams:read:org',
  },

  // Bottom items
  { icon: LayoutDashboard, label: '', href: '', isSeparator: true },
  {
    icon: Store,
    label: 'Marketplace',
    href: `${APP_BASE}/marketplace`,
    requiredPermission: 'marketplace:browse',
  },
  {
    icon: Shield,
    label: 'Admin',
    href: `${APP_BASE}/admin`,
    requiredPermission: 'admin:access',
  },
];
```

---

## Implementation Steps

### 1. Database Migration

Create migration file: `backend/rbac_navigation_permissions.sql`

```sql
-- ============================================
-- Navigation RBAC Updates
-- Date: 2025-11-16
-- Purpose: Add permissions for new navigation pages
-- ============================================

-- Teams permissions
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('teams:read:org', 'View Team Members', 'View all team members in organization', 'team', 'org'),
('teams:read:self', 'View Own Profile', 'View own team profile', 'team', 'self'),
('teams:invite', 'Invite Members', 'Send invitations to new team members', 'team', 'org'),
('teams:remove', 'Remove Members', 'Remove team members from organization', 'team', 'org'),
('teams:update:roles', 'Update Member Roles', 'Change roles of team members', 'team', 'org'),
('teams:settings:read', 'View Team Settings', 'View organization team settings', 'team', 'org'),
('teams:settings:update', 'Update Team Settings', 'Modify organization team settings', 'team', 'org');

-- Compiler permissions
INSERT INTO permissions (code, name, description, resource_type, scope)
VALUES
('compiler:use', 'Use Compiler', 'Access the DIS compiler tool', 'compiler', 'org'),
('compiler:validate', 'Validate DIS', 'Validate DIS schemas', 'compiler', 'org'),
('compiler:import', 'Import DIS', 'Import DIS definitions and create agents', 'compiler', 'org'),
('compiler:export', 'Export to DIS', 'Export agents to DIS format', 'compiler', 'org'),
('compiler:schema:manage', 'Manage DIS Schemas', 'Manage custom DIS schema definitions', 'compiler', 'org');

-- Grant permissions to roles
-- Platform Owner gets all
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'platform_owner'
AND p.code IN (
  'teams:read:org', 'teams:read:self', 'teams:invite', 'teams:remove',
  'teams:update:roles', 'teams:settings:read', 'teams:settings:update',
  'compiler:use', 'compiler:validate', 'compiler:import',
  'compiler:export', 'compiler:schema:manage'
);

-- Org Admin
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'org_admin'
AND p.code IN (
  'teams:read:org', 'teams:read:self', 'teams:invite', 'teams:remove',
  'teams:update:roles', 'teams:settings:read', 'teams:settings:update',
  'compiler:use', 'compiler:validate', 'compiler:import',
  'compiler:export', 'compiler:schema:manage'
);

-- Domain Architect
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'domain_architect'
AND p.code IN (
  'teams:read:org', 'teams:read:self',
  'compiler:use', 'compiler:validate', 'compiler:import',
  'compiler:export', 'compiler:schema:manage'
);

-- Org Developer
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'org_developer'
AND p.code IN (
  'teams:read:org', 'teams:read:self', 'teams:invite',
  'compiler:use', 'compiler:validate', 'compiler:import'
);

-- Org Operator
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'org_operator'
AND p.code IN (
  'teams:read:org', 'teams:read:self',
  'compiler:use', 'compiler:validate'
);

-- Org Viewer
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'org_viewer'
AND p.code IN (
  'teams:read:org', 'teams:read:self'
);

-- API Client
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'api_client'
AND p.code IN (
  'teams:read:org',
  'compiler:use', 'compiler:import', 'compiler:export'
);

-- Verify installation
SELECT
  r.name as role,
  COUNT(DISTINCT p.id) FILTER (WHERE p.code LIKE 'teams:%') as teams_permissions,
  COUNT(DISTINCT p.id) FILTER (WHERE p.code LIKE 'compiler:%') as compiler_permissions
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE r.name IN ('platform_owner', 'org_admin', 'domain_architect', 'org_developer', 'org_operator', 'org_viewer', 'api_client')
GROUP BY r.name
ORDER BY r.name;
```

### 2. Apply Migration

```bash
# Run the migration
cd /Users/nwalker/Development/Projects/agentfoundry

# If using PostgreSQL
psql $DATABASE_URL -f backend/rbac_navigation_permissions.sql

# If using SQLite (current setup)
sqlite3 data/foundry.db < backend/rbac_navigation_permissions.sql
```

### 3. Update Permission Check Utility

Create: `app/lib/permissions/navigation-permissions.ts`

```typescript
import { usePermissions } from '@/app/lib/hooks/usePermissions';

export function useNavigationVisibility() {
  const { hasPermission, hasAnyPermission } = usePermissions();

  return {
    canViewDashboard: hasPermission('dashboard:view'),
    canViewCompiler: hasPermission('compiler:use'),
    canViewForge: hasPermission('forge:use'),
    canViewAgents: hasPermission('agents:read'),
    canViewDatasets: hasPermission('datasets:read'),
    canViewTools: hasPermission('tools:read'),
    canViewTest: hasPermission('playground:use'),
    canViewDeploy: hasPermission('deploy:view'),
    canViewMonitor: hasPermission('monitoring:view'),
    canViewProjects: hasPermission('projects:read'),
    canViewDomains: hasPermission('domains:read'),
    canViewTeams: hasPermission('teams:read:org'),
    canViewMarketplace: hasPermission('marketplace:browse'),
    canViewAdmin: hasPermission('admin:access'),
  };
}
```

### 4. Update LeftNav Component

```typescript
// In app/components/layout/LeftNav.tsx

import { useNavigationVisibility } from '@/app/lib/permissions/navigation-permissions';

export function LeftNav() {
  const permissions = useNavigationVisibility();

  // Filter navigation items based on permissions
  const visibleNavItems = navItems.filter((item) => {
    if (item.isSeparator || item.section) return true;
    if (!item.requiredPermission) return true;

    if (Array.isArray(item.requiredPermission)) {
      return item.requiredPermission.some((perm) => hasPermission(perm));
    }
    return hasPermission(item.requiredPermission);
  });

  // ... rest of component
}
```

---

## Testing Checklist

### Permission Tests

- [ ] Platform owner sees all navigation items
- [ ] Org admin sees all org-level items
- [ ] Domain architect sees compiler and domain tools
- [ ] Org developer sees appropriate create/manage items
- [ ] Org operator sees read-only items
- [ ] Org viewer sees limited read-only items
- [ ] API client has programmatic access only

### Navigation Tests

- [ ] Teams page accessible with `teams:read:org` permission
- [ ] Teams page shows appropriate actions based on role
- [ ] Compiler page accessible with `compiler:use` permission
- [ ] Compiler import requires `compiler:import` permission
- [ ] Navigation items hidden when permission denied
- [ ] Section headers show/hide appropriately based on items
- [ ] Empty sections don't display

### Database Tests

```sql
-- Verify all permissions created
SELECT code, name FROM permissions WHERE code LIKE 'teams:%' OR code LIKE 'compiler:%';

-- Verify role assignments
SELECT r.name, COUNT(*) as permission_count
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE p.code LIKE 'teams:%' OR p.code LIKE 'compiler:%'
GROUP BY r.name;
```

---

## Summary

### New Permissions Added: 12

**Teams:** 7 permissions  
**Compiler:** 5 permissions

### Roles Updated: 7

All standard roles receive appropriate permissions based on their access level.

### Pages Protected: 2

- `/app/teams` - Team management
- `/app/compiler` - DIS compilation

### Navigation Behavior

- Permission-based visibility
- Role-appropriate access
- Graceful degradation for limited permissions

---

## Next Steps

1. **Apply Migration**

   - Run SQL migration script
   - Verify permissions in database

2. **Update Frontend**

   - Add permission checks to LeftNav
   - Implement useNavigationVisibility hook
   - Test visibility with different roles

3. **Documentation**

   - Update RBAC_QUICK_REFERENCE.md
   - Update RBAC_IMPLEMENTATION.md
   - Add navigation permissions guide

4. **Testing**
   - Unit tests for permission checks
   - E2E tests for navigation visibility
   - Role-based access tests

---

**Created By:** AI Assistant  
**Date:** 2025-11-16  
**Status:** Ready for Review & Implementation
