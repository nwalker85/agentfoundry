#!/usr/bin/env node

/**
 * Simplified MCP Server for Agent Foundry
 * ----------------------------------------
 * Minimal working example using @modelcontextprotocol/sdk
 *
 * This is a simplified version that works while the full implementation
 * is being completed. It demonstrates the core MCP protocol.
 *
 * Usage:
 *   npx tsx src/simple-server.ts
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

// Get service URL
const BACKEND_URL = process.env.SVC_BACKEND_HOST
  ? `http://${process.env.SVC_BACKEND_HOST}:${process.env.BACKEND_PORT || '8080'}`
  : 'http://localhost:8000';

console.error('🚀 Agent Foundry MCP Server (Simplified)');
console.error(`Backend: ${BACKEND_URL}`);
console.error('');

// Create server
const server = new Server(
  {
    name: 'agent-foundry',
    version: '1.0.0-simple',
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// Request handler for tools
server.setRequestHandler('tools/call', async (request) => {
  const toolName = (request.params as any)?.name;
  const args = (request.params as any)?.arguments || {};

  try {
    switch (toolName) {
      case 'agent_list': {
        const response = await fetch(`${BACKEND_URL}/api/agents`);
        const data: any = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(data.agents, null, 2),
            },
          ],
        };
      }

      case 'agent_execute': {
        const { agent_id, input, session_id } = args;

        if (!agent_id || !input) {
          throw new Error('agent_id and input are required');
        }

        const response = await fetch(`${BACKEND_URL}/api/agent/invoke`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id,
            input,
            session_id: session_id || `mcp-${Date.now()}`,
            route_via_supervisor: true,
          }),
        });

        const result: any = await response.json();

        return {
          content: [
            {
              type: 'text',
              text: result.output || 'Agent executed successfully',
            },
          ],
          isError: result.error ? true : false,
        };
      }

      case 'data_query': {
        const { question } = args;

        if (!question) {
          throw new Error('question is required');
        }

        const response = await fetch(`${BACKEND_URL}/api/control/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question }),
        });

        const result: any = await response.json();

        if (result.error) {
          return {
            content: [
              {
                type: 'text',
                text: `Error: ${result.error}\n\nSQL: ${result.sql || 'N/A'}`,
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: 'text',
              text: `SQL: ${result.sql}\n\nResults:\n${JSON.stringify(result.rows, null, 2)}`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${toolName}`);
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error instanceof Error ? error.message : String(error)}`,
        },
      ],
      isError: true,
    };
  }
});

// Tool list handler
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'agent_list',
        description: 'List all available LangGraph agents',
        inputSchema: {
          type: 'object',
          properties: {},
        },
      },
      {
        name: 'agent_execute',
        description: 'Execute a LangGraph agent with user input',
        inputSchema: {
          type: 'object',
          properties: {
            agent_id: { type: 'string', description: 'Agent ID' },
            input: { type: 'string', description: 'User input' },
            session_id: { type: 'string', description: 'Session ID (optional)' },
          },
          required: ['agent_id', 'input'],
        },
      },
      {
        name: 'data_query',
        description: 'Query control-plane database using natural language',
        inputSchema: {
          type: 'object',
          properties: {
            question: { type: 'string', description: 'Natural language question' },
          },
          required: ['question'],
        },
      },
    ],
  };
});

// Resource handler
server.setRequestHandler('resources/read', async (request) => {
  const uri = (request.params as any)?.uri;

  // agent://agent-id
  const agentMatch = uri?.match(/^agent:\/\/([^\/]+)$/);
  if (agentMatch) {
    const agent_id = agentMatch[1];
    const response = await fetch(`${BACKEND_URL}/api/agents/${agent_id}`);
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
  }

  throw new Error(`Unknown resource: ${uri}`);
});

// Resource list handler
server.setRequestHandler('resources/list', async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/api/agents`);
    const data: any = await response.json();
    const agents = data.agents || [];

    return {
      resources: agents.map((agent: any) => ({
        uri: `agent://${agent.id}`,
        name: agent.name,
        description: agent.description || 'Agent configuration',
        mimeType: 'application/json',
      })),
    };
  } catch (error) {
    return { resources: [] };
  }
});

// Connect with stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);

console.error('✅ MCP server connected via stdio');
console.error('Ready for Cursor/Claude Desktop!');
