# MCP SDK Migration Plan

## Executive Summary

Migrate Agent Foundry from custom REST-based "MCP" implementation to official
`@modelcontextprotocol/sdk`. This enables compatibility with Cursor, Claude
Desktop, and other MCP clients while maintaining the excellent n8n integration
gateway pattern.

**Timeline:** 2-3 days  
**Risk:** Low (parallel run strategy)  
**Status:** SDK already installed, ready to use

## Current vs Target

### Current Architecture (Custom)

```
┌──────────────┐
│ mcp_server.py│ ❌ Custom FastAPI REST API
│ (Port 8001)  │ ❌ Not real MCP protocol
└──────┬───────┘
       │ Direct API calls
┌──────▼───────┐
│ Notion/GitHub│ ❌ Hard to maintain
│ Direct APIs  │ ❌ No schema validation
└──────────────┘
```

### Target Architecture (Official SDK)

```
┌──────────────────────────────────────────┐
│  Official MCP Server (TypeScript)        │ ✅ Real MCP protocol
│  @modelcontextprotocol/sdk               │ ✅ stdio/SSE transport
│  Port: stdio (Cursor) or 3100 (SSE)      │ ✅ Discoverable
└────────────┬──────────────────────────────┘
             │ HTTP to backend (service discovery)
┌────────────▼─────────────────────────────┐
│  Foundry Backend (FastAPI)               │ ✅ OpenFGA auth
│  http://foundry-backend:8080             │ ✅ LocalStack secrets
└────────────┬─────────────────────────────┘
             │ (Optional: For n8n tools)
┌────────────▼─────────────────────────────┐
│  MCP Integration Gateway (FastAPI)        │ ✅ Keep this!
│  http://mcp-integration:8080             │ ✅ Manifest-driven
└────────────┬─────────────────────────────┘
             │
┌────────────▼─────────────────────────────┐
│  n8n Workflows                            │ ✅ Keep this!
└───────────────────────────────────────────┘
```

## Migration Phases

### Phase 1: Setup Official MCP Server (Day 1, 3-4 hours)

#### 1.1 Create MCP Server Package

```bash
# Create new MCP server directory
mkdir -p mcp-server/src/{tools,resources,prompts,config}

# Initialize package.json
cd mcp-server
npm init -y
```

#### 1.2 Install Dependencies

```bash
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node tsx
```

#### 1.3 Configure TypeScript

Create `mcp-server/tsconfig.json`

#### 1.4 Create Server Entry Point

Create `mcp-server/src/index.ts` with:

- Server initialization
- Transport setup (stdio + SSE)
- Service discovery integration
- Error handling

#### 1.5 Add to Docker Compose

```yaml
mcp-server:
  build:
    context: ./mcp-server
    dockerfile: Dockerfile
  ports:
    - '3100:3100' # SSE transport
  environment:
    - SVC_BACKEND_HOST=foundry-backend
    - SVC_MCP_GATEWAY_HOST=mcp-integration
  networks:
    - foundry
```

**Deliverables:**

- ✅ Working MCP server responding to `tools/list`
- ✅ Docker integration
- ✅ Service discovery configured

### Phase 2: Migrate Core Tools (Day 1-2, 6-8 hours)

#### 2.1 Agent Tools

**Migrate from:** `mcp_server.py` agent endpoints  
**Migrate to:** `mcp-server/src/tools/agents.ts`

**Tools:**

1. `agent_list` - List available agents
2. `agent_get` - Get agent details
3. `agent_execute` - Execute an agent
4. `agent_create` - Create new agent (Forge)
5. `agent_deploy` - Deploy agent to production

#### 2.2 Integration Tools (via Gateway)

**Keep gateway, add MCP wrapper**  
**New file:** `mcp-server/src/tools/integrations.ts`

**Tools:**

1. `notion_create_story` → Calls integration gateway
2. `github_create_issue` → Calls integration gateway
3. `servicenow_create_incident` → Calls integration gateway
4. Dynamic tool loading from manifest

#### 2.3 Data/Admin Tools

**Migrate from:** `mcp/tools/data.py`, `mcp/tools/admin.py`  
**Migrate to:** `mcp-server/src/tools/data.ts`

**Tools:**

1. `data_query` - Natural language database queries
2. `admin_list_orgs` - List organizations
3. `admin_get_domain` - Get domain details

**Deliverables:**

- ✅ 10-15 core tools migrated to SDK
- ✅ Integration gateway still used for n8n tools
- ✅ Type-safe schemas with Zod

### Phase 3: Add Resources (Day 2, 2-3 hours)

**New capability!** MCP resources let clients fetch context.

**Implement:**

1. **Agent Resources** (`mcp-server/src/resources/agents.ts`)

   - `agent://{agent_id}` - YAML configuration
   - `agent://{agent_id}/graph` - ReactFlow graph JSON
   - `agent://{agent_id}/history` - Execution history

2. **Domain Resources** (`mcp-server/src/resources/domains.ts`)

   - `domain://{domain_id}` - Domain metadata
   - `domain://{domain_id}/agents` - List of agents
   - `domain://{domain_id}/secrets` - Secret status (not values!)

3. **Organization Resources** (`mcp-server/src/resources/organizations.ts`)
   - `organization://{org_id}` - Org settings
   - `organization://{org_id}/domains` - List of domains
   - `organization://{org_id}/users` - User list (RBAC filtered)

**Deliverables:**

- ✅ 9-12 resource providers
- ✅ Clients can fetch context without API calls
- ✅ Type-safe resource schemas

### Phase 4: Add Prompts (Day 2, 2 hours)

**New capability!** MCP prompts provide pre-built templates.

**Implement:**

1. **Agent Design Prompts** (`mcp-server/src/prompts/agent-design.ts`)

   - `create_agent_from_requirements`
   - `refactor_agent_workflow`
   - `add_error_handling`

2. **Testing Prompts** (`mcp-server/src/prompts/testing.ts`)

   - `generate_test_cases`
   - `create_integration_test`

3. **Debugging Prompts** (`mcp-server/src/prompts/debugging.ts`)
   - `debug_agent_error`
   - `analyze_performance`

**Deliverables:**

- ✅ 6-8 prompt templates
- ✅ LLMs can use prompts for common tasks
- ✅ Consistent prompt structure

### Phase 5: Testing & Documentation (Day 3, 3-4 hours)

#### 5.1 Test with Cursor

```json
// ~/.cursor/mcp.json (or workspace .cursor/mcp.json)
{
  "mcpServers": {
    "agent-foundry": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/agentfoundry/mcp-server"
    }
  }
}
```

#### 5.2 Test with Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "agent-foundry": {
      "command": "node",
      "args": ["dist/index.js"],
      "cwd": "/path/to/agentfoundry/mcp-server",
      "env": {
        "BACKEND_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### 5.3 Test via HTTP/SSE

```bash
# Start server with SSE transport
node mcp-server/dist/index.js --transport sse --port 3100

# Connect
curl http://localhost:3100/sse

# Send tool list request
# (via SSE client)
```

**Deliverables:**

- ✅ Works with Cursor
- ✅ Works with Claude Desktop
- ✅ Works via SSE for web clients
- ✅ Complete test suite
- ✅ Documentation updated

### Phase 6: Deprecate Legacy (Ongoing)

#### 6.1 Mark as Deprecated

```python
# mcp_server.py
"""
DEPRECATED: This custom MCP server is being replaced by the official
@modelcontextprotocol/sdk implementation in /mcp-server/

For new integrations, use the MCP SDK server.
This server will be removed in v1.0.0.
"""
```

#### 6.2 Update References

- Update docs to point to new server
- Update frontend to use new server (if applicable)
- Remove from startup scripts

#### 6.3 Final Cleanup

```bash
# After 30 days of successful operation:
# 1. Archive old server
mv mcp_server.py archive/mcp_server_legacy.py
mv mcp/tools archive/mcp/tools_legacy

# 2. Update imports
# (Remove old tool imports from codebase)

# 3. Update docker-compose
# (Remove legacy server service if present)
```

## Implementation Details

### Official MCP Server Structure

```typescript
// mcp-server/src/index.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

// Import tool handlers
import { registerAgentTools } from './tools/agents.js';
import { registerIntegrationTools } from './tools/integrations.js';
import { registerDataTools } from './tools/data.js';

// Import resource handlers
import { registerAgentResources } from './resources/agents.js';
import { registerDomainResources } from './resources/domains.js';

// Import prompts
import { registerAgentPrompts } from './prompts/agent-design.js';

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

// Register all tools
registerAgentTools(server);
registerIntegrationTools(server);
registerDataTools(server);

// Register all resources
registerAgentResources(server);
registerDomainResources(server);

// Register prompts
registerAgentPrompts(server);

// Transport selection
const transport = process.argv.includes('--sse')
  ? new SSEServerTransport('/sse', 3100)
  : new StdioServerTransport();

await server.connect(transport);
```

### Tool Handler Example

```typescript
// mcp-server/src/tools/agents.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { z } from 'zod';
import { getServiceUrl } from '../config/services.js';

export function registerAgentTools(server: Server) {
  // Tool 1: Execute Agent
  server.tool(
    'agent_execute',
    'Execute a LangGraph agent with user input',
    {
      agent_id: z.string().describe('Agent ID (e.g., "cibc-card-activation")'),
      input: z.string().describe('User input to process'),
      session_id: z
        .string()
        .optional()
        .describe('Session ID for state persistence'),
    },
    async ({ agent_id, input, session_id }) => {
      const backendUrl = getServiceUrl('backend');

      const response = await fetch(`${backendUrl}/api/agent/invoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id,
          input,
          session_id,
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
            text: result.output,
          },
        ],
        isError: result.error ? true : false,
      };
    }
  );

  // Tool 2: List Agents
  server.tool(
    'agent_list',
    'List all available agents',
    {
      organization_id: z.string().optional(),
      domain_id: z.string().optional(),
    },
    async ({ organization_id, domain_id }) => {
      const backendUrl = getServiceUrl('backend');
      let url = `${backendUrl}/api/agents`;

      const params = new URLSearchParams();
      if (organization_id) params.append('organization_id', organization_id);
      if (domain_id) params.append('domain_id', domain_id);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url);
      const data = await response.json();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(data.agents, null, 2),
          },
        ],
      };
    }
  );

  // Tool 3: Create Agent (Forge)
  server.tool(
    'agent_create',
    'Create a new agent in Forge',
    {
      name: z.string(),
      description: z.string(),
      domain_id: z.string(),
      organization_id: z.string(),
    },
    async ({ name, description, domain_id, organization_id }) => {
      const backendUrl = getServiceUrl('backend');

      const response = await fetch(`${backendUrl}/api/graphs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metadata: {
            name,
            description,
            type: 'user',
            domain_id,
            organization_id,
          },
          spec: {
            graph: { nodes: [], edges: [] },
          },
        }),
      });

      const agent = await response.json();

      return {
        content: [
          {
            type: 'text',
            text: `Agent created: ${agent.id}`,
          },
        ],
      };
    }
  );
}
```

### Resource Provider Example

```typescript
// mcp-server/src/resources/agents.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

export function registerAgentResources(server: Server) {
  // Resource: Agent Configuration
  server.resource(
    'agent://{agent_id}',
    'LangGraph agent configuration and metadata',
    async ({ agent_id }) => {
      const backendUrl = getServiceUrl('backend');

      const response = await fetch(`${backendUrl}/api/agents/${agent_id}`);
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
  );

  // Resource: Agent Graph (ReactFlow)
  server.resource(
    'agent://{agent_id}/graph',
    'Visual graph representation for Forge',
    async ({ agent_id }) => {
      const backendUrl = getServiceUrl('backend');

      const response = await fetch(`${backendUrl}/api/graphs/${agent_id}`);
      const graph = await response.json();

      return {
        contents: [
          {
            uri: `agent://${agent_id}/graph`,
            mimeType: 'application/json',
            text: graph.yaml_content || '{}',
          },
        ],
      };
    }
  );

  // Resource Template: List all agents
  server.resourceTemplate('agent://*', 'All agents in the system', async () => {
    const backendUrl = getServiceUrl('backend');

    const response = await fetch(`${backendUrl}/api/agents`);
    const data = await response.json();

    return {
      resources: data.agents.map((agent: any) => ({
        uri: `agent://${agent.id}`,
        name: agent.name,
        description: agent.description,
        mimeType: 'application/json',
      })),
    };
  });
}
```

### Prompt Template Example

```typescript
// mcp-server/src/prompts/agent-design.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';

export function registerAgentPrompts(server: Server) {
  server.prompt(
    'create_agent_from_requirements',
    'Design a LangGraph agent from natural language requirements',
    [
      {
        name: 'requirements',
        description:
          'Natural language description of agent behavior, inputs, outputs, and workflow',
        required: true,
      },
      {
        name: 'domain',
        description: 'Business domain (e.g., "customer-service", "finance")',
        required: false,
      },
    ],
    async ({ requirements, domain }) => {
      const systemPrompt = `You are an expert LangGraph agent designer.

Design a production-ready agent based on these requirements:

${requirements}

${domain ? `Domain: ${domain}` : ''}

Provide:
1. State schema (fields, types, reducers)
2. Node definitions (names, logic, tools)
3. Edge connections (node transitions)
4. Entry/exit points
5. Error handling strategy

Format as Agent YAML compatible with Forge.`;

      return {
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: systemPrompt,
            },
          },
        ],
      };
    }
  );

  server.prompt(
    'debug_agent_error',
    'Analyze and fix agent execution errors',
    [
      {
        name: 'agent_id',
        description: 'Agent ID that failed',
        required: true,
      },
      {
        name: 'error_message',
        description: 'Error message from execution',
        required: true,
      },
      {
        name: 'session_id',
        description: 'Session ID for context',
        required: false,
      },
    ],
    async ({ agent_id, error_message, session_id }) => {
      // Fetch agent configuration
      const backendUrl = getServiceUrl('backend');
      const response = await fetch(`${backendUrl}/api/agents/${agent_id}`);
      const agent = await response.json();

      // Fetch session activities if session_id provided
      let activities = '';
      if (session_id) {
        const actResponse = await fetch(
          `${backendUrl}/api/monitoring/sessions/${session_id}/activities`
        );
        const actData = await actResponse.json();
        activities = JSON.stringify(actData.activities, null, 2);
      }

      const debugPrompt = `Debug this LangGraph agent error:

Agent: ${agent.name} (${agent_id})
Error: ${error_message}

Agent Configuration:
${JSON.stringify(agent, null, 2)}

${activities ? `Recent Activities:\n${activities}` : ''}

Analyze:
1. What caused the error?
2. Which node/edge is problematic?
3. How to fix it?
4. Prevention strategy?

Provide specific code fixes and configuration changes.`;

      return {
        messages: [
          {
            role: 'user',
            content: { type: 'text', text: debugPrompt },
          },
        ],
      };
    }
  );
}
```

## Service Discovery Integration

### MCP Server Config

```typescript
// mcp-server/src/config/services.ts
interface ServiceConfig {
  backend: string;
  mcpGateway: string;
  openfga: string;
  localstack: string;
}

export function getServices(): ServiceConfig {
  const environment = process.env.ENVIRONMENT || 'development';

  if (environment === 'production') {
    // Production: Use K8s service names
    return {
      backend: 'http://foundry-backend:8080',
      mcpGateway: 'http://mcp-integration:8080',
      openfga: 'http://openfga:8081',
      localstack: 'http://localstack:4566', // Would be AWS in prod
    };
  }

  // Development: Use Docker Compose service names
  return {
    backend: process.env.SVC_BACKEND_URL || 'http://foundry-backend:8080',
    mcpGateway:
      process.env.SVC_MCP_GATEWAY_URL || 'http://mcp-integration:8080',
    openfga: process.env.SVC_OPENFGA_URL || 'http://openfga:8081',
    localstack: process.env.SVC_LOCALSTACK_URL || 'http://localstack:4566',
  };
}

export function getServiceUrl(service: keyof ServiceConfig): string {
  const services = getServices();
  return services[service];
}

export const SERVICES = getServices();
```

## Integration Gateway Enhancement

### Keep Current Gateway, Add MCP Wrapper

```typescript
// mcp-server/src/tools/integrations.ts
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

export async function registerIntegrationTools(server: Server) {
  // Fetch manifest from integration gateway
  const gatewayUrl = getServiceUrl('mcpGateway');
  const response = await fetch(`${gatewayUrl}/tools`);
  const catalog = await response.json();

  // Register each tool from manifest
  for (const tool of catalog.items) {
    // Convert manifest to Zod schema
    const inputSchema = manifestToZod(tool.inputSchema);

    server.tool(tool.toolName, tool.description, inputSchema, async (args) => {
      // Proxy to integration gateway
      const invokeResponse = await fetch(
        `${gatewayUrl}/tools/${tool.toolName}/invoke`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(args),
        }
      );

      if (!invokeResponse.ok) {
        throw new Error(`Tool invocation failed: ${invokeResponse.statusText}`);
      }

      const result = await invokeResponse.json();

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    });
  }
}

function manifestToZod(jsonSchema: any): z.ZodObject<any> {
  // Convert JSON Schema to Zod schema
  // (Implementation details...)
}
```

## Migration Checklist

### Setup Phase

- [x] SDK already installed in package.json ✅
- [ ] Create `/mcp-server/` directory structure
- [ ] Initialize TypeScript project
- [ ] Create `index.ts` entry point
- [ ] Add to docker-compose.yml
- [ ] Configure service discovery

### Tool Migration

- [ ] Migrate agent tools (list, get, execute, create, deploy)
- [ ] Wrap integration gateway tools (dynamic from manifest)
- [ ] Migrate data/admin tools
- [ ] Add observability tools
- [ ] Test each tool with MCP inspector

### Resource Implementation

- [ ] Agent resources (config, graph, history)
- [ ] Domain resources (metadata, agents, secrets)
- [ ] Organization resources (settings, domains, users)
- [ ] Session resources (state, activities)
- [ ] Test resource fetching

### Prompt Implementation

- [ ] Agent design prompts
- [ ] Testing prompts
- [ ] Debugging prompts
- [ ] Test with Claude/Cursor

### Integration

- [ ] Test with Cursor MCP integration
- [ ] Test with Claude Desktop
- [ ] Test SSE transport for web clients
- [ ] Verify service discovery works
- [ ] Verify OpenFGA authorization
- [ ] Verify LocalStack secrets access (via backend)

### Documentation

- [ ] Update MCP_N8N_ARCHITECTURE.md
- [ ] Create MCP_SDK_USAGE.md
- [ ] Update QUICK_START.md
- [ ] Create example MCP client configs
- [ ] Document tool catalog

### Deprecation

- [ ] Mark `mcp_server.py` as deprecated
- [ ] Update references in codebase
- [ ] Remove from startup scripts
- [ ] Archive legacy tools

## Compatibility Matrix

| Client          | Current (Custom)      | After (SDK)           |
| --------------- | --------------------- | --------------------- |
| Cursor          | ❌ Not compatible     | ✅ Native support     |
| Claude Desktop  | ❌ Not compatible     | ✅ Native support     |
| Custom REST     | ✅ Works              | ⚠️ Need adapter       |
| Frontend API    | ✅ Works              | ⚠️ Need adapter       |
| LangGraph Tools | ⚠️ Custom integration | ✅ Standard MCP tools |

## Summary

### Current State

- ❌ Custom REST API, not MCP protocol
- ❌ Not discoverable by MCP clients
- ❌ Missing resources and prompts
- ✅ SDK installed but unused
- ✅ Excellent integration gateway pattern (keep!)

### After Migration

- ✅ Official MCP protocol (JSON-RPC 2.0)
- ✅ Works with Cursor, Claude Desktop
- ✅ Resources for context fetching
- ✅ Prompts for common workflows
- ✅ Integration gateway enhanced with SDK
- ✅ Service discovery integrated
- ✅ OpenFGA authorization
- ✅ LocalStack secrets (via backend)

### Effort Estimate

| Phase         | Hours     | Priority |
| ------------- | --------- | -------- |
| Setup server  | 3-4       | High     |
| Migrate tools | 6-8       | High     |
| Add resources | 2-3       | Medium   |
| Add prompts   | 2         | Medium   |
| Testing       | 3-4       | High     |
| Documentation | 1-2       | High     |
| **Total**     | **17-23** |          |

### Recommendation

✅ **Proceed with migration** using Phase 1-6 plan above.

**Key Benefits:**

1. Cursor/Claude integration
2. Official MCP protocol compliance
3. Resources and prompts (new capabilities)
4. Keep n8n integration strategy
5. Better tooling and ecosystem support

---

**Next Step:** Review this plan, then I'll implement the official MCP server
structure.
