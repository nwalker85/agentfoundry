/**
 * Organization Resources for MCP Server
 * --------------------------------------
 * Provides access to organization settings and hierarchy.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register organization resource providers
 */
export async function registerOrganizationResources(server: Server) {
  const currentHandler = server.requestHandlers.get('resources/read');

  server.setRequestHandler('resources/read', async (request) => {
    const uri = request.params.uri;

    // Match organization://{org_id} pattern
    const orgMatch = uri.match(/^organization:\/\/([^\/]+)$/);

    if (orgMatch) {
      const org_id = orgMatch[1];

      try {
        const url = `${getServiceUrl('backend')}/api/control/organizations`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error('Failed to fetch organizations');
        }

        const orgs = await response.json();
        const org = orgs.find((o: any) => o.id === org_id);

        if (!org) {
          throw new Error(`Organization not found: ${org_id}`);
        }

        return {
          contents: [
            {
              uri: `organization://${org_id}`,
              mimeType: 'application/json',
              text: JSON.stringify(org, null, 2),
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to read organization resource: ${error instanceof Error ? error.message : String(error)}`
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
