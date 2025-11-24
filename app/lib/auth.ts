/**
 * Authentication utilities for NextAuth + RBAC integration
 */

import { Session } from 'next-auth';

/**
 * Get user permissions from session
 */
export function getUserPermissions(session: Session | null): string[] {
  return session?.user?.permissions || [];
}

/**
 * Check if user has a specific permission
 */
export function hasPermission(session: Session | null, permission: string): boolean {
  const permissions = getUserPermissions(session);
  return permissions.includes(permission);
}

/**
 * Check if user has any of the specified permissions
 */
export function hasAnyPermission(session: Session | null, permissions: string[]): boolean {
  const userPermissions = getUserPermissions(session);
  return permissions.some((p) => userPermissions.includes(p));
}

/**
 * Check if user has all of the specified permissions
 */
export function hasAllPermissions(session: Session | null, permissions: string[]): boolean {
  const userPermissions = getUserPermissions(session);
  return permissions.every((p) => userPermissions.includes(p));
}

/**
 * Get user roles from session
 */
export function getUserRoles(session: Session | null): string[] {
  return session?.user?.roles?.map((r) => r.name) || [];
}

/**
 * Check if user has a specific role
 */
export function hasRole(session: Session | null, roleName: string): boolean {
  const roles = getUserRoles(session);
  return roles.includes(roleName);
}

/**
 * Check if user is platform admin
 */
export function isPlatformAdmin(session: Session | null): boolean {
  return hasRole(session, 'platform_owner');
}

/**
 * Check if user is org admin
 */
export function isOrgAdmin(session: Session | null): boolean {
  return hasAnyPermission(session, ['org:update', 'user:update']);
}

/**
 * Get organization ID from session
 */
export function getOrganizationId(session: Session | null): string | undefined {
  return session?.user?.organizationId;
}

/**
 * Generate authorization header for backend API calls
 *
 * Uses the OIDC access token from Zitadel when available (RS256).
 * Falls back to legacy base64-encoded payload for internal authentication.
 *
 * The backend supports both token types:
 * - RS256 tokens from Zitadel are validated via JWKS
 * - Legacy tokens are decoded and validated internally
 */
export function getAuthHeader(session: Session | null): Record<string, string> {
  if (!session?.user?.id) {
    return {};
  }

  // Prefer OIDC access token (RS256) when available
  // This is the token from Zitadel
  if (session.user.accessToken) {
    return {
      Authorization: `Bearer ${session.user.accessToken}`,
    };
  }

  // Fallback: Sign JWT client-side with NEXTAUTH_SECRET (HS256)
  // This is used when no OIDC token is available
  // Note: The backend must have the same JWT_SECRET configured
  const payload = {
    sub: session.user.id,
    email: session.user.email,
    org_id: session.user.organizationId,
    name: session.user.name,
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + 3600, // 1 hour
  };

  // For client-side, we can't sign JWTs without exposing the secret
  // Instead, use a server-side API route to get a signed token
  // For now, encode as Base64 (legacy support) with a marker
  const legacyToken = Buffer.from(
    JSON.stringify({
      ...payload,
      permissions: session.user.permissions,
      _legacy: true, // Marker for backend to handle specially
    })
  ).toString('base64');

  return {
    Authorization: `Bearer ${legacyToken}`,
    'X-Auth-Method': 'legacy-base64', // Tell backend this is legacy format
  };
}

/**
 * Get access token for server-side API calls
 * Use this in server components or API routes
 */
export function getAccessToken(session: Session | null): string | undefined {
  return session?.user?.accessToken;
}

/**
 * Check if session has a valid OIDC token
 */
export function hasOIDCToken(session: Session | null): boolean {
  return !!session?.user?.accessToken;
}

/**
 * Get the authentication provider used for this session
 */
export function getAuthProvider(session: Session | null): string | undefined {
  return session?.user?.provider;
}
