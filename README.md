# Agent Foundry

**Modern AI Agent Development Platform** - Professional platform for building, deploying, and managing AI agents with voice capabilities and multi-agent orchestration.

## Project Status

**Current Phase:** MVP UI Scaffolding Complete
**Version:** 0.8.1-dev
**Status:** **Development - Production-Ready UI Shell**

### Latest Achievement (Nov 16, 2025)
🎉 **v0.8.1-dev** - Complete MVP UI scaffolding with Shadcn component library and Ravenhelm dark theme. Professional navigation system, dashboard, and page architecture ready for feature development.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- OpenAI API Key (required)
- Notion API Token (optional - mock mode available)
- GitHub Personal Access Token (optional - mock mode available)

### Installation & Running

```bash
# Clone and navigate to project
cd "/Users/nwalker/Development/Projects/agentfoundry"

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies (includes autoprefixer fix)
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your OpenAI API key (required)
# Notion and GitHub tokens optional - mock mode works without them

# Start both services
./start_dev.sh

# Or run separately:
# Terminal 1: Start Backend (FastAPI on port 8000)
python mcp_server.py

# Terminal 2: Start Frontend (Next.js on port 3000)
npm run dev

# Visit http://localhost:3000 to see the Dashboard!
```

## ✅ What's Working

### Backend (90% Complete)
- **LangGraph PM Agent**: Sophisticated GPT-4 powered state machine
  - Understand → Clarify → Validate → Plan → Execute pipeline
  - Multi-turn clarification loops with intelligent stopping
  - Structured task extraction and validation
  - Error handling and recovery
- **MCP Server**: FastAPI server with 8 operational endpoints
- **Notion Integration**: Story creation with idempotency protection (mock mode available)
- **GitHub Integration**: Issue creation with proper linking (mock mode available)
- **Audit Logging**: Complete JSONL-based compliance trail
- **Mock Mode**: Full functionality without external API credentials

### Frontend (MVP Complete) ⭐ v0.8.1
- **Design System**: Professional Ravenhelm dark theme
  - ✅ Shadcn UI component library
  - ✅ Custom color palette (bg-0/1/2, fg-0/1/2, blue-600, cyan-400)
  - ✅ CSS variables for consistent theming
  - ✅ Lucide React icons throughout
- **Global Navigation**: Persistent app shell
  - ✅ TopNav with org switcher, app menu, user dropdown
  - ✅ LeftNav with collapsible sidebar (responsive - hidden on mobile)
  - ✅ Organization switcher modal (stub)
  - ✅ App launcher modal (Forge AI, Crucible AI, DIS)
- **Dashboard** (`/`): Command center
  - ✅ Metric cards (Organizations, Projects, Instances, Artifacts)
  - ✅ System status with API integration monitoring
  - ✅ Recent activity feed (empty state)
- **Projects** (`/projects`): Project management
  - ✅ Table with search and filter controls
  - ✅ Empty state with CTA
  - ✅ Ready for CRUD implementation
- **Instances** (`/instances`): Agent instance monitoring (stub)
- **Artifacts** (`/artifacts`): Generated artifact browser (stub)
- **Chat Interface** (`/chat`): AI conversation
  - ✅ Migrated to work within app shell
  - ✅ Enhanced markdown rendering with syntax highlighting
  - ✅ Real-time connection status
  - ✅ Voice integration toggle (LiveKit)
  - ✅ WebSocket communication with fallback
- **State Management**: Zustand store with session tracking
- **Responsive Design**: Mobile-first with tablet/desktop breakpoints

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js UI (Port 3000)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Global App Shell - Shadcn Components + Ravenhelm     │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ TopNav: Org Switcher | App Menu | User Menu         │   │
│  ├────────┬─────────────────────────────────────────────┤   │
│  │LeftNav │ Dashboard  | Projects | Instances | Chat   │   │
│  │        │ Artifacts  | Admin    | More...            │   │
│  └────────┴─────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/REST + WebSocket
┌───────────────────────────▼─────────────────────────────────┐
│              Backend Server (Port 8000)                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FastAPI Orchestration Layer                          │   │
│  │ • RESTful API endpoints                              │   │
│  │ • WebSocket for real-time chat                       │   │
│  │ • Health checks & status monitoring                  │   │
│  └──────────────────────┬───────────────────────────────┘   │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              LangGraph PM Agent (pm_graph.py)                │
│  GPT-4 Powered State Machine with:                          │
│  • Understand → Clarify → Validate → Plan → Execute         │
│  • Multi-turn clarification loops                           │
│  • Structured task extraction                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                      Tool & Integration Layer                │
├──────────────────────────────────────────────────────────────┤
│ • Notion API     - Story management (mock available)         │
│ • GitHub API     - Issue tracking (mock available)           │
│ • LiveKit        - Voice agent infrastructure                │
│ • Audit Logs     - Compliance trail                          │
└──────────────────────────────────────────────────────────────┘
```

## Key Features

- **🤖 AI-Powered Understanding**: GPT-4 comprehends natural language requests
- **🔄 Sophisticated Workflow**: LangGraph state machine with validation and planning
- **💬 Production-Ready Chat UI**: Modern, responsive interface with animations
- **📝 Automatic Story Creation**: Notion stories with proper structure and metadata
- **🎯 GitHub Integration**: Issues created with acceptance criteria and DoD
- **🔐 Idempotency Protection**: Prevents duplicate creation with content hashing
- **📊 Audit Trail**: Complete logging of all operations
- **🧪 Mock Mode**: Test without real API credentials
- **⚡ Fast Performance**: Optimized with proper caching and state management

## UI Navigation

**Main Pages:**
- **Dashboard** (`/`) - Overview with metrics, system status, and activity
- **Projects** (`/projects`) - Project management (stub - ready for implementation)
- **Instances** (`/instances`) - Running agent instances (stub)
- **Artifacts** (`/artifacts`) - Generated artifacts browser (stub)
- **Chat** (`/chat`) - AI-powered conversation interface

**Navigation:**
- **TopNav** - Organization switcher, app launcher, user menu
- **LeftNav** - Main navigation (responsive - hidden on mobile)
- **Modals** - Org switcher and app launcher overlays

## Demo Scenarios

Try these in the chat interface at http://localhost:3000/chat:

### Basic Story Creation
```
"Create a story for adding user authentication to our platform with P1 priority"
```

### With Epic Assignment
```
"Under the Security epic, create a story for implementing 2FA with SMS and email options"
```

### Complex Request with Details
```
"We need a P0 story in the Platform Hardening epic for adding rate limiting to our API. 
It should handle 1000 requests per minute per IP address and return 429 status codes 
when exceeded."
```

The interface will show:
1. Your message in a blue bubble
2. Typing indicator while processing
3. PM Agent response with story creation confirmation
4. Clickable links to view in Notion and GitHub
5. Connection status showing "Ready" when idle

## Project Structure

```
engineeringdepartment/
├── mcp_server.py              # FastAPI MCP server (port 8001)
├── agent/
│   ├── pm_graph.py            # ⭐ LangGraph PM Agent (production)
│   ├── pm_agent_simple.py     # Fallback agent (not actively used)
│   └── simple_pm.py           # Legacy agent
├── mcp/
│   ├── tools/                 # Tool implementations
│   │   ├── notion.py          # Notion API integration + mock
│   │   ├── github.py          # GitHub API integration + mock
│   │   └── audit.py           # Audit logging
│   └── schemas.py             # Pydantic models
├── app/                       # ⭐ Next.js frontend (port 3000)
│   ├── page.tsx              # Home/status page
│   ├── layout.tsx            # Root layout with Tailwind
│   ├── globals.css           # Global styles with Tailwind directives
│   ├── chat/                 # ⭐ Chat interface (fully operational)
│   │   ├── page.tsx          # Main chat page with message thread
│   │   ├── components/       # UI components
│   │   │   ├── MessageInput.tsx
│   │   │   ├── ConnectionStatus.tsx
│   │   │   └── MessageThread.tsx
│   │   └── hooks/           # Custom React hooks
│   ├── api/                 # API routes
│   │   └── chat/           # Chat endpoint proxy
│   ├── components/          # Shared components
│   │   └── messages/       # Message display components
│   └── lib/                 # Libraries
│       ├── stores/          # ⭐ Zustand state management
│       │   └── chat.store.ts
│       └── types/           # TypeScript definitions
├── tailwind.config.js         # ⭐ Tailwind configuration (root level)
├── postcss.config.js          # ⭐ PostCSS with autoprefixer
├── tests/                     # Test suites
│   ├── e2e/                  # End-to-end tests
│   └── integration/          # Integration tests
├── docs/                      # Documentation
└── progressaudit/             # Development progress tracking
    └── CURRENT_STATE_20251111.md  # Latest status
```

## Environment Variables

Create `.env.local` with:

```bash
# Required - LangGraph Agent needs this
OPENAI_API_KEY=sk-...

# Optional - Leave blank for mock mode (stories/issues created in logs only)
NOTION_API_TOKEN=secret_...
NOTION_DATABASE_STORIES_ID=<database-id>
NOTION_DATABASE_EPICS_ID=<database-id>

# Optional - Leave blank for mock mode
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo
GITHUB_DEFAULT_BRANCH=main

# Development settings (defaults shown)
ENVIRONMENT=development
TENANT_ID=default
MCP_SERVER_PORT=8000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Endpoints

### Agent Endpoints
- `POST /api/agent/process` - Process message through LangGraph PM agent
- `POST /api/agent/chat` - Legacy chat endpoint (deprecated)

### Tool Endpoints
- `POST /api/tools/notion/create-story` - Create story in Notion
- `POST /api/tools/notion/list-stories` - List stories with filters
- `POST /api/tools/github/create-issue` - Create GitHub issue
- `GET /api/tools/audit/query` - Query audit logs

### Status Endpoints
- `GET /` - Health check with integration status
- `GET /health` - Simple health check
- `GET /api/status` - Detailed API status
- `GET /api/tools/schema` - OpenAPI schemas

## Testing

```bash
# Run all tests
./run_tests.sh

# Run specific test suites
pytest tests/e2e/              # End-to-end tests
pytest tests/integration/       # Integration tests

# Test the LangGraph agent directly
python tests/integration/test_langgraph_agent.py

# Test with mock mode (no external API credentials needed)
NOTION_DATABASE_STORIES_ID="" GITHUB_REPO="" python mcp_server.py
```

## Documentation

### Core Docs
- [Current State (v0.7.0)](progressaudit/CURRENT_STATE_20251112.md) - **Start here** for latest status
- [Architecture](docs/ARCHITECTURE.md) - System design and technology decisions
- [Frontend Development Plan](docs/FRONTEND_DEVELOPMENT_PLAN.md) - UI roadmap and v0.7.0 targets
- [Testing Guide](docs/TESTING_GUIDE.md) - Testing strategy and UAT procedures
- [POC Scope](docs/POC_SCOPE.md) - Proof of concept requirements
- [Admin UI Requirements](docs/ADMIN_UI_REQUIREMENTS.md) - v0.8.0 agent management UI

### Reference Docs
- [POC Personas & Use Cases](docs/POC_PERSONAS_USE_CASES.md)
- [Production Requirements](docs/PROD_IMPLEMENTATION_REQUIREMENTS.md)
- [Notion Schema Design](docs/NOTION_SCHEMA_DESIGN.md)
- [Code Inventory](docs/CODE_INVENTORY.md)

## Current Limitations & Next Steps

### Completed ✅ v0.7.0
- [x] Chat UI rendering correctly with Tailwind
- [x] Message thread with proper styling
- [x] Connection status indicator
- [x] Loading states and error handling
- [x] Zustand state management
- [x] API proxy layer operational
- [x] Markdown rendering for AI responses (react-markdown + remark-gfm)
- [x] Enhanced tool result cards with richer UI (branded Notion/GitHub cards)
- [x] Code syntax highlighting in messages (prism-react-renderer)
- [x] Backlog view at `/backlog` route with priority filtering
- [x] Copy buttons for code blocks
- [x] Dark mode implementation

### Planned: v0.8.0+ - Production Features
- [ ] WebSocket support for streaming responses
- [ ] Conversation persistence with Redis
- [ ] Export conversation feature
- [ ] **Admin UI for agent management** (see ADMIN_UI_REQUIREMENTS.md)
- [ ] Multi-agent orchestration (QA, SRE agents)
- [ ] Docker containerization
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Production authentication (SSO/OIDC)
- [ ] Observability with OpenTelemetry

## Troubleshooting

### UI Not Rendering Styles
If you see unstyled HTML:
1. Ensure `tailwind.config.js` exists at project root (not in `/app`)
2. Ensure `postcss.config.js` exists at project root
3. Run `npm install` to ensure autoprefixer is installed
4. Delete `.next` folder and restart: `rm -rf .next && npm run dev`

### MCP Server Not Starting
1. Check Python version: `python --version` (needs 3.12+)
2. Activate venv: `source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Check port: `lsof -ti:8001` (kill if needed)

### Frontend Not Connecting to Backend
1. Ensure MCP server running on port 8001
2. Check `.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8001`
3. Check browser console for CORS errors
4. Verify proxy at `/app/api/chat/route.ts` is configured correctly

## Contributing

1. Check [Current State (v0.7.0)](progressaudit/CURRENT_STATE_20251112.md) for latest status
2. Review [Frontend Development Plan](docs/FRONTEND_DEVELOPMENT_PLAN.md) for v0.7.0 tasks
3. See [Testing Guide](docs/TESTING_GUIDE.md) for test requirements
4. Follow existing patterns in `agent/pm_graph.py` for agent modifications
5. Use TypeScript for all frontend code
6. Follow Tailwind CSS conventions for styling

## Recent Updates

- **v0.7.0** (Nov 12, 2025): 🎉 **Feature Complete - Enhanced UI & Backlog View**
  - Enhanced markdown rendering with GitHub Flavored Markdown
  - Code syntax highlighting with Prism (GitHub Dark theme)
  - Rich tool result cards for Notion stories and GitHub issues
  - Comprehensive backlog view with filtering and search
  - Production-ready dark mode across all components
  - Mobile-responsive design throughout
  
- **v0.6.0** (Nov 11, 2025): **UI Rendering Fixed - Chat Interface Operational**
  - Fixed Tailwind CSS configuration (moved to root, added autoprefixer)
  - Chat interface now rendering with full styling and animations
  - Professional UI with gradient headers, smooth transitions
  - Connection status, typing indicators, empty states all working
  - Ready for stakeholder demonstrations

- **v0.5.0** (Nov 11, 2025): Frontend implementation complete
  - Full chat UI with message thread and input components
  - LangGraph agent properly integrated
  - Mock mode for testing without API credentials
  - Basic artifact display for stories/issues
  
- **v0.4.0** (Nov 10, 2025): LangGraph PM Agent operational
  - Sophisticated state machine workflow
  - GPT-4 powered understanding
  - Multi-turn clarification loops

## License

Private - Internal Use Only

---

**MCP Server:** http://localhost:8001  
**Frontend Chat:** http://localhost:3000/chat  
**Status Dashboard:** http://localhost:3000  
**Backlog View:** http://localhost:3000/backlog  
**Last Updated:** November 15, 2025 - v0.8.0-dev Agent Foundry Rebrand  
**Version:** 0.8.0-dev
