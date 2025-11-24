/**
 * Service Discovery Configuration (Frontend)
 * -------------------------------------------
 * Infrastructure-as-Registry pattern for Next.js frontend.
 *
 * Philosophy:
 * - Server-side API routes use internal Docker DNS names
 * - Client-side (browser) uses public localhost URLs in dev
 * - NO hardcoded URLs scattered across components
 * - Single source of truth for all service endpoints
 *
 * Usage:
 *   Client-side:
 *     const url = `${SERVICES.backend.public}/api/agents`
 *
 *   Server-side (API routes):
 *     const url = `${SERVICES.backend.internal}/api/agents`
 */

/** Service endpoint configuration */
interface ServiceEndpoint {
  /** Internal Docker/K8s URL (for server-side Next.js API routes) */
  internal: string;
  /** Public URL (for browser/client-side requests) */
  public: string;
}

interface ServiceConfig {
  backend: ServiceEndpoint;
  compiler: ServiceEndpoint;
  livekit: ServiceEndpoint;
  websocket: ServiceEndpoint;
}

/**
 * Get service configuration based on environment.
 *
 * In Docker Compose:
 * - Internal: http://foundry-backend:8080
 * - Public: http://localhost:8000 (mapped port)
 *
 * In Production (K8s):
 * - Internal: http://foundry-backend:8080
 * - Public: https://api.yourdomain.com
 */
function getServiceConfig(): ServiceConfig {
  // ============================================================================
  // BACKEND SERVICE
  // ============================================================================
  const backendInternal =
    process.env.SVC_BACKEND_URL || process.env.BACKEND_URL || 'http://foundry-backend:8080';

  const backendPublic = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // ============================================================================
  // COMPILER SERVICE
  // ============================================================================
  const compilerInternal = process.env.SVC_COMPILER_URL || 'http://foundry-compiler:8080';

  const compilerPublic = process.env.NEXT_PUBLIC_COMPILER_URL || 'http://localhost:8002';

  // ============================================================================
  // LIVEKIT SERVICE
  // ============================================================================
  const livekitInternal = process.env.SVC_LIVEKIT_URL || 'ws://livekit:7880';

  const livekitPublic = process.env.NEXT_PUBLIC_LIVEKIT_URL || 'ws://localhost:7880';

  // ============================================================================
  // WEBSOCKET SERVICE (same as backend, different protocol)
  // ============================================================================
  const wsInternal = backendInternal.replace('http://', 'ws://');
  const wsPublic = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  return {
    backend: {
      internal: backendInternal,
      public: backendPublic,
    },
    compiler: {
      internal: compilerInternal,
      public: compilerPublic,
    },
    livekit: {
      internal: livekitInternal,
      public: livekitPublic,
    },
    websocket: {
      internal: wsInternal,
      public: wsPublic,
    },
  };
}

/**
 * Singleton service configuration.
 * Import this in your components/API routes.
 */
export const SERVICES = getServiceConfig();

/**
 * Helper to determine if we're in server-side context
 */
export function isServerSide(): boolean {
  return typeof window === 'undefined';
}

/**
 * Get the appropriate endpoint (internal vs public) based on context.
 *
 * @param service - Service name ('backend', 'compiler', etc.)
 * @returns URL to use for the current context
 *
 * @example
 * ```tsx
 * // Automatically uses correct URL based on context
 * const url = getServiceUrl('backend')
 * const response = await fetch(`${url}/api/agents`)
 * ```
 */
export function getServiceUrl(service: keyof ServiceConfig): string {
  if (isServerSide()) {
    return SERVICES[service].internal;
  }
  return SERVICES[service].public;
}

/**
 * Type-safe service URL builder
 *
 * @example
 * ```tsx
 * const url = buildServiceUrl('backend', '/api/agents', { status: 'active' })
 * // => "http://foundry-backend:8080/api/agents?status=active"
 * ```
 */
export function buildServiceUrl(
  service: keyof ServiceConfig,
  path: string,
  params?: Record<string, string | number | boolean>
): string {
  const baseUrl = getServiceUrl(service);
  const cleanPath = path.startsWith('/') ? path : `/${path}`;

  if (!params || Object.keys(params).length === 0) {
    return `${baseUrl}${cleanPath}`;
  }

  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    searchParams.append(key, String(value));
  });

  return `${baseUrl}${cleanPath}?${searchParams.toString()}`;
}

/**
 * Export individual service URLs for convenience
 */
export const API = {
  /** Backend API endpoints */
  backend: {
    internal: SERVICES.backend.internal,
    public: SERVICES.backend.public,
    /** Helper for common endpoints */
    agents: () => `${getServiceUrl('backend')}/api/agents`,
    integrations: () => `${getServiceUrl('backend')}/api/integrations/tools`,
    control: () => `${getServiceUrl('backend')}/api/control/organizations`,
  },

  /** Compiler endpoints */
  compiler: {
    internal: SERVICES.compiler.internal,
    public: SERVICES.compiler.public,
    compile: () => `${getServiceUrl('compiler')}/api/compile`,
  },

  /** LiveKit voice endpoints */
  livekit: {
    internal: SERVICES.livekit.internal,
    public: SERVICES.livekit.public,
  },

  /** WebSocket endpoints */
  websocket: {
    internal: SERVICES.websocket.internal,
    public: SERVICES.websocket.public,
    events: () => `${getServiceUrl('websocket')}/api/events/subscribe`,
    chat: () => `${getServiceUrl('websocket')}/ws/chat`,
  },
};

/**
 * Development-only: Log service configuration
 */
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  console.log('🔧 Service Registry:', {
    context: isServerSide() ? 'server' : 'client',
    services: SERVICES,
  });
}
