# Engineering Department - Project Summary

## Vision

A multi-agent software development team where agents work as engineers, PMs,
QAs, etc. to build software with you (Director) providing requirements.

## Key Workflow

```
Director (You)
  ↓ requirements
Product Owner Agent (interviews, creates epics/stories/tasks)
  ↓
Backlog (Notion)
  ↓
Project Manager (prioritizes, assigns to agent queues)
  ↓
Engineering Agents (monitor queue, execute, update status/notes)
  ↓
QA Agents (validate, pass/fail)
  ↓
Done
```

## Critical Requirements

1. **Product Owner**: Conducts user interviews, creates
   releases/epics/stories/tasks
2. **Project Manager**: THE MOST IMPORTANT - coordinates, prioritizes, assigns
3. **Agent Queues**: Each agent monitors their queue, picks highest priority
   task
4. **Task Lifecycle**: Backlog → To Do → In Progress → In Review → In QA → Done
5. **Definition of Done**: Every task has acceptance criteria, validation, test
   cases
6. **QA Agents**: Separate QA for functional, security, performance testing
7. **Priority Resolution**: If tied, PM decides. Tasks have P0-P3 priority
   levels
8. **Status Updates**: Agents update tasks with notes throughout lifecycle
9. **Conflict Resolution**: Judge agent (from previous design) handles disputes

## Project Location

`/Users/nate/Development/1. Projects/Engineering Department/`

## What's Been Created

### Files Created ✅

```
Engineering Department/
├── core/
│   └── state.py                    # Complete state definitions
│       - Task, Epic, Story, Release types
│       - TaskStatus, TaskPriority, TaskType enums
│       - DefinitionOfDone dataclass
│       - AgentQueue, GlobalState
│       - All agent state types
├── agents/ (empty - ready for agents)
├── qa/ (empty - ready for QA agents)
└── (waiting for more files)
```

### Previously Scaffolded (in MCPManager/langgraph_agents/) ✅

These can be adapted/moved:

- `core/mcp_bridge.py` - MCP integration with RBAC
- `agents/project_manager.py` - Notion PM (needs major refactor for new
  workflow)
- `agents/python_generalist.py` - Example engineer agent
- `agents_ui.py` - Streamlit chat UI

## Next Steps (Priority Order)

1. **Product Owner Agent** - Interview Director, create work items
2. **Project Manager Agent** - Queue management, prioritization, assignment
3. **Queue System** - Agent queue monitoring and task pickup
4. **Engineer Agents** - Execute tasks, update status/notes
5. **QA Agents** - Validate work, pass/fail
6. **LangGraph Workflow** - Connect everything
7. **Streamlit UI** - Dashboard + chat

## Key Design Points

- **Notion as SSOT**: All work items, queues, status in Notion
- **Agent Autonomy**: Agents pull from queue, work independently
- **PM Coordination**: PM is the orchestrator, not supervisor
- **Proper SDLC**: Requirements → Design → Dev → QA → Done
- **MCP Integration**: File operations via existing filemanager.py
- **No overspecialization**: Agents cover domains, not microspecialized

## Token-Efficient Next Actions

1. Copy relevant code from `MCPManager/langgraph_agents/`
2. Refactor PM for queue-based workflow
3. Create Product Owner agent (partial started, interrupted)
4. Build queue monitoring system
5. Test end-to-end with simple task

## Git Repo

Initialized at: `/Users/nate/Development/1. Projects/Engineering Department/`
Ready for first commit.
