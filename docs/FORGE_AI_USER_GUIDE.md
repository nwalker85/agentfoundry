# Forge AI User Guide

**Version:** 0.9.0 (Phase 1 - Visual Graph Editor MVP)
**Status:** MVP Complete - Ready for Testing

---

## Overview

Forge AI is a visual agent configuration tool that allows you to create, edit, and deploy AI agents using an intuitive graph-based interface. Instead of writing YAML by hand, you can drag-and-drop nodes to build agent workflows and see the generated YAML in real-time.

## Accessing Forge AI

**URL:** http://localhost:3000/forge

**Navigation:** Click "Forge AI" in the left sidebar

---

## Quick Start

### 1. Create Your First Agent

1. **Name Your Agent**
   - Enter a unique name in the header (e.g., `customer-support-agent`)

2. **Add Nodes**
   - Click the "Add Node" panel on the left
   - Start with an **Entry Point** node
   - Add **Process** nodes for LLM tasks
   - Add **Tool Call** nodes for API integrations
   - Add **Decision** nodes for conditional logic
   - End with an **End** node

3. **Connect Nodes**
   - Drag from the bottom circle (output) of one node
   - Connect to the top circle (input) of another node
   - Create your workflow path

4. **Configure Nodes**
   - Click any node to open the editor panel
   - Edit properties like label, description, model settings
   - For Process nodes: set model, temperature, max tokens
   - For Tool Call nodes: specify the tool name
   - For Decision nodes: add conditions

5. **Save Your Agent**
   - Click "Save" in the header
   - Agent is saved as YAML in `/agents` directory
   - Auto-creates or updates the agent file

### 2. Deploy Your Agent

1. **Select Environment**
   - Choose **dev**, **staging**, or **prod** from the dropdown

2. **Click Deploy**
   - Deploys agent YAML to selected environment
   - Creates environment-specific file (e.g., `agent.dev.agent.yaml`)

3. **Verify Deployment**
   - Check console for success message
   - Agent is now available to Marshal for hot-reload

---

## Node Types

### Entry Point (Green)
- **Purpose:** Start of the workflow
- **Outputs:** 1 connection
- **Use Case:** Define where the agent begins processing

### Process (Blue)
- **Purpose:** LLM processing step
- **Configuration:**
  - Model (gpt-4o, gpt-4o-mini, claude-3-opus, etc.)
  - Temperature (0.0 - 2.0)
  - Max Tokens
- **Use Case:** Natural language understanding, generation, reasoning

### Decision (Yellow)
- **Purpose:** Conditional branching
- **Configuration:**
  - Add conditions (field, operator, value)
  - Multiple output paths (true, false, default)
- **Use Case:** Route based on state, validate inputs, implement logic

### Tool Call (Purple)
- **Purpose:** Execute external tools/APIs
- **Configuration:**
  - Tool name (e.g., `web_search`, `calculator`)
  - Parameters (JSON)
- **Use Case:** Call external services, fetch data, perform actions

### End (Red)
- **Purpose:** Terminate the workflow
- **Inputs:** 1 connection
- **Use Case:** Define successful completion points

---

## YAML Preview

**Location:** Bottom panel

**Features:**
- **Live Update:** YAML updates as you modify the graph
- **Validation:** Shows errors if graph is invalid
- **Copy:** Copy YAML to clipboard
- **Download:** Save YAML file locally
- **Syntax Highlighting:** Easy to read format

**Validation Rules:**
- Must have at least one Entry Point
- All nodes must be connected
- No circular dependencies (future enhancement)

---

## Keyboard Shortcuts

- **Delete Node:** Select node → Delete/Backspace key (future enhancement)
- **Pan Canvas:** Click and drag on background
- **Zoom:** Mouse wheel / trackpad pinch
- **Select Multiple:** Shift + Click (future enhancement)

---

## API Reference

Forge AI uses the Forge Service API (port 8003):

### Create Agent
```bash
POST /api/forge/agents
{
  "name": "my-agent",
  "graph": { "nodes": [...], "edges": [...] },
  "environment": "dev",
  "description": "My custom agent"
}
```

### List Agents
```bash
GET /api/forge/agents
```

### Get Agent
```bash
GET /api/forge/agents/{agent_name}
```

### Update Agent
```bash
PUT /api/forge/agents/{agent_name}
{
  "graph": { "nodes": [...], "edges": [...] }
}
```

### Deploy Agent
```bash
POST /api/forge/agents/{agent_name}/deploy
{
  "environment": "prod",
  "git_commit": false
}
```

### Delete Agent
```bash
DELETE /api/forge/agents/{agent_name}
```

---

## Environment Configuration

Add to `.env.local`:

```bash
# Forge Service
FORGE_PORT=8003
NEXT_PUBLIC_FORGE_API_URL=http://localhost:8003
```

---

## Troubleshooting

### Agent Won't Save
- **Check:** Agent name must be unique
- **Check:** Graph must have at least one Entry Point
- **Check:** Forge Service running on port 8003

### YAML Validation Errors
- **Missing Entry Point:** Add an Entry Point node
- **Invalid YAML:** Check error details in red banner
- **Empty Graph:** Add at least one node

### Deploy Fails
- **Check:** Agent must be saved first
- **Check:** Environment must be dev/staging/prod
- **Check:** No syntax errors in graph

### Forge Service Not Running
```bash
# Start Forge Service
docker-compose up forge-service

# Or run standalone
cd forge_service
python main.py
```

---

## File Locations

**Agent YAML Files:**
- Dev: `/agents/{name}.dev.agent.yaml`
- Staging: `/agents/{name}.staging.agent.yaml`
- Production: `/agents/{name}.agent.yaml`

**Forge Data:**
- `/data/forge/` - Forge-specific metadata

---

## Roadmap (Future Phases)

### Phase 2: Enhanced CRUD
- [ ] Manual YAML editing with Monaco
- [ ] Import existing YAML files
- [ ] Agent registry browser
- [ ] Search and filter agents

### Phase 3: System Agents
- [ ] System agent configuration panel
- [ ] Supervisor, IO, Coherence agent templates
- [ ] Health monitoring dashboard

### Phase 4: Multi-Environment
- [ ] Environment switcher
- [ ] Promote from dev → staging → prod
- [ ] Diff view before deployment
- [ ] Rollback capability

### Phase 5: GitOps
- [ ] Auto-commit to Git on save
- [ ] Pull latest from Git branch
- [ ] Create PR for production deploys
- [ ] Git history browser

### Phase 6: Multi-User
- [ ] Role-based access control
- [ ] Concurrent editing (optimistic locking)
- [ ] Activity feed
- [ ] Draft mode

---

## Support

**Documentation:** `/docs/FORGE_AI_USER_GUIDE.md`
**API Docs:** http://localhost:8003/docs
**Issues:** Report bugs via GitHub Issues

---

**Built with:**
- React Flow (graph visualization)
- Monaco Editor (YAML editing)
- FastAPI (backend API)
- Shadcn UI (components)
- Ravenhelm theme (dark mode)
