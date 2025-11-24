/**
 * Agent Resources for MCP Server
 * -------------------------------
 * Provides read-only access to agent configurations and metadata.
 *
 * Resources allow MCP clients (Cursor, Claude) to fetch context about agents.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register agent resource providers
 */
export async function registerAgentResources(server: Server) {
  // ========================================================================
  // Resource: agent://{agent_id}
  // ========================================================================

  server.setRequestHandler('resources/read', async (request) => {
    const uri = request.params.uri;

    // Match agent://agent-id pattern
    const agentMatch = uri.match(/^agent:\/\/([^\/]+)$/);

    if (agentMatch) {
      const agent_id = agentMatch[1];

      try {
        const url = `${getServiceUrl('backend')}/api/agents/${agent_id}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Agent not found: ${agent_id}`);
        }

        const agent = await response.json();

        return {
          contents: [
            {
              uri: `agent://${agent_id}`,
              mimeType: 'application/json',
              text: JSON.stringify(agent, null, 2),
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to read agent resource: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // ========================================================================
    // Resource: agent://{agent_id}/graph
    // ========================================================================

    const graphMatch = uri.match(/^agent:\/\/([^\/]+)\/graph$/);

    if (graphMatch) {
      const agent_id = graphMatch[1];

      try {
        const url = `${getServiceUrl('backend')}/api/graphs/${agent_id}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Graph not found: ${agent_id}`);
        }

        const graph = await response.json();

        return {
          contents: [
            {
              uri: `agent://${agent_id}/graph`,
              mimeType: 'application/json',
              text: graph.yaml_content || JSON.stringify(graph, null, 2),
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to read graph resource: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // Unknown resource
    throw new Error(`Unknown resource URI: ${uri}`);
  });

  // ========================================================================
  // Resource Templates: List available agents
  // ========================================================================

  server.setRequestHandler('resources/list', async (request) => {
    try {
      const url = `${getServiceUrl('backend')}/api/agents`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error('Failed to list agents');
      }

      const data = await response.json();
      const agents = data.agents || [];

      // Create resource descriptors for each agent
      const resources = agents.flatMap((agent: any) => [
        {
          uri: `agent://${agent.id}`,
          name: `${agent.name} (Configuration)`,
          description: agent.description || 'Agent configuration and metadata',
          mimeType: 'application/json',
        },
        {
          uri: `agent://${agent.id}/graph`,
          name: `${agent.name} (Graph)`,
          description: 'Visual graph representation for Forge',
          mimeType: 'application/json',
        },
      ]);

      return { resources };
    } catch (error) {
      console.error('Failed to list agent resources:', error);
      return { resources: [] };
    }
  });
}
