# LangGraph Agents Overview - Agent Foundry

**Last Updated:** 2025-11-16 **Total LangGraph Agents:** 12+ agents across
multiple layers

This document catalogs all LangGraph-based agents in the Agent Foundry platform,
organized by architecture layer.

---

## 🏗️ Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Interface                        │
│                    (Chat, Voice, API)                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        IO Agent                             │
│           (Channel Detection & Normalization)               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Supervisor Agent                         │
│              (LangGraph StateGraph Orchestrator)            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Context    │  │   Worker     │  │  Coherence   │    │
│  │   Agent      │→ │   Routing    │→ │   Agent      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────┬────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │ Worker   │ │ Worker   │ │ Worker   │
         │ Agents   │ │ Agents   │ │ Agents   │
         └──────────┘ └──────────┘ └──────────┘
```

---

## 📊 Agent Catalog

### **Layer 1: Infrastructure Agents** (Meta-Agents)

#### 1. **MarshalAgent** 🎖️

- **File:** `agents/marshal_agent.py`
- **Type:** Meta-Agent (Agent Lifecycle Manager)
- **LangGraph:** No (Pure orchestration)
- **Purpose:** Manages the entire agent registry
- **Responsibilities:**
  - Load agents from YAML files
  - Hot-reload on file changes
  - Validate agent configurations
  - Health monitoring
  - Registry management

```python
# Usage
marshal = MarshalAgent(agents_dir="/path/to/agents")
await marshal.start()
# Manages all agents in background
```

---

### **Layer 2: I/O & Orchestration**

#### 2. **IOAgent** 📡

- **File:** `agents/io_agent.py`
- **Type:** I/O Adapter
- **LangGraph:** No (Pure I/O)
- **Purpose:** Channel detection and format normalization
- **Responsibilities:**
  - Detect channel (voice, chat, API)
  - Normalize input to standard format
  - Route to Supervisor
  - Format responses per channel
  - Deliver to user

```python
# Channels supported:
- chat (WebSocket, UI)
- voice (LiveKit)
- api (REST/GraphQL)
```

#### 3. **SupervisorAgent** 🧠

- **File:** `agents/supervisor_agent.py`
- **Type:** LangGraph StateGraph Orchestrator
- **LangGraph:** ✅ **Yes** - Main coordination graph
- **Purpose:** Orchestrate all worker agents
- **Architecture:**
  ```python
  StateGraph(AgentState):
    1. load_context    → ContextAgent
    2. analyze_request → LLM routing
    3. route_workers   → Conditional routing
    4. compile_response→ CoherenceAgent
    5. END
  ```

**Graph Nodes:**

- `load_context` - Context enrichment
- `analyze_request` - Intent analysis & routing
- `pm_agent` - PM worker (conditional)
- `compile_response` - Response aggregation

**Routing Logic:**

```python
{
    "pm_agent": "pm_agent",      # Project management tasks
    "FINISH": "compile_response" # Generic responses
}
```

---

### **Layer 3: Platform Agents** (Supervisor's Helpers)

#### 4. **ContextAgent** 🗂️

- **File:** `agents/workers/context_agent.py`
- **Type:** Context Enrichment
- **LangGraph:** No (Helper)
- **Purpose:** Load session and user context
- **Features:**
  - Session history retrieval
  - User preferences
  - Project context
  - Conversation memory

#### 5. **CoherenceAgent** 🎯

- **File:** `agents/workers/coherence_agent.py`
- **Type:** Response Aggregation
- **LangGraph:** No (Helper)
- **Purpose:** Compile multi-agent responses
- **Features:**
  - Merge responses from multiple workers
  - Resolve conflicts
  - Ensure consistent tone
  - Format final output

---

### **Layer 4: Worker Agents** (Domain-Specific)

#### 6. **PMAgent** (Primary) 📋

- **File:** `agent/pm_graph.py`
- **Type:** LangGraph ReAct Agent
- **LangGraph:** ✅ **Yes** - `create_react_agent`
- **Purpose:** Project management tasks
- **Tools:**
  - `create_notion_story` - Create stories in Notion
  - Story validation
  - Epic management
  - Priority assignment

```python
# Built with create_react_agent pattern
graph = create_react_agent(
    model=llm,
    tools=[create_notion_story],
    state_modifier=system_message
)
```

**Capabilities:**

- Create user stories
- Link to epics
- Set priorities (P0-P3)
- Acceptance criteria
- Definition of done

#### 7. **PMAgent** (Worker) 📊

- **File:** `agents/workers/pm_agent.py`
- **Type:** Simplified PM Worker
- **LangGraph:** No (Tool wrapper)
- **Purpose:** Delegated from Supervisor
- **Note:** Wrapper around main PMAgent for supervisor integration

#### 8. **SimplifiedPMAgent** 🎨

- **File:** `agent/pm_agent_simple.py`
- **Type:** Lightweight PM Agent
- **LangGraph:** No
- **Purpose:** Simple PM tasks without full graph

---

### **Layer 5: Specialized Agents**

#### 9. **ManifestAgent** 📜

- **File:** `agent/manifest_agent.py`
- **Type:** LangGraph StateGraph
- **LangGraph:** ✅ **Yes**
- **Purpose:** Agent manifest management (YAML → Runtime)
- **Architecture:**
  ```python
  StateGraph(ManifestState):
    1. validate_yaml
    2. parse_structure
    3. generate_graph
    4. compile_agent
  ```

**Responsibilities:**

- Parse .agent.yaml files
- Validate structure
- Generate LangGraph from YAML
- Register in manifest

#### 10. **DataAgent** 💾

- **File:** `agent/data_agent.py`
- **Type:** LangGraph StateGraph
- **LangGraph:** ✅ **Yes**
- **Purpose:** Data operations and transformations
- **Architecture:**
  ```python
  StateGraph(DataAgentState):
    1. fetch_data
    2. transform
    3. validate
    4. store
  ```

**Use Cases:**

- Database queries
- Data transformations
- ETL operations
- Schema validation

#### 11. **FormDataAgent** 📝

- **File:** `agent/form_data_agent.py`
- **Type:** LangGraph StateGraph
- **LangGraph:** ✅ **Yes**
- **Purpose:** Form data validation and processing
- **Architecture:**
  ```python
  StateGraph(FormDataState):
    1. parse_form
    2. validate_fields
    3. process_submission
    4. generate_response
  ```

#### 12. **ObjectAdminAgent** ⚙️

- **File:** `agent/object_admin_agent.py`
- **Type:** LangGraph StateGraph
- **LangGraph:** ✅ **Yes**
- **Purpose:** Admin operations on objects
- **Architecture:**
  ```python
  StateGraph(ObjectAdminState):
    1. authenticate
    2. validate_permissions
    3. execute_operation
    4. audit_log
  ```

---

### **Layer 6: Platform Support Agents**

#### 13. **ExceptionAgent** ⚠️

- **File:** `agents/workers/exception_agent.py`
- **Type:** Error Handling
- **LangGraph:** No
- **Purpose:** Exception handling and recovery
- **Features:**
  - Error categorization
  - Recovery strategies
  - User-friendly error messages
  - Retry logic

#### 14. **GovernanceAgent** 🛡️

- **File:** `agents/workers/governance_agent.py`
- **Type:** Policy Enforcement
- **LangGraph:** No
- **Purpose:** Governance and compliance
- **Features:**
  - Policy checks
  - Compliance validation
  - Audit logging
  - Access control

#### 15. **ObservabilityAgent** 📈

- **File:** `agents/workers/observability_agent.py`
- **Type:** Monitoring & Telemetry
- **LangGraph:** No
- **Purpose:** System observability
- **Features:**
  - Metrics collection
  - Trace propagation
  - Log aggregation
  - Performance monitoring

---

## 🔧 LangGraph Usage Patterns

### **Pattern 1: StateGraph (Custom Workflows)**

Used by: ManifestAgent, DataAgent, FormDataAgent, ObjectAdminAgent

```python
from langgraph.graph import StateGraph, END

class CustomState(TypedDict):
    field1: str
    field2: list

builder = StateGraph(CustomState)
builder.add_node("step1", step1_func)
builder.add_node("step2", step2_func)
builder.set_entry_point("step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", END)

graph = builder.compile()
```

### **Pattern 2: create_react_agent (ReAct Pattern)**

Used by: PMAgent

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def my_tool(arg: str) -> str:
    """Tool description."""
    return f"Result: {arg}"

graph = create_react_agent(
    model=llm,
    tools=[my_tool],
    state_modifier=system_message
)
```

### **Pattern 3: Conditional Routing**

Used by: SupervisorAgent

```python
workflow.add_conditional_edges(
    "analyze_request",
    route_function,
    {
        "worker1": "worker1_node",
        "worker2": "worker2_node",
        "default": END
    }
)

def route_function(state):
    if state["intent"] == "pm":
        return "worker1"
    return "default"
```

---

## 📁 File Organization

```
agentfoundry/
├── agents/                    # Main agent system
│   ├── io_agent.py           # I/O adapter
│   ├── supervisor_agent.py   # Main orchestrator (LangGraph)
│   ├── marshal_agent.py      # Meta-agent
│   ├── state.py              # Shared state definitions
│   └── workers/              # Worker agents
│       ├── pm_agent.py       # PM worker
│       ├── context_agent.py  # Context enrichment
│       ├── coherence_agent.py# Response aggregation
│       ├── exception_agent.py
│       ├── governance_agent.py
│       └── observability_agent.py
│
└── agent/                     # Specialized agents
    ├── pm_graph.py           # PM ReAct agent (LangGraph)
    ├── manifest_agent.py     # Manifest management (LangGraph)
    ├── data_agent.py         # Data operations (LangGraph)
    ├── form_data_agent.py    # Form processing (LangGraph)
    ├── object_admin_agent.py # Admin operations (LangGraph)
    └── pm_agent_simple.py    # Lightweight PM
```

---

## 🎯 Agent Selection Guide

**When to use which agent:**

| Task                 | Agent                 | Why                      |
| -------------------- | --------------------- | ------------------------ |
| User message arrives | IOAgent               | Channel detection        |
| Orchestrate workflow | SupervisorAgent       | Multi-agent coordination |
| PM task              | PMAgent (pm_graph.py) | Full ReAct with tools    |
| Load YAML agent      | ManifestAgent         | YAML → Graph conversion  |
| Data transformation  | DataAgent             | ETL operations           |
| Form validation      | FormDataAgent         | Structured input         |
| Admin operations     | ObjectAdminAgent      | Privileged operations    |
| Error handling       | ExceptionAgent        | Recovery strategies      |

---

## 🔄 Message Flow Example

```
User: "Create a story for user authentication"
  │
  ▼
IOAgent (detects channel: chat)
  │
  ▼
SupervisorAgent (StateGraph)
  │
  ├─> load_context (ContextAgent)
  │     └─> Session history, user preferences
  │
  ├─> analyze_request (LLM)
  │     └─> Intent: "pm_task"
  │
  ├─> route_workers (Conditional)
  │     └─> Route to: pm_agent
  │
  ├─> pm_agent (PMAgent ReAct)
  │     ├─> Tool: create_notion_story
  │     ├─> Epic: User Authentication
  │     ├─> Priority: P1
  │     └─> Result: Story created
  │
  └─> compile_response (CoherenceAgent)
        └─> "✅ Created story: User Auth Login"
  │
  ▼
IOAgent (format for chat channel)
  │
  ▼
User receives: "✅ Created story: User Auth Login in Epic 'User Authentication' with priority P1"
```

---

## 📊 Statistics

- **Total Agents:** 15+
- **LangGraph Agents:** 6 (SupervisorAgent, PMAgent, ManifestAgent, DataAgent,
  FormDataAgent, ObjectAdminAgent)
- **StateGraph Pattern:** 5 agents
- **ReAct Pattern:** 1 agent (PMAgent)
- **Helper Agents:** 9 (Context, Coherence, Exception, Governance,
  Observability, etc.)

---

## 🚀 Adding New Agents

### **Option 1: YAML-Defined Agent (Recommended)**

1. Create `.agent.yaml` file in agents directory
2. MarshalAgent auto-loads on startup
3. ManifestAgent compiles to LangGraph

### **Option 2: Custom LangGraph Agent**

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class MyAgentState(TypedDict):
    input: str
    output: str

class MyAgent:
    def __init__(self):
        builder = StateGraph(MyAgentState)
        builder.add_node("process", self.process_node)
        builder.set_entry_point("process")
        builder.add_edge("process", END)
        self.graph = builder.compile()

    def process_node(self, state: MyAgentState):
        # Your logic here
        return {"output": f"Processed: {state['input']}"}

    async def run(self, input_text: str):
        result = await self.graph.ainvoke({"input": input_text})
        return result["output"]
```

### **Option 3: ReAct Agent**

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Tool description."""
    return "Result"

class MyReActAgent:
    def __init__(self):
        self.graph = create_react_agent(
            model=ChatOpenAI(model="gpt-4"),
            tools=[my_tool]
        )
```

---

## 📚 Resources

- **LangGraph Docs:** https://langchain-ai.github.io/langgraph/
- **Agent State:** `agents/state.py`
- **Tests:** `tests/unit/agents/` and `tests/integration/`
- **Examples:** `archive/pm_agent/` (historical implementations)

---

**Generated by:** Claude Code **Version:** 1.0 **Last Updated:** 2025-11-16
