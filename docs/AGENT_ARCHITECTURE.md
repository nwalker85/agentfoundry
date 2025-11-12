# PM Agent Architecture Deep Dive

**Understanding the LangGraph-Based PM Agent**

---

## Core Components

### 1. State Machine (LangGraph StateGraph)

The agent is a **finite state machine** with typed state and deterministic transitions.

**State Definition:**
```python
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]          # Conversation history
    current_task: Optional[Dict[str, Any]]   # Current task being worked on
    epic_title: Optional[str]                # Extracted epic name
    story_title: Optional[str]               # Extracted story title
    priority: Optional[str]                  # P0/P1/P2/P3
    acceptance_criteria: Optional[List[str]] # AC list
    definition_of_done: Optional[List[str]]  # DoD checklist
    description: Optional[str]               # Story description
    clarifications_needed: Optional[List[str]] # Questions for user
    clarification_count: int                 # Prevents infinite loops
    story_url: Optional[str]                 # Created Notion story URL
    issue_url: Optional[str]                 # Created GitHub issue URL
    error_message: Optional[str]             # Error tracking
    next_action: Optional[str]               # State indicator
```

This is **strongly typed** - each field has a specific type and purpose.

### 2. Workflow Graph (6 Nodes)

```
┌─────────────┐
│  UNDERSTAND │  Node 1: Extract task details from user message
└──────┬──────┘
       │
       ├─ clarify? ──> ┌─────────┐
       │                │ CLARIFY │  Node 2: Ask follow-up questions
       │                └────┬────┘
       │                     │
       └─ validate ─────────┘
                             ↓
                      ┌──────────┐
                      │ VALIDATE │  Node 3: Ensure all required fields present
                      └─────┬────┘
                            │
                      ┌─────────┐
                      │  PLAN   │  Node 4: Decide execution steps
                      └────┬────┘
                           │
                   ┌───────────────┐
                   │ CREATE_STORY  │  Node 5: Call MCP API to create Notion story
                   └───────┬───────┘
                           │
                      ┌─────────┐
                      │COMPLETE │  Node 6: Build success response
                      └─────────┘
```

**Error Node** (not shown): Handles failures at any stage

### 3. LLM Integration (GPT-4)

The agent uses GPT-4 for **structured extraction only**:
- Extracting epic, title, priority, description from natural language
- NOT for decision-making (graph controls workflow)

```python
self.llm = ChatOpenAI(
    model="gpt-4",           # Could use Claude instead
    temperature=0.3,         # Low = deterministic
    api_key=os.getenv("OPENAI_API_KEY")
)
```

**Temperature 0.3** = relatively deterministic responses.

### 4. Node Functions (Business Logic)

Each node is a pure async function:

```python
async def understand_task(self, state: AgentState) -> AgentState:
    """
    Takes: AgentState with user message
    Does: Calls GPT-4 to extract structured fields
    Returns: Updated AgentState with extracted data
    """
```

**Key insight**: Nodes transform state, they don't mutate globals.

### 5. Routing Logic (Deterministic)

Routers use Python logic, not LLM calls:

```python
def route_after_understand(self, state: AgentState) -> str:
    """Decision tree executed in milliseconds"""
    if state.get("error_message"):
        return "error"
    if state.get("clarifications_needed"):
        return "clarify"  
    return "validate"
```

This is **fast and deterministic** - no LLM call needed.

### 6. MCP Integration (HTTP Client)

Agent calls MCP Server for tool execution:

```python
self.client = httpx.AsyncClient(base_url="http://localhost:8001")

# In create_story node:
response = await self.client.post(
    "/api/tools/notion/create-story",
    json={"epic_title": ..., "story_title": ...}
)
```

**Why MCP layer?**
- Separation of concerns
- Idempotency protection  
- Audit logging
- Rate limiting
- Error handling

---

## Architecture Patterns

### 1. State-Driven
All data flows through `AgentState`. No globals, no side effects.

### 2. Deterministic Routing
Business logic in Python, not prompts. Faster and more reliable.

### 3. Separation of Concerns
- **Agent**: Workflow orchestration
- **LLM**: Natural language understanding only
- **MCP Server**: Tool execution
- **Tools**: External API integration

### 4. Error Recovery
Every node can set `error_message`, routing logic detects and handles.

### 5. Loop Prevention
`clarification_count` limits prevent infinite clarification loops (max 2).

---

## What Makes This Different?

### Simple LLM Approach:
```python
response = llm.invoke("Create a story for user auth")
# Hope it works, parse manually, no validation
```

### LangGraph Agent:
```python
state = {"messages": [HumanMessage(content="...")]}
final_state = await graph.ainvoke(state)
# - Structured extraction
# - Validation with defaults
# - Retry logic
# - Multi-turn clarification
# - Tool execution
# - Error handling
# - Audit trail
```

---

## Current Capabilities

### What It Can Do ✅
- Extract structured task details from natural language
- Ask clarifying questions (max 2 rounds)
- Create Notion stories with AC/DoD
- Handle errors gracefully
- Maintain conversation context

### What It Cannot Do ❌
- Answer general questions
- Search the web
- Execute code
- Read/write files
- Access databases directly
- Complex multi-turn reasoning
- Tool selection (only has 1 tool)

---

## How to Extend

### Add More Nodes:
```python
workflow.add_node("research", self.research_topic)
workflow.add_edge("plan", "research")
```

### Add More Tools (via MCP):
```python
# In MCP server:
@app.post("/api/tools/search")
async def search_web(query: str):
    return {"results": [...]}
    
# In agent:
async def research_topic(self, state: AgentState):
    response = await self.client.post(
        "/api/tools/search",
        json={"query": state["research_query"]}
    )
    state["research_results"] = response.json()
    return state
```

### Add LLM Tool Selection:
```python
from langgraph.prebuilt import ToolExecutor
from langchain.tools import Tool

tools = [
    Tool(name="create_story", func=...),
    Tool(name="search_web", func=...),
    Tool(name="execute_code", func=...)
]

tool_executor = ToolExecutor(tools)
# Now LLM can choose which tool to use
```

---

## Comparison to Other Patterns

| Pattern | Decision Making | Speed | Flexibility |
|---------|----------------|-------|-------------|
| **This Agent** | Predefined workflow | Fast | Medium |
| ReAct Agent | LLM decides each step | Slow | High |
| Function Calling | Single LLM call | Fast | Low |
| LangChain Chains | Linear pipeline | Fast | Low |

---

## Configuration

### Recursion Limit:
```python
final_state = await self.graph.ainvoke(
    initial_state,
    config={"recursion_limit": 100}
)
```
Default is 25. Increase for complex workflows.

### Streaming:
```python
async for state in graph.astream(initial_state):
    # Send real-time updates to UI
    await websocket.send({"state": state})
```

---

## Memory & Context

### Short-term Memory
`state["messages"]` contains full conversation history.

### Long-term Memory
**Not implemented**. Would require:
- Vector database (Pinecone, Weaviate)
- Embedding model
- Retrieval node in graph

### Working Memory
The entire `AgentState` object. Only persists during single request.

---

## Cost & Performance

### Per Request:
- **LLM calls**: 1-3
- **Tokens**: 500-2000
- **Time**: 2-5 seconds
- **Cost**: $0.01-0.05 (GPT-4)

### Optimization:
- Use GPT-3.5 for extraction (10x cheaper)
- Cache similar requests
- Batch multiple stories

---

## Observability

### Built-in Debugging:
```python
print("[Node: understand] Starting...")
print(f"State: {state}")
```

### State Inspection:
```python
import json
print(json.dumps(state, indent=2))
```

### Audit Trail:
MCP server logs all tool calls, agent logs all transitions.

---

## Summary

**This is a specialized workflow agent for story creation.**

**Design Philosophy**: "Do one thing well"

**Optimized for**:
- Structured task extraction
- Validated story creation
- Reliable execution
- Clear error handling

**NOT optimized for**:
- General conversation
- Open-ended research
- Complex reasoning
- Multi-tool orchestration

---

**File**: `/agent/pm_graph.py`  
**Framework**: LangGraph 0.2.39  
**LLM**: GPT-4 (temperature 0.3)  
**Tool Count**: 1 (Notion story creation)  
**Node Count**: 7 (6 workflow + 1 error)
