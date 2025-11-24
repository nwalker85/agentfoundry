# Unified Agent Graphs Implementation

## Overview

Successfully implemented a unified "Agent Graphs" designer that consolidates:

- User Agents (previously `/app/forge`)
- Channel Workflows (previously `/app/workflows`)
- System Agents (new capability)

All graph types now use the same visual designer, YAML storage, and database
infrastructure.

## ✅ Completed Implementation

### Phase 1: Backend Foundation

**1.1 Database Schema Extensions**

- File: `backend/db_schema_sqlite.sql`
- Added columns to agents table:
  - `graph_type TEXT DEFAULT 'user'` - Type: user, channel, or system
  - `channel TEXT` - For channel workflows (chat/voice/api)
  - `yaml_content TEXT` - Full YAML graph definition
- Created indexes:
  - `idx_agents_graph_type`
  - `idx_agents_channel`
  - `idx_agents_org_domain`

**1.2 YAML Storage Utilities**

- File: `backend/utils/yaml_storage.py`
- Functions for reading/writing/deleting graph YAMLs
- Directory management:
  ```
  agents/
    user/{org-id}/{domain-id}/
    channels/{channel}/
    system/
    templates/
  ```
- Path resolution for all graph types

**1.3 Unified Graph CRUD**

- File: `backend/db.py` (lines 935-1127)
- New functions:
  - `list_graphs()` - Filter by type/channel/org/domain
  - `get_graph(graph_id)` - Get single graph
  - `upsert_graph(graph_data)` - Create/update with YAML sync
  - `delete_graph(graph_id)` - Remove from DB and filesystem

**1.4 Unified API Endpoints**

- File: `backend/main.py` (lines 1500-1607)
- New routes:
  - `GET /api/graphs` - List with filtering
  - `GET /api/graphs/{id}` - Get single graph
  - `POST /api/graphs` - Create/update
  - `DELETE /api/graphs/{id}` - Delete
  - `POST /api/graphs/{id}/deploy` - Deploy to production

**1.5 Graph Hot-Reload System**

- File: `backend/utils/graph_hot_reload.py`
- `GraphCache` class - In-memory caching with mtime tracking
- `GraphLoader` class - Load graphs with automatic cache invalidation
- Compiles graphs to Python LangGraph code on demand

### Phase 2: Frontend Components

**2.1 Graph Type Selector**

- File: `app/app/graphs/components/GraphTypeSelector.tsx`
- Radio buttons for User Agent / Channel Workflow / System Agent
- Shows count badges for each type
- Clean design with lucide icons

**2.2 Graph Gallery**

- File: `app/app/graphs/components/GraphGallery.tsx`
- Card grid layout with search and sort
- Type/channel badges
- Quick actions: Open, Duplicate, Delete
- Node count display
- Empty state with "Create New" prompt

**2.3 Unified Graphs Page**

- File: `app/app/graphs/page.tsx`
- Gallery mode: Browse and manage graphs
- Editor mode: Visual designer with toolbar
- Type-specific features:
  - User agents: Org/Domain selectors
  - Channel workflows: Channel dropdown
  - System agents: System badge, edit warnings
- History/undo-redo
- State schema management
- Trigger configuration
- Python code preview

### Phase 3: Navigation Updates

**3.1 Left Navigation**

- File: `app/components/layout/LeftNav.tsx`
- Removed: "New Agent", "Workflows"
- Added: "Agent Graphs" with GitBranch icon in CREATE section

**3.2 Top Navigation**

- File: `app/components/layout/TopNav.tsx`
- Removed: `/forge`, `/workflows` configs
- Added: `/graphs` config with "Agent Graphs" title

**3.3 App Menu**

- File: `app/components/layout/AppMenu.tsx`
- Removed: "New Agent" card
- Added: "Agent Graphs" card with comprehensive description

### Phase 4: Templates & Migration

**4.1 Default Templates**

- `agents/templates/user-agent-react.yaml` - ReAct pattern
- `agents/templates/user-agent-plan-execute.yaml` - Plan-Execute pattern
- `agents/templates/channel-workflow-basic.yaml` - IO + Supervisor + Goal
  Manager
- `agents/templates/system-agent-minimal.yaml` - Minimal system agent

**4.2 Migration Scripts**

- `scripts/apply_schema_changes.py` - Apply database schema changes
- `scripts/migrate_to_unified_graphs.py` - Migrate channel workflows to YAML

## Testing Checklist

### Pre-Testing Setup

1. **Apply Schema Changes**

   ```bash
   cd /Users/nwalker/Development/Projects/agentfoundry
   python scripts/apply_schema_changes.py
   ```

2. **Migrate Channel Workflows** (if any exist)

   ```bash
   python scripts/migrate_to_unified_graphs.py
   ```

3. **Restart Backend**

   ```bash
   docker-compose restart foundry-backend
   ```

4. **Restart Frontend** (if needed)
   ```bash
   docker-compose restart agent-foundry-ui
   ```

### Functional Tests

**Navigation Tests:**

- [ ] Left nav shows "Agent Graphs" instead of "New Agent" and "Workflows"
- [ ] Clicking "Agent Graphs" navigates to `/app/graphs`
- [ ] Top nav shows "Agent Graphs" title when on `/app/graphs`
- [ ] App menu (Cmd+K) shows "Agent Graphs" card

**Gallery View Tests:**

- [ ] Type selector shows User Agent / Channel Workflow / System Agent
- [ ] Clicking type selector filters graphs correctly
- [ ] Graph cards display: name, description, badges, last modified
- [ ] Search filters graphs by name/description
- [ ] Sort by name/updated works correctly
- [ ] "New Graph" button creates empty graph of selected type
- [ ] Empty state shows when no graphs exist

**Editor - User Agent:**

- [ ] Create new user agent
- [ ] Org/Domain selectors visible in toolbar
- [ ] GraphEditor (ReactFlow) loads correctly
- [ ] Add nodes from palette (Entry, Process, Decision, Tool Call, End)
- [ ] Connect nodes with edges
- [ ] Select node opens NodeEditor sidebar
- [ ] Edit node properties (label, description, model, temperature)
- [ ] Delete node removes it and connected edges
- [ ] Undo/Redo history works
- [ ] State schema selector works
- [ ] Trigger configuration works
- [ ] Python code preview shows generated code
- [ ] Save creates YAML in `agents/user/{org}/{domain}/`
- [ ] Save updates agents table with graph_type='user'

**Editor - Channel Workflow:**

- [ ] Create new channel workflow
- [ ] Channel selector shows Chat/Voice/API
- [ ] Changing channel updates metadata
- [ ] No org/domain selectors (not required for channel type)
- [ ] Save creates YAML in `agents/channels/{channel}/`
- [ ] Save updates agents table with graph_type='channel' and channel field

**Editor - System Agent:**

- [ ] Create new system agent
- [ ] "System Agent" badge visible
- [ ] No org/domain selectors
- [ ] Edit warning about affecting core platform (if implemented)
- [ ] Save creates YAML in `agents/system/`
- [ ] Save updates agents table with graph_type='system', is_system_agent=1

**CRUD Operations:**

- [ ] Duplicate graph creates copy with new ID
- [ ] Delete graph removes from DB and deletes YAML file
- [ ] Navigate away with unsaved changes shows warning
- [ ] Back to Gallery button returns to gallery view

**Hot-Reload Tests:**

- [ ] Edit YAML file directly
- [ ] Reload graph in UI shows updated data
- [ ] Cache invalidates when file modified

**API Tests:**

```bash
# List graphs
curl http://localhost:8000/api/graphs?graph_type=user

# Get single graph
curl http://localhost:8000/api/graphs/{graph_id}

# Create graph
curl -X POST http://localhost:8000/api/graphs \
  -H "Content-Type: application/json" \
  -d '{"metadata": {...}, "spec": {...}}'

# Delete graph
curl -X DELETE http://localhost:8000/api/graphs/{graph_id}
```

## File Structure

```
agents/
  user/
    {org-id}/
      {domain-id}/
        *.yaml
  channels/
    chat/
      *.yaml
    voice/
      *.yaml
    api/
      *.yaml
  system/
    *.yaml
  templates/
    user-agent-react.yaml
    user-agent-plan-execute.yaml
    channel-workflow-basic.yaml
    system-agent-minimal.yaml

app/
  app/
    graphs/
      page.tsx
      components/
        GraphTypeSelector.tsx
        GraphGallery.tsx

backend/
  db_schema_sqlite.sql (updated)
  db.py (new CRUD functions)
  main.py (new API endpoints)
  utils/
    yaml_storage.py (new)
    graph_hot_reload.py (new)

scripts/
  apply_schema_changes.py (new)
  migrate_to_unified_graphs.py (new)
```

## Known Limitations

1. **Old Routes**: `/app/forge` and `/app/workflows` still exist but are
   deprecated
2. **Manifest Sync**: Deploy endpoint needs full implementation for manifest
   updates
3. **Permissions**: No permission checks for system agent editing yet
4. **File Watchers**: Hot-reload uses mtime polling, not filesystem events

## Next Steps (Post-Testing)

1. **Add Redirect Pages**

   - Create `/app/forge/page.tsx` → redirects to `/app/graphs?type=user`
   - Create `/app/workflows/page.tsx` → redirects to `/app/graphs?type=channel`

2. **Deprecation Notice**

   - Show banner on old routes for 1-2 releases
   - Link to migration guide

3. **Complete Deployment Logic**

   - Implement manifest sync in `/api/graphs/{id}/deploy`
   - Add agent reload triggers

4. **Documentation**
   - User guide for unified graphs designer
   - Migration guide from old routes
   - Template creation guide

## Success Metrics

✅ Single "Agent Graphs" navigation item ✅ Type selector for
User/Channel/System ✅ All graphs stored as YAML files ✅ Shared designer
components work across types ✅ Python code generation from graphs ✅ Database +
filesystem sync ✅ Hot-reload with cache invalidation ✅ Gallery view with
search/filter ✅ Migration script for channel workflows ✅ Default templates for
quick start

## Support

For issues or questions:

- Check logs: `docker-compose logs foundry-backend`
- Verify database: `sqlite3 backend/foundry.db`
- Check YAML files: `ls -R agents/`

---

**Implementation Date:** 2025-11-17 **Status:** ✅ Complete - Ready for Testing
