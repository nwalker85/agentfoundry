# Engineering Department

An autonomous software development lifecycle (SDLC) control plane that orchestrates AI agents to handle the complete development process from requirements gathering through deployment.

## Project Status

**Current Phase:** Phase 3 Complete - MCP Tools & Agent Integration  
**Status:** Core functionality operational, frontend integration pending

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
python test_e2e.py
```

## Documentation

- [Current State](Current%20State.md) - Implementation status
- [Project Plan](PROJECT_PLAN.md) - Development roadmap
- [POC Scope](POC_SCOPE.md) - Proof of concept requirements
- [Testing Guide](UAT_GUIDE.md) - User acceptance testing

## Architecture

```
User → Chat Interface → PM Agent → MCP Server → External Systems
                                         ↓
                                    [Notion API]
                                    [GitHub API]
                                    [Audit Logs]
```

## Key Features

- Conversational story creation
- Automatic GitHub issue generation
- Idempotency protection
- Complete audit trail
- Multi-agent orchestration (planned)

---

**MCP Server:** http://localhost:8001  
**Last Updated:** November 9, 2025
