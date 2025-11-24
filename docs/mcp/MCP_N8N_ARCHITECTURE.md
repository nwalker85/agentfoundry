# MCP ↔ n8n Integration Architecture

## Overview & Rationale

Agent Foundry must prove to technical executives that integrations are available
on day one without a multi-year connector program. n8n already ships with
hundreds of workflows, templates, and OAuth connectors. By wrapping those
workflows behind MCP tools we:

- **Instantly inherit n8n’s catalog.** No bespoke ServiceNow, Zendesk, Jira,
  Slack, Google, or Salesforce clients.
- **Expose predictable MCP tool surfaces.** Agents and designers see
  `servicenow.createIncident`, not “run this n8n workflow”.
- **Keep Foundry’s codebase clean.** n8n runs as an integration sidecar while
  Foundry focuses on LangGraph, DIS, and runtime orchestration.
- **Impress buyers.** The Foundry UI can display recognizable logos and tool
  names, signaling breadth without additional engineering.

This document defines the architecture, manifest contract, UI expectations, and
deployment model required to make MCP + n8n the default integration strategy.

## Core Architecture

```
┌──────────────────────────────────────────────────────────────┐
│        Agent / LangGraph / Foundry Runtime                   │
│  (Forge-designed agents calling MCP tools)                   │
└───────────────▲──────────────────────────────────────────────┘
                │  JSON tool calls (e.g., servicenow.createIncident)
                │
┌───────────────┴──────────────────────────────────────────────┐
│           MCP Integration Server (our code)                  │
│  • Loads manifest                                           │
│  • Validates inputs/outputs                                 │
│  • Proxies to n8n via HTTP                                  │
└───────────────▲──────────────────────────────────────────────┘
                │  Authenticated webhook call + payload
                │
┌───────────────┴──────────────────────────────────────────────┐
│                n8n Sidecar (5678)                            │
│  • Workflow editor + connector library                      │
│  • Handles OAuth/connectors/retries                         │
└───────────────▲──────────────────────────────────────────────┘
                │  Connectors (REST/SOAP/GraphQL/gRPC/etc.)
                ▼
          External SaaS APIs (SNOW, Slack, Zendesk, Jira…)
```

**Responsibilities**

- **Agents / LangGraph:** call MCP tools with clean JSON schemas and trust the
  responses.
- **MCP integration server:** enforces contracts, provides observability, and
  keeps n8n abstracted away.
- **n8n:** supplies the actual connectors, retry logic, secrets storage, and
  workflow design UX.

## Manifest Contract

The manifest is the single source of truth describing every MCP tool that
proxies to n8n. Proposed location:
`mcp/integration_server/config/integrations.manifest.json` (mounted read-only).

### Schema

```json
[
  {
    "toolName": "servicenow.createIncident",
    "displayName": "ServiceNow · Create Incident",
    "description": "Create or update an incident ticket in ServiceNow ITSM.",
    "category": "ITSM",
    "logo": "servicenow",
    "n8n": {
      "type": "webhook",
      "url": "http://n8n:5678/webhook/servicenow-create-incident",
      "timeoutSeconds": 30
    },
    "inputSchema": { "... JSON schema ..." },
    "outputSchema": { "... JSON schema ..." },
    "examples": [
      {
        "input": { "shortDescription": "VPN down", "priority": "P1" },
        "output": { "incidentId": "INC0012345", "url": "https://..." }
      }
    ],
    "metadata": {
      "authType": "oauth2",
      "n8nWorkflowId": "12",
      "docsUrl": "https://docs.servicenow.com/..."
    }
  }
]
```

Key fields:

- `toolName`: canonical identifier surfaced to designers and DIS.
- `displayName` + `logo`: consumed by the Foundry UI catalog.
- `category` + optional tags: allow filtering (ITSM, Messaging, CRM, Finance).
- `n8n`: connection details (webhook URL, optional credentials/headers, workflow
  id).
- `inputSchema` / `outputSchema`: JSON Schema used by MCP server for validation
  and UI form generation.
- `examples`: short request/response pairs for LLM grounding.
- `metadata`: free-form; includes docs links, auth requirements, owner, etc.

**Auto-generation:** the manifest can be generated from n8n via its REST API or
exported workflows. Initially we maintain it manually, but the contract allows
automation so any new n8n workflow becomes a selectable MCP tool with no backend
code changes.

## MCP Integration Server

The server (FastAPI or Node) must provide:

### Startup

1. Load manifest and validate schema.
2. Warm cache of tool metadata for `/health` and UI requests.
3. Optionally ping each n8n webhook (HEAD) to flag offline connectors.

### Runtime

1. Expose MCP tool endpoints (one per `toolName`) to Foundry/agents.
2. For each invocation:
   - Validate input JSON against `inputSchema` (pydantic/AJV).
   - Inject tracing metadata (tool name, agent, request id).
   - POST payload to configured n8n webhook URL (internal network).
   - Verify response matches `outputSchema`.
   - Return normalized JSON or structured error (including n8n error message,
     HTTP status, retry hints).
3. Maintain health metrics (latency, success rate, last error per tool).

### Failure Handling

- Surface meaningful MCP errors when n8n fails:
  `{"code":"INTEGRATION_DOWN","tool":"slack.postMessage","detail":"n8n 500 Bad Gateway"}`
- Allow Foundry UI to query tool health for status badges.
- Optionally degrade to mocked responses in dev environments.

## Foundry UI Catalog

Executives must visually confirm “we already integrate with X.” The UI should:

1. Consume the manifest via `/api/integrations/tools` (served by the MCP server
   or backend cache).
2. Display each tool with:
   - Vendor logo (SVG/PNG reference or icon name).
   - Display name + short description.
   - Category badges and search/filter controls (“Messaging”, “ITSM”, “CRM”).
   - Health indicator (green/yellow/red) sourced from integration server
     metrics.
3. Allow designers to attach a tool to an agent with one click. Since the MCP
   server enforces schemas, the UI can render parameter forms automatically from
   `inputSchema`.
4. Communicate the rationale: banners/tooltips remind users that “These
   integrations are powered by n8n’s connector library—no custom coding
   required.”

This catalog becomes living proof of our integration breadth and removes any
assumption that backend work is necessary per connector.

**Current implementation:** the FastAPI backend now exposes
`/api/integrations/tools`, `/api/integrations/tools/{tool}`, and invoke
endpoints that proxy to the integration gateway. The Next.js `/tools` page calls
this API, renders the manifest data with logos/health badges, and highlights
that these integrations require zero bespoke wiring.

## Deployment Model

### Local (docker-compose)

```yaml
services:
  n8n:
    image: n8nio/n8n:latest
    ports: ['5678:5678']
    networks: [foundry]

  mcp-integration:
    build:
      context: .
      dockerfile: mcp/integration_server/Dockerfile
    environment:
      - PORT=8100
      - N8N_BASE_URL=http://n8n:5678
      - INTEGRATIONS_MANIFEST=/app/config/integrations.manifest.json
    volumes:
      - ./mcp/integration_server/config:/app/config:ro
    depends_on: [n8n]
    networks: [foundry]
```

`foundry-backend` talks to `http://mcp-integration:8100` inside the Docker
network. n8n stays internal-only; no host exposure is required beyond developer
convenience.

### AWS ECS

- **n8n service:** ECS Fargate task, internal security group, persistent volume
  or S3 for workflows.
- **mcp-integration service:** companion ECS task; environment variables mirror
  local setup but `N8N_BASE_URL` uses service discovery (e.g.,
  `http://n8n.local:5678`).
- **Foundry backend:** set
  `MCP_INTEGRATION_URL=http://mcp-integration.local:8100`.
- No public ALB for n8n/integration server; only UI/API are internet-facing.
- CloudWatch metrics/alarms around error rate per tool, n8n latency, and
  manifest load failures.

## DIS & FunctionCatalog Integration

DIS already models FunctionCatalog entries. Each entry referencing an external
SaaS simply points to an MCP tool:

```json
{
  "functionId": "F:CreateIncident_SN",
  "functionName": "CreateIncident_ServiceNow",
  "executionType": "API_CALL",
  "implementation": {
    "type": "MCP_TOOL",
    "toolName": "servicenow.createIncident"
  },
  "inputs": [...],
  "outputs": [...]
}
```

Compilation flow:

1. Designer selects a FunctionCatalog entry in Forge.
2. Compiler emits a LangGraph node that calls the referenced MCP tool.
3. At runtime the MCP integration server proxies to n8n.

Versioning considerations:

- Tool schema changes bump `manifestVersion` and FunctionCatalog entry
  revisions.
- DIS tracks which agents depend on which tools, enabling impact analysis when a
  workflow changes.

## Next Steps

1. **Implement the integration server** with `/tools`, `/health`, and MCP tool
   endpoints.
2. **Seed the manifest** with Slack, ServiceNow, Zendesk, Jira workflows already
   present in n8n.
3. **Hook Foundry UI** to the manifest API so the catalog is visible with
   logos/health metrics.
4. **Automate manifest generation** from n8n exports to keep the catalog fresh.
5. **Add governance/observability**: request tracing, tool-level rate limits,
   and incident alerting.
