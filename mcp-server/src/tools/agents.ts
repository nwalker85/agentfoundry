/**
 * Agent Tools for MCP Server
 * ---------------------------
 * Tools for interacting with LangGraph agents via Foundry Backend API.
 *
 * All tools use service discovery to call foundry-backend:8080
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { z } from 'zod';
import { buildServiceUrl, getServiceUrl } from '../config/services.js';

/**
 * Register all agent-related MCP tools
 */
export async function registerAgentTools(server: Server) {
  // ========================================================================
  // Tool: agent_list
  // ========================================================================

  server.setRequestHandler('tools/call', async (request) => {
    if (request.params.name === 'agent_list') {
      const { organization_id, domain_id, environment } = (request.params.arguments as any) || {};

      try {
        const params: Record<string, string> = {};
        if (organization_id) params.organization_id = organization_id;
        if (domain_id) params.domain_id = domain_id;
        if (environment) params.environment = environment;

        const url = buildServiceUrl('backend', '/api/agents', params);
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to list agents: ${response.statusText}`);
        }

        const data = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(data.agents, null, 2),
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error listing agents: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // ========================================================================
    // Tool: agent_get
    // ========================================================================

    if (request.params.name === 'agent_get') {
      const { agent_id } = (request.params.arguments as any) || {};

      if (!agent_id) {
        return {
          content: [
            {
              type: 'text',
              text: 'Error: agent_id is required',
            },
          ],
          isError: true,
        };
      }

      try {
        const url = `${getServiceUrl('backend')}/api/agents/${agent_id}`;
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to get agent: ${response.statusText}`);
        }

        const agent = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(agent, null, 2),
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error getting agent: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // ========================================================================
    // Tool: agent_execute
    // ========================================================================

    if (request.params.name === 'agent_execute') {
      const { agent_id, input, session_id } = (request.params.arguments as any) || {};

      if (!agent_id || !input) {
        return {
          content: [
            {
              type: 'text',
              text: 'Error: agent_id and input are required',
            },
          ],
          isError: true,
        };
      }

      try {
        const url = `${getServiceUrl('backend')}/api/agent/invoke`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id,
            input,
            session_id: session_id || `mcp-${Date.now()}`,
            route_via_supervisor: true,
          }),
        });

        if (!response.ok) {
          throw new Error(`Agent execution failed: ${response.statusText}`);
        }

        const result = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: result.output || 'Agent executed successfully',
            },
          ],
          isError: result.error ? true : false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing agent: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // ========================================================================
    // Tool: agent_create
    // ========================================================================

    if (request.params.name === 'agent_create') {
      const { name, description, domain_id, organization_id } =
        (request.params.arguments as any) || {};

      if (!name || !domain_id || !organization_id) {
        return {
          content: [
            {
              type: 'text',
              text: 'Error: name, domain_id, and organization_id are required',
            },
          ],
          isError: true,
        };
      }

      try {
        const url = `${getServiceUrl('backend')}/api/graphs`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            metadata: {
              name,
              description: description || '',
              type: 'user',
              domain_id,
              organization_id,
              version: '1.0.0',
            },
            spec: {
              graph: {
                nodes: [],
                edges: [],
              },
            },
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to create agent: ${response.statusText}`);
        }

        const agent = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: `Agent created successfully!\n\nID: ${agent.id}\nName: ${name}\nDesign it in Forge: http://localhost:3000/forge/${agent.id}`,
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error creating agent: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // ========================================================================
    // Tool: agent_deploy
    // ========================================================================

    if (request.params.name === 'agent_deploy') {
      const { graph_id } = (request.params.arguments as any) || {};

      if (!graph_id) {
        return {
          content: [
            {
              type: 'text',
              text: 'Error: graph_id is required',
            },
          ],
          isError: true,
        };
      }

      try {
        const url = `${getServiceUrl('backend')}/api/graphs/${graph_id}/deploy`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
          throw new Error(`Deployment failed: ${response.statusText}`);
        }

        const result = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: `Agent deployed successfully!\n\n${result.message}\nAgent ID: ${result.agent_id}\nDeployed at: ${result.deployed_at}`,
            },
          ],
          isError: false,
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error deploying agent: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
          isError: true,
        };
      }
    }

    // Unknown tool
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

  // Register tool list handler
  const currentToolsHandler = server.requestHandlers.get('tools/list');

  server.setRequestHandler('tools/list', async (request) => {
    const existingTools = currentToolsHandler ? await currentToolsHandler(request) : { tools: [] };

    const agentTools = [
      {
        name: 'agent_list',
        description:
          'List all available LangGraph agents. Optionally filter by organization, domain, or environment.',
        inputSchema: {
          type: 'object',
          properties: {
            organization_id: {
              type: 'string',
              description: 'Filter by organization ID',
            },
            domain_id: {
              type: 'string',
              description: 'Filter by domain ID',
            },
            environment: {
              type: 'string',
              description: 'Filter by environment (dev, staging, prod)',
              enum: ['dev', 'staging', 'prod'],
            },
          },
        },
      },
      {
        name: 'agent_get',
        description:
          'Get detailed information about a specific agent including configuration, workflow, and metrics.',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: {
              type: 'string',
              description: 'Agent ID (e.g., "cibc-card-activation")',
            },
          },
          required: ['agent_id'],
        },
      },
      {
        name: 'agent_execute',
        description:
          'Execute a LangGraph agent with user input. The agent processes the input through its workflow and returns a response.',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: {
              type: 'string',
              description: 'Agent ID to execute',
            },
            input: {
              type: 'string',
              description: 'User input to process',
            },
            session_id: {
              type: 'string',
              description: 'Optional session ID for state persistence',
            },
          },
          required: ['agent_id', 'input'],
        },
      },
      {
        name: 'agent_create',
        description:
          'Create a new agent in Forge (visual designer). Creates an empty agent ready for design.',
        inputSchema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'Agent name',
            },
            description: {
              type: 'string',
              description: 'Agent description',
            },
            domain_id: {
              type: 'string',
              description: 'Domain ID this agent belongs to',
            },
            organization_id: {
              type: 'string',
              description: 'Organization ID',
            },
          },
          required: ['name', 'domain_id', 'organization_id'],
        },
      },
      {
        name: 'agent_deploy',
        description:
          'Deploy an agent from Forge to production. Generates Python code and YAML configuration.',
        inputSchema: {
          type: 'object',
          properties: {
            graph_id: {
              type: 'string',
              description: 'Graph/Agent ID to deploy',
            },
          },
          required: ['graph_id'],
        },
      },
    ];

    return {
      tools: [...(existingTools.tools || []), ...agentTools],
    };
  });
}
