# Admin UI Requirements - Agent Management

**Date**: November 11, 2025  
**Version**: v0.8.0 Target  
**Priority**: P1 - Core Operations Feature  

---

## Overview

Administrative interface for viewing, monitoring, and configuring AI agents in the Engineering Department environment.

## User Stories

### As a System Administrator
- I need to see all active agents in the environment
- I need to view each agent's configuration and capabilities
- I need to monitor agent performance and health
- I need to adjust agent settings without code changes
- I need to enable/disable agents dynamically
- I need to view agent execution history and logs

### As a DevOps Engineer
- I need to debug agent behavior in production
- I need to see which tools each agent has access to
- I need to monitor token usage and costs per agent
- I need to trace agent state transitions
- I need to export agent configurations

### As a Product Owner
- I need to understand what agents can do
- I need to see agent usage metrics
- I need to plan agent capacity and scaling

---

## UI Structure

```
┌─────────────────────────────────────────────┐
│  Engineering Department - Admin             │
├─────────────────────────────────────────────┤
│                                             │
│  Sidebar:                                   │
│  ├─ Dashboard                              │
│  ├─ Agents ◄── YOU ARE HERE                │
│  ├─ Tools                                   │
│  ├─ Integrations                           │
│  ├─ Audit Logs                             │
│  ├─ Settings                               │
│  └─ Users                                   │
│                                             │
│  Main Content:                              │
│  ┌─────────────────────────────────────┐   │
│  │  Agents Overview                     │   │
│  ├─────────────────────────────────────┤   │
│  │                                      │   │
│  │  [Search] [Filter ▼] [+ New Agent]  │   │
│  │                                      │   │
│  │  ┌────────────────────────────────┐ │   │
│  │  │ PM Agent              ●Active  │ │   │
│  │  │ Story creation & management    │ │   │
│  │  │ Tools: 1 | LLM: GPT-4         │ │   │
│  │  │ [View] [Configure] [Disable]  │ │   │
│  │  └────────────────────────────────┘ │   │
│  │                                      │   │
│  │  ┌────────────────────────────────┐ │   │
│  │  │ QA Agent              ○Inactive│ │   │
│  │  │ Test generation & execution    │ │   │
│  │  │ Tools: 0 | LLM: GPT-3.5       │ │   │
│  │  │ [View] [Configure] [Enable]   │ │   │
│  │  └────────────────────────────────┘ │   │
│  │                                      │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Agent Detail View

```
┌─────────────────────────────────────────────────┐
│  PM Agent                                       │
├─────────────────────────────────────────────────┤
│                                                 │
│  [← Back to Agents]                             │
│                                                 │
│  ┌─ Overview ─────────────────────────────────┐│
│  │ Status: ●Active                            ││
│  │ Type: LangGraph StateGraph                 ││
│  │ Version: 1.0.0                             ││
│  │ Created: 2025-11-10                        ││
│  │ Last Modified: 2025-11-11                  ││
│  └───────────────────────────────────────────┘│
│                                                 │
│  ┌─ Configuration ──────────────────────────┐  │
│  │ LLM Model: GPT-4                  [Edit] │  │
│  │ Temperature: 0.3                  [Edit] │  │
│  │ Max Tokens: 2000                  [Edit] │  │
│  │ Recursion Limit: 100              [Edit] │  │
│  │ Timeout: 30s                      [Edit] │  │
│  │                                           │  │
│  │ [Save Changes] [Reset to Default]        │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Workflow Graph ─────────────────────────┐  │
│  │                                           │  │
│  │     understand → validate → plan          │  │
│  │         ↓           ↓                     │  │
│  │      clarify    create_story → complete   │  │
│  │                     ↓                     │  │
│  │                   error                   │  │
│  │                                           │  │
│  │  [View Full Graph] [Export DOT]          │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Tools (1) ──────────────────────────────┐  │
│  │ ✓ Notion Story Creation                  │  │
│  │   - Create stories with AC/DoD           │  │
│  │   - Endpoint: /api/tools/notion/create   │  │
│  │   - Status: Connected                    │  │
│  │                                           │  │
│  │ [Add Tool] [Manage Tools]                │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Performance Metrics ────────────────────┐  │
│  │ Total Requests: 147                      │  │
│  │ Success Rate: 94.6%                      │  │
│  │ Avg Response Time: 3.2s                  │  │
│  │ Avg Tokens Used: 1,450                   │  │
│  │ Total Cost (24h): $2.47                  │  │
│  │                                           │  │
│  │ [View Detailed Metrics]                  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌─ Recent Activity ────────────────────────┐  │
│  │ 2 min ago  │ Story created   │ Success   │  │
│  │ 5 min ago  │ Clarification   │ Success   │  │
│  │ 12 min ago │ Story created   │ Success   │  │
│  │ 18 min ago │ Validation fail │ Error     │  │
│  │                                           │  │
│  │ [View Full History] [Export Logs]        │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Agent Discovery
- **Auto-detection** of agents in the system
- **Agent registry** with metadata
- **Health checks** for each agent
- **Dependency tracking** (which agents depend on which tools)

### 2. Configuration Management
- **Live editing** of agent parameters
- **Version control** for configurations
- **Environment-specific** settings (dev/staging/prod)
- **Rollback** to previous configurations
- **Validation** before applying changes

### 3. Monitoring & Observability
- **Real-time metrics** dashboard
- **Performance graphs** (latency, throughput, errors)
- **Cost tracking** per agent
- **Token usage** visualization
- **Alert configuration** for anomalies

### 4. Workflow Visualization
- **Interactive graph** of agent state machine
- **Node execution counts** (which nodes run most often)
- **Path analysis** (common execution paths)
- **Bottleneck detection**
- **Export to Graphviz/Mermaid**

### 5. Execution History
- **Request/response logs**
- **State transitions** for each execution
- **Error traces** with stack traces
- **Performance profiling** per node
- **Search and filter** by date, status, user

### 6. Security & Access Control
- **Role-based access** (admin, operator, viewer)
- **Audit trail** of configuration changes
- **API key management** per agent
- **Rate limiting** configuration
- **IP whitelisting**

---

## Backend API Requirements

### Agent Registry API

```python
# GET /api/admin/agents
# Returns list of all agents
{
  "agents": [
    {
      "id": "pm-agent-1",
      "name": "PM Agent",
      "type": "langgraph",
      "status": "active",
      "version": "1.0.0",
      "created_at": "2025-11-10T10:00:00Z",
      "updated_at": "2025-11-11T14:30:00Z",
      "config": {...},
      "metrics": {...}
    }
  ]
}

# GET /api/admin/agents/{agent_id}
# Returns detailed info about specific agent

# PUT /api/admin/agents/{agent_id}/config
# Update agent configuration

# POST /api/admin/agents/{agent_id}/enable
# Enable agent

# POST /api/admin/agents/{agent_id}/disable
# Disable agent

# GET /api/admin/agents/{agent_id}/metrics
# Get performance metrics

# GET /api/admin/agents/{agent_id}/history
# Get execution history
```

### Agent Metadata Schema

```python
class AgentMetadata(BaseModel):
    id: str
    name: str
    description: str
    type: str  # "langgraph", "react", "function_calling"
    version: str
    status: str  # "active", "inactive", "error"
    
    # Configuration
    llm_model: str
    temperature: float
    max_tokens: int
    timeout: int
    recursion_limit: Optional[int]
    
    # Workflow
    nodes: List[str]
    edges: List[Dict[str, str]]
    entry_point: str
    
    # Tools
    tools: List[ToolInfo]
    
    # Metrics
    total_requests: int
    success_rate: float
    avg_response_time: float
    avg_tokens_used: float
    total_cost: float
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_execution: Optional[datetime]
```

---

## Implementation Plan

### Phase 1: Backend Infrastructure (3-4 hours)

#### 1.1 Agent Registry
```python
# File: mcp/registry/agent_registry.py

class AgentRegistry:
    """Central registry for all agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentMetadata] = {}
    
    def register(self, agent: AgentMetadata):
        """Register a new agent."""
        self.agents[agent.id] = agent
    
    def get(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_all(self) -> List[AgentMetadata]:
        """List all registered agents."""
        return list(self.agents.values())
    
    def update_metrics(self, agent_id: str, metrics: Dict):
        """Update agent metrics."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.total_requests += 1
            # Update other metrics
```

#### 1.2 Agent Discovery
```python
# File: mcp/registry/agent_discovery.py

class AgentDiscovery:
    """Automatically discover agents in the system."""
    
    async def discover_agents(self) -> List[AgentMetadata]:
        """Scan codebase for agent implementations."""
        agents = []
        
        # Scan agent directory
        agent_files = Path("agent").glob("*_agent.py")
        
        for file in agent_files:
            metadata = await self._extract_metadata(file)
            agents.append(metadata)
        
        return agents
    
    async def _extract_metadata(self, file: Path) -> AgentMetadata:
        """Extract metadata from agent file."""
        # Parse file, extract class, read docstrings, etc.
        pass
```

#### 1.3 Admin API Endpoints
```python
# File: mcp_server.py

from mcp.registry.agent_registry import AgentRegistry

registry = AgentRegistry()

@app.get("/api/admin/agents")
async def list_agents(auth: str = Depends(verify_admin_auth)):
    """List all agents."""
    agents = registry.list_all()
    return {"agents": [a.dict() for a in agents]}

@app.get("/api/admin/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    auth: str = Depends(verify_admin_auth)
):
    """Get agent details."""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.dict()

@app.put("/api/admin/agents/{agent_id}/config")
async def update_agent_config(
    agent_id: str,
    config: Dict[str, Any],
    auth: str = Depends(verify_admin_auth)
):
    """Update agent configuration."""
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Validate config
    # Update agent
    # Reload if needed
    
    return {"success": True, "agent": agent.dict()}

@app.get("/api/admin/agents/{agent_id}/metrics")
async def get_agent_metrics(
    agent_id: str,
    time_range: str = "24h",
    auth: str = Depends(verify_admin_auth)
):
    """Get agent performance metrics."""
    # Query metrics from audit logs or metrics DB
    return {
        "agent_id": agent_id,
        "time_range": time_range,
        "metrics": {...}
    }

@app.get("/api/admin/agents/{agent_id}/history")
async def get_agent_history(
    agent_id: str,
    limit: int = 50,
    offset: int = 0,
    auth: str = Depends(verify_admin_auth)
):
    """Get agent execution history."""
    # Query audit logs
    return {
        "executions": [...],
        "total": 1000,
        "limit": limit,
        "offset": offset
    }
```

### Phase 2: Frontend UI (4-6 hours)

#### 2.1 Create Admin Layout
```typescript
// app/admin/layout.tsx
export default function AdminLayout({ children }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

#### 2.2 Agents List Page
```typescript
// app/admin/agents/page.tsx
'use client';

import { useState, useEffect } from 'react';

export default function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchAgents();
  }, []);
  
  const fetchAgents = async () => {
    const response = await fetch('/api/admin/agents');
    const data = await response.json();
    setAgents(data.agents);
    setLoading(false);
  };
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Agents</h1>
      
      <div className="grid gap-4">
        {agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </div>
  );
}
```

#### 2.3 Agent Detail Page
```typescript
// app/admin/agents/[id]/page.tsx
export default function AgentDetailPage({ params }) {
  const { id } = params;
  const [agent, setAgent] = useState(null);
  
  // Fetch agent details, metrics, history
  
  return (
    <div className="p-6">
      <AgentOverview agent={agent} />
      <AgentConfiguration agent={agent} />
      <WorkflowGraph agent={agent} />
      <PerformanceMetrics agentId={id} />
      <RecentActivity agentId={id} />
    </div>
  );
}
```

#### 2.4 Configuration Editor
```typescript
// app/admin/agents/[id]/components/ConfigurationEditor.tsx
export function ConfigurationEditor({ agent, onSave }) {
  const [config, setConfig] = useState(agent.config);
  const [dirty, setDirty] = useState(false);
  
  const handleSave = async () => {
    await fetch(`/api/admin/agents/${agent.id}/config`, {
      method: 'PUT',
      body: JSON.stringify(config)
    });
    onSave();
  };
  
  return (
    <div className="space-y-4">
      <ConfigField 
        label="LLM Model"
        value={config.llm_model}
        onChange={(v) => setConfig({...config, llm_model: v})}
      />
      <ConfigField 
        label="Temperature"
        type="number"
        value={config.temperature}
        onChange={(v) => setConfig({...config, temperature: v})}
      />
      {/* More fields */}
      
      {dirty && (
        <div className="flex gap-2">
          <button onClick={handleSave}>Save Changes</button>
          <button onClick={resetConfig}>Reset</button>
        </div>
      )}
    </div>
  );
}
```

### Phase 3: Visualization & Monitoring (3-4 hours)

#### 3.1 Workflow Graph Visualization
```typescript
// Using React Flow or D3.js
import ReactFlow from 'reactflow';

export function WorkflowGraph({ agent }) {
  const nodes = agent.nodes.map(node => ({
    id: node,
    data: { label: node },
    position: calculatePosition(node)
  }));
  
  const edges = agent.edges.map(edge => ({
    id: `${edge.source}-${edge.target}`,
    source: edge.source,
    target: edge.target
  }));
  
  return (
    <ReactFlow nodes={nodes} edges={edges} />
  );
}
```

#### 3.2 Metrics Dashboard
```typescript
// Using Recharts
import { LineChart, Line, XAxis, YAxis } from 'recharts';

export function MetricsDashboard({ agentId }) {
  const [metrics, setMetrics] = useState([]);
  
  useEffect(() => {
    fetchMetrics(agentId);
  }, [agentId]);
  
  return (
    <div className="grid grid-cols-2 gap-4">
      <MetricCard 
        title="Response Time"
        value={metrics.avgResponseTime}
        chart={<ResponseTimeChart data={metrics.timeSeries} />}
      />
      <MetricCard 
        title="Success Rate"
        value={`${metrics.successRate}%`}
        chart={<SuccessRateChart data={metrics.timeSeries} />}
      />
      {/* More metrics */}
    </div>
  );
}
```

---

## Security Considerations

### Authentication
- Admin routes require authentication
- JWT tokens with admin role
- Session management
- API key rotation

### Authorization
- Role-based access control (RBAC)
- Permissions: `agent:read`, `agent:write`, `agent:execute`
- Audit all configuration changes
- IP whitelisting for admin endpoints

### Data Protection
- Sensitive config values encrypted
- API keys stored in secrets manager
- Logs sanitized (no PII)
- Export restrictions on production data

---

## Testing Requirements

### Unit Tests
- Agent registry CRUD operations
- Configuration validation
- Metrics aggregation
- Access control logic

### Integration Tests
- API endpoints
- Agent discovery
- Configuration updates
- Metrics collection

### E2E Tests
- Admin login flow
- View agents list
- Edit configuration
- View metrics dashboard

---

## Documentation

### Admin Guide
- How to access admin UI
- How to configure agents
- How to interpret metrics
- Troubleshooting common issues

### API Documentation
- OpenAPI spec for admin endpoints
- Authentication guide
- Rate limits
- Example requests/responses

---

## Success Criteria

- [ ] All agents visible in UI
- [ ] Configuration editable via UI
- [ ] Metrics displayed in real-time
- [ ] Execution history searchable
- [ ] Workflow graph visualized
- [ ] Changes require authentication
- [ ] All actions audited
- [ ] Performance acceptable (< 500ms page load)

---

**Estimated Effort**: 10-14 hours  
**Priority**: P1  
**Dependencies**: Agent registry, metrics collection, audit logging  
**Target Release**: v0.8.0
