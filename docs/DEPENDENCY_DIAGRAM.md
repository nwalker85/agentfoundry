# Engineering Department - Dependency Diagram

**Visual representation of code dependencies**

---

## Complete Dependency Graph

```
┌────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL APIS                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    │
│  │ Notion   │    │ GitHub   │    │ OpenAI   │    │  File    │    │
│  │   API    │    │   API    │    │   API    │    │  System  │    │
│  └────▲─────┘    └────▲─────┘    └────▲─────┘    └────▲─────┘    │
│       │               │               │               │            │
└───────│───────────────│───────────────│───────────────│────────────┘
        │               │               │               │
        │               │               │               │
┌───────│───────────────│───────────────│───────────────│────────────┐
│       │               │               │               │  BACKEND   │
│       │               │               │               │            │
│  ┌────┴─────┐    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐      │
│  │ Notion   │    │ GitHub  │    │ Agent   │    │ Audit   │      │
│  │  Tool    │    │  Tool   │    │ pm_graph│    │  Tool   │      │
│  │ 335 LOC  │    │ 214 LOC │    │ 406 LOC │    │ 224 LOC │      │
│  └────▲─────┘    └────▲────┘    └────▲────┘    └────▲────┘      │
│       │               │               │               │            │
│       │               │               │               │            │
│       │               └───────┬───────┘               │            │
│       │                       │                       │            │
│       └───────────┬───────────┴───────────┬───────────┘            │
│                   │                       │                        │
│              ┌────┴────┐           ┌──────┴──────┐                │
│              │  Tools  │           │   Schemas   │                │
│              │__init__ │◄──────────│   159 LOC   │                │
│              │  7 LOC  │           │             │                │
│              └────▲────┘           └──────▲──────┘                │
│                   │                       │                        │
│                   │                       │                        │
│              ┌────┴────────────────────┬──┴──────┐                │
│              │                         │         │                │
│         ┌────┴────┐              ┌─────┴─────┐  │                │
│         │  MCP    │◄─────────────│  Simple   │  │                │
│         │ Server  │              │   Agent   │  │                │
│         │ 407 LOC │              │  196 LOC  │  │                │
│         └────▲────┘              └───────────┘  │                │
│              │                                   │                │
└──────────────│───────────────────────────────────│────────────────┘
               │                                   │
               │ HTTP/REST                         │ HTTP (Internal)
               │                                   │
┌──────────────┴───────────────────────────────────┴────────────────┐
│                         FRONTEND                                   │
│                                                                    │
│         ┌────────────┐           ┌────────────┐                  │
│         │  Layout    │◄──────────│   Page     │                  │
│         │  16 LOC    │           │  117 LOC   │                  │
│         └────────────┘           └────────────┘                  │
│                                                                    │
│         ┌────────────┐                                            │
│         │  Tailwind  │                                            │
│         │  Config    │                                            │
│         │  11 LOC    │                                            │
│         └────────────┘                                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-Layer Breakdown

### Layer 1: Data Models (Foundation)

```
┌────────────────────────────────────────┐
│         mcp/schemas.py                 │
│           159 lines                    │
│                                        │
│  • Priority (Enum)                    │
│  • StoryStatus (Enum)                 │
│  • CreateStoryRequest                 │
│  • CreateStoryResponse                │
│  • CreateIssueRequest                 │
│  • CreateIssueResponse                │
│  • ListStoriesRequest                 │
│  • ListStoriesResponse                │
│  • AuditEntry                         │
│                                        │
│  Dependencies: None (Foundation)      │
└────────────────────────────────────────┘
```

### Layer 2: MCP Tools

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│  mcp/tools/notion.py    │  │  mcp/tools/github.py    │  │  mcp/tools/audit.py     │
│      335 lines          │  │      214 lines          │  │      224 lines          │
│                         │  │                         │  │                         │
│  Imports:               │  │  Imports:               │  │  Imports:               │
│  • schemas (internal)   │  │  • schemas (internal)   │  │  • schemas (internal)   │
│  • httpx (external)     │  │  • httpx (external)     │  │  • aiofiles (external)  │
│  • os, hashlib, typing  │  │  • os, typing, datetime │  │  • os, json, hashlib    │
│                         │  │                         │  │                         │
│  Calls:                 │  │  Calls:                 │  │  Calls:                 │
│  • Notion API           │  │  • GitHub API           │  │  • File System          │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
                │                        │                        │
                └────────────────────────┴────────────────────────┘
                                         │
                                         ▼
                            ┌─────────────────────────┐
                            │  mcp/tools/__init__.py  │
                            │        7 lines          │
                            │                         │
                            │  Exports:               │
                            │  • NotionTool           │
                            │  • GitHubTool           │
                            │  • AuditTool            │
                            └─────────────────────────┘
```

### Layer 3: Agents

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│    agent/simple_pm.py           │  │    agent/pm_graph.py            │
│        196 lines                │  │        406 lines                │
│                                 │  │                                 │
│  State Machine Agent            │  │  LangGraph AI Agent             │
│  • No AI dependencies           │  │  • LangChain/LangGraph          │
│  • Regex-based parsing          │  │  • OpenAI GPT-4                 │
│  • Direct HTTP to MCP           │  │  • Complex state graph          │
│                                 │  │                                 │
│  Status: ⚠️ LEGACY (Not in use) │  │  Status: ✅ OPERATIONAL (v0.4.0)│
│                                 │  │                                 │
│  Imports:                       │  │  Imports:                       │
│  • httpx (external)             │  │  • langgraph (external)         │
│  • os, typing, enum, re         │  │  • langchain (external)         │
│                                 │  │  • httpx (external)             │
│                                 │  │  • os, typing, enum             │
│                                 │  │                                 │
│  Calls:                         │  │  Calls:                         │
│  • MCP Server (HTTP)            │  │  • MCP Server (HTTP)            │
│  •   /api/tools/notion/*        │  │  • OpenAI API                   │
│  •   /api/tools/github/*        │  │                                 │
└─────────────────────────────────┘  └─────────────────────────────────┘
```

### Layer 4: Server (Orchestration)

```
┌────────────────────────────────────────────────────────────────┐
│                      mcp_server.py                             │
│                        407 lines                               │
│                                                                │
│  FastAPI Application                                           │
│                                                                │
│  Imports:                                                      │
│  • schemas (internal)      - All request/response models      │
│  • tools (internal)        - NotionTool, GitHubTool, AuditTool│
│  • pm_graph (internal)     - PMAgent                          │
│  • fastapi (external)      - Web framework                    │
│  • uvicorn (external)      - ASGI server                      │
│                                                                │
│  Endpoints:                                                    │
│  • GET  /                           - Health check            │
│  • GET  /api/status                 - Integration status      │
│  • POST /api/tools/notion/create-story                        │
│  • POST /api/tools/notion/list-stories                        │
│  • POST /api/tools/github/create-issue                        │
│  • GET  /api/tools/audit/query                                │
│  • GET  /api/tools/schema                                     │
│                                                                │
│  Middleware:                                                   │
│  • CORS                             - Cross-origin support    │
│  • Request Tracking                 - Performance monitoring  │
│                                                                │
│  Lifecycle:                                                    │
│  • Startup: Initialize tools and agents                       │
│  • Shutdown: Cleanup resources                                │
└────────────────────────────────────────────────────────────────┘
```

### Layer 5: Frontend

```
┌────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                      │
│                          144 lines total                       │
│                                                                │
│  ┌──────────────────────┐                                     │
│  │   app/layout.tsx     │                                     │
│  │     16 lines         │                                     │
│  │                      │                                     │
│  │  • Root HTML         │                                     │
│  │  • Global styles     │                                     │
│  │  • Metadata          │                                     │
│  └──────────┬───────────┘                                     │
│             │                                                  │
│             ▼                                                  │
│  ┌──────────────────────┐        ┌──────────────────────┐    │
│  │   app/page.tsx       │        │ app/tailwind.config  │    │
│  │     117 lines        │        │      11 lines        │    │
│  │                      │        │                      │    │
│  │  • Status display    │        │  • Tailwind config   │    │
│  │  • Integration check │        │                      │    │
│  │  • Navigation        │        │                      │    │
│  │                      │        │                      │    │
│  │  Calls:              │        │                      │    │
│  │  • /api/status (HTTP)│        │                      │    │
│  └──────────────────────┘        └──────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Story Creation Flow

```
User Input
    │
    ▼
┌───────────────────┐
│  Frontend         │  HTTP Request
│  app/page.tsx     │─────────────┐
└───────────────────┘             │
                                  ▼
                        ┌───────────────────┐
                        │  MCP Server       │
                        │  mcp_server.py    │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌───────────────────┐      ┌───────────────────┐
          │  Simple Agent     │      │  LangGraph Agent  │
          │  simple_pm.py     │      │  pm_graph.py      │
          │  ⚠️ LEGACY        │      │  ✅ ACTIVE        │
          └─────────┬─────────┘      └─────────┬─────────┘
                    │                           │
                    │ HTTP                      │ HTTP
                    ▼                           ▼
          ┌───────────────────┐      ┌───────────────────┐
          │  MCP Endpoints    │      │  MCP Endpoints    │
          └─────────┬─────────┘      └─────────┬─────────┘
                    │                           │
      ┌─────────────┼─────────────┬─────────────┘
      │             │             │
      ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Notion   │  │ GitHub   │  │  Audit   │
│  Tool    │  │  Tool    │  │  Tool    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Notion   │  │ GitHub   │  │  File    │
│   API    │  │   API    │  │  System  │
└──────────┘  └──────────┘  └──────────┘
```

### Request Processing Flow

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────┐
│  FastAPI Middleware                 │
│  • CORS                             │
│  • Request Tracking                 │
│  • Add request_id                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Route Handler                      │
│  • Validate request (Pydantic)      │
│  • Call tool method                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Tool Implementation                │
│  • Check idempotency                │
│  • Process request                  │
│  • Call external API                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Audit Logging                      │
│  • Log action                       │
│  • Generate hashes                  │
│  • Write to JSONL                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Response                           │
│  • Format response (Pydantic)       │
│  • Return JSON                      │
└─────────────────────────────────────┘
```

---

## Import Dependency Tree

### Most Depended Upon

```
mcp/schemas.py
    ├── mcp_server.py (imports 8 models)
    ├── mcp/tools/notion.py (imports 6 models)
    ├── mcp/tools/github.py (imports 3 models)
    └── mcp/tools/audit.py (imports 1 model)
```

### Tool Package Structure

```
mcp/tools/__init__.py
    ├── exports NotionTool (from notion.py)
    ├── exports GitHubTool (from github.py)
    └── exports AuditTool (from audit.py)
    
Used by:
    └── mcp_server.py (imports all 3)
```

### Agent Dependencies

```
agent/simple_pm.py  ⚠️ LEGACY (Not in use)
    ├── httpx → MCP Server
    └── Standard library only
    
agent/pm_graph.py  ✅ OPERATIONAL (v0.4.0)
    ├── langgraph → State machine
    ├── langchain → Prompts & messages
    ├── langchain_openai → GPT-4
    ├── httpx → MCP Server
    └── pydantic → Models
```

---

## Circular Dependencies

### None Detected ✅

The architecture has clean, acyclic dependencies:

1. **Foundation Layer** (schemas) → No dependencies
2. **Tool Layer** → Depends on schemas only
3. **Server Layer** → Depends on tools and schemas
4. **Agent Layer** → Calls server via HTTP (loose coupling)
5. **Frontend Layer** → Calls server via HTTP (loose coupling)

**Note:** Agents call the MCP server via HTTP, which is loose coupling and avoids circular imports.

---

## Module Coupling Analysis

### Highly Coupled Modules

1. **mcp_server.py** ↔ **mcp/tools/***
   - Tight coupling (direct imports)
   - Justified: Server orchestrates tools
   - Mitigation: Tool interface abstraction

2. **All Tools** ↔ **mcp/schemas.py**
   - Tight coupling (all import schemas)
   - Justified: Shared data models
   - Mitigation: Schemas are stable

### Loosely Coupled Modules

1. **Agents** ↔ **MCP Server**
   - Loose coupling (HTTP only)
   - Good: Can deploy separately
   - Good: Easy to test in isolation

2. **Frontend** ↔ **Backend**
   - Loose coupling (HTTP only)
   - Good: Can develop independently
   - Good: Clear API contract

---

## Refactoring Opportunities

### 1. Configuration Centralization

**Current:**
```
mcp_server.py
    └── os.getenv("NOTION_API_TOKEN")

mcp/tools/notion.py
    └── os.getenv("NOTION_API_TOKEN")

agent/simple_pm.py  ⚠️ LEGACY
    └── os.getenv("MCP_AUTH_TOKEN")
```

**Proposed:**
```
config.py (new)
    └── class Config
        ├── notion_token
        ├── github_token
        └── mcp_auth_token

All modules:
    └── from config import Config
```

### 2. Tool Interface Abstraction

**Current:**
```
mcp_server.py
    ├── from mcp.tools import NotionTool
    ├── from mcp.tools import GitHubTool
    └── notion_tool = NotionTool()
```

**Proposed:**
```
mcp/tools/base.py (new)
    └── class BaseTool (ABC)

All tools:
    └── inherit from BaseTool

mcp_server.py:
    └── tools: List[BaseTool]
```

### 3. Agent Interface Standardization

**Current:**
```
agent/simple_pm.py  ⚠️ LEGACY (Not in use)
    └── class SimplePMAgent (no interface)

agent/pm_graph.py  ✅ OPERATIONAL (Active in MCP Server v0.4.0)
    └── class PMAgent (different interface)
```

**Proposed:**
```
agent/base.py (new)
    └── class BaseAgent (Protocol)
        └── async def process_message(message: str)

Both agents:
    └── implement BaseAgent protocol
```

---

**Dependency Analysis Complete**  
*Generated: November 10, 2025*

