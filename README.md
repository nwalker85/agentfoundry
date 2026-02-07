# Agent Foundry

AI agent development platform with LangGraph orchestration, voice capabilities, and multi-agent workflows.

## What It Does

Agent Foundry provides a complete environment for building, testing, and deploying AI agents:

- **LangGraph State Machine** - GPT-4 powered agent with structured understand-clarify-validate-plan-execute pipeline
- **Multi-turn Conversations** - Intelligent clarification loops with context retention
- **Voice Integration** - LiveKit-based voice agent infrastructure
- **Tool Orchestration** - Notion, GitHub, and custom tool integrations with idempotency protection
- **Audit Trail** - Complete JSONL-based compliance logging for all agent actions

## Architecture

```
Next.js UI ──── REST + WebSocket ────→ FastAPI Backend
                                           │
                                    LangGraph PM Agent
                                    (GPT-4 State Machine)
                                           │
                                    ┌──────┼──────┐
                                    │      │      │
                                 Notion  GitHub  Audit
                                  API     API    Logs
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI, Python 3.12 |
| AI | LangGraph, GPT-4, OpenAI |
| Voice | LiveKit |
| State | Zustand, WebSocket |

## Quick Start

```bash
# Backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env.local  # Add your OpenAI API key
python mcp_server.py

# Frontend (separate terminal)
npm install
npm run dev

# Visit http://localhost:3000
```

## Features

- Dark theme UI with Ravenhelm design system
- Dashboard with metrics, system status, activity feed
- Chat interface with markdown rendering and syntax highlighting
- Project management views
- Mock mode for development without external API credentials
- Mobile-responsive design

## License

MIT
