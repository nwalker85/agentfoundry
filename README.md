# Engineering Department

An autonomous software development lifecycle (SDLC) control plane that orchestrates AI agents to handle the complete development process from requirements gathering through deployment.

## Project Status

**Current Phase:** Phase 4 - Frontend Operational with LangGraph Agent  
**Version:** 0.5.0  
**Status:** Core functionality operational, POC demonstration ready

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Notion API Token (optional - mock mode available)
- GitHub Personal Access Token (optional - mock mode available)
- OpenAI API Key

### Installation & Running

```bash
# Clone the repository
git clone <repo-url>
cd engineeringdepartment

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up Node environment
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your API tokens (or leave blank for mock mode)

# Start both services
./start_dev.sh

# Or run separately:
# Terminal 1: Start MCP server
python mcp_server.py

# Terminal 2: Start frontend
npm run dev

# Visit http://localhost:3000/chat
```

## ✅ What's Working

### Backend (90% Complete)
- **LangGraph PM Agent**: Sophisticated multi-step workflow with GPT-4
  - Understand → Clarify → Validate → Plan → Execute pipeline
  - Multi-turn clarification loops
  - Intelligent task extraction and validation
- **MCP Server**: FastAPI server with 8 operational endpoints
- **Notion Integration**: Story creation with idempotency protection (mock mode available)
- **GitHub Integration**: Automated issue creation linked to stories (mock mode available)
- **Audit Logging**: Complete JSONL-based compliance trail

### Frontend (75% Complete)
- **Chat Interface**: Full conversational UI at `/chat`
  - Message thread with user/assistant messages
  - Real-time connection status
  - Loading states and error handling
- **State Management**: Zustand store with session persistence
- **API Integration**: Proxy layer connecting to MCP server
- **Artifact Display**: Basic cards for created stories/issues

## Architecture

```
┌──────────────┐
│  Next.js UI  │ ← Chat interface, message thread
└──────┬───────┘
       │ HTTP/REST (WebSocket planned)
┌──────▼───────────┐
│   MCP Server     │ ← FastAPI orchestration layer
│    (Port 8001)   │
└──────┬───────────┘
       │
┌──────▼───────────┐
│ LangGraph Agent  │ ← GPT-4 powered state machine
│   (pm_graph.py)  │
└──────┬───────────┘
       │
┌──────▼──────────┐
│   Tool Layer    │
├─────────────────┤
│ • Notion API    │ ← Story management (mock available)
│ • GitHub API    │ ← Issue tracking (mock available)
│ • Audit Logs    │ ← Compliance trail
└─────────────────┘
```

## Key Features

- **🤖 AI-Powered Understanding**: GPT-4 comprehends natural language requests
- **🔄 Sophisticated Workflow**: LangGraph state machine with validation and planning
- **💬 Conversational Interface**: Natural chat-based interaction
- **📝 Automatic Story Creation**: Notion stories with proper structure and metadata
- **🎯 GitHub Integration**: Issues created with acceptance criteria and DoD
- **🔐 Idempotency Protection**: Prevents duplicate creation with content hashing
- **📊 Audit Trail**: Complete logging of all operations
- **🧪 Mock Mode**: Test without real API credentials

## Demo Scenarios

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

## Project Structure

```
engineeringdepartment/
├── mcp_server.py              # FastAPI MCP server
├── agent/
│   ├── pm_graph.py            # LangGraph PM Agent (active)
│   ├── pm_agent_simple.py     # Simplified fallback agent
│   └── simple_pm.py           # Legacy simple agent
├── mcp/
│   ├── tools/                 # Tool implementations
│   │   ├── notion.py          # Notion API integration
│   │   ├── github.py          # GitHub API integration
│   │   └── audit.py           # Audit logging
│   └── schemas.py             # Pydantic models
├── app/                       # Next.js frontend
│   ├── chat/                  # Chat interface
│   │   ├── page.tsx          # Main chat page
│   │   └── components/       # Message, Input, Thread components
│   ├── api/                  # API routes
│   │   └── chat/            # Chat endpoint proxy
│   └── lib/                  # Libraries
│       ├── stores/          # Zustand state management
│       └── types/           # TypeScript definitions
├── tests/                     # Test suites
│   ├── e2e/                  # End-to-end tests
│   └── integration/          # Integration tests
├── docs/                      # Documentation
└── progressaudit/             # Development progress tracking
```

## Environment Variables

Create `.env.local` with:

```bash
# Required for LangGraph Agent
OPENAI_API_KEY=sk-...

# Optional - Leave blank for mock mode
NOTION_API_TOKEN=secret_...
NOTION_DATABASE_STORIES_ID=<database-id>
NOTION_DATABASE_EPICS_ID=<database-id>

# Optional - Leave blank for mock mode
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo

# Development settings
ENVIRONMENT=development
TENANT_ID=default
MCP_SERVER_PORT=8001
```

## API Endpoints

### Agent Endpoints
- `POST /api/agent/process` - Process message through LangGraph PM agent
- `POST /api/agent/chat` - Legacy chat endpoint

### Tool Endpoints
- `POST /api/tools/notion/create-story` - Create story in Notion
- `POST /api/tools/notion/list-stories` - List stories with filters
- `POST /api/tools/github/create-issue` - Create GitHub issue
- `GET /api/tools/audit/query` - Query audit logs

### Status Endpoints
- `GET /` - Health check with tool status
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

# Test with mock mode (no API credentials needed)
NOTION_DATABASE_STORIES_ID="" GITHUB_REPO="" python mcp_server.py
```

## Documentation

- [Frontend Development Plan](docs/FRONTEND_DEVELOPMENT_PLAN.md) - Frontend roadmap
- [Architecture](docs/ARCHITECTURE.md) - System design decisions
- [Testing Guide](docs/TESTING_GUIDE.md) - Testing documentation
- [POC Scope](docs/POC_SCOPE.md) - Proof of concept requirements
- [Progress Audits](progressaudit/) - Development progress tracking

## Current Limitations & Next Steps

### In Progress
- [ ] WebSocket support for streaming responses
- [ ] Backlog view at `/backlog`
- [ ] Enhanced tool result cards with better UI
- [ ] Markdown rendering in chat messages
- [ ] Conversation persistence with Redis

### Planned Enhancements
- [ ] Multi-agent orchestration (QA, SRE agents)
- [ ] Docker containerization
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Production authentication (SSO/OIDC)
- [ ] Observability with OpenTelemetry

## Contributing

1. Check [Current State](progressaudit/CURRENT_STATE_20251111.md) for latest status
2. Review [Frontend Development Plan](docs/FRONTEND_DEVELOPMENT_PLAN.md) for UI tasks
3. See [Testing Guide](docs/TESTING_GUIDE.md) for test requirements
4. Follow existing patterns in `agent/pm_graph.py` for agent modifications

## Recent Updates

- **v0.5.0** (Nov 11, 2025): Frontend operational with chat interface
  - Full chat UI with message thread and input
  - LangGraph agent properly integrated
  - Mock mode for testing without API credentials
  - Basic artifact display for stories/issues
  
- **v0.4.0** (Nov 10, 2025): LangGraph PM Agent operational
  - Sophisticated state machine workflow
  - GPT-4 powered understanding
  - Multi-turn clarification loops

- **v0.3.0**: MCP tools integration complete
- **v0.2.0**: Initial MCP server implementation

## License

Private - Internal Use Only

---

**MCP Server:** http://localhost:8001  
**Frontend:** http://localhost:3000  
**Last Updated:** November 11, 2025  
**Version:** 0.5.0
