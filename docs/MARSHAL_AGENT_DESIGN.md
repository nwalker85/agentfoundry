# Marshal Agent - Design Document

**Version:** 0.1.0  
**Date:** November 15, 2025  
**Status:** Design Phase

---

## Overview

The **Marshal Agent** is a meta-agent responsible for monitoring, loading, and managing the agent registry. It ensures agents are healthy, properly configured, and ready to serve requests.

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Marshal Agent                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────┐     ┌───────────────┐       │
│  │ File Watcher │────>│ YAML Validator│       │
│  │ (watchfiles) │     │ (Pydantic)    │       │
│  └──────────────┘     └───────┬───────┘       │
│                               │                │
│  ┌─────────────────────────── v ─────────┐    │
│  │       Agent Loader                    │    │
│  │  - Parse YAML                         │    │
│  │  - Create LangGraph instance          │    │
│  │  - Register in registry               │    │
│  └────────────┬──────────────────────────┘    │
│               │                                │
│  ┌────────────v──────────────────────────┐    │
│  │       Agent Registry                  │    │
│  │  - In-memory: Dict[str, AgentInstance]│    │
│  │  - Redis: Persistent metadata         │    │
│  └────────────┬──────────────────────────┘    │
│               │                                │
│  ┌────────────v──────────────────────────┐    │
│  │       Health Monitor                  │    │
│  │  - Periodic health checks             │    │
│  │  - Metrics collection                 │    │
│  │  - Alert generation                   │    │
│  └────────────┬──────────────────────────┘    │
│               │                                │
│  ┌────────────v──────────────────────────┐    │
│  │       Admin Reporter                  │    │
│  │  - Validation errors                  │    │
│  │  - Health alerts                      │    │
│  │  - Metrics summary                    │    │
│  └───────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## File Structure

```
agents/
├── __init__.py
├── marshal_agent.py          # Main orchestrator
├── agent_loader.py           # Dynamic agent loading from YAML
├── agent_registry.py         # Central registry
├── health_monitor.py         # Health checks and metrics
├── yaml_validator.py         # Pydantic models for YAML schema
├── file_watcher.py          # Directory monitoring
├── state.py                 # Shared state definitions
│
├── pm-agent.agent.yaml      # Example: PM agent definition
├── qa-agent.agent.yaml      # Future: QA agent
├── sre-agent.agent.yaml     # Future: SRE agent
│
└── workers/                 # Worker implementations
    ├── pm_agent.py
    ├── qa_agent.py
    └── sre_agent.py
```

## Implementation Plan

### Phase 1: Core Infrastructure (This PR)

Files to create:
1. `agents/yaml_validator.py` - Pydantic models
2. `agents/agent_loader.py` - Dynamic loading
3. `agents/agent_registry.py` - Registry
4. `agents/file_watcher.py` - File monitoring
5. `agents/health_monitor.py` - Health checks
6. `agents/marshal_agent.py` - Main orchestrator

MCP Tools to add (in `backend/main.py`):
1. `GET /api/agents/list` - List all agents
2. `GET /api/agents/{id}/status` - Agent status
3. `POST /api/agents/{id}/reload` - Hot reload
4. `POST /api/agents/validate` - Validate YAML

Tests to create:
1. `tests/agents/test_yaml_validator.py`
2. `tests/agents/test_agent_loader.py`
3. `tests/agents/test_marshal_agent.py`

### Phase 2: Integration (Next PR)

1. Integrate Marshal with supervisor
2. Add health check UI
3. Create agent management admin page
4. Full E2E testing

## Success Criteria

- ✅ Marshal loads all `.agent.yaml` at startup
- ✅ Hot-reload on file changes
- ✅ Validation errors reported
- ✅ Health checks every 60s
- ✅ MCP tools functional
- ✅ < 1s from YAML save to agent ready

---

Apply this, or do you have notes?