/**
 * usePermissions hook for checking user permissions in React components
 */

import { useSession } from 'next-auth/react';
import {
  getUserPermissions,
  hasPermission,
  hasAnyPermission,
  hasAllPermissions,
  getUserRoles,
  isPlatformAdmin,
  isOrgAdmin,
} from '../auth';

export function usePermissions() {
  const { data: session, status } = useSession();

  const loading = status === 'loading';
  const authenticated = status === 'authenticated';

  return {
    // Session info
    session,
    loading,
    authenticated,

    // User info
    userId: session?.user?.id,
    userEmail: session?.user?.email,
    userName: session?.user?.name,
    organizationId: session?.user?.organizationId,

    // Permissions
    permissions: getUserPermissions(session),
    roles: getUserRoles(session),

    // Permission checks
    hasPermission: (permission: string) => hasPermission(session, permission),
    hasAnyPermission: (permissions: string[]) => hasAnyPermission(session, permissions),
    hasAllPermissions: (permissions: string[]) => hasAllPermissions(session, permissions),

    // Role checks
    isPlatformAdmin: isPlatformAdmin(session),
    isOrgAdmin: isOrgAdmin(session),

    // Common permission shortcuts
    canCreateAgents: hasPermission(session, 'agent:create'),
    canViewOrgAgents: hasPermission(session, 'agent:read:org'),
    canUpdateOrgAgents: hasPermission(session, 'agent:update:org'),
    canDeleteOrgAgents: hasPermission(session, 'agent:delete:org'),
    canExecuteAgents: hasPermission(session, 'agent:execute'),
    canManageUsers: hasPermission(session, 'user:update'),
    canViewAuditLogs: hasPermission(session, 'audit:read:org'),
    canManageOrgSettings: hasPermission(session, 'org:update'),
  };
}
