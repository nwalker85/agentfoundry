/**
 * Data & Admin Tools for MCP Server
 * ----------------------------------
 * Tools for querying control-plane data and admin operations.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register data and admin tools
 */
export async function registerDataTools(server: Server) {
  const currentHandler = server.requestHandlers.get('tools/call');

  server.setRequestHandler('tools/call', async (request) => {
    // ========================================================================
    // Tool: data_query
    // ========================================================================

    if (request.params.name === 'data_query') {
      const { question } = (request.params.arguments as any) || {};

      if (!question) {
        return {
          content: [
            {
              type: 'text',
              text: 'Error: question is required',
            },
          ],
          isError: true,
        };
      }

      try {
        const url = `${getServiceUrl('backend')}/api/control/query`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
        });

        if (!response.ok) {
          throw new Error(`Data query failed: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.error) {
          return {
            content: [
              {
                type: 'text',
                text: `Query error: ${result.error}\n\nGenerated SQL:\n${result.sql || 'N/A'}`,
              },
            ],
            isError: true,
          };
        }

        const rows = result.rows || [];
        const formattedResult = `SQL Query:\n${result.sql}\n\nResults (${rows.length} rows):\n${JSON.stringify(rows, null, 2)}`;

        return {
          content: [
            {
              type: 'text',
              text: formattedResult,
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error querying data: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // ========================================================================
    // Tool: organization_list
    // ========================================================================

    if (request.params.name === 'organization_list') {
      try {
        const url = `${getServiceUrl('backend')}/api/control/organizations`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to list organizations: ${response.statusText}`);
        }

        const orgs = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(orgs, null, 2),
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error listing organizations: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // Delegate to existing handler
    if (currentHandler) {
      return await currentHandler(request);
    }

    return {
      content: [
        {
          type: 'text',
          text: `Unknown tool: ${request.params.name}`,
        },
      ],
      isError: true,
    };
  });

  // Add to tool list
  const currentListHandler = server.requestHandlers.get('tools/list');

  server.setRequestHandler('tools/list', async (request) => {
    const existingTools = currentListHandler ? await currentListHandler(request) : { tools: [] };

    const dataTools = [
      {
        name: 'data_query',
        description:
          'Query control-plane database using natural language. Converts your question to SQL and executes it.',
        inputSchema: {
          type: 'object',
          properties: {
            question: {
              type: 'string',
              description:
                'Natural language question about organizations, domains, instances, deployments, or users',
            },
          },
          required: ['question'],
        },
      },
      {
        name: 'organization_list',
        description: 'List all organizations with their domains',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
    ];

    return {
      tools: [...(existingTools.tools || []), ...dataTools],
    };
  });
}
