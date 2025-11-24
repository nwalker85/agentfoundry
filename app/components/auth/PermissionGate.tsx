/**
 * PermissionGate component for conditional rendering based on permissions
 */

'use client';

import { ReactNode } from 'react';
import { usePermissions } from '@/app/lib/hooks/usePermissions';

interface PermissionGateProps {
  children: ReactNode;
  permission?: string;
  permissions?: string[];
  requireAll?: boolean;
  fallback?: ReactNode;
  showLoading?: boolean;
}

/**
 * Conditionally render children based on user permissions
 *
 * @example
 * <PermissionGate permission="agent:create">
 *   <CreateAgentButton />
 * </PermissionGate>
 *
 * @example
 * <PermissionGate permissions={["agent:update:self", "agent:update:org"]} requireAll={false}>
 *   <EditAgentButton />
 * </PermissionGate>
 */
export function PermissionGate({
  children,
  permission,
  permissions,
  requireAll = true,
  fallback = null,
  showLoading = false,
}: PermissionGateProps) {
  const { loading, hasPermission, hasAnyPermission, hasAllPermissions } = usePermissions();

  // Show loading state if requested
  if (loading && showLoading) {
    return <>{fallback}</>;
  }

  // Check single permission
  if (permission) {
    if (!hasPermission(permission)) {
      return <>{fallback}</>;
    }
  }

  // Check multiple permissions
  if (permissions && permissions.length > 0) {
    const hasRequiredPermissions = requireAll
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);

    if (!hasRequiredPermissions) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
}

/**
 * Show content only to platform admins
 */
export function PlatformAdminOnly({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { isPlatformAdmin } = usePermissions();

  if (!isPlatformAdmin) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Show content only to org admins
 */
export function OrgAdminOnly({
  children,
  fallback = null,
}: {
  children: ReactNode;
  fallback?: ReactNode;
}) {
  const { isOrgAdmin } = usePermissions();

  if (!isOrgAdmin) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

/**
 * Show content based on role
 */
export function RoleGate({
  children,
  role,
  roles,
  fallback = null,
}: {
  children: ReactNode;
  role?: string;
  roles?: string[];
  fallback?: ReactNode;
}) {
  const perms = usePermissions();
  const userRoles = perms.roles;

  if (role && !userRoles.includes(role)) {
    return <>{fallback}</>;
  }

  if (roles && roles.length > 0) {
    const hasRole = roles.some((r) => userRoles.includes(r));
    if (!hasRole) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
}
