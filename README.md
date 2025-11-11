# Engineering Department

An autonomous software development lifecycle (SDLC) control plane that orchestrates AI agents to handle the complete development process from requirements gathering through deployment.

## Project Status

**Current Phase:** Phase 3 Complete - LangGraph Agent Operational  
**Version:** 0.4.0  
**Status:** Core functionality operational with AI-powered agent, frontend integration pending

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Notion API Token
- GitHub Personal Access Token
- OpenAI API Key

### Installation

1. Set up Python environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your API tokens
```

3. Start the MCP server:
```bash
python mcp_server.py
# Server runs on http://localhost:8001
```

4. Run tests:
```bash
# Full test suite
./run_tests.sh

# Or run specific test suites:
pytest tests/e2e/              # End-to-end tests
pytest tests/integration/      # Integration tests
python tests/integration/test_langgraph_agent.py  # LangGraph agent test
```

## Documentation

- [Project Status](docs/PROJECT_STATUS.md) - Current implementation status
- [Architecture](docs/ARCHITECTURE.md) - System design and decisions
- [Testing Guide](docs/TESTING_GUIDE.md) - Comprehensive testing documentation
- [Code Inventory](docs/CODE_INVENTORY.md) - Codebase structure and dependencies
- [POC Scope](docs/POC_SCOPE.md) - Proof of concept requirements
- [Documentation Index](docs/README.md) - Full documentation listing

## Architecture

```
User → Chat Interface → LangGraph PM Agent (GPT-4) → MCP Server → External Systems
                           (agent/pm_graph.py)              ↓
                                                       [Notion API]
                                                       [GitHub API]
                                                       [Audit Logs]
```

### Key Components
- **LangGraph PM Agent**: AI-powered task understanding, multi-turn clarification, validation
- **MCP Server (FastAPI)**: Tool orchestration, idempotency, audit logging
- **External Integrations**: Notion (stories), GitHub (issues), OpenAI (GPT-4)

## Key Features

- **AI-Powered Understanding**: GPT-4 powered task comprehension and clarification
- **LangGraph State Machine**: Multi-step workflow with validation and planning
- **Conversational Story Creation**: Natural language to structured Notion stories
- **Automatic GitHub Issue Generation**: Synchronized issue tracking
- **Idempotency Protection**: Safe retries and duplicate prevention
- **Complete Audit Trail**: JSONL-based compliance logging
- **Multi-Agent Orchestration**: Ready for engineer/QA/SRE agents (Phase 5)

## Recent Updates

- **v0.4.0** (Nov 10, 2025): LangGraph PM Agent operational, compatibility issues resolved
  - See [LangGraph Integration Complete](progressaudit/LANGGRAPH_INTEGRATION_COMPLETE.md) for details
- **v0.3.0**: SimplePMAgent implementation (now deprecated)
- **v0.2.0**: MCP tools integration complete

## What's Working Now

✅ **MCP Server** (FastAPI) running on port 8001  
✅ **LangGraph PM Agent** with GPT-4 powered understanding  
✅ **Notion Integration** - Create and list stories with idempotency  
✅ **GitHub Integration** - Create issues with metadata  
✅ **Audit Logging** - JSONL-based compliance trail  
✅ **E2E Test Suite** - Comprehensive integration tests  

🔄 **In Progress**: Frontend chat interface, WebSocket transport

## Project Structure

```
engineeringdepartment/
├── mcp_server.py              # FastAPI MCP server
├── agent/
│   ├── pm_graph.py            # LangGraph PM Agent ✅ (active)
│   └── simple_pm.py           # Legacy agent (deprecated)
├── mcp/
│   ├── tools/                 # NotionTool, GitHubTool, AuditTool
│   └── schemas.py             # Pydantic models
├── app/                       # Next.js frontend (WIP)
├── tests/                     # Test suites (e2e, integration, uat)
├── docs/                      # Comprehensive documentation
└── progressaudit/             # Development progress tracking
```

---

**MCP Server:** http://localhost:8001 (v0.4.0)  
**Last Updated:** November 10, 2025
