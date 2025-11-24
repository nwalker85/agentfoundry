#!/usr/bin/env node

/**
 * Agent Foundry MCP Server
 * -------------------------
 * Official Model Context Protocol server using @modelcontextprotocol/sdk
 *
 * Features:
 * - Tools: Agent execution, data queries, integration tools
 * - Resources: Agent configs, domain metadata, org settings
 * - Prompts: Agent design templates, debugging, testing
 * - Transports: stdio (Cursor/Claude) and SSE (web clients)
 *
 * Usage:
 *   node dist/index.js              # stdio (for Cursor/Claude)
 *   node dist/index.js --transport sse --port 3100  # SSE for web
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

// Import tool registrations
import { registerAgentTools } from './tools/agents.js';
import { registerIntegrationTools } from './tools/integrations.js';
import { registerDataTools } from './tools/data.js';

// Import resource registrations
import { registerAgentResources } from './resources/agents.js';
import { registerDomainResources } from './resources/domains.js';
import { registerOrganizationResources } from './resources/organizations.js';

// Import prompt registrations
import { registerAgentPrompts } from './prompts/agent-design.js';
import { registerDebugPrompts } from './prompts/debugging.js';

// Parse command line arguments
const args = process.argv.slice(2);
const transportFlag = args.indexOf('--transport');
const portFlag = args.indexOf('--port');

const transport = transportFlag >= 0 ? args[transportFlag + 1] : 'stdio';
const port = portFlag >= 0 ? parseInt(args[portFlag + 1], 10) : 3100;

/**
 * Initialize MCP server
 */
async function main() {
  console.error('🚀 Agent Foundry MCP Server');
  console.error('============================');
  console.error(`Transport: ${transport}`);
  console.error(`Environment: ${process.env.ENVIRONMENT || 'development'}`);
  console.error('');

  // Create server instance
  const server = new Server(
    {
      name: 'agent-foundry',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
        resources: {},
        prompts: {},
      },
    }
  );

  // Register error handlers
  server.onerror = (error) => {
    console.error('[MCP Error]', error);
  };

  process.on('SIGINT', async () => {
    console.error('\n🛑 Shutting down MCP server...');
    await server.close();
    process.exit(0);
  });

  // ========================================================================
  // REGISTER TOOLS
  // ========================================================================

  console.error('📦 Registering tools...');

  try {
    await registerAgentTools(server);
    console.error('  ✓ Agent tools registered');
  } catch (error) {
    console.error('  ✗ Agent tools failed:', error);
  }

  try {
    await registerIntegrationTools(server);
    console.error('  ✓ Integration tools registered');
  } catch (error) {
    console.error('  ✗ Integration tools failed:', error);
  }

  try {
    await registerDataTools(server);
    console.error('  ✓ Data tools registered');
  } catch (error) {
    console.error('  ✗ Data tools failed:', error);
  }

  // ========================================================================
  // REGISTER RESOURCES
  // ========================================================================

  console.error('📚 Registering resources...');

  try {
    await registerAgentResources(server);
    console.error('  ✓ Agent resources registered');
  } catch (error) {
    console.error('  ✗ Agent resources failed:', error);
  }

  try {
    await registerDomainResources(server);
    console.error('  ✓ Domain resources registered');
  } catch (error) {
    console.error('  ✗ Domain resources failed:', error);
  }

  try {
    await registerOrganizationResources(server);
    console.error('  ✓ Organization resources registered');
  } catch (error) {
    console.error('  ✗ Organization resources failed:', error);
  }

  // ========================================================================
  // REGISTER PROMPTS
  // ========================================================================

  console.error('💡 Registering prompts...');

  try {
    await registerAgentPrompts(server);
    console.error('  ✓ Agent design prompts registered');
  } catch (error) {
    console.error('  ✗ Agent prompts failed:', error);
  }

  try {
    await registerDebugPrompts(server);
    console.error('  ✓ Debugging prompts registered');
  } catch (error) {
    console.error('  ✗ Debug prompts failed:', error);
  }

  // ========================================================================
  // START TRANSPORT
  // ========================================================================

  console.error('');
  console.error('🌐 Starting transport...');

  let serverTransport;

  if (transport === 'sse') {
    // SSE transport for web clients
    serverTransport = new SSEServerTransport('/messages', server);
    await serverTransport.start();
    console.error(`✅ MCP server running on SSE at http://localhost:${port}/messages`);
    console.error('');
    console.error('Connect via:');
    console.error(`  curl http://localhost:${port}/messages`);
  } else {
    // stdio transport for Cursor/Claude Desktop
    serverTransport = new StdioServerTransport();
    console.error('✅ MCP server running on stdio');
    console.error('');
    console.error('Connect via Cursor config:');
    console.error('  ~/.cursor/mcp.json');
  }

  await server.connect(serverTransport);
}

// Start server
main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
