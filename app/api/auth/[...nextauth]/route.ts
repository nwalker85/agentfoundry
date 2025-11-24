import NextAuth from 'next-auth';
import type { NextAuthOptions } from 'next-auth';
import type { OAuthConfig } from 'next-auth/providers/oauth';

interface ZitadelProfile {
  sub: string;
  name?: string;
  email?: string;
  preferred_username?: string;
  picture?: string;
}

interface AuthConfig {
  provider: string;
  configured: boolean;
  client_id: string | null;
  issuer_url: string | null;
  internal_issuer_url?: string | null;
}

// Cache for auth config from service registry
let authConfigCache: AuthConfig | null = null;
let authConfigFetchedAt = 0;
const AUTH_CONFIG_TTL = 60000; // 1 minute cache

/**
 * Fetch auth configuration from backend service registry (LocalStack)
 *
 * This follows the Infrastructure-as-Registry pattern:
 * - Config is stored in LocalStack Secrets Manager
 * - Backend exposes public (non-secret) config via /api/config/auth
 * - Frontend fetches at runtime, not hardcoded
 */
async function getAuthConfig(): Promise<AuthConfig> {
  const now = Date.now();

  // Return cached config if still valid
  if (authConfigCache && now - authConfigFetchedAt < AUTH_CONFIG_TTL) {
    return authConfigCache;
  }

  try {
    const backendUrl = process.env.BACKEND_URL || 'http://foundry-backend:8080';
    const response = await fetch(`${backendUrl}/api/config/auth`, {
      cache: 'no-store',
    });

    if (response.ok) {
      authConfigCache = await response.json();
      authConfigFetchedAt = now;
      console.log(
        `Auth config loaded from service registry: client_id=${authConfigCache?.client_id}`
      );
      return authConfigCache!;
    }
  } catch (error) {
    console.error('Failed to fetch auth config from backend:', error);
  }

  // Fallback to env vars if service registry unavailable
  console.warn('Using env var fallback for auth config');
  return {
    provider: 'zitadel',
    configured: !!process.env.ZITADEL_CLIENT_ID,
    client_id: process.env.ZITADEL_CLIENT_ID || null,
    issuer_url: process.env.ZITADEL_URL || 'http://localhost:8082',
  };
}

/**
 * Zitadel OIDC Provider Configuration
 *
 * Agent Foundry uses Zitadel as the sole identity provider.
 * Configuration is fetched from the service registry (LocalStack).
 *
 * Note: Uses internal Docker URL for server-side OIDC discovery,
 * but external URL for browser redirects.
 */
function ZitadelProvider(config: AuthConfig): OAuthConfig<ZitadelProfile> {
  // External URL for browser redirects (user's browser hits localhost:8082)
  const externalUrl = config.issuer_url || 'http://localhost:8082';
  // Server-side URL: Use zitadel-proxy which adds the correct Host header
  // The proxy forwards to zitadel:8080 with Host: localhost:8082
  const serverUrl = 'http://zitadel-proxy:8080';
  const clientId = config.client_id;

  if (!clientId) {
    console.warn(
      'Zitadel not configured in service registry. Run: python scripts/setup_zitadel.py'
    );
  }

  return {
    id: 'zitadel',
    name: 'Zitadel',
    type: 'oauth',
    // Manual OIDC configuration (avoids wellKnown fetch issues with Docker networking)
    // Issuer must match what's in the ID token - Zitadel sets this to the external URL
    issuer: externalUrl,
    authorization: {
      // Browser redirects use external URL
      url: `${externalUrl}/oauth/v2/authorize`,
      params: {
        scope: 'openid profile email',
      },
    },
    token: {
      url: `${serverUrl}/oauth/v2/token`,
    },
    userinfo: {
      url: `${serverUrl}/oidc/v1/userinfo`,
    },
    jwks_endpoint: `${serverUrl}/oauth/v2/keys`,
    clientId: clientId || 'not-configured',
    clientSecret: process.env.ZITADEL_CLIENT_SECRET || '',
    checks: ['pkce', 'state'],
    idToken: true,
    profile(profile: ZitadelProfile) {
      return {
        id: profile.sub,
        name: profile.name || profile.preferred_username || '',
        email: profile.email || '',
        image: profile.picture,
      };
    },
  };
}

/**
 * Load user RBAC data from backend via OpenFGA
 */
async function loadUserRBACData(email: string) {
  try {
    const backendUrl = process.env.BACKEND_URL || 'http://foundry-backend:8080';
    const response = await fetch(`${backendUrl}/api/auth/user-permissions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    if (response.ok) {
      const data = await response.json();
      return {
        userId: data.user_id,
        organizationId: data.organization_id,
        permissions: data.permissions || [],
        roles: data.roles || [],
      };
    }
  } catch (error) {
    console.error('Failed to load user RBAC data:', error);
  }

  return null;
}

/**
 * Build NextAuth options with config from service registry
 */
async function buildAuthOptions(): Promise<NextAuthOptions> {
  const config = await getAuthConfig();

  return {
    providers: [ZitadelProvider(config)],
    pages: {
      signIn: '/login',
      error: '/login',
    },
    callbacks: {
      async signIn({ user }) {
        // For development: allow login even without email
        // In production, email should be required
        const identifier = user.email || user.id;
        if (!identifier) {
          console.error('SignIn rejected: no email or id in user object');
          return false;
        }

        if (user.email) {
          const rbacData = await loadUserRBACData(user.email);
          if (!rbacData) {
            console.warn(`User ${user.email} not found in RBAC system`);
          }
        }

        return true;
      },
      async session({ session, token }) {
        if (session.user) {
          session.user.id = (token.id as string) || token.sub || '';
          session.user.organizationId = token.organizationId as string;
          session.user.permissions = (token.permissions as string[]) || [];
          session.user.roles =
            (token.roles as Array<{ name: string; description?: string }>) || [];
          session.user.accessToken = token.accessToken as string | undefined;
          session.user.provider = token.provider as string | undefined;
        }
        return session;
      },
      async jwt({ token, user, account, trigger }) {
        if (user || trigger === 'update') {
          const email = user?.email || token.email;

          if (email) {
            const rbacData = await loadUserRBACData(email);

            if (rbacData) {
              token.id = rbacData.userId;
              token.organizationId = rbacData.organizationId;
              token.permissions = rbacData.permissions;
              token.roles = rbacData.roles;
            }
          }

          if (account?.access_token) {
            token.accessToken = account.access_token;
            token.provider = account.provider;
          }
        }

        return token;
      },
    },
    session: {
      strategy: 'jwt',
      maxAge: 30 * 24 * 60 * 60, // 30 days
    },
    secret: process.env.NEXTAUTH_SECRET,
  };
}

// NextAuth handler with dynamic config
// Next.js 16+ requires params to be awaited
async function handler(
  req: Request,
  context: { params: Promise<{ nextauth: string[] }> }
) {
  const authOptions = await buildAuthOptions();
  const params = await context.params;
  return NextAuth(authOptions)(req, { params });
}

export { handler as GET, handler as POST };
