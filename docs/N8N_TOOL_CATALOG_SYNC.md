# N8N Tool Catalog Integration

**Automatic synchronization of all n8n integrations into Agent Foundry's tool
catalog.**

## Overview

Agent Foundry automatically discovers and exposes **all n8n integrations** as
tools that can be used by agents. This eliminates the need to manually configure
each integration and gives you instant access to hundreds of pre-built
connectors.

## How It Works

```
┌─────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────┐
│   n8n   │────▶│ Sync Scripts │────▶│ Function       │────▶│   UI    │
│ (5678)  │     │              │     │ Catalog (DB)   │     │ /tools  │
└─────────┘     └──────────────┘     └────────────────┘     └─────────┘
    │                  │                      │                    │
    │                  │                      │                    │
    ▼                  ▼                      ▼                    ▼
Available         Manifest JSON          SQLite Table        Tool Cards
Node Types        integrations.          function_catalog    with logos,
(REST API)        manifest.json                              categories,
                                                             health stats
```

### Sync Pipeline

1. **Discovery**: Query n8n REST API for all available node types
2. **Categorization**: Automatically categorize nodes (Communication, CRM, ITSM,
   etc.)
3. **Schema Generation**: Convert n8n node properties to JSON Schema
4. **Manifest Generation**: Create `integrations.manifest.json` with all tools
5. **Database Population**: Insert/update entries in `function_catalog` table
6. **UI Display**: Tools appear in `/app/tools` automatically

## Automatic Sync on Startup

**The sync happens automatically when you start Docker Compose!**

When `docker-compose up` runs:

1. n8n service starts
2. Backend service waits for n8n to be ready
3. Startup script (`backend/startup.sh`) runs:
   - Calls `sync_integrations_startup.sh`
   - Syncs manifest from n8n
   - Populates function catalog
4. FastAPI server starts
5. All n8n integrations are available in the UI

## Manual Sync

To manually refresh the tool catalog (e.g., after adding new n8n integrations):

```bash
# Run the manual sync script
./scripts/sync_integrations.sh

# Or run individual steps:

# 1. Sync manifest from n8n
python scripts/sync_n8n_manifest.py

# 2. Populate function catalog
python scripts/populate_function_catalog.py --clear

# 3. Restart services to pick up changes
docker-compose restart foundry-backend mcp-integration
```

## Files & Components

### Scripts

| File                                   | Purpose                                      |
| -------------------------------------- | -------------------------------------------- |
| `mcp/tools/n8n_client.py`              | N8N REST API client                          |
| `scripts/sync_n8n_manifest.py`         | Queries n8n, generates manifest              |
| `scripts/populate_function_catalog.py` | Populates database from manifest             |
| `scripts/sync_integrations_startup.sh` | Runs full sync (called on startup)           |
| `scripts/sync_integrations.sh`         | Manual sync script for users                 |
| `backend/startup.sh`                   | Backend startup wrapper (runs sync + server) |

### Data Files

| File                                                       | Purpose                                  |
| ---------------------------------------------------------- | ---------------------------------------- |
| `mcp/integration_server/config/integrations.manifest.json` | Auto-generated manifest of all n8n tools |
| `data/foundry.db` (SQLite)                                 | Function catalog table with all tools    |

### Database Schema

```sql
CREATE TABLE function_catalog (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,              -- e.g., "slack.execute"
  display_name TEXT NOT NULL,             -- e.g., "Slack"
  description TEXT,
  category TEXT NOT NULL,                 -- Communication, CRM, etc.
  type TEXT NOT NULL,                     -- "integration" for n8n tools
  integration_tool_name TEXT,             -- Links to manifest
  input_schema TEXT,                      -- JSON Schema
  output_schema TEXT,                     -- JSON Schema
  tags TEXT,                              -- JSON array
  metadata TEXT,                          -- JSON blob
  is_active INTEGER DEFAULT 1,
  created_at TEXT,
  updated_at TEXT
);
```

## Categories

The sync script automatically categorizes tools based on node names and groups:

- **Communication**: Slack, Discord, Telegram, Teams, Email
- **CRM**: Salesforce, HubSpot, Pipedrive, Zoho
- **Project Management**: Jira, Asana, Trello, Notion, ClickUp
- **ITSM**: ServiceNow, Freshservice, Zendesk
- **Analytics**: Google Analytics, Mixpanel, Segment
- **Cloud Services**: AWS, GCP, Azure, S3, Lambda
- **Database**: Postgres, MySQL, MongoDB, Redis, Supabase
- **AI & ML**: OpenAI, Anthropic, Cohere, HuggingFace
- **Productivity**: Google Drive, Dropbox, Airtable, Sheets
- **Other**: Everything else

## Configuration

### Environment Variables

Set these in `.env` or `docker-compose.yml`:

```bash
# N8N Connection
N8N_BASE_URL=http://n8n:5678
N8N_API_KEY=                    # Optional API key
N8N_BASIC_AUTH_USER=            # Optional basic auth
N8N_BASIC_AUTH_PASSWORD=        # Optional basic auth

# Database
DATABASE_URL=sqlite:///data/foundry.db
```

### Filtering

To limit which nodes are synced, edit `scripts/sync_n8n_manifest.py`:

```python
# Skip certain node types
if any(skip in node_name.lower() for skip in [
    "trigger",
    "webhook",
    ...
]):
    continue
```

## Testing

```bash
# 1. Start services
docker-compose up -d

# 2. Check n8n is accessible
curl http://localhost:5678

# 3. Check manifest was generated
cat mcp/integration_server/config/integrations.manifest.json | jq '. | length'

# 4. Check function catalog was populated
sqlite3 data/foundry.db "SELECT COUNT(*) FROM function_catalog WHERE type='integration';"

# 5. Check API
curl http://localhost:8000/api/function-catalog | jq '. | length'

# 6. Check UI
open http://localhost:3000/app/tools
```

## Viewing Synced Tools

### Web UI

Visit **http://localhost:3000/app/tools** to see all synced integrations with:

- Logos and icons
- Categories and tags
- Health metrics (success/failure counts)
- Configuration options

### API

```bash
# List all functions
curl http://localhost:8000/api/function-catalog

# Filter by category
curl http://localhost:8000/api/function-catalog?category=Communication

# Get specific function
curl http://localhost:8000/api/function-catalog/{function_id}
```

### Database

```bash
# Query function catalog
sqlite3 data/foundry.db

SELECT category, COUNT(*)
FROM function_catalog
WHERE type='integration'
GROUP BY category
ORDER BY COUNT(*) DESC;
```

## Troubleshooting

### No tools appear in UI

1. Check n8n is running: `docker-compose ps n8n`
2. Check backend logs: `docker-compose logs foundry-backend | grep sync`
3. Manually run sync: `./scripts/sync_integrations.sh`

### Sync script fails

1. Verify n8n is accessible:

   ```bash
   curl http://localhost:5678
   ```

2. Check n8n API returns node types:

   ```bash
   curl http://localhost:5678/types/nodes.json | head
   ```

3. Run sync with debug logging:
   ```bash
   export LOG_LEVEL=DEBUG
   python scripts/sync_n8n_manifest.py
   ```

### Tools missing schemas

Some n8n nodes have dynamic properties. The sync script does its best to convert
them to JSON Schema, but some may need manual refinement.

Edit the generated manifest and update schemas as needed:

```bash
vim mcp/integration_server/config/integrations.manifest.json
```

Then re-populate:

```bash
python scripts/populate_function_catalog.py --clear
```

## Advanced: Adding Custom Integrations

While n8n integrations sync automatically, you can also add custom tools
manually:

```bash
curl -X POST http://localhost:8000/api/function-catalog \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_custom_tool",
    "display_name": "My Custom Tool",
    "description": "Does something custom",
    "category": "Custom",
    "type": "custom",
    "input_schema": {...},
    "output_schema": {...},
    "handler_code": "def execute(params): ..."
  }'
```

## Next Steps

- **Configure Credentials**: Use the "Configure" button in the UI to set up
  org-specific credentials for each tool
- **Bind to Agents**: In Forge, select tools to make available to specific
  agents
- **Create Workflows**: Use n8n UI to create workflows that agents can invoke

## References

- [N8N API Documentation](https://docs.n8n.io/api/)
- [MCP N8N Architecture](./MCP_N8N_ARCHITECTURE.md)
- [Function Catalog API](../backend/routes/function_catalog.py)
