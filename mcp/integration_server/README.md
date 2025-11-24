# MCP Integration Gateway

Bridges Model Context Protocol (MCP) tool calls to n8n workflows through a
manifest contract. The gateway:

1. Loads `config/integrations.manifest.json` (see
   `docs/MCP_N8N_ARCHITECTURE.md`)
2. Exposes HTTP endpoints for tool discovery, health, and invocation
3. Validates payloads against the manifest schemas before/after proxying to n8n

## Local development

```bash
export INTEGRATIONS_MANIFEST=mcp/integration_server/config/integrations.manifest.json
export N8N_BASE_URL=http://n8n:5678
uvicorn mcp.integration_server.main:app --reload --port 8100
```

When running via Docker Compose the env vars above are supplied automatically.

## Manifest format (excerpt)

See the working sample manifest in `config/integrations.manifest.json`. Each
entry includes:

- `toolName`: canonical MCP identifier
- `displayName`, `description`, `category`, `logo`, `tags`
- `n8n`: webhook metadata
- `inputSchema`/`outputSchema`: JSON schema fragments used for validation
- `examples`: grounding pairs for UI/LLM surfaces
- `metadata`: docs url, auth type, owner, etc.

The loader validates the manifest on startup, so syntax/semantic errors will
fail fast and surface in the gateway logs.

## HTTP Endpoints

| Method | Path                   | Description                                           |
| ------ | ---------------------- | ----------------------------------------------------- |
| `GET`  | `/health`              | Overall status + per-tool metrics                     |
| `GET`  | `/tools`               | Catalog list consumed by Foundry UI                   |
| `GET`  | `/tools/{tool}`        | Full metadata including schemas/examples              |
| `POST` | `/tools/{tool}/invoke` | Validates payload, proxies to n8n, validates response |
