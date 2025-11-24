# Agent Foundry MCP Server

Official Model Context Protocol server for Agent Foundry using
`@modelcontextprotocol/sdk`.

## Features

### ✅ Tools (10+)

- **Agent Tools**: Execute, list, create, deploy agents
- **Integration Tools**: Dynamic loading from n8n gateway manifest
- **Data Tools**: Natural language database queries

### ✅ Resources (NEW!)

- `agent://{agent_id}` - Agent configuration
- `agent://{agent_id}/graph` - Visual graph for Forge
- `domain://{domain_id}` - Domain metadata
- `organization://{org_id}` - Organization settings

### ✅ Prompts (NEW!)

- `create_agent_from_requirements` - Design agents from NL
- `refactor_agent_workflow` - Optimize workflows
- `debug_agent_error` - Analyze and fix errors
- `analyze_performance` - Performance optimization

### ✅ Transports

- **stdio**: For Cursor, Claude Desktop (default)
- **SSE**: For web clients (port 3100)

## Quick Start

### 1. Install Dependencies

```bash
cd mcp-server
npm install
```

### 2. Build

```bash
npm run build
```

### 3. Run

```bash
# stdio (for Cursor/Claude Desktop)
npm start

# SSE (for web clients)
npm run start:sse
```

## Integration

### Cursor

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
        "BACKEND_PORT": "8000"
      }
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agent-foundry": {
      "command": "node",
      "args": ["/absolute/path/to/agentfoundry/mcp-server/dist/index.js"],
      "env": {
        "SVC_BACKEND_HOST": "localhost",
        "BACKEND_PORT": "8000"
      }
    }
  }
}
```

### Docker Compose

Already configured! Just run:

```bash
docker-compose up -d mcp-server
```

## Usage Examples

### Execute an Agent

```
Use tool: agent_execute
Arguments:
  agent_id: "cibc-card-activation"
  input: "I want to activate my new credit card"
  session_id: "session-123"
```

### List Agents

```
Use tool: agent_list
Arguments:
  organization_id: "acme-corp"
  domain_id: "card-services"
```

### Get Agent Configuration

```
Read resource: agent://cibc-card-activation
```

### Design New Agent

```
Use prompt: create_agent_from_requirements
Arguments:
  requirements: "Create a customer support agent that handles refund requests"
  domain: "customer-service"
```

### Debug Agent Error

```
Use prompt: debug_agent_error
Arguments:
  agent_id: "my-agent"
  error_message: "KeyError: 'messages'"
  session_id: "session-456"
```

## Architecture

### Service Discovery

The MCP server uses Agent Foundry's Infrastructure as Registry pattern:

```typescript
// Automatically resolves to:
// Development: http://foundry-backend:8080
// Production: Same! (K8s service names)

import { SERVICES } from './config/services';
const url = SERVICES.backend; // http://foundry-backend:8080
```

### Integration with Other Systems

```
MCP Server (TypeScript)
  ↓ Service Discovery
  ├─→ Foundry Backend:8080 (Agent execution, OpenFGA auth)
  ├─→ MCP Integration Gateway:8080 (n8n proxy)
  ├─→ OpenFGA:8081 (Authorization - future)
  └─→ LocalStack:4566 (Secrets via backend)
```

## Development

### Watch Mode

```bash
npm run dev
```

### Type Check

```bash
npm run typecheck
```

### Inspect Tools

```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/inspector

# Inspect server
npm run inspect
```

## Tools Reference

| Tool                | Description           | Arguments                                     |
| ------------------- | --------------------- | --------------------------------------------- |
| `agent_list`        | List agents           | organization_id?, domain_id?, environment?    |
| `agent_get`         | Get agent details     | agent_id                                      |
| `agent_execute`     | Execute agent         | agent_id, input, session_id?                  |
| `agent_create`      | Create agent in Forge | name, description, domain_id, organization_id |
| `agent_deploy`      | Deploy to production  | graph_id                                      |
| `data_query`        | NL database query     | question                                      |
| `organization_list` | List orgs             | -                                             |
| `{integration}.*`   | n8n tools             | Dynamic from manifest                         |

## Resources Reference

| URI Pattern           | Description         |
| --------------------- | ------------------- |
| `agent://{id}`        | Agent configuration |
| `agent://{id}/graph`  | Visual graph JSON   |
| `domain://{id}`       | Domain metadata     |
| `organization://{id}` | Org settings        |

## Prompts Reference

| Prompt                           | Description          | Arguments                            |
| -------------------------------- | -------------------- | ------------------------------------ |
| `create_agent_from_requirements` | Design agent from NL | requirements, domain?                |
| `refactor_agent_workflow`        | Optimize workflow    | agent_id, improvement_goals?         |
| `debug_agent_error`              | Fix errors           | agent_id, error_message, session_id? |
| `analyze_performance`            | Performance analysis | agent_id, session_id?                |

## Environment Variables

| Variable               | Default           | Description             |
| ---------------------- | ----------------- | ----------------------- |
| `SVC_BACKEND_HOST`     | `foundry-backend` | Backend DNS name        |
| `SVC_MCP_HOST`         | `mcp-integration` | Integration gateway DNS |
| `BACKEND_PORT`         | `8080`            | Backend port            |
| `MCP_INTEGRATION_PORT` | `8080`            | Gateway port            |
| `ENVIRONMENT`          | `development`     | Environment             |

## Troubleshooting

### Server Won't Start

```bash
# Check dependencies
npm install

# Check build
npm run build

# Check TypeScript
npm run typecheck
```

### Can't Connect from Cursor

1. Verify server is built: `npm run build`
2. Check config path in `~/.cursor/mcp.json`
3. Restart Cursor
4. Check Cursor logs: View → Output → MCP

### Tools Not Working

```bash
# Test backend is reachable
curl http://localhost:8000/health

# Test integration gateway
curl http://localhost:8100/health

# Check MCP server logs
docker-compose logs mcp-server
```

## Migration from Legacy

If you have the old `mcp_server.py`:

1. This replaces it entirely
2. Old REST endpoints → MCP protocol
3. Integration gateway stays (reused!)
4. Update client code to use MCP SDK

See `/docs/MCP_SDK_MIGRATION_PLAN.md` for details.

---

**Status:** ✅ Production Ready  
**Protocol:** MCP (JSON-RPC 2.0)  
**SDK Version:** @modelcontextprotocol/sdk ^1.22.0  
**Compatibility:** Cursor, Claude Desktop, Custom Clients
