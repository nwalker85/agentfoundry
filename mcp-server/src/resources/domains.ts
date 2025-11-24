/**
 * Domain Resources for MCP Server
 * --------------------------------
 * Provides access to domain metadata and hierarchy.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register domain resource providers
 */
export async function registerDomainResources(server: Server) {
  const currentHandler = server.requestHandlers.get('resources/read');

  server.setRequestHandler('resources/read', async (request) => {
    const uri = request.params.uri;

    // Match domain://{domain_id} pattern
    const domainMatch = uri.match(/^domain:\/\/([^\/]+)$/);

    if (domainMatch) {
      const domain_id = domainMatch[1];

      try {
        // Fetch domain details (would need a dedicated endpoint)
        // For now, fetch from organizations endpoint
        const url = `${getServiceUrl('backend')}/api/control/organizations`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error('Failed to fetch domains');
        }

        const orgs = await response.json();

        // Find the domain across all orgs
        let foundDomain: any = null;
        for (const org of orgs) {
          const domain = org.domains?.find((d: any) => d.id === domain_id);
          if (domain) {
            foundDomain = {
              ...domain,
              organization: {
                id: org.id,
                name: org.name,
              },
            };
            break;
          }
        }

        if (!foundDomain) {
          throw new Error(`Domain not found: ${domain_id}`);
        }

        return {
          contents: [
            {
              uri: `domain://${domain_id}`,
              mimeType: 'application/json',
              text: JSON.stringify(foundDomain, null, 2),
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to read domain resource: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // Delegate to existing handler
    if (currentHandler) {
      return await currentHandler(request);
    }

    throw new Error(`Unknown resource URI: ${uri}`);
  });
}
