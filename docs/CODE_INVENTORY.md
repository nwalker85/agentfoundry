# Engineering Department - Code Inventory & Dependency Map

**Generated:** November 10, 2025  
**Project Version:** Phase 3 Complete  
**Total Code Files:** 12 files | ~2,092 lines

---

## Executive Summary

### Code Distribution

| Category                        | Files | Lines | Percentage |
| ------------------------------- | ----- | ----- | ---------- |
| **Backend (Python)**            | 9     | 1,948 | 93%        |
| **Frontend (TypeScript/React)** | 3     | 144   | 7%         |
| **Total**                       | 12    | 2,092 | 100%       |

### Technology Stack

**Backend:**

- Python 3.9.6
- FastAPI 0.115.5
- LangChain/LangGraph 0.2.x
- Pydantic 2.10.3
- httpx 0.27.2

**Frontend:**

- Next.js 14.2.33 (App Router)
- React 18
- TypeScript 5
- Tailwind CSS

---

## 1. Backend Code Files

### 1.1 Main Server (`mcp_server.py`)

**Path:** `/mcp_server.py`  
**Lines:** 407  
**Role:** Main application entry point, FastAPI server

**Purpose:**

- MCP server implementation
- HTTP endpoint definitions
- Tool initialization and lifecycle management
- Request routing and middleware
- CORS configuration

**Dependencies:**

**Standard Library:**

- `os` - Environment variables
- `time` - Performance tracking
- `contextlib.asynccontextmanager` - Lifespan management
- `datetime` - Timestamps
- `typing` - Type hints

**Third-Party:**

- `fastapi` - Web framework
  - `FastAPI` - App instance
  - `HTTPException` - Error handling
  - `Request` - Request object
  - `CORSMiddleware` - CORS support
  - `JSONResponse` - Response formatting
- `dotenv.load_dotenv` - Environment config
- `uvicorn` - ASGI server

**Internal:**

- `mcp.schemas` - Data models
  - `CreateStoryRequest`
  - `CreateStoryResponse`
  - `CreateIssueRequest`
  - `CreateIssueResponse`
  - `ListStoriesRequest`
  - `ListStoriesResponse`
  - `ToolResponse`
  - `AuditEntry`
- `mcp.tools` - Tool implementations
  - `NotionTool`
  - `GitHubTool`
  - `AuditTool`
- `agent.pm_graph` - Agent implementation
  - `PMAgent`

**Key Endpoints:**

- `GET /` - Health check
- `GET /api/status` - Integration status
- `POST /api/tools/notion/create-story` - Create Notion story
- `POST /api/tools/notion/list-stories` - List stories
- `POST /api/tools/github/create-issue` - Create GitHub issue
- `GET /api/tools/audit/query` - Query audit logs
- `GET /api/tools/schema` - Get tool schemas

**Dependency Graph:**

```
mcp_server.py
├── mcp/schemas.py (models)
├── mcp/tools/__init__.py (tools)
│   ├── mcp/tools/notion.py
│   ├── mcp/tools/github.py
│   └── mcp/tools/audit.py
└── agent/pm_graph.py (agent)
```

---

### 1.2 Schema Definitions (`mcp/schemas.py`)

**Path:** `/mcp/schemas.py`  
**Lines:** 159  
**Role:** Data models and validation

**Purpose:**

- Pydantic models for request/response
- Enums for priority and status
- Data validation
- Idempotency key generation
- Type safety

**Dependencies:**

**Standard Library:**

- `typing` - Type hints (List, Optional, Dict, Any, Literal)
- `datetime` - Timestamps
- `hashlib` - Idempotency keys
- `json` - Serialization
- `enum.Enum` - Enumerations

**Third-Party:**

- `pydantic` - Data validation
  - `BaseModel` - Base class
  - `Field` - Field definitions
  - `validator` - Custom validation

**Models Defined:**

- `Priority` - P0, P1, P2, P3
- `StoryStatus` - Backlog, Todo, In Progress, etc.
- `CreateStoryRequest` - Story creation input
- `CreateStoryResponse` - Story creation output
- `StoryItem` - Story representation
- `ListStoriesRequest` - Story query input
- `ListStoriesResponse` - Story query output
- `CreateIssueRequest` - GitHub issue input
- `CreateIssueResponse` - GitHub issue output
- `ToolResponse` - Generic tool response
- `AuditEntry` - Audit log entry

**Used By:**

- `mcp_server.py` - API endpoints
- `mcp/tools/notion.py` - Notion tool
- `mcp/tools/github.py` - GitHub tool
- `mcp/tools/audit.py` - Audit tool

**Dependency Graph:**

```
mcp/schemas.py
├── (no internal dependencies)
└── Used by:
    ├── mcp_server.py
    ├── mcp/tools/notion.py
    ├── mcp/tools/github.py
    └── mcp/tools/audit.py
```

---

### 1.3 MCP Tools Package (`mcp/tools/`)

#### 1.3.1 Package Init (`mcp/tools/__init__.py`)

**Path:** `/mcp/tools/__init__.py`  
**Lines:** 7  
**Role:** Package exports

**Purpose:**

- Export tool classes
- Define public API

**Exports:**

- `NotionTool`
- `GitHubTool`
- `AuditTool`

---

#### 1.3.2 Notion Tool (`mcp/tools/notion.py`)

**Path:** `/mcp/tools/notion.py`  
**Lines:** 335  
**Role:** Notion API integration

**Purpose:**

- Create stories in Notion
- Find and create epics
- List/filter stories
- Idempotency protection
- Story lifecycle management

**Dependencies:**

**Standard Library:**

- `os` - Environment variables
- `hashlib` - Idempotency keys
- `typing` - Type hints
- `datetime` - Timestamps

**Third-Party:**

- `httpx.AsyncClient` - HTTP client
- `pydantic.BaseModel` - Models

**Internal:**

- `mcp.schemas`
  - `CreateStoryRequest`
  - `CreateStoryResponse`
  - `ListStoriesRequest`
  - `ListStoriesResponse`
  - `StoryItem`
  - `Priority`
  - `StoryStatus`
  - `AuditEntry`

**External APIs:**

- Notion API v1 (https://api.notion.com/v1)

**Key Methods:**

- `create_story()` - Create story with idempotency
- `list_stories()` - Query and filter stories
- `_find_epic_by_title()` - Find existing epic
- `_create_epic()` - Create new epic
- `_create_story_page()` - Create Notion page
- `_query_stories()` - Query stories database

**Configuration Required:**

- `NOTION_API_TOKEN` - API authentication
- `NOTION_DATABASE_STORIES_ID` - Stories database ID
- `NOTION_DATABASE_EPICS_ID` - Epics database ID

**Dependency Graph:**

```
mcp/tools/notion.py
├── mcp/schemas.py (models)
└── External: Notion API
```

---

#### 1.3.3 GitHub Tool (`mcp/tools/github.py`)

**Path:** `/mcp/tools/github.py`  
**Lines:** 214  
**Role:** GitHub API integration

**Purpose:**

- Create GitHub issues
- Link issues to Notion stories
- Idempotency protection
- Label management
- PR creation (scaffolded)

**Dependencies:**

**Standard Library:**

- `os` - Environment variables
- `typing` - Type hints
- `datetime` - Timestamps

**Third-Party:**

- `httpx.AsyncClient` - HTTP client
- `pydantic.BaseModel` - Models

**Internal:**

- `mcp.schemas`
  - `CreateIssueRequest`
  - `CreateIssueResponse`
  - `Priority`
  - `AuditEntry`

**External APIs:**

- GitHub API v3 (https://api.github.com)

**Key Methods:**

- `create_issue()` - Create issue with idempotency
- `_format_issue_body()` - Format issue description
- `_embed_metadata()` - Embed idempotency key
- `close()` - Cleanup HTTP client

**Configuration Required:**

- `GITHUB_TOKEN` - API authentication
- `GITHUB_REPO` - Repository (format: owner/repo)
- `GITHUB_DEFAULT_BRANCH` - Default branch (optional)

**Dependency Graph:**

```
mcp/tools/github.py
├── mcp/schemas.py (models)
└── External: GitHub API
```

---

#### 1.3.4 Audit Tool (`mcp/tools/audit.py`)

**Path:** `/mcp/tools/audit.py`  
**Lines:** 224  
**Role:** Audit logging and querying

**Purpose:**

- Append-only audit logs
- JSONL format
- Query interface
- Hash-based integrity
- Async file operations

**Dependencies:**

**Standard Library:**

- `os` - Environment variables
- `json` - Serialization
- `hashlib` - Content hashing
- `datetime` - Timestamps
- `pathlib.Path` - File paths
- `typing` - Type hints
- `asyncio` - Async locking

**Third-Party:**

- `aiofiles` - Async file I/O

**Internal:**

- `mcp.schemas.AuditEntry` - Audit model

**Key Methods:**

- `log_action()` - Write audit entry
- `query()` - Query audit logs with filters
- `_generate_hash()` - Generate content hash
- `_parse_audit_line()` - Parse JSONL entry

**Configuration Required:**

- `AUDIT_DIR` - Audit directory (default: ./audit)
- `TENANT_ID` - Tenant identifier
- `ENVIRONMENT` - Environment name

**Storage:**

- File pattern: `audit/actions_YYYYMMDD.jsonl`
- Format: One JSON object per line
- Rotation: Daily

**Dependency Graph:**

```
mcp/tools/audit.py
├── mcp/schemas.py (AuditEntry)
└── File System: audit/*.jsonl
```

---

### 1.4 Agent Implementations (`agent/`)

#### 1.4.1 Simple PM Agent (`agent/simple_pm.py`) [LEGACY]

**Path:** `/agent/simple_pm.py`  
**Lines:** 196  
**Role:** Legacy PM agent (no longer in use)

**Status:** ⚠️ **NOT IN USE** - Replaced by LangGraph PMAgent

**Purpose:**

- Message parsing (regex-based)
- Story creation workflow
- GitHub issue creation
- Error handling
- No LangGraph dependencies

**Note:** This was a temporary implementation to avoid LangGraph compatibility
issues. Now that LangGraph is operational, this agent is no longer used by the
MCP server.

**Dependencies:**

**Standard Library:**

- `os` - Environment variables
- `typing` - Type hints
- `datetime` - Timestamps
- `enum.Enum` - State enumeration
- `json` - Serialization
- `re` - Regex for parsing

**Third-Party:**

- `httpx.AsyncClient` - HTTP client for MCP server

**Internal:**

- None (standalone)

**Key Methods:**

- `process_message()` - Main processing pipeline
- `_parse_message()` - Extract story details from text
- `_create_story()` - Call MCP to create story
- `_create_issue()` - Call MCP to create issue
- `close()` - Cleanup HTTP client

**State Machine:**

- `UNDERSTANDING` - Initial state
- `NEEDS_CLARIFICATION` - Missing info
- `PLANNING` - Planning execution
- `CREATING_STORY` - Creating Notion story
- `CREATING_ISSUE` - Creating GitHub issue
- `COMPLETED` - Success
- `ERROR` - Error state

**Dependency Graph:**

```
agent/simple_pm.py
├── (no internal dependencies)
└── Calls: mcp_server.py (via HTTP)
    └── MCP endpoints
```

---

#### 1.4.2 LangGraph PM Agent (`agent/pm_graph.py`) ✅ OPERATIONAL

**Path:** `/agent/pm_graph.py`  
**Lines:** 406  
**Role:** LangGraph-based PM agent with AI

**Purpose:**

- AI-powered task understanding (GPT-4)
- Conversation management
- Multi-turn clarification
- LangGraph state machine
- OpenAI integration
- Validation and planning pipeline

**Status:** ✅ **OPERATIONAL** - Active in MCP Server v0.4.0

**Dependencies:**

**Standard Library:**

- `typing` - Type hints (TypedDict, Annotated, Sequence, etc.)
- `datetime` - Timestamps
- `enum.Enum` - Enumerations
- `os` - Environment variables

**Third-Party:**

- `httpx.AsyncClient` - HTTP client
- `langgraph` - Agent framework
  - `StateGraph` - State machine
  - `Graph` - Graph construction
  - `END` - Terminal node
  - `ToolExecutor` - Tool execution
- `langchain_core.messages` - Message types
  - `BaseMessage`
  - `HumanMessage`
  - `AIMessage`
  - `SystemMessage`
- `langchain_openai.ChatOpenAI` - OpenAI integration
- `langchain_core.prompts` - Prompt templates
  - `ChatPromptTemplate`
  - `MessagesPlaceholder`
- `pydantic` - Data models
  - `BaseModel`
  - `Field`

**Internal:**

- None (standalone)

**Key Components:**

- `AgentState` - State definition (TypedDict)
- `PMAgent` - Main agent class
- `understand_task` - Task comprehension node
- `request_clarification` - Clarification node
- `validate_requirements` - Validation node
- `plan_execution` - Planning node
- `create_story` - Story creation node
- `create_issue` - Issue creation node
- `complete_task` - Completion node

**Configuration Required:**

- `OPENAI_API_KEY` - OpenAI API key
- MCP server running on port 8001

**Dependency Graph:**

```
agent/pm_graph.py
├── LangChain/LangGraph (external)
├── OpenAI API (external)
└── Calls: mcp_server.py (via HTTP)
    └── MCP endpoints
```

---

## 2. Frontend Code Files

### 2.1 Root Layout (`app/layout.tsx`)

**Path:** `/app/layout.tsx`  
**Lines:** 16  
**Role:** Next.js root layout component

**Purpose:**

- Define HTML structure
- Apply global styles
- Set metadata

**Dependencies:**

**Next.js:**

- `Metadata` type from "next"
- `ReactNode` type from "react"

**Internal:**

- `./globals.css` - Global styles

**Exports:**

- `metadata` - Page metadata
- `RootLayout` component

**Dependency Graph:**

```
app/layout.tsx
├── app/globals.css (styles)
└── React (external)
```

---

### 2.2 Home Page (`app/page.tsx`)

**Path:** `/app/page.tsx`  
**Lines:** 117  
**Role:** Next.js home page component

**Purpose:**

- Display system status
- Show integration health
- Provide navigation
- API status monitoring

**Dependencies:**

**React:**

- `useEffect` - Side effects
- `useState` - State management

**External:**

- MCP Server API (http://localhost:8001/api/status)

**Components:**

- `HomePage` - Main page component
- `IntegrationRow` - Status display
- `NavLink` - Navigation button

**Environment Variables:**

- `NEXT_PUBLIC_API_URL` - MCP server URL

**Dependency Graph:**

```
app/page.tsx
├── React (external)
└── Calls: mcp_server.py/api/status (via HTTP)
```

---

### 2.3 Tailwind Config (`app/tailwind.config.js`)

**Path:** `/app/tailwind.config.js`  
**Lines:** 11  
**Role:** Tailwind CSS configuration

**Purpose:**

- Configure Tailwind CSS
- Define content paths
- Set theme extensions

**Dependency Graph:**

```
app/tailwind.config.js
├── (configuration only)
└── Used by: Next.js build system
```

---

## 3. Dependency Map Visualization

### 3.1 Backend Dependency Flow

```
┌─────────────────────────────────────────────────────────┐
│ Entry Point: mcp_server.py                             │
└─────────────┬───────────────────────────────────────────┘
              │
              ├─── mcp/schemas.py (data models)
              │    └─── Used by all tools
              │
              ├─── mcp/tools/__init__.py
              │    ├─── mcp/tools/notion.py
              │    │    ├─── mcp/schemas.py
              │    │    └─── External: Notion API
              │    │
              │    ├─── mcp/tools/github.py
              │    │    ├─── mcp/schemas.py
              │    │    └─── External: GitHub API
              │    │
              │    └─── mcp/tools/audit.py
              │         ├─── mcp/schemas.py
              │         └─── File System
              │
              └─── agent/pm_graph.py
                   ├─── LangChain/LangGraph
                   ├─── OpenAI API
                   └─── Calls: mcp_server.py (HTTP)
```

### 3.2 Frontend Dependency Flow

```
┌─────────────────────────────────────────────────────────┐
│ Entry Point: app/layout.tsx                            │
└─────────────┬───────────────────────────────────────────┘
              │
              ├─── app/globals.css
              │
              └─── app/page.tsx
                   └─── Calls: mcp_server.py (HTTP)
```

### 3.3 Cross-Layer Communication

```
Frontend (Next.js)
       │
       │ HTTP/REST
       ↓
Backend (FastAPI)
       │
       ├─→ MCP Tools
       │   ├─→ Notion API
       │   ├─→ GitHub API
       │   └─→ File System
       │
       └─→ Agent (LangGraph PMAgent ✅ Active)
           └─→ MCP Tools (via HTTP)
```

---

## 4. External Dependencies

### 4.1 Python Packages (requirements.txt)

**Core:**

- `fastapi==0.115.5` - Web framework
- `uvicorn[standard]==0.32.1` - ASGI server
- `python-dotenv==1.0.1` - Environment config
- `httpx==0.27.2` - HTTP client
- `pydantic==2.10.3` - Data validation
- `pydantic-settings==2.6.1` - Settings management

**LangChain/LangGraph:**

- `langchain==0.2.16` - LangChain framework
- `langchain-core==0.2.41` - Core components
- `langchain-openai==0.1.25` - OpenAI integration
- `langgraph==0.2.39` - Graph-based agents
- `langsmith==0.1.134` - LangSmith tracing

**AI/ML:**

- `openai==1.57.0` - OpenAI SDK

**Async:**

- `aiofiles==24.1.0` - Async file I/O

**Testing:**

- `pytest==8.3.4` - Testing framework
- `pytest-asyncio==0.24.0` - Async test support

**Development:**

- `black==24.10.0` - Code formatter
- `ruff==0.8.2` - Linter
- `mypy==1.13.0` - Type checker

### 4.2 Node Packages (package.json)

**Core:**

- `next@14.2.33` - Next.js framework
- `react@^18` - React library
- `react-dom@^18` - React DOM

**Styling:**

- `tailwindcss@^3.4.1` - CSS framework
- `autoprefixer@^10.4.18` - CSS post-processor
- `postcss@^8.4.35` - CSS processor

**TypeScript:**

- `typescript@^5` - TypeScript compiler
- `@types/node@^20` - Node.js types
- `@types/react@^18` - React types
- `@types/react-dom@^18` - React DOM types

**Development:**

- `eslint@^8` - Linter
- `eslint-config-next@14.2.33` - Next.js ESLint config

### 4.3 External APIs

**Notion API:**

- Base URL: https://api.notion.com/v1
- Version: 2022-06-28
- Authentication: Bearer token
- Used by: `mcp/tools/notion.py`

**GitHub API:**

- Base URL: https://api.github.com
- Version: v3 (2022-11-28)
- Authentication: Bearer token
- Used by: `mcp/tools/github.py`

**OpenAI API:**

- Used by: `agent/pm_graph.py`
- Model: GPT-4
- Authentication: API key

---

## 5. Code Statistics

### 5.1 Lines of Code by File

| File                     | Lines     | Category               |
| ------------------------ | --------- | ---------------------- |
| `mcp_server.py`          | 407       | Backend/Server         |
| `agent/pm_graph.py` ✅   | 406       | Backend/Agent (ACTIVE) |
| `mcp/tools/notion.py`    | 335       | Backend/Tool           |
| `mcp/tools/audit.py`     | 224       | Backend/Tool           |
| `mcp/tools/github.py`    | 214       | Backend/Tool           |
| `agent/simple_pm.py` ⚠️  | 196       | Backend/Agent (LEGACY) |
| `mcp/schemas.py`         | 159       | Backend/Model          |
| `app/page.tsx`           | 117       | Frontend/Page          |
| `app/layout.tsx`         | 16        | Frontend/Layout        |
| `app/tailwind.config.js` | 11        | Frontend/Config        |
| `mcp/tools/__init__.py`  | 7         | Backend/Package        |
| **Total**                | **2,092** |                        |

### 5.2 Code Distribution

**By Layer:**

- Server Layer: 407 lines (19%)
- Tool Layer: 780 lines (37%)
- Agent Layer: 602 lines (29%)
- Model Layer: 159 lines (8%)
- Frontend Layer: 144 lines (7%)

**By Language:**

- Python: 1,948 lines (93%)
- TypeScript/React: 133 lines (6%)
- JavaScript: 11 lines (1%)

### 5.3 Complexity Metrics

**Backend (Python):**

- Average file size: ~216 lines
- Largest file: `mcp_server.py` (407 lines)
- Smallest file: `mcp/tools/__init__.py` (7 lines)

**Frontend (TypeScript/React):**

- Average file size: ~48 lines
- Largest file: `app/page.tsx` (117 lines)
- Smallest file: `app/tailwind.config.js` (11 lines)

---

## 6. Import Analysis

### 6.1 Most Used Modules

**Standard Library:**

1. `typing` - Used in 9 files
2. `os` - Used in 7 files
3. `datetime` - Used in 6 files
4. `enum` - Used in 4 files
5. `json` - Used in 3 files

**Third-Party:**

1. `httpx` - Used in 5 files (HTTP communication)
2. `pydantic` - Used in 4 files (data validation)
3. `fastapi` - Used in 1 file (web framework)
4. `langchain` - Used in 1 file (agent framework)

**Internal:**

1. `mcp.schemas` - Imported by 4 files (most depended upon)
2. `mcp.tools` - Imported by 1 file

### 6.2 Dependency Depth

**Leaf Nodes (no internal dependencies):**

- `mcp/schemas.py` - Core data models
- `agent/simple_pm.py` - Standalone agent (LEGACY - not in use)

**Level 1 (depends on leaf nodes):**

- `mcp/tools/notion.py` - Depends on schemas
- `mcp/tools/github.py` - Depends on schemas
- `mcp/tools/audit.py` - Depends on schemas

**Level 2 (depends on level 1):**

- `mcp/tools/__init__.py` - Exports from level 1
- `agent/pm_graph.py` - Calls MCP tools via HTTP ✅ (ACTIVE)

**Root (depends on all):**

- `mcp_server.py` - Orchestrates everything

---

## 7. Configuration Files

### 7.1 Environment Variables Required

**Notion Integration:**

- `NOTION_API_TOKEN` - Notion API token
- `NOTION_DATABASE_STORIES_ID` - Stories database ID
- `NOTION_DATABASE_EPICS_ID` - Epics database ID

**GitHub Integration:**

- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_REPO` - Repository (format: owner/repo)
- `GITHUB_DEFAULT_BRANCH` - Default branch (optional, default: main)

**OpenAI Integration:**

- `OPENAI_API_KEY` - OpenAI API key

**Server Configuration:**

- `ENVIRONMENT` - Environment name (default: development)
- `TENANT_ID` - Tenant identifier (default: local-dev)
- `AUDIT_DIR` - Audit directory (default: ./audit)
- `MCP_AUTH_TOKEN` - MCP server auth token (default: dev-token)

**Frontend Configuration:**

- `NEXT_PUBLIC_API_URL` - MCP server URL

---

## 8. Key Observations

### 8.1 Strengths

1. **Clear Separation of Concerns**

   - Models, tools, agents, and server are well-separated
   - Each component has a single responsibility

2. **Type Safety**

   - Pydantic models provide runtime validation
   - TypeScript provides compile-time type checking
   - Comprehensive type hints in Python

3. **Modular Design**

   - Tools are independent and swappable
   - Agents are separate from server
   - Clean dependency boundaries

4. **Async Throughout**

   - All I/O operations are async
   - Non-blocking architecture
   - Scalable design

5. **Idempotency Protection**
   - Built into tools at the lowest level
   - Content-based hashing
   - Safe retry logic

### 8.2 Areas for Improvement

1. **Circular Dependency Risk**

   - Agent calls MCP server via HTTP (tight coupling)
   - Consider: Direct tool imports vs HTTP calls

2. **Configuration Management**

   - Environment variables scattered across files
   - Consider: Centralized config module

3. **Error Handling**

   - Not standardized across tools
   - Consider: Common error handling framework

4. **Testing Coverage**

   - Unit tests needed for core functions
   - Consider: Test doubles for external APIs

5. **Frontend Development**
   - Minimal UI implementation
   - Consider: Complete chat interface

### 8.3 Technical Debt

1. **Legacy Agent Cleanup**

   - `agent/simple_pm.py` is no longer in use
   - Consider archiving or removing
   - Update tests that reference it

2. **In-Memory Caches**

   - Idempotency caches lost on restart
   - Need: Redis or persistent storage

3. **Hardcoded URLs**

   - MCP server URL hardcoded in agents
   - Need: Configuration injection

4. **No Authentication**
   - MCP server has no real auth
   - Need: JWT or API key auth

---

## 9. Recommendations

### 9.1 Immediate Actions

1. **Resolve LangGraph Issues**

   - Fix dependency conflicts
   - Or remove `pm_graph.py`
   - Document decision in ADR

2. **Add Unit Tests**

   - Test message parsing
   - Test schema validation
   - Test idempotency logic

3. **Centralize Configuration**
   - Create `config.py` module
   - Load all env vars in one place
   - Inject config into components

### 9.2 Short-Term Improvements

1. **Improve Error Handling**

   - Create custom exception hierarchy
   - Standardize error responses
   - Add error recovery logic

2. **Add Logging**

   - Structured logging throughout
   - Correlation IDs
   - Debug mode support

3. **Complete Frontend**
   - Implement chat interface
   - Add backlog view
   - Real-time updates

### 9.3 Long-Term Enhancements

1. **Add Redis**

   - Persistent idempotency cache
   - Session storage
   - Rate limiting

2. **Add WebSocket Support**

   - Real-time updates
   - Streaming responses
   - Connection management

3. **Add Observability**
   - OpenTelemetry instrumentation
   - Metrics collection
   - Distributed tracing

---

## 10. Dependency Installation

### 10.1 Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 10.2 Frontend Setup

```bash
# Install Node dependencies
npm install

# Or with yarn
yarn install
```

### 10.3 Development Tools

```bash
# Install pre-commit hooks (if configured)
pre-commit install

# Run linters
black .
ruff check .
mypy .

# Run tests
pytest tests/ -v
```

---

**Inventory Complete** | Generated: November 10, 2025  
_For questions or updates, see
[docs/PROJECT_STATUS.md](./docs/PROJECT_STATUS.md)_
