# Official MCP Server Setup Guide

## Overview

Agent Foundry now has an **official MCP server** using
`@modelcontextprotocol/sdk`. This replaces the custom REST API with proper Model
Context Protocol support.

## What You Get

### 1. Real MCP Protocol ✅

- JSON-RPC 2.0 standard
- stdio and SSE transports
- Compatible with Cursor, Claude Desktop
- Discoverable by MCP clients

### 2. 10+ Tools

- Execute agents
- List/create/deploy agents
- Data queries (NL → SQL)
- Integration tools (from n8n gateway)

### 3. Resources (NEW!)

- `agent://{id}` - Fetch agent configs
- `domain://{id}` - Domain metadata
- `organization://{id}` - Org settings

### 4. Prompts (NEW!)

- Design agents from requirements
- Debug errors with context
- Refactor workflows
- Analyze performance

## 10-Minute Setup

### Step 1: Install & Build

```bash
cd mcp-server
npm install
npm run build
```

### Step 2: Configure Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "agent-foundry": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/Users/nwalker/Development/Projects/agentfoundry/mcp-server",
      "env": {
        "SVC_BACKEND_HOST": "localhost",
        "BACKEND_PORT": "8000",
        "SVC_MCP_HOST": "localhost",
        "MCP_INTEGRATION_PORT": "8100"
      }
    }
  }
}
```

### Step 3: Restart Cursor

```bash
# Restart Cursor completely
# CMD+Q → Reopen
```

### Step 4: Test

In Cursor chat:

```
@agent-foundry List all agents
```

Or:

```
Use the agent_list tool to show me available agents
```

## Usage in Cursor

### Execute an Agent

```
Use agent_execute to run the "cibc-card-activation" agent with input "I want to activate my card"
```

### Get Agent Configuration

```
Read the resource agent://cibc-card-activation
```

### Design New Agent

```
Use the create_agent_from_requirements prompt with:
- requirements: "Create a customer support agent"
- domain: "customer-service"
```

### Debug Agent

```
Use debug_agent_error prompt to analyze error "KeyError: messages" in agent "my-agent"
```

## Docker Usage

### Start MCP Server

```bash
docker-compose up -d mcp-server
```

### View Logs

```bash
docker-compose logs -f mcp-server
```

### Rebuild After Changes

```bash
docker-compose build mcp-server
docker-compose restart mcp-server
```

## Integration with Architecture

### Service Discovery

```typescript
// MCP server uses same pattern as all services
SERVICES.backend       → http://foundry-backend:8080
SERVICES.mcpGateway   → http://mcp-integration:8080
SERVICES.openfga      → http://openfga:8081
```

### OpenFGA Authorization

Tools check permissions via backend (which uses OpenFGA):

```typescript
// Backend validates:
// 1. JWT token (user identity)
// 2. OpenFGA check (can user execute agent?)
// 3. Execute agent
// 4. Return result
```

### LocalStack Secrets

Secrets are retrieved by backend (MCP server never sees them):

```typescript
// MCP server: Execute agent
//   ↓
// Backend: Get secret from LocalStack for this org
//   ↓
// Backend: Execute agent with secret
//   ↓
// MCP server: Return result (NOT the secret)
```

## Advanced Usage

### SSE Transport (Web Clients)

```bash
# Start with SSE
node dist/index.js --transport sse --port 3100

# Connect
curl http://localhost:3100/messages
```

### Custom Client

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const transport = new StdioClientTransport({
  command: 'node',
  args: ['dist/index.js'],
  cwd: '/path/to/mcp-server',
});

const client = new Client(
  {
    name: 'my-client',
    version: '1.0.0',
  },
  {
    capabilities: {},
  }
);

await client.connect(transport);

// List tools
const tools = await client.listTools();

// Call tool
const result = await client.callTool({
  name: 'agent_list',
  arguments: {},
});
```

## Troubleshooting

### Cursor Can't Find Server

1. Check path in `mcp.json` is absolute
2. Verify built: `ls mcp-server/dist/index.js`
3. Check Cursor logs: View → Output → MCP
4. Restart Cursor completely

### Tools Return Errors

```bash
# Check backend is running
curl http://localhost:8000/health

# Check integration gateway
curl http://localhost:8100/health

# Test tool manually
node dist/index.js << EOF
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "agent_list",
    "arguments": {}
  }
}
EOF
```

### Resources Not Loading

```bash
# Test resource fetch
curl http://localhost:8000/api/agents/test-agent

# Check MCP server has access
docker-compose exec mcp-server curl http://foundry-backend:8080/health
```

## Complete Feature Matrix

| Feature               | Legacy mcp_server.py | New MCP Server         |
| --------------------- | -------------------- | ---------------------- |
| **Protocol**          | ❌ Custom REST       | ✅ MCP (JSON-RPC 2.0)  |
| **Cursor Support**    | ❌ No                | ✅ Yes                 |
| **Claude Desktop**    | ❌ No                | ✅ Yes                 |
| **Tools**             | ✅ Custom            | ✅ MCP Standard        |
| **Resources**         | ❌ No                | ✅ Yes                 |
| **Prompts**           | ❌ No                | ✅ Yes                 |
| **Transport**         | REST only            | ✅ stdio + SSE         |
| **Service Discovery** | ⚠️ Partial           | ✅ Full                |
| **n8n Integration**   | ✅ Via gateway       | ✅ Via gateway (kept!) |

## Next Steps

1. **Configure Cursor**: Add to `~/.cursor/mcp.json`
2. **Test Tools**: Try `agent_list` in Cursor
3. **Use Resources**: Fetch agent configs
4. **Try Prompts**: Design an agent
5. **Explore n8n Tools**: Use integration tools

## Documentation

- **Architecture**: `/docs/MCP_SDK_MIGRATION_PLAN.md`
- **API Reference**: Run `npm run inspect`
- **Examples**: See `/docs/MCP_SERVER_USAGE_EXAMPLES.md`
- **Troubleshooting**: See troubleshooting section above

---

**Status:** ✅ Ready for Use  
**Version:** 1.0.0  
**Protocol:** Model Context Protocol  
**SDK:** @modelcontextprotocol/sdk ^1.22.0
