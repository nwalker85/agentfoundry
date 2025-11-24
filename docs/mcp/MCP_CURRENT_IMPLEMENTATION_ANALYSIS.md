# Current MCP Implementation Analysis

## Overview

Agent Foundry currently uses a **custom Python/FastAPI-based MCP
implementation** rather than the official `@modelcontextprotocol/sdk`. This
document analyzes the current state and prepares for migration.

## Current Architecture

### Two Separate MCP Systems

#### 1. **Legacy MCP Server** (`mcp_server.py`)

**Type:** Custom FastAPI server  
**Purpose:** Original Engineering Department tools  
**Status:** ⚠️ Legacy - Not using official MCP protocol

**Components:**

- Custom tool classes (NotionTool, GitHubTool, AuditTool, etc.)
- FastAPI REST endpoints (not true MCP protocol)
- Direct API integrations to Notion, GitHub
- WebSocket for chat
- PM Agent integration

**Issues:**

- ❌ Not using official MCP protocol
- ❌ Custom schemas (not MCP standard)
- ❌ REST endpoints instead of MCP JSON-RPC
- ❌ No resource/prompt support (MCP core features)
- ❌ Not discoverable by MCP clients

#### 2. **MCP Integration Gateway** (`mcp/integration_server/`)

**Type:** FastAPI proxy to n8n  
**Purpose:** Bridge MCP tool calls to n8n workflows  
**Status:** ✅ Good architecture, but not using SDK

**Components:**

- Manifest-driven tool catalog (`integrations.manifest.json`)
- Input/output schema validation
- n8n webhook proxy
- Health monitoring per tool

**Issues:**

- ❌ Not using MCP SDK (custom HTTP proxy)
- ❌ Custom validation logic
- ✅ Good: Manifest pattern (can be adapted)
- ✅ Good: n8n integration strategy

### Package Dependency

```json
// package.json (line 19)
"@modelcontextprotocol/sdk": "^1.22.0"
```

**Status:** ✅ Installed but **NOT USED**

## What's Wrong with Current Implementation

### 1. Not Real MCP

```python
# Current: Custom REST endpoints
@app.post("/api/tools/notion/create-story")
async def create_story(request: CreateStoryRequest):
    ...

# Real MCP: JSON-RPC 2.0 over stdio/SSE
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "notion_create_story",
    "arguments": {...}
  }
}
```

### 2. Missing MCP Core Features

| MCP Feature      | Current Status                     |
| ---------------- | ---------------------------------- |
| **Tools**        | ⚠️ Custom REST, not MCP format     |
| **Resources**    | ❌ Not implemented                 |
| **Prompts**      | ❌ Not implemented                 |
| **Sampling**     | ❌ Not implemented                 |
| **Roots**        | ❌ Not implemented                 |
| **JSON-RPC 2.0** | ❌ Using REST instead              |
| **Transport**    | ❌ HTTP REST (should be stdio/SSE) |

### 3. Not Discoverable by MCP Clients

```bash
# Official MCP clients expect:
mcp inspect mcp://localhost:8001

# Current server can't respond to this
# Uses custom REST API instead
```

### 4. Incompatible with Cursor/Claude Desktop

```json
// Claude Desktop MCP config expects:
{
  "mcpServers": {
    "agent-foundry": {
      "command": "node",
      "args": ["path/to/mcp-server.js"]
    }
  }
}


// Current Python server doesn't work with this
```

## What's Good About Current Implementation

### ✅ Integration Gateway Pattern

```
Agent → MCP Integration Gateway → n8n → External APIs
```

This pattern is **excellent** and should be kept!

- Clean separation of concerns
- Manifest-driven tool catalog
- Schema validation
- n8n handles OAuth/retries
- Easy to add new tools

### ✅ Comprehensive Tool Set

You have working implementations for:

- Notion (stories, epics)
- GitHub (issues, repos)
- Audit logging
- Data queries
- Admin operations
- Observability

These can be **ported to proper MCP format**.

### ✅ Schema Validation

```python
validate_payload(payload, manifest.inputSchema)
validate_payload(data, manifest.outputSchema)
```

This is good practice and aligns with MCP's typed tool system.

## Migration Path

### Option A: Dual Implementation (Recommended)

**Keep both during transition:**

```
┌─────────────────────────────────────────┐
│  Official MCP Server (Node.js + SDK)    │  ← New
│  - Uses @modelcontextprotocol/sdk       │
│  - stdio/SSE transport                  │
│  - MCP protocol                         │
│  - Discoverable by Cursor/Claude        │
└────────────┬────────────────────────────┘
             │ Calls via HTTP
┌────────────▼────────────────────────────┐
│  Integration Gateway (FastAPI)          │  ← Keep
│  - Manifest-driven                      │
│  - n8n proxy                            │
│  - Schema validation                    │
│  - Health monitoring                    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  n8n Workflows                          │  ← Keep
└─────────────────────────────────────────┘
```

**Benefits:**

- Official MCP clients can connect
- Keep existing FastAPI backend integration
- Gradual migration
- Both systems work

### Option B: Pure MCP (Clean Slate)

**Replace everything with SDK:**

```
┌─────────────────────────────────────────┐
│  MCP Server (Node.js + Official SDK)    │
│  - Tools defined in TypeScript          │
│  - Built-in schema validation           │
│  - Direct integration clients           │
└─────────────────────────────────────────┘
```

**Benefits:**

- Simpler architecture
- Official protocol compliance
- Better tooling support

**Drawbacks:**

- Lose n8n integration strategy
- More implementation work
- Harder to maintain

## Recommended Approach

**Hybrid: Official MCP Server + Keep Integration Gateway**

### Architecture

```
┌──────────────────────────────────────────────────┐
│           MCP Clients                            │
│  (Cursor, Claude Desktop, Custom)                │
└─────────────────┬────────────────────────────────┘
                  │ MCP Protocol (JSON-RPC 2.0)
┌─────────────────▼────────────────────────────────┐
│      Official MCP Server (Node.js/TypeScript)     │
│      Uses @modelcontextprotocol/sdk               │
│                                                   │
│  Tools:                                           │
│  - notion_create_story                           │
│  - github_create_issue                           │
│  - agent_execute                                 │
│  - data_query                                     │
│                                                   │
│  Resources:                                       │
│  - agent://{agent_id}                            │
│  - domain://{domain_id}                          │
│  - organization://{org_id}                       │
│                                                   │
│  Prompts:                                         │
│  - create_agent_from_requirements                │
│  - generate_test_cases                           │
└─────────────────┬────────────────────────────────┘
                  │ HTTP calls (internal)
┌─────────────────▼────────────────────────────────┐
│      Foundry Backend (FastAPI)                    │
│      Service Discovery Integration                │
│                                                   │
│  Routes:                                          │
│  - /api/agents                                    │
│  - /api/secrets (OpenFGA protected)               │
│  - /api/integrations/tools                        │
└─────────────────┬────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────┐
│      MCP Integration Gateway (FastAPI)            │  ← Keep this!
│      Manifest-driven n8n proxy                    │
└─────────────────┬────────────────────────────────┘
                  │
┌─────────────────▼────────────────────────────────┐
│              n8n Workflows                        │
│      Hundreds of pre-built connectors             │
└───────────────────────────────────────────────────┘
```

## What to Build

### 1. Official MCP Server (Node.js/TypeScript)

**Location:** `/mcp-server/`

**Using:** `@modelcontextprotocol/sdk`

**Features:**

- Proper MCP protocol (JSON-RPC 2.0)
- stdio and SSE transports
- Tool definitions with JSON schemas
- Resource providers (agents, domains, etc.)
- Prompt templates
- Service discovery integration

### 2. Keep Integration Gateway

**Location:** `/mcp/integration_server/` (existing)

**Improvements:**

- Update to use official SDK types
- Keep manifest-driven approach
- Keep n8n proxy logic

### 3. Deprecate Legacy Server

**Location:** `/mcp_server.py` (existing)

**Action:** Mark as deprecated, gradually migrate

## File Structure

### Current

```
agentfoundry/
├── mcp_server.py                  ❌ Custom, not real MCP
├── mcp/
│   ├── tools/                     ❌ Custom implementations
│   │   ├── notion.py
│   │   ├── github.py
│   │   └── ...
│   ├── integration_server/        ⚠️ Good pattern, not using SDK
│   │   ├── main.py
│   │   ├── client.py
│   │   └── config/
│   │       └── integrations.manifest.json
│   └── schemas.py                 ❌ Custom schemas
```

### Proposed

```
agentfoundry/
├── mcp-server/                    ✅ NEW - Official MCP server
│   ├── src/
│   │   ├── index.ts              ✅ Main entry point
│   │   ├── server.ts             ✅ MCP server setup
│   │   ├── tools/                ✅ Tool definitions
│   │   │   ├── agents.ts         ✅ Agent tools
│   │   │   ├── integrations.ts   ✅ Integration tools
│   │   │   └── data.ts           ✅ Data query tools
│   │   ├── resources/            ✅ Resource providers
│   │   │   ├── agents.ts
│   │   │   └── domains.ts
│   │   └── prompts/              ✅ Prompt templates
│   │       └── agent-design.ts
│   ├── package.json              ✅ Uses @modelcontextprotocol/sdk
│   └── tsconfig.json
│
├── mcp/
│   ├── integration_server/        ✅ KEEP - n8n gateway
│   │   └── ...                    ✅ Already good
│   └── tools/                     ⚠️ DEPRECATE gradually
│
└── mcp_server.py                  ⚠️ DEPRECATE - Legacy
```

## SDK Features We Can Now Use

### 1. Official Tool Definitions

```typescript
// mcp-server/src/tools/agents.ts
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

server.tool(
  'agent_execute',
  'Execute a LangGraph agent',
  {
    agent_id: z.string().describe('Agent ID to execute'),
    input: z.string().describe('User input'),
    session_id: z.string().optional(),
  },
  async ({ agent_id, input, session_id }) => {
    // Call backend API via service discovery
    const response = await fetch(
      `http://foundry-backend:8080/api/agent/invoke`,
      {
        method: 'POST',
        body: JSON.stringify({ agent_id, input, session_id }),
      }
    );

    return await response.json();
  }
);
```

### 2. Resource Providers

```typescript
// mcp-server/src/resources/agents.ts
server.resource(
  'agent://{agent_id}',
  'LangGraph Agent Configuration',
  async ({ agent_id }) => {
    // Fetch agent details from backend
    const response = await fetch(
      `http://foundry-backend:8080/api/agents/${agent_id}`
    );

    const agent = await response.json();

    return {
      uri: `agent://${agent_id}`,
      mimeType: 'application/json',
      text: JSON.stringify(agent, null, 2),
    };
  }
);
```

### 3. Prompt Templates

```typescript
// mcp-server/src/prompts/agent-design.ts
server.prompt(
  'create_agent_from_requirements',
  'Create a LangGraph agent from natural language requirements',
  [
    {
      name: 'requirements',
      description: 'Natural language description of agent behavior',
      required: true,
    },
  ],
  async ({ requirements }) => {
    return {
      messages: [
        {
          role: 'user',
          content: {
            type: 'text',
            text: `Design a LangGraph agent with these requirements:\n\n${requirements}\n\nProvide: state schema, nodes, edges, and workflow logic.`,
          },
        },
      ],
    };
  }
);
```

## Current vs SDK Comparison

### Tool Invocation

#### Current (Custom REST)

```python
# Client makes HTTP POST
POST /api/tools/notion/create-story
Content-Type: application/json

{
  "epic_title": "User Management",
  "story_title": "Add login page",
  "priority": "P1"
}

# Response
{
  "story_id": "abc123",
  "story_url": "https://notion.so/..."
}
```

#### SDK (MCP Protocol)

```json
// Client sends JSON-RPC over stdio/SSE
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "notion_create_story",
    "arguments": {
      "epic_title": "User Management",
      "story_title": "Add login page",
      "priority": "P1"
    }
  }
}

// Server responds
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "Story created: abc123"
    }],
    "isError": false
  }
}
```

### Tool Discovery

#### Current (Custom)

```python
# No standard discovery mechanism
# Tools hardcoded in code
```

#### SDK (MCP Protocol)

```json
// Client requests tool list
{
  "jsonrpc": "2.0",
  "method": "tools/list"
}

// Server responds with all available tools
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "notion_create_story",
        "description": "Create a story in Notion",
        "inputSchema": {
          "type": "object",
          "properties": {...}
        }
      }
    ]
  }
}
```

## Migration Benefits

### Why Migrate to Official SDK

1. **Protocol Compliance**

   - ✅ Works with Cursor, Claude Desktop, and any MCP client
   - ✅ JSON-RPC 2.0 standard
   - ✅ Proper error handling
   - ✅ Schema validation built-in

2. **Advanced Features**

   - ✅ Resources (expose agent configs, domain data)
   - ✅ Prompts (pre-built prompt templates)
   - ✅ Sampling (LLM completion requests)
   - ✅ Progress notifications
   - ✅ Cancellation support

3. **Better Integration**

   - ✅ TypeScript type safety
   - ✅ Built-in logging
   - ✅ Transport abstraction (stdio, SSE, custom)
   - ✅ Zod schema validation

4. **Ecosystem**
   - ✅ Official docs and examples
   - ✅ Community support
   - ✅ Future protocol updates
   - ✅ Tooling (inspectors, debuggers)

## Current Tool Inventory

### Tools to Migrate

1. **NotionTool** (`mcp/tools/notion.py`)

   - `create_story()` → `notion_create_story` tool
   - `list_top_stories()` → `notion_list_stories` tool

2. **GitHubTool** (`mcp/tools/github.py`)

   - `create_issue()` → `github_create_issue` tool
   - `create_pr()` → `github_create_pr` tool

3. **DataTool** (`mcp/tools/data.py`)

   - `query()` → `data_query` tool (NL → SQL)

4. **AdminTool** (`mcp/tools/admin.py`)

   - `list_objects()` → `admin_list` tool
   - `get_object()` → `admin_get` tool

5. **ManifestTool** (`mcp/tools/manifest.py`)

   - `register_agent()` → `agent_register` tool

6. **ObservabilityTools** (`mcp/tools/observability_tools.py`)
   - 11 functions → MCP tools for monitoring

### Resources to Add (New Capability!)

MCP resources allow clients to fetch context:

1. `agent://{agent_id}` - Agent configuration YAML
2. `domain://{domain_id}` - Domain metadata
3. `organization://{org_id}` - Org settings
4. `session://{session_id}` - Session state
5. `graph://{graph_id}` - Visual graph JSON

### Prompts to Add (New Capability!)

MCP prompts provide pre-built templates:

1. `create_agent_from_requirements` - Design agent from NL
2. `generate_test_cases` - Create test scenarios
3. `debug_agent_error` - Analyze agent failures
4. `optimize_workflow` - Suggest improvements

## Integration with Service Discovery

The new MCP server will use service discovery:

```typescript
// mcp-server/src/config/services.ts
import { SERVICES } from '../../app/lib/config/services';

// Call backend API
const backendUrl = SERVICES.backend.internal; // http://foundry-backend:8080

// Call integration gateway
const mcpGatewayUrl = SERVICES.mcp_integration; // http://mcp-integration:8080
```

## Integration with OpenFGA

MCP server tools will check permissions:

```typescript
// mcp-server/src/tools/agents.ts
server.tool(
  'agent_execute',
  'Execute an agent',
  schema,
  async ({ agent_id }, { user_id }) => {
    // Check permission via OpenFGA
    const allowed = await checkPermission(
      user_id,
      'can_execute',
      `agent:${agent_id}`
    );

    if (!allowed) {
      throw new McpError('PERMISSION_DENIED', 'Cannot execute this agent');
    }

    // Execute...
  }
);
```

## Integration with LocalStack Secrets

```typescript
// MCP server never gets secrets directly
// It calls backend, which retrieves from LocalStack

server.tool(
  'agent_execute',
  'Execute agent',
  schema,
  async ({ agent_id, org_id }) => {
    // Backend handles secret retrieval
    const response = await fetch(`${backendUrl}/api/agent/invoke`, {
      method: 'POST',
      headers: {
        'X-Organization-ID': org_id,
      },
      body: JSON.stringify({ agent_id }),
    });

    // Backend internally:
    // 1. Gets secret from LocalStack
    // 2. Executes agent
    // 3. Returns result (NOT the secret)

    return await response.json();
  }
);
```

## Summary

### Current State

| Component                 | Status                      | Action               |
| ------------------------- | --------------------------- | -------------------- |
| `mcp_server.py`           | ❌ Custom, not MCP protocol | Deprecate            |
| `mcp/tools/*`             | ⚠️ Working but custom       | Reimplement with SDK |
| `mcp/integration_server/` | ✅ Good pattern             | Keep & enhance       |
| SDK Dependency            | ✅ Installed                | Use it!              |

### Migration Plan

1. **Phase 1:** Build new MCP server with SDK (parallel to existing)
2. **Phase 2:** Migrate tools one-by-one to SDK format
3. **Phase 3:** Add resources and prompts (new capabilities)
4. **Phase 4:** Deprecate `mcp_server.py` (legacy)
5. **Phase 5:** Keep integration gateway for n8n proxy

### Time Estimate

- **Phase 1 (Setup):** 2-3 hours
- **Phase 2 (Tool Migration):** 4-6 hours
- **Phase 3 (Resources/Prompts):** 2-3 hours
- **Phase 4 (Testing):** 2-3 hours
- **Phase 5 (Documentation):** 1-2 hours

**Total:** 11-17 hours for complete migration

### Risk Level

**Low** because:

- SDK is installed and ready
- Can run both systems in parallel
- Integration gateway can stay unchanged
- Gradual migration path

---

**Next Step:** Review this analysis, then I'll implement the official MCP server
with the SDK.
