/**
 * Integration Tools for MCP Server
 * ---------------------------------
 * Dynamically loads tools from MCP Integration Gateway manifest.
 * Proxies tool calls to n8n workflows via the gateway.
 *
 * This preserves your excellent manifest-driven n8n integration pattern!
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

interface ToolManifest {
  toolName: string;
  displayName: string;
  description: string;
  category: string;
  inputSchema: any;
  outputSchema: any;
  examples: any[];
}

/**
 * Register integration tools dynamically from gateway manifest
 */
export async function registerIntegrationTools(server: Server) {
  try {
    // Fetch tool catalog from integration gateway
    const gatewayUrl = getServiceUrl('mcpGateway');
    const response = await fetch(`${gatewayUrl}/tools`);

    if (!response.ok) {
      console.error('Failed to load integration tools from gateway');
      return;
    }

    const catalog = await response.json();
    const tools: ToolManifest[] = catalog.items || [];

    console.error(`  → Loaded ${tools.length} integration tools from gateway`);

    // Register each tool from manifest
    const currentHandler = server.requestHandlers.get('tools/call');

    server.setRequestHandler('tools/call', async (request) => {
      const toolName = request.params.name;

      // Check if this is an integration tool
      const tool = tools.find((t) => t.toolName === toolName);

      if (tool) {
        try {
          // Proxy to integration gateway
          const invokeUrl = `${gatewayUrl}/tools/${toolName}/invoke`;
          const invokeResponse = await fetch(invokeUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request.params.arguments || {}),
          });

          if (!invokeResponse.ok) {
            const error = await invokeResponse.text();
            throw new Error(`Tool invocation failed: ${error}`);
          }

          const result = await invokeResponse.json();

          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(result, null, 2),
              },
            ],
            isError: false,
          };
        } catch (error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error invoking ${toolName}: ${error instanceof Error ? error.message : String(error)}`,
              },
            ],
            isError: true,
          };
        }
      }

      // Not an integration tool, delegate to other handlers
      if (currentHandler) {
        return await currentHandler(request);
      }

      return {
        content: [
          {
            type: 'text',
            text: `Unknown tool: ${toolName}`,
          },
        ],
        isError: true,
      };
    });

    // Add integration tools to tool list
    const currentListHandler = server.requestHandlers.get('tools/list');

    server.setRequestHandler('tools/list', async (request) => {
      const existingTools = currentListHandler ? await currentListHandler(request) : { tools: [] };

      const integrationTools = tools.map((tool) => ({
        name: tool.toolName,
        description: tool.description,
        inputSchema: tool.inputSchema,
      }));

      return {
        tools: [...(existingTools.tools || []), ...integrationTools],
      };
    });
  } catch (error) {
    console.error('Failed to register integration tools:', error);
  }
}
