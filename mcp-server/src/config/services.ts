/**
 * Service Discovery Configuration for MCP Server
 * -----------------------------------------------
 * Integrates with Agent Foundry's Infrastructure as Registry pattern.
 *
 * Uses DNS-based service names in Docker/K8s.
 */

interface ServiceConfig {
  backend: string;
  mcpGateway: string;
  openfga: string;
  localstack: string;
}

/**
 * Get service URLs based on environment.
 *
 * Development: Docker Compose service names
 * Production: Kubernetes service names (same!)
 */
function getServices(): ServiceConfig {
  const environment = process.env.ENVIRONMENT || 'development';

  // Service discovery - uses DNS names
  const backendHost = process.env.SVC_BACKEND_HOST || 'foundry-backend';
  const mcpHost = process.env.SVC_MCP_HOST || 'mcp-integration';
  const openfgaHost = process.env.SVC_OPENFGA_HOST || 'openfga';
  const localstackHost = process.env.SVC_LOCALSTACK_HOST || 'localstack';

  // Standard ports (8080 for app services, custom for infrastructure)
  const backendPort = process.env.BACKEND_PORT || '8080';
  const mcpPort = process.env.MCP_INTEGRATION_PORT || '8080';
  const openfgaPort = process.env.OPENFGA_HTTP_PORT || '8081';
  const localstackPort = process.env.LOCALSTACK_PORT || '4566';

  return {
    backend: `http://${backendHost}:${backendPort}`,
    mcpGateway: `http://${mcpHost}:${mcpPort}`,
    openfga: `http://${openfgaHost}:${openfgaPort}`,
    localstack: `http://${localstackHost}:${localstackPort}`,
  };
}

export const SERVICES = getServices();

/**
 * Get service URL by name
 */
export function getServiceUrl(service: keyof ServiceConfig): string {
  return SERVICES[service];
}

/**
 * Build full URL with path and query params
 */
export function buildServiceUrl(
  service: keyof ServiceConfig,
  path: string,
  params?: Record<string, string | number>
): string {
  const baseUrl = SERVICES[service];
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
 * Log service configuration (development only)
 */
if (process.env.NODE_ENV === 'development') {
  console.log('🔧 MCP Server - Service Discovery:', SERVICES);
}
