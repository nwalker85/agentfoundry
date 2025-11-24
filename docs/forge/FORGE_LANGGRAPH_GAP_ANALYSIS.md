# Forge LangGraph Gap Analysis

## Overview

The current Forge implementation provides a basic visual agent builder but is
missing numerous critical LangGraph features that are essential for building
production-ready agentic workflows.

## Reference Documentation

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [LangGraph Graph API Overview](https://docs.langchain.com/oss/python/langgraph/graph-api)

---

## Critical Missing Features

### 1. **State Management**

#### What LangGraph Provides

- **Typed State Schemas**: Define state using TypedDict with explicit types
- **State Reducers**: Use `Annotated` types with operators (e.g., `operator.add`
  for appending to lists)
- **Persistent State**: State that evolves throughout agent execution
- **Custom Reducers**: Define custom merge strategies for state fields

```python
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int
    context: dict
```

#### What Forge Currently Has

- Hardcoded state schema with only basic fields:
  ```typescript
  state_schema: {
    messages: 'list',
    context: 'dict',
    current_node: 'string',
  }
  ```

#### Gaps

- ❌ No visual state schema designer
- ❌ No ability to define custom state fields
- ❌ No reducer/merge strategy configuration
- ❌ No state type annotations
- ❌ State schema is hardcoded and cannot be customized per agent
- ❌ No validation of state field types
- ❌ No ability to specify which nodes read/write which state fields

---

### 2. **Node Function Definitions**

#### What LangGraph Provides

- Nodes are Python functions that:
  - Receive state as input
  - Return partial state updates
  - Can be async
  - Have clear input/output contracts

```python
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [model_with_tools.invoke([SystemMessage(...)] + state["messages"])],
        "llm_calls": state.get('llm_calls', 0) + 1
    }
```

#### What Forge Currently Has

- Visual node representations with metadata:
  - Labels and descriptions
  - Model configuration (for process nodes)
  - Tool names (for tool nodes)
  - Conditions (for decision nodes)

#### Gaps

- ❌ No actual function/code definition
- ❌ No way to specify what state fields a node reads
- ❌ No way to specify what state fields a node writes
- ❌ No prompt templates for LLM nodes
- ❌ No system message configuration
- ❌ No way to define custom Python/JavaScript logic
- ❌ No async vs sync specification
- ❌ No error handling configuration

---

### 3. **Conditional Edges (Routing Logic)**

#### What LangGraph Provides

- Conditional edge functions that:
  - Examine state
  - Return the next node to execute (or END)
  - Enable dynamic routing
  - Support literal type hints for valid targets

```python
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    return END
```

#### What Forge Currently Has

- Decision nodes with basic condition objects:
  ```typescript
  conditions: [{ field: '', operator: '==', value: '', target: '' }];
  ```

#### Gaps

- ❌ Conditions are simplistic (field/operator/value)
- ❌ No support for complex boolean logic (AND/OR/NOT)
- ❌ No way to write custom routing functions
- ❌ No way to access full state in conditions
- ❌ No support for runtime evaluation of conditions
- ❌ Decision nodes don't map to specific edge targets properly
- ❌ No support for computed/derived values in conditions
- ❌ No END node routing (what LangGraph calls `END` constant)

---

### 4. **Tool Integration**

#### What LangGraph Provides

- Proper tool definitions using `@tool` decorator:
  ```python
  @tool
  def multiply(a: int, b: int) -> int:
      """Multiply `a` and `b`."""
      return a * b
  ```
- Tool binding to models: `model.bind_tools(tools)`
- Automatic tool call handling with `ToolMessage`
- Tool result tracking

#### What Forge Currently Has

- ToolCall nodes with:
  - Tool name field
  - Basic parameters object

#### Gaps

- ❌ No tool registry or catalog
- ❌ No tool schema definitions
- ❌ No tool parameter validation
- ❌ No way to browse available tools
- ❌ No integration with actual tool implementations
- ❌ No tool result handling
- ❌ No automatic tool call detection/parsing
- ❌ No multi-tool execution support
- ❌ Tool parameters are free-form, not schema-validated

---

### 5. **Message Handling**

#### What LangGraph Provides

- Structured message types:
  - `HumanMessage`
  - `SystemMessage`
  - `AIMessage`
  - `ToolMessage`
  - `FunctionMessage`
- Message history management
- Helper functions like `add_messages()`

#### What Forge Currently Has

- Generic "messages" reference in state
- No message type system

#### Gaps

- ❌ No message type definitions
- ❌ No message role specifications
- ❌ No system prompt configuration at the graph level
- ❌ No message history visualization
- ❌ No message transformation logic
- ❌ No way to specify which nodes add which message types

---

### 6. **Graph Compilation and Execution**

#### What LangGraph Provides

- Graph builder pattern:
  ```python
  agent_builder = StateGraph(MessagesState)
  agent_builder.add_node("llm_call", llm_call)
  agent_builder.add_edge(START, "llm_call")
  agent = agent_builder.compile()
  ```
- START and END special nodes
- Checkpointing for persistence
- Streaming support
- Invocation methods: `.invoke()`, `.stream()`, `.ainvoke()`

#### What Forge Currently Has

- Visual graph representation
- YAML export
- Basic save/load functionality

#### Gaps

- ❌ No START node concept (only "entryPoint")
- ❌ No explicit END node handling
- ❌ No compilation step
- ❌ No validation before "deployment"
- ❌ No execution/testing within Forge
- ❌ No streaming mode configuration
- ❌ No checkpointing/persistence configuration
- ❌ Can't test agents in Forge directly

---

### 7. **Advanced Control Flow**

#### What LangGraph Provides

- **Cycles/Loops**: Edges can go back to previous nodes
- **Parallel Execution**: Send API for map-reduce patterns
- **Subgraphs**: Nested graph compositions
- **Command API**: Combine state updates with node transitions
- **Branches**: Multiple conditional paths

#### What Forge Currently Has

- Basic linear flow with branches
- ReactFlow supports cycles visually

#### Gaps

- ❌ No parallel execution configuration
- ❌ No subgraph/composition support
- ❌ No loop/iteration limits
- ❌ No map-reduce patterns
- ❌ No fan-out/fan-in patterns
- ❌ Cycles might work visually but no runtime loop protection

---

### 8. **Visualization and Introspection**

#### What LangGraph Provides

- Graph visualization with Mermaid
- XRay mode for detailed inspection
- State snapshots
- Execution traces

```python
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))
```

#### What Forge Currently Has

- ReactFlow visual editor
- YAML preview
- Mini-map

#### Gaps

- ❌ No execution trace visualization
- ❌ No state inspection during execution
- ❌ No execution playback
- ❌ No performance metrics
- ❌ Can't see intermediate state values
- ❌ No debugging tools

---

### 9. **Persistence and Memory**

#### What LangGraph Provides

- Checkpointing for long-running agents
- State persistence across invocations
- Memory configuration
- Thread/session management

#### What Forge Currently Has

- Save agent definitions to backend
- Version selector (UI only, not functional)

#### Gaps

- ❌ No checkpoint configuration
- ❌ No memory backend selection
- ❌ No conversation persistence setup
- ❌ No thread/session handling
- ❌ Version selector not connected to actual versioning system

---

### 10. **Configuration and Metadata**

#### What LangGraph Provides

- Agent configuration via compile options
- Runtime configuration
- Model configuration per node
- Environment variables
- Tracing with LangSmith

#### What Forge Currently Has

- Basic agent metadata (name, description, version, tags)
- Model selection for process nodes
- Temperature and token limits

#### Gaps

- ❌ No global agent configuration
- ❌ No environment-specific configs (dev/staging/prod)
- ❌ No secrets management
- ❌ No tracing configuration
- ❌ No retry policies
- ❌ No timeout configuration
- ❌ No rate limiting
- ❌ No cost tracking

---

### 11. **Error Handling and Resilience**

#### What LangGraph Provides

- Error handling in node functions
- Fallback mechanisms
- Retry logic
- Timeout handling

#### What Forge Currently Has

- Nothing specific

#### Gaps

- ❌ No error handler nodes
- ❌ No retry configuration
- ❌ No fallback paths
- ❌ No timeout settings
- ❌ No dead letter queue
- ❌ No circuit breaker patterns

---

### 12. **Testing and Validation**

#### What LangGraph Provides

- Direct invocation for testing
- State introspection
- Unit testable node functions

#### What Forge Currently Has

- Visual validation (entry point check)
- YAML validation

#### Gaps

- ❌ No test mode or sandbox
- ❌ No mock data injection
- ❌ No test case definitions
- ❌ No expected output validation
- ❌ Can't run agent from Forge
- ❌ No integration testing support

---

### 13. **Functional API Support**

#### What LangGraph Provides

- Alternative Functional API using:
  - `@entrypoint()` decorator
  - `@task` decorator
  - Standard control flow (loops, conditionals)
  - Cleaner for simple agents

#### What Forge Currently Has

- Only Graph API representation

#### Gaps

- ❌ No Functional API support
- ❌ Can't convert between Graph and Functional APIs
- ❌ No code generation for either API

---

## Priority Recommendations

### Phase 1: Critical Foundation (MVP+)

1. **State Schema Designer**

   - Visual state field editor
   - Type selection (list, dict, string, int, etc.)
   - Reducer configuration (add, replace, custom)
   - Per-node state read/write tracking

2. **Enhanced Node Configuration**

   - Prompt template editor for Process nodes
   - System message configuration
   - State field mapping (input/output)
   - Function code editor (advanced mode)

3. **Proper Conditional Routing**

   - Routing function editor
   - Support for complex boolean logic
   - State-based routing
   - Multiple output targets from decision nodes

4. **Tool Registry Integration**
   - Browse available tools
   - Tool schema validation
   - Parameter mapping UI
   - Tool result handling

### Phase 2: Essential Features

5. **START and END Nodes**

   - Explicit START node (convert current entryPoint)
   - Multiple END nodes for different outcomes
   - Entry/exit state validation

6. **Message System**

   - Message type specifications
   - Role assignments
   - System prompt at graph level
   - Message transformation nodes

7. **Execution Testing**

   - In-Forge test runner
   - State inspection
   - Step-by-step debugging
   - Test input designer

8. **Error Handling**
   - Error handler nodes
   - Retry configuration
   - Fallback paths
   - Timeout settings

### Phase 3: Advanced Features

9. **Advanced Control Flow**

   - Parallel execution (Send API)
   - Subgraphs
   - Loop limits and protection
   - Fan-out/fan-in patterns

10. **Persistence Configuration**

    - Checkpoint settings
    - Memory backend selection
    - Session management

11. **Code Generation**

    - Generate actual LangGraph Python code
    - Generate TypeScript code
    - Export as runnable module

12. **Monitoring and Observability**
    - Execution traces
    - State snapshots
    - Performance metrics
    - LangSmith integration

---

## Architecture Recommendations

### 1. Split YAML Format

The current single YAML format is too simplistic. Propose a more comprehensive
format:

```yaml
apiVersion: foundry.ai/v1
kind: Agent
metadata:
  name: example-agent
  version: 1.0.0

spec:
  # State schema with types and reducers
  state:
    fields:
      - name: messages
        type: list<Message>
        reducer: add
      - name: llm_calls
        type: int
        reducer: replace
      - name: context
        type: dict
        reducer: merge

  # System-level configuration
  config:
    system_message: 'You are a helpful assistant'
    checkpointing:
      enabled: true
      backend: postgres
    tracing:
      enabled: true
      provider: langsmith

  # Node definitions with actual logic
  nodes:
    - id: entry
      type: START

    - id: llm_call
      type: llm
      label: 'Call LLM'
      model:
        provider: anthropic
        name: claude-sonnet-4-5
        temperature: 0.7
      prompt:
        template: |
          {{ system_message }}

          {{ messages }}
      input_state:
        - messages
        - context
      output_state:
        - messages
        - llm_calls

    - id: tool_router
      type: router
      label: 'Should call tool?'
      function: |
        def route(state):
          if state['messages'][-1].tool_calls:
            return 'tool_call'
          return 'END'
      targets:
        - tool_call
        - END

    - id: tool_call
      type: tool
      label: 'Execute Tool'
      tools:
        - multiply
        - add
        - divide
      input_state:
        - messages
      output_state:
        - messages

    - id: end
      type: END

  # Edge definitions
  edges:
    - source: entry
      target: llm_call

    - source: llm_call
      target: tool_router
      type: normal

    - source: tool_router
      target: tool_call
      type: conditional
      condition: 'tool_call'

    - source: tool_router
      target: end
      type: conditional
      condition: 'END'

    - source: tool_call
      target: llm_call
      type: normal

  # Tool definitions
  tools:
    - name: multiply
      function: multiply
      parameters:
        a:
          type: int
          description: 'First number'
        b:
          type: int
          description: 'Second number'
```

### 2. Backend Agent Runtime

The Forge should connect to an actual LangGraph runtime that can:

- Execute agents
- Stream results
- Handle state persistence
- Provide execution traces

Current `/forge_service/main.py` is minimal - needs expansion.

### 3. Frontend Enhancements

- Monaco editor for code editing (prompts, functions)
- State inspector panel
- Execution timeline visualization
- Tool catalog sidebar
- Test runner panel

### 4. Code Generation

Instead of just YAML, generate actual runnable LangGraph code:

```python
# Generated from Forge
from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

def llm_call(state: AgentState):
    # Generated from Process node configuration
    ...

# etc.
```

---

## Conclusion

The current Forge provides a good foundation for visual agent design, but it's
essentially a **simple graph editor** rather than a **LangGraph builder**. To
truly leverage LangGraph's power, the Forge needs:

1. **Much richer node configuration** (prompts, state mapping, actual logic)
2. **Proper state management system** (schema designer, types, reducers)
3. **Real conditional routing** (not just simple field comparisons)
4. **Tool integration** (registry, schemas, validation)
5. **Execution capabilities** (test in Forge, debug, inspect)
6. **Code generation** (export as runnable LangGraph code)

The current implementation is about **10-15%** of what a full LangGraph visual
builder should offer. It handles the visual graph part well, but misses most of
the agent logic, state management, execution, and LangGraph-specific features
that make agents actually work.
