# Agent Foundry Documentation

**Version:** 0.9.0
**Last Updated:** November 2024

## Documentation Index

This directory contains all technical documentation for Agent Foundry. Documentation is organized into the following structure:

### Getting Started

| Document | Description |
|----------|-------------|
| [START_HERE.md](../START_HERE.md) | New engineer onboarding (30 min) |
| [DOCKER_DEV_WORKFLOW.md](DOCKER_DEV_WORKFLOW.md) | Local development with Docker |
| [DEPLOYMENT.md](DEPLOYMENT.md) | AWS ECS deployment guide |
| [DEVELOPER_QUICK_START.md](DEVELOPER_QUICK_START.md) | Quick reference for developers |

### Architecture

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture overview |
| [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) | Agent design patterns |
| [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) | Multi-agent orchestration |
| [FOUNDARY_INSTANCE_ARCHITECTURE.md](FOUNDARY_INSTANCE_ARCHITECTURE.md) | DIS and instance design |
| [architecture/SERVICE_DISCOVERY.md](architecture/SERVICE_DISCOVERY.md) | Infrastructure-as-Registry pattern |
| [architecture/PLATFORM_ROADMAP_WISHLIST.md](architecture/PLATFORM_ROADMAP_WISHLIST.md) | Strategic gaps & wishlist items |

### Feature Documentation

#### Forge (Visual Agent Builder)
Located in `docs/forge/`:
- [FORGE_AI_USER_GUIDE.md](forge/FORGE_AI_USER_GUIDE.md) - User guide
- [FORGE_LANGGRAPH_GAP_ANALYSIS.md](forge/FORGE_LANGGRAPH_GAP_ANALYSIS.md) - LangGraph feature coverage
- [FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md](forge/FORGE_VS_SYSTEM_AGENTS_ARCHITECTURE.md) - Architecture comparison

#### LiveKit (Voice Integration)
Located in `docs/livekit/`:
- [LIVEKIT_SETUP.md](livekit/LIVEKIT_SETUP.md) - Setup and configuration
- [LIVEKIT_QUICK_REFERENCE.md](livekit/LIVEKIT_QUICK_REFERENCE.md) - Quick reference
- [LIVEKIT_TESTING_GUIDE.md](livekit/LIVEKIT_TESTING_GUIDE.md) - Testing voice features

#### MCP (Model Context Protocol)
Located in `docs/mcp/`:
- [MCP_SERVER_SETUP_GUIDE.md](mcp/MCP_SERVER_SETUP_GUIDE.md) - Server setup
- [MCP_N8N_ARCHITECTURE.md](mcp/MCP_N8N_ARCHITECTURE.md) - N8N integration
- [MCP_SDK_MIGRATION_PLAN.md](mcp/MCP_SDK_MIGRATION_PLAN.md) - SDK migration

#### OpenFGA (Authorization)
Located in `docs/openfga/`:
- [OPENFGA_QUICKSTART.md](openfga/OPENFGA_QUICKSTART.md) - Quick start guide
- [OPENFGA_ARCHITECTURE.md](openfga/OPENFGA_ARCHITECTURE.md) - Architecture overview
- [OPENFGA_LOCALSTACK_SETUP.md](openfga/OPENFGA_LOCALSTACK_SETUP.md) - LocalStack integration

#### RBAC (Role-Based Access Control)
Located in `docs/rbac/`:
- [RBAC_QUICKSTART.md](rbac/RBAC_QUICKSTART.md) - Quick start guide
- [RBAC_IMPLEMENTATION.md](rbac/RBAC_IMPLEMENTATION.md) - Implementation details
- [RBAC_QUICK_REFERENCE.md](rbac/RBAC_QUICK_REFERENCE.md) - Quick reference

#### System Agents
Located in `docs/system-agents/`:
- [SYSTEM_AGENTS_DESIGN.md](system-agents/SYSTEM_AGENTS_DESIGN.md) - Design document
- [SYSTEM_AGENTS_IMPLEMENTATION.md](system-agents/SYSTEM_AGENTS_IMPLEMENTATION.md) - Implementation guide
- [SYSTEM_AGENTS_INTEGRATION_GUIDE.md](system-agents/SYSTEM_AGENTS_INTEGRATION_GUIDE.md) - Integration guide

#### WebSocket
Located in `docs/websocket/`:
- [WEBSOCKET_IMPLEMENTATION_PLAN.md](websocket/WEBSOCKET_IMPLEMENTATION_PLAN.md) - Implementation plan
- [WEBSOCKET_IMPLEMENTATION_SUMMARY.md](websocket/WEBSOCKET_IMPLEMENTATION_SUMMARY.md) - Summary

### Operations

| Document | Description |
|----------|-------------|
| [AWS_DEPLOYMENT_ECS.md](AWS_DEPLOYMENT_ECS.md) | AWS ECS deployment |
| [DATABASE_IMPORT_EXPORT_GUIDE.md](DATABASE_IMPORT_EXPORT_GUIDE.md) | Database management |
| [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) | Secrets and configuration |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing strategies |

### Reference

| Document | Description |
|----------|-------------|
| [CODE_INVENTORY.md](CODE_INVENTORY.md) | Codebase overview |
| [DEPENDENCY_DIAGRAM.md](DEPENDENCY_DIAGRAM.md) | Dependency visualization |
| [LANGGRAPH_AGENTS_OVERVIEW.md](LANGGRAPH_AGENTS_OVERVIEW.md) | LangGraph patterns |

### Archive

Historical documentation, implementation summaries, and session notes are in `docs/archive/`:
- `archive/sessions/` - Session handoff documents
- `archive/implementations/` - Implementation completion docs
- `archive/fixes/` - Bug fix documentation
- `archive/phases/` - Phase completion docs
- `archive/cibc/` - CIBC agent implementation docs
- `archive/migrations/` - Migration documentation

---

## Documentation Guidelines

When adding new documentation:

1. **Feature docs** go in the appropriate subdirectory (forge/, livekit/, etc.)
2. **Architecture docs** stay in the main docs/ directory
3. **Implementation summaries** go in archive/implementations/
4. **Session handoffs** go in archive/sessions/

## Quick Links

- **Main README:** [../README.md](../README.md)
- **Changelog:** [../CHANGELOG.md](../CHANGELOG.md)
- **Roadmap:** [../ROADMAP.md](../ROADMAP.md)
- **Scripts Reference:** [../scripts/README.md](../scripts/README.md)
