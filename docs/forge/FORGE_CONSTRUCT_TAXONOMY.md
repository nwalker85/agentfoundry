# Forge Visual Designer - Complete Construct Taxonomy

**Date:** 2025-11-16  
**Based On:** FORGE_LANGGRAPH_GAP_ANALYSIS.md  
**Purpose:** Catalog ALL constructs for GUI designer implementation

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT DEFINITION                         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   STATE      │  │    GRAPH     │  │  CONFIGURATION   │ │
│  │   SCHEMA     │  │   TOPOLOGY   │  │    & RUNTIME     │ │
│  └──────────────┘  └──────────────┘  └──────────────────┘ │
│         │                 │                     │           │
│         │                 │                     │           │
│         ▼                 ▼                     ▼           │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  NODES (with Functions, Tools, Prompts, Logic)      │ │
│  └──────────────────────────────────────────────────────┘ │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  EDGES (Sequential, Conditional, Parallel, Cycles)  │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              GENERATED ARTIFACTS                            │
│  • Python LangGraph Code                                    │
│  • YAML Agent Manifest                                      │
│  • Executable Module                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Category 1: GRAPHS

### 1.1 Graph Types

```typescript
enum GraphType {
  STATE_GRAPH = 'StateGraph', // Standard state machine
  MESSAGE_GRAPH = 'MessageGraph', // Message-focused (sugar for StateGraph)
  COMPILED_GRAPH = 'CompiledGraph', // After compilation
  SUBGRAPH = 'Subgraph', // Nested graph component
}
```

### 1.2 Graph Configuration

```typescript
interface GraphConfig {
  // Identity
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  tags: string[];

  // Type
  graphType: GraphType;
  stateSchemaId: string; // Reference to state schema

  // Execution
  checkpointing: CheckpointConfig;
  streaming: StreamingConfig;
  parallelism: ParallelismConfig;

  // Observability
  tracing: TracingConfig;
  logging: LoggingConfig;
  metrics: MetricsConfig;

  // Runtime
  timeout: number;
  max_retries: number;
  retry_policy: RetryPolicy;

  // Environment
  environment: 'dev' | 'staging' | 'prod';
  secrets: SecretReference[];
}
```

### 1.3 Graph Metadata

```typescript
interface GraphMetadata {
  createdAt: timestamp;
  updatedAt: timestamp;
  deployedAt: timestamp;
  deployedBy: string;
  deployment_status: 'draft' | 'active' | 'deprecated';
  execution_count: number;
  last_execution: timestamp;
  success_rate: number;
}
```

---

## 📦 Category 2: STATE SCHEMAS

### 2.1 State Schema Definition

```typescript
interface StateSchema {
  id: string;
  name: string;
  description: string;

  // Fields
  fields: StateField[];

  // Inheritance (extend base schemas)
  extends?: string[]; // ['MessagesState', 'ToolState']

  // Validation
  validation_rules: ValidationRule[];
}
```

### 2.2 State Fields

```typescript
interface StateField {
  // Identity
  name: string;
  description: string;

  // Type System
  type: StateFieldType;
  subtype?: string; // For List[Message], Dict[str, int], etc.
  optional: boolean;
  default_value?: any;

  // Reducer/Merge Strategy
  reducer: ReducerType;
  custom_reducer?: string; // Python function name

  // Validation
  validators: Validator[];

  // Metadata
  is_sensitive: boolean; // For secrets/PII
  is_computed: boolean; // Derived from other fields
  compute_function?: string;

  // Tracking
  read_by_nodes: string[]; // Which nodes read this field
  written_by_nodes: string[]; // Which nodes write this field
}
```

### 2.3 State Field Types

```typescript
enum StateFieldType {
  // Primitives
  STRING = 'string',
  INT = 'int',
  FLOAT = 'float',
  BOOL = 'bool',

  // Collections
  LIST = 'list',
  DICT = 'dict',
  SET = 'set',
  TUPLE = 'tuple',

  // LangChain Types
  MESSAGE = 'Message',
  MESSAGE_LIST = 'List[Message]',
  DOCUMENT = 'Document',
  DOCUMENT_LIST = 'List[Document]',

  // Special
  ANY = 'any',
  JSON = 'json',
  CUSTOM = 'custom',
}
```

### 2.4 Reducer Types

```typescript
enum ReducerType {
  ADD = 'add', // Append to list
  REPLACE = 'replace', // Overwrite value
  MERGE = 'merge', // Merge dicts
  MAX = 'max', // Take maximum
  MIN = 'min', // Take minimum
  SUM = 'sum', // Sum numbers
  CUSTOM = 'custom', // Custom function
}
```

---

## 📦 Category 3: NODES

### 3.1 Core Node Types

```typescript
enum CoreNodeType {
  // Special
  START = 'start', // Entry point (LangGraph START)
  END = 'end', // Terminal node (LangGraph END)

  // Processing
  LLM = 'llm', // LLM call with messages
  TOOL = 'tool', // Tool execution
  FUNCTION = 'function', // Custom Python function
  TRANSFORM = 'transform', // State transformation

  // Control Flow
  ROUTER = 'router', // Conditional routing
  DECISION = 'decision', // Simple if/else
  PARALLEL_GATEWAY = 'parallel_gateway', // Fork execution
  MERGE_GATEWAY = 'merge_gateway', // Join parallel paths

  // Interaction
  HUMAN = 'human', // Human-in-loop
  WEBHOOK = 'webhook', // External HTTP call
  EVENT_EMITTER = 'event_emitter', // Emit events

  // Composite
  REACT_AGENT = 'react_agent', // ReAct pattern (LLM+Tools+Loop)
  SUBGRAPH = 'subgraph', // Nested graph
  PLAN_EXECUTE = 'plan_execute', // Plan-Execute pattern
}
```

### 3.2 Node Base Configuration

```typescript
interface NodeBase {
  // Identity
  id: string;
  type: CoreNodeType;
  label: string;
  description: string;

  // Visual
  position: { x: number; y: number };
  color?: string;
  icon?: string;

  // State Mapping
  input_state: StateFieldMapping[];
  output_state: StateFieldMapping[];
  state_transformations: StateTransform[];

  // Execution
  timeout?: number;
  retry_policy?: RetryConfig;
  error_handler?: string; // Node ID to route to on error

  // Metadata
  tags: string[];
  notes: string;
}
```

### 3.3 LLM Node Configuration

```typescript
interface LLMNode extends NodeBase {
  type: 'llm';

  // Model Configuration
  model: LLMModelConfig;

  // Prompt Engineering
  prompt: PromptConfig;
  system_message?: string;

  // Generation Parameters
  temperature: number;
  max_tokens: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stop_sequences?: string[];

  // Tool Binding
  tools: string[]; // Tool IDs
  tool_choice?: 'auto' | 'required' | 'none';
  parallel_tool_calls?: boolean;

  // Response Handling
  response_format?: 'text' | 'json' | 'json_schema';
  json_schema?: JSONSchema;

  // Streaming
  streaming: boolean;
  stream_handler?: string; // Function to handle streamed chunks
}
```

### 3.4 Tool Node Configuration

```typescript
interface ToolNode extends NodeBase {
  type: 'tool';

  // Tool Selection
  tools: ToolReference[];

  // Execution
  parallel_execution: boolean;
  max_concurrent: number;

  // Error Handling
  on_error: 'fail' | 'continue' | 'fallback';
  fallback_value?: any;

  // Result Handling
  result_transformation?: string; // Python function
  result_validation?: Validator[];
}
```

### 3.5 Router Node Configuration

```typescript
interface RouterNode extends NodeBase {
  type: 'router';

  // Routing Strategy
  routing_type: 'conditional' | 'llm' | 'intent' | 'custom';

  // Routes
  routes: Route[];
  default_route?: string; // Node ID or END

  // LLM-based Routing (if routing_type = 'llm')
  routing_llm?: LLMModelConfig;
  routing_prompt?: string;

  // Custom Function (if routing_type = 'custom')
  routing_function?: string; // Python code
}
```

### 3.6 ReAct Agent Node Configuration

```typescript
interface ReactAgentNode extends NodeBase {
  type: 'react_agent';

  // Agent Configuration
  model: LLMModelConfig;
  tools: string[]; // Tool IDs

  // Loop Control
  max_iterations: number;
  early_stopping: 'force' | 'generate';

  // State Modifier
  state_modifier?: string; // Python function

  // Message Handling
  message_modifier?: string; // Transform messages before agent
}
```

### 3.7 Subgraph Node Configuration

```typescript
interface SubgraphNode extends NodeBase {
  type: 'subgraph';

  // Subgraph Reference
  subgraph_id: string; // Reference to another graph
  subgraph_version?: string;

  // State Mapping
  input_mapping: Record<string, string>; // Parent state → Subgraph state
  output_mapping: Record<string, string>; // Subgraph state → Parent state

  // Execution
  isolated: boolean; // Isolated state or shared
}
```

### 3.8 Human Node Configuration

```typescript
interface HumanNode extends NodeBase {
  type: 'human';

  // Interaction
  prompt: string;
  prompt_template?: string;

  // Timing
  timeout: number; // seconds
  timeout_action: 'fail' | 'continue' | 'default';
  default_value?: any;

  // UI Configuration
  input_type: 'text' | 'choice' | 'form' | 'approval';
  choices?: string[]; // For choice type
  form_schema?: JSONSchema; // For form type

  // Notification
  notify_via?: 'email' | 'slack' | 'webhook';
  notification_config?: any;
}
```

---

## 📦 Category 4: EDGES

### 4.1 Edge Types

```typescript
enum EdgeType {
  SEQUENTIAL = 'sequential', // Simple A → B
  CONDITIONAL = 'conditional', // A → B if condition
  PARALLEL = 'parallel', // Multiple from same source
  FEEDBACK = 'feedback', // Loop back (cycle)
  START_EDGE = 'start_edge', // From START node
  END_EDGE = 'end_edge', // To END node
}
```

### 4.2 Edge Configuration

```typescript
interface Edge {
  // Identity
  id: string;
  source: string; // Node ID
  target: string; // Node ID or 'END'
  label?: string;

  // Type & Behavior
  type: EdgeType;
  animated: boolean;

  // Conditional Logic (if type = conditional)
  condition?: EdgeCondition;

  // Parallel Execution (if type = parallel)
  parallel_config?: ParallelConfig;

  // Feedback Loop (if type = feedback)
  feedback_config?: FeedbackConfig;

  // Visual
  style?: EdgeStyle;
}
```

### 4.3 Edge Conditions

```typescript
interface EdgeCondition {
  // Condition Type
  type: 'simple' | 'function' | 'state_check' | 'llm';

  // Simple Condition
  field?: string;
  operator?: '==' | '!=' | '>' | '<' | '>=' | '<=' | 'in' | 'contains';
  value?: any;

  // Function Condition
  function?: string; // Python function returning bool or node_id

  // State Check
  state_predicate?: string; // Python expression

  // LLM Condition (AI-driven routing)
  llm_prompt?: string;
  llm_model?: LLMModelConfig;

  // Compound Conditions
  logical_operator?: 'AND' | 'OR' | 'NOT';
  sub_conditions?: EdgeCondition[];
}
```

### 4.4 Feedback Configuration

```typescript
interface FeedbackConfig {
  // Loop Protection
  max_iterations: number;
  current_iteration_field: string; // State field tracking count

  // Exit Condition
  exit_condition: EdgeCondition;

  // Timeout
  max_duration?: number; // seconds

  // State Updates per Iteration
  iteration_state_updates?: Record<string, any>;
}
```

---

## 📦 Category 5: DEEP AGENTS (Composite Patterns)

### 5.1 Agent Pattern Types

```typescript
enum AgentPattern {
  REACT = 'react', // Reasoning + Acting
  PLAN_EXECUTE = 'plan_execute', // Planning then execution
  REFLECTION = 'reflection', // Generate + Reflect + Refine
  MULTIAGENT = 'multiagent', // Multiple specialized agents
  SUPERVISOR = 'supervisor', // Supervisor + workers
  HIERARCHICAL = 'hierarchical', // Tree of agents
  SELF_RAG = 'self_rag', // Self-reflective RAG
}
```

### 5.2 ReAct Agent

```typescript
interface ReactAgent {
  pattern: 'react';

  // Components (auto-generated as nodes internally)
  reasoning_model: LLMModelConfig;
  tools: ToolReference[];

  // Loop Configuration
  max_iterations: number;
  early_stopping: 'force' | 'generate';

  // Optimization
  scratchpad: boolean; // Keep reasoning history
  reflection: boolean; // Self-critique
}
```

### 5.3 Plan-Execute Agent

```typescript
interface PlanExecuteAgent {
  pattern: 'plan_execute';

  // Planner
  planner_model: LLMModelConfig;
  planner_prompt: string;

  // Executor
  executor_tools: ToolReference[];
  executor_model: LLMModelConfig;

  // Replanner
  replanning: boolean;
  replan_trigger: EdgeCondition;
}
```

### 5.4 Multi-Agent System

```typescript
interface MultiAgentSystem {
  pattern: 'multiagent';

  // Agents
  agents: AgentReference[];

  // Orchestration
  orchestration: 'sequential' | 'parallel' | 'supervisor';

  // Supervisor (if orchestration = supervisor)
  supervisor_model?: LLMModelConfig;
  supervisor_prompt?: string;

  // Communication
  message_bus: boolean;
  shared_state: boolean;
  agent_communication_protocol: 'direct' | 'broadcast' | 'routed';
}
```

---

## 📦 Category 6: EXTENSIONS

### 6.1 Extension Types

```typescript
enum ExtensionType {
  CHECKPOINT = 'checkpoint', // State persistence
  MEMORY = 'memory', // Long-term memory
  CACHE = 'cache', // Response caching
  RATE_LIMITER = 'rate_limiter', // API rate limiting
  RETRY = 'retry', // Retry logic
  CIRCUIT_BREAKER = 'circuit_breaker',
  TRACING = 'tracing', // LangSmith, etc.
  MONITORING = 'monitoring', // Metrics collection
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
}
```

### 6.2 Checkpoint Extension

```typescript
interface CheckpointExtension {
  type: 'checkpoint';
  enabled: boolean;

  // Backend
  backend: 'memory' | 'postgres' | 'redis' | 'sqlite' | 's3';
  connection_config: any;

  // Behavior
  save_frequency: 'every_node' | 'every_n_nodes' | 'on_error';
  checkpoint_namespace?: string;

  // Recovery
  auto_recovery: boolean;
  max_checkpoint_age?: number;
}
```

### 6.3 Memory Extension

```typescript
interface MemoryExtension {
  type: 'memory';

  // Memory Type
  memory_type: 'conversation' | 'entity' | 'summary' | 'vector';

  // Storage
  storage_backend: 'postgres' | 'redis' | 'pinecone' | 'chroma';
  storage_config: any;

  // Retrieval
  retrieval_strategy: 'last_n' | 'window' | 'summary' | 'semantic';
  max_tokens?: number;

  // Vector Memory (if memory_type = vector)
  embedding_model?: string;
  similarity_threshold?: number;
}
```

### 6.4 Tracing Extension

```typescript
interface TracingExtension {
  type: 'tracing';
  enabled: boolean;

  // Provider
  provider: 'langsmith' | 'langfuse' | 'phoenix' | 'custom';

  // Configuration
  api_key_secret: string;
  project_name: string;

  // What to Trace
  trace_inputs: boolean;
  trace_outputs: boolean;
  trace_intermediate: boolean;
  trace_llm_calls: boolean;
  trace_tool_calls: boolean;

  // Sampling
  sampling_rate: number; // 0-1
}
```

---

## 📦 Category 7: LANGCHAIN FUNCTIONS

### 7.1 Function Types

```typescript
enum FunctionType {
  // Message Operations
  ADD_MESSAGES = 'add_messages',
  TRIM_MESSAGES = 'trim_messages',
  FILTER_MESSAGES = 'filter_messages',

  // State Operations
  MERGE_STATE = 'merge_state',
  UPDATE_STATE = 'update_state',
  RESET_STATE = 'reset_state',

  // Document Operations
  SPLIT_DOCUMENTS = 'split_documents',
  EMBED_DOCUMENTS = 'embed_documents',
  RETRIEVE_DOCUMENTS = 'retrieve_documents',

  // Custom
  CUSTOM_FUNCTION = 'custom',
}
```

### 7.2 Function Definition

```typescript
interface LangChainFunction {
  // Identity
  id: string;
  name: string;
  type: FunctionType;
  description: string;

  // Signature
  parameters: FunctionParameter[];
  return_type: string;

  // Implementation
  implementation_type: 'builtin' | 'langchain' | 'custom';
  function_code?: string; // Python code
  langchain_import?: string; // e.g., 'langchain.schema.messages.add_messages'

  // State Access
  reads_state: string[];
  writes_state: string[];

  // Async
  is_async: boolean;
}
```

### 7.3 Built-in Functions

```typescript
const BUILTIN_FUNCTIONS = {
  // Message Utilities
  add_messages: {
    import: 'from langchain.schema.messages import add_messages',
    signature: '(existing: list, new: list) -> list',
    description: 'Append messages to conversation history',
  },
  trim_messages: {
    import: 'from langchain.schema.messages import trim_messages',
    signature: '(messages: list, max_tokens: int) -> list',
    description: 'Trim messages to fit token limit',
  },

  // Document Utilities
  split_text: {
    import:
      'from langchain.text_splitter import RecursiveCharacterTextSplitter',
    signature: '(text: str, chunk_size: int) -> list[Document]',
    description: 'Split text into chunks',
  },

  // State Utilities
  merge_dicts: {
    import: 'built-in',
    signature: '(dict1: dict, dict2: dict) -> dict',
    description: 'Deep merge two dictionaries',
  },
};
```

---

## 📦 Category 8: LLM ENDPOINTS

### 8.1 LLM Provider Configuration

```typescript
interface LLMModelConfig {
  // Provider
  provider: LLMProvider;

  // Model
  model_name: string;
  model_version?: string;

  // Authentication
  api_key_secret: string; // Reference to secret
  api_base_url?: string; // For custom endpoints

  // Organization (for some providers)
  organization_id?: string;

  // Timeouts
  request_timeout: number;
  connection_timeout: number;

  // Retry
  max_retries: number;
  retry_on: string[]; // Error types to retry

  // Rate Limiting
  requests_per_minute?: number;
  tokens_per_minute?: number;
}
```

### 8.2 LLM Providers

```typescript
enum LLMProvider {
  OPENAI = 'openai',
  ANTHROPIC = 'anthropic',
  GOOGLE = 'google',
  COHERE = 'cohere',
  AZURE_OPENAI = 'azure_openai',
  BEDROCK = 'bedrock',
  VERTEX_AI = 'vertex_ai',
  HUGGINGFACE = 'huggingface',
  OLLAMA = 'ollama', // Local models
  CUSTOM = 'custom',
}
```

### 8.3 Model Registry

```typescript
interface ModelRegistryEntry {
  // Identity
  id: string;
  provider: LLMProvider;
  model_name: string;
  display_name: string;

  // Capabilities
  capabilities: ModelCapability[];

  // Limits
  context_window: number;
  max_output_tokens: number;
  supports_functions: boolean;
  supports_vision: boolean;
  supports_json_mode: boolean;

  // Pricing
  input_cost_per_1k_tokens: number;
  output_cost_per_1k_tokens: number;

  // Metadata
  release_date: string;
  deprecation_date?: string;
}
```

---

## 📦 Category 9: MCP SERVERS

### 9.1 MCP Server Configuration

```typescript
interface MCPServerConfig {
  // Identity
  id: string;
  name: string;
  description: string;

  // Connection
  server_type: 'http' | 'stdio' | 'sse';
  endpoint: string;
  authentication: MCPAuthConfig;

  // Protocol
  mcp_version: string; // "1.0.0"
  transport: 'stdio' | 'sse' | 'websocket';

  // Discovery
  capabilities_endpoint: string;
  tools_endpoint: string;
  resources_endpoint: string;

  // Lifecycle
  startup_command?: string; // For stdio servers
  health_check_endpoint?: string;
  shutdown_command?: string;
}
```

### 9.2 MCP Tools

```typescript
interface MCPTool {
  // Identity
  id: string;
  name: string;
  description: string;

  // Source
  mcp_server_id: string;
  tool_path: string; // Path on MCP server

  // Schema
  input_schema: JSONSchema;
  output_schema?: JSONSchema;

  // Execution
  timeout: number;
  retry_policy: RetryConfig;

  // Caching
  cacheable: boolean;
  cache_ttl?: number;

  // Rate Limiting
  rate_limit?: RateLimitConfig;
}
```

### 9.3 MCP Resources

```typescript
interface MCPResource {
  // Identity
  id: string;
  uri: string;
  name: string;
  description: string;

  // Type
  resource_type: 'document' | 'dataset' | 'config' | 'template';
  mime_type: string;

  // Access
  mcp_server_id: string;
  access_method: 'GET' | 'POST' | 'STREAM';

  // Metadata
  size?: number;
  updated_at?: timestamp;
}
```

---

## 📦 Category 10: PROMPT ENGINEERING

### 10.1 Prompt Configuration

```typescript
interface PromptConfig {
  // Template
  template: string; // Jinja2/f-string template
  template_format: 'jinja2' | 'fstring' | 'mustache';

  // Variables
  variables: PromptVariable[];

  // System Message
  system_message?: string;
  system_message_template?: string;

  // Few-Shot Examples
  examples?: FewShotExample[];
  example_selector?: ExampleSelectorConfig;

  // Chat History
  include_history: boolean;
  history_max_tokens?: number;
  history_summary?: boolean;

  // Output Formatting
  output_format_instructions?: string;
  response_schema?: JSONSchema;
}
```

### 10.2 Prompt Variables

```typescript
interface PromptVariable {
  name: string;
  description: string;

  // Source
  source: 'state' | 'context' | 'computed' | 'constant';
  source_path?: string; // e.g., 'state.user_query'

  // Type & Validation
  type: string;
  required: boolean;
  default_value?: any;

  // Transformation
  transformation?: string; // Python function
}
```

### 10.3 Few-Shot Examples

```typescript
interface FewShotExample {
  id: string;

  // Example Pair
  input: string;
  output: string;

  // Metadata
  tags: string[];
  relevance_score?: number;

  // Conditional Inclusion
  include_condition?: EdgeCondition;
}
```

---

## 📦 Category 11: TOOLS & ACTIONS

### 11.1 Tool Definition

```typescript
interface ToolDefinition {
  // Identity
  id: string;
  name: string;
  description: string;

  // Source
  source_type: 'langchain' | 'mcp' | 'custom' | 'openapi';
  source_reference: string;

  // Schema
  input_schema: JSONSchema;
  output_schema?: JSONSchema;

  // Implementation
  implementation_type: 'python' | 'api' | 'mcp';
  implementation_code?: string;
  api_config?: APIConfig;
  mcp_config?: MCPToolReference;

  // Execution
  is_async: boolean;
  timeout: number;
  retry_policy: RetryConfig;

  // Behavior
  side_effects: boolean;
  idempotent: boolean;
  cacheable: boolean;

  // Authorization
  required_permissions: string[];
  api_key_secret?: string;
}
```

### 11.2 Tool Categories

```typescript
enum ToolCategory {
  // Data Access
  DATABASE_QUERY = 'database_query',
  API_CALL = 'api_call',
  FILE_READ = 'file_read',
  WEB_SEARCH = 'web_search',

  // Computation
  CALCULATOR = 'calculator',
  CODE_EXECUTION = 'code_execution',
  DATA_TRANSFORMATION = 'data_transformation',

  // Communication
  EMAIL = 'email',
  SLACK = 'slack',
  SMS = 'sms',
  WEBHOOK = 'webhook',

  // AI/ML
  EMBEDDING = 'embedding',
  VECTOR_SEARCH = 'vector_search',
  IMAGE_GENERATION = 'image_generation',
  SPEECH_TO_TEXT = 'speech_to_text',

  // Business Logic
  VALIDATION = 'validation',
  APPROVAL = 'approval',
  NOTIFICATION = 'notification',

  // Custom
  CUSTOM = 'custom',
}
```

### 11.3 Tool Registry

```typescript
interface ToolRegistry {
  // Catalog
  tools: ToolDefinition[];
  categories: ToolCategory[];

  // Discovery
  mcp_servers: MCPServerConfig[];
  langchain_tools: LangChainToolReference[];
  custom_tools: CustomToolDefinition[];

  // Management
  enabled_tools: string[];
  disabled_tools: string[];

  // Versioning
  tool_versions: ToolVersionInfo[];
}
```

---

## 📦 Category 12: RUNTIME CONFIGURATION

### 12.1 Execution Configuration

```typescript
interface ExecutionConfig {
  // Mode
  execution_mode: 'sync' | 'async' | 'streaming';

  // Parallelism
  max_parallel_nodes: number;
  parallel_strategy: 'thread' | 'process' | 'async';

  // Timeouts
  graph_timeout: number;
  node_timeout: number;

  // Resource Limits
  max_memory_mb: number;
  max_cpu_percent: number;

  // Retry & Error Handling
  global_retry_policy: RetryConfig;
  error_strategy: 'fail_fast' | 'continue' | 'fallback';

  // Observability
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  trace_all_nodes: boolean;
  metrics_enabled: boolean;
}
```

### 12.2 Deployment Configuration

```typescript
interface DeploymentConfig {
  // Environment
  environment: 'dev' | 'staging' | 'prod';
  region: string;

  // Infrastructure
  runtime: 'lambda' | 'ecs' | 'kubernetes' | 'local';
  runtime_config: any;

  // Scaling
  min_instances: number;
  max_instances: number;
  scaling_policy: ScalingPolicy;

  // Networking
  vpc_config?: VPCConfig;
  security_groups?: string[];

  // Secrets
  secrets_manager: 'aws_ssm' | 'hashicorp_vault' | 'env';
  secret_references: SecretReference[];
}
```

---

## 📦 Category 13: VALIDATION & TESTING

### 13.1 Validation Rules

```typescript
interface ValidationRule {
  // Identity
  id: string;
  name: string;
  severity: 'error' | 'warning' | 'info';

  // Rule Type
  rule_type:
    | 'graph_structure'
    | 'state_schema'
    | 'node_config'
    | 'edge_logic'
    | 'custom';

  // Condition
  validation_function: string; // Python function returning (bool, message)

  // Context
  applies_to: 'graph' | 'node' | 'edge' | 'state' | 'all';
  target_types?: string[]; // Specific node/edge types
}
```

### 13.2 Test Cases

```typescript
interface TestCase {
  // Identity
  id: string;
  name: string;
  description: string;

  // Input
  initial_state: any;
  input_messages?: any[];
  mock_tool_responses?: Record<string, any>;

  // Expected Output
  expected_final_state?: any;
  expected_path?: string[]; // Node IDs traversed
  expected_duration_ms?: number;

  // Assertions
  assertions: TestAssertion[];

  // Configuration
  timeout: number;
  skip: boolean;
  tags: string[];
}
```

### 13.3 Test Assertions

```typescript
interface TestAssertion {
  type:
    | 'state_field'
    | 'message_count'
    | 'path_includes'
    | 'execution_time'
    | 'custom';

  // State Field Assertion
  field?: string;
  expected_value?: any;
  operator?: '==' | '!=' | '>' | '<' | 'contains';

  // Path Assertion
  expected_nodes?: string[];

  // Custom
  assertion_function?: string; // Python function
}
```

---

## 📦 Category 14: MESSAGES & COMMUNICATION

### 14.1 Message Types

```typescript
enum MessageType {
  HUMAN = 'HumanMessage',
  AI = 'AIMessage',
  SYSTEM = 'SystemMessage',
  TOOL = 'ToolMessage',
  FUNCTION = 'FunctionMessage',
  CUSTOM = 'CustomMessage',
}
```

### 14.2 Message Configuration

```typescript
interface MessageConfig {
  // Type
  message_type: MessageType;

  // Content
  content: string;
  content_template?: string;
  content_variables?: string[];

  // Metadata
  role: 'system' | 'user' | 'assistant' | 'tool';
  name?: string; // For multi-agent

  // Tool Calls (for AI messages)
  tool_calls?: ToolCall[];

  // Function Calls (deprecated but still used)
  function_call?: FunctionCall;

  // Additional Data
  additional_kwargs?: Record<string, any>;
}
```

### 14.3 Message History Management

```typescript
interface MessageHistoryConfig {
  // Storage
  storage_type: 'memory' | 'persistent';
  storage_backend?: 'postgres' | 'redis' | 'dynamodb';

  // Trimming
  max_messages: number;
  max_tokens: number;
  trim_strategy: 'oldest_first' | 'semantic' | 'summary';

  // Summarization
  enable_summarization: boolean;
  summarize_every_n_messages?: number;
  summary_model?: LLMModelConfig;
}
```

---

## 📦 Category 15: ERROR HANDLING & RESILIENCE

### 15.1 Retry Configuration

```typescript
interface RetryConfig {
  enabled: boolean;
  max_attempts: number;

  // Backoff Strategy
  backoff_type: 'constant' | 'exponential' | 'fibonacci';
  base_delay_ms: number;
  max_delay_ms: number;

  // Retry Conditions
  retry_on_errors: string[]; // Error types
  retry_on_status_codes?: number[]; // HTTP status codes

  // Jitter
  jitter: boolean;
  jitter_max_ms?: number;
}
```

### 15.2 Fallback Configuration

```typescript
interface FallbackConfig {
  enabled: boolean;

  // Fallback Chain
  fallback_chain: FallbackStep[];

  // Final Fallback
  final_fallback: 'error' | 'default_value' | 'human_escalation';
  default_value?: any;
  escalation_config?: HumanEscalationConfig;
}
```

### 15.3 Circuit Breaker

```typescript
interface CircuitBreakerConfig {
  enabled: boolean;

  // Thresholds
  failure_threshold: number; // Failed requests before opening
  success_threshold: number; // Successful requests to close
  timeout_ms: number;

  // States
  half_open_after_ms: number;

  // Fallback
  fallback_value?: any;
  fallback_node?: string;
}
```

---

## 📦 Category 16: OBSERVABILITY & MONITORING

### 16.1 Metrics Configuration

```typescript
interface MetricsConfig {
  enabled: boolean;

  // Providers
  providers: MetricsProvider[];

  // What to Measure
  metrics: MetricDefinition[];

  // Aggregation
  aggregation_window: number; // seconds
  retention_period: number; // days
}
```

### 16.2 Metric Types

```typescript
enum MetricType {
  // Performance
  EXECUTION_TIME = 'execution_time',
  NODE_LATENCY = 'node_latency',
  THROUGHPUT = 'throughput',

  // Quality
  SUCCESS_RATE = 'success_rate',
  ERROR_RATE = 'error_rate',
  RETRY_COUNT = 'retry_count',

  // Cost
  TOKEN_USAGE = 'token_usage',
  API_CALLS = 'api_calls',
  COST_USD = 'cost_usd',

  // Business
  CONVERSATION_LENGTH = 'conversation_length',
  TOOL_USAGE = 'tool_usage',
  HUMAN_INTERVENTIONS = 'human_interventions',
}
```

### 16.3 Logging Configuration

```typescript
interface LoggingConfig {
  // Level
  log_level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';

  // Destinations
  log_destinations: LogDestination[];

  // Format
  format: 'json' | 'text' | 'structured';

  // What to Log
  log_inputs: boolean;
  log_outputs: boolean;
  log_intermediate: boolean;
  log_llm_prompts: boolean;
  log_llm_responses: boolean;
  log_tool_calls: boolean;

  // PII Handling
  redact_pii: boolean;
  pii_fields: string[];

  // Sampling
  sampling_rate: number;
}
```

---

## 📦 Category 17: SECURITY & COMPLIANCE

### 17.1 Authentication

```typescript
interface AuthenticationConfig {
  // Strategy
  auth_type: 'none' | 'api_key' | 'oauth' | 'jwt' | 'custom';

  // API Key
  api_key_secret?: string;
  api_key_header?: string;

  // OAuth
  oauth_config?: OAuthConfig;

  // JWT
  jwt_config?: JWTConfig;

  // Custom
  custom_auth_function?: string;
}
```

### 17.2 Authorization

```typescript
interface AuthorizationConfig {
  enabled: boolean;

  // Policy
  policy_type: 'rbac' | 'abac' | 'custom';

  // RBAC
  required_roles?: string[];
  required_permissions?: string[];

  // ABAC
  attributes?: Record<string, any>;
  policy_rules?: PolicyRule[];

  // Custom
  authorization_function?: string;
}
```

### 17.3 Data Privacy

```typescript
interface PrivacyConfig {
  // PII Handling
  pii_detection: boolean;
  pii_redaction: boolean;
  pii_encryption: boolean;

  // Compliance
  compliance_standards: ('GDPR' | 'HIPAA' | 'SOC2' | 'PCI')[];

  // Data Retention
  retention_policy: RetentionPolicy;

  // Audit
  audit_logging: boolean;
  audit_retention_days: number;
}
```

---

## 📦 Category 18: METADATA & DOCUMENTATION

### 18.1 Agent Metadata

```typescript
interface AgentMetadata {
  // Identity
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;

  // Authorship
  author: string;
  maintainers: string[];
  created_at: timestamp;
  updated_at: timestamp;

  // Classification
  category: AgentCategory;
  tags: string[];
  use_cases: string[];

  // Status
  status: 'draft' | 'active' | 'deprecated' | 'archived';
  maturity: 'experimental' | 'beta' | 'stable';

  // Documentation
  readme: string; // Markdown
  changelog: string;
  examples: ExampleUsage[];

  // Dependencies
  dependencies: Dependency[];
  required_extensions: string[];
  required_tools: string[];
}
```

### 18.2 Documentation

```typescript
interface AgentDocumentation {
  // Overview
  overview: string;
  architecture_diagram?: string; // Mermaid or image URL

  // Usage
  quick_start: string;
  usage_examples: CodeExample[];

  // API
  inputs: InputDocumentation[];
  outputs: OutputDocumentation[];

  // Configuration
  configuration_guide: string;
  environment_variables: EnvVarDoc[];

  // Troubleshooting
  common_issues: TroubleshootingItem[];
  faq: FAQItem[];
}
```

---

## 📦 Category 19: INTEGRATIONS

### 19.1 Integration Types

```typescript
enum IntegrationType {
  // External APIs
  REST_API = 'rest_api',
  GRAPHQL = 'graphql',
  GRPC = 'grpc',
  WEBSOCKET = 'websocket',

  // Databases
  POSTGRES = 'postgres',
  MONGODB = 'mongodb',
  REDIS = 'redis',

  // Vector DBs
  PINECONE = 'pinecone',
  WEAVIATE = 'weaviate',
  CHROMA = 'chroma',
  QDRANT = 'qdrant',

  // Cloud Services
  AWS_S3 = 'aws_s3',
  AWS_LAMBDA = 'aws_lambda',
  GCP_CLOUD_FUNCTIONS = 'gcp_cloud_functions',

  // Communication
  SLACK = 'slack',
  TEAMS = 'teams',
  EMAIL = 'email',

  // MCP
  MCP_SERVER = 'mcp_server',
}
```

### 19.2 Integration Configuration

```typescript
interface IntegrationConfig {
  // Identity
  id: string;
  name: string;
  type: IntegrationType;

  // Connection
  connection: ConnectionConfig;

  // Authentication
  authentication: AuthenticationConfig;

  // Capabilities
  available_operations: Operation[];

  // Usage
  used_by_nodes: string[];
  used_by_tools: string[];
}
```

---

## 📦 Category 20: VERSION CONTROL & DEPLOYMENT

### 20.1 Version Information

```typescript
interface AgentVersion {
  // Version
  version: string; // Semantic versioning
  version_date: timestamp;

  // Changes
  changelog: string;
  breaking_changes: boolean;
  migration_guide?: string;

  // Snapshot
  graph_snapshot: GraphSnapshot;
  state_schema_snapshot: StateSchema;

  // Git Integration
  git_commit?: string;
  git_branch?: string;
  git_repository?: string;

  // Deployment
  deployments: DeploymentRecord[];
}
```

### 20.2 Deployment Record

```typescript
interface DeploymentRecord {
  // Identity
  deployment_id: string;
  version: string;

  // Environment
  environment: 'dev' | 'staging' | 'prod';
  region: string;

  // Timing
  deployed_at: timestamp;
  deployed_by: string;

  // Status
  status: 'deploying' | 'active' | 'failed' | 'rolled_back';
  health_status: 'healthy' | 'degraded' | 'unhealthy';

  // Metrics
  invocation_count: number;
  error_rate: number;
  avg_duration_ms: number;

  // Rollback
  can_rollback: boolean;
  rollback_target?: string; // Previous deployment ID
}
```

---

## 🎯 COMPLETE TAXONOMY SUMMARY

### Hierarchy

```
AGENT
├── Graph Configuration
│   ├── Identity (name, version, tags)
│   ├── Type (StateGraph, MessageGraph)
│   ├── Execution settings
│   └── Extensions
│
├── State Schema
│   ├── Fields (with types, reducers)
│   ├── Validation rules
│   └── Computed fields
│
├── Nodes
│   ├── START (entry point)
│   ├── Processing Nodes
│   │   ├── LLM (with prompts, models)
│   │   ├── Tool (with tool refs, params)
│   │   ├── Function (custom code)
│   │   └── Transform (state manipulation)
│   ├── Control Flow Nodes
│   │   ├── Router (conditional routing)
│   │   ├── Decision (simple branching)
│   │   ├── Parallel Gateway (fan-out)
│   │   └── Merge Gateway (fan-in)
│   ├── Interaction Nodes
│   │   ├── Human (pause for input)
│   │   ├── Webhook (external call)
│   │   └── Event Emitter
│   ├── Composite Nodes
│   │   ├── ReAct Agent (LLM+Tools+Loop)
│   │   ├── Plan-Execute
│   │   └── Subgraph
│   └── END (termination)
│
├── Edges
│   ├── Sequential (A → B)
│   ├── Conditional (with routing logic)
│   ├── Parallel (fan-out)
│   └── Feedback (cycles)
│
├── Tools & Actions
│   ├── Tool Registry
│   ├── Tool Definitions (schema, impl)
│   ├── MCP Tools
│   └── Custom Tools
│
├── Prompts & Templates
│   ├── Prompt Templates (Jinja2)
│   ├── System Messages
│   ├── Few-shot Examples
│   └── Output Formats
│
├── Runtime Configuration
│   ├── Execution (sync/async/stream)
│   ├── Checkpointing
│   ├── Memory
│   ├── Tracing
│   └── Logging
│
├── Security
│   ├── Authentication
│   ├── Authorization
│   ├── Secrets Management
│   └── Data Privacy
│
├── Testing & Validation
│   ├── Validation Rules
│   ├── Test Cases
│   ├── Assertions
│   └── Mock Data
│
├── Deployment
│   ├── Environment Config
│   ├── Infrastructure
│   ├── Scaling
│   └── Monitoring
│
└── Metadata
    ├── Documentation
    ├── Version History
    ├── Deployment Records
    └── Usage Statistics
```

---

## 📊 Implementation Statistics

### Total Construct Types: 20 Categories

1. ✅ Graphs - 3 types, 12 config fields
2. ⚠️ State Schemas - 4 field types, 7 reducers (CRITICAL GAP)
3. ✅ Nodes - 13 types implemented, 8 more needed
4. ✅ Edges - 4 types, 3 configurations
5. ⏳ Deep Agents - 4 patterns, 2 implemented
6. ❌ Extensions - 10 types, 0 implemented
7. ❌ LangChain Functions - 20+ built-ins, not integrated
8. ⚠️ LLM Endpoints - 9 providers, basic support only
9. ❌ MCP Servers - Spec defined, not integrated
10. ❌ Prompts - Templates needed, only basic config
11. ⚠️ Tools - Structure defined, no registry
12. ❌ Runtime Config - Defined but not configurable
13. ❌ Testing - Framework needed
14. ❌ Messages - Types defined, not manageable
15. ❌ Error Handling - No resilience patterns
16. ❌ Observability - No monitoring integration
17. ❌ Security - Not implemented
18. ⚠️ Metadata - Basic only
19. ❌ Integrations - Not managed
20. ❌ Deployment - Manual only

**Current Coverage: ~25%**  
**Critical Gaps: State Schema, Tool Registry, Testing, Extensions**

---

## 🎯 Prioritized Roadmap

### Phase 1: Foundation (Weeks 1-2)

1. State Schema Designer UI
2. Tool Registry & Browser
3. Prompt Template Editor
4. Enhanced Node Configuration

### Phase 2: Execution (Weeks 3-4)

5. In-Forge Test Runner
6. State Inspector
7. Execution Timeline
8. Error Handling Nodes

### Phase 3: Production (Weeks 5-6)

9. Extensions (Checkpoint, Memory, Tracing)
10. Deployment Configuration
11. Security & Secrets
12. Monitoring Integration

### Phase 4: Advanced (Weeks 7-8)

13. Subgraphs
14. Message History Management
15. Advanced Control Flow
16. Code Generation Improvements

---

**Status:** Taxonomy Complete  
**Next Steps:** Implement high-priority constructs  
**Documentation:** Ready for development planning
