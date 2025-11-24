"""
Monitoring API - Agent Status and Health
Provides real-time status of deployed agents in a domain.
"""

from datetime import datetime
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/domains/{domain_id}/agents/status")
async def get_deployed_agents(domain_id: str) -> dict:
    """
    Return status of all agents deployed to this domain.

    Returns:
    - System agents (always deployed)
    - Domain agents (from agents/ directory)

    Args:
        domain_id: Domain identifier

    Returns:
        Dictionary with system_agents and domain_agents lists
    """

    # System agents (always deployed)
    system_agents = [
        {
            "id": "io_agent",
            "name": "IO Agent",
            "type": "system",
            "status": "healthy",
            "description": "Handles voice/text I/O via LiveKit",
        },
        {
            "id": "supervisor_agent",
            "name": "Supervisor Agent",
            "type": "system",
            "status": "healthy",
            "description": "Routes requests to appropriate agents",
        },
        {
            "id": "context_agent",
            "name": "Context Agent",
            "type": "system",
            "status": "healthy",
            "description": "Manages conversation context and state",
        },
        {
            "id": "coherence_agent",
            "name": "Coherence Agent",
            "type": "system",
            "status": "healthy",
            "description": "Ensures response consistency and quality",
        },
        {
            "id": "exception_agent",
            "name": "Exception Agent",
            "type": "system",
            "status": "healthy",
            "description": "Handles errors and exceptional conditions",
        },
        {
            "id": "observability_agent",
            "name": "Observability Agent",
            "type": "system",
            "status": "healthy",
            "description": "Monitors and logs agent activities",
        },
        {
            "id": "governance_agent",
            "name": "Governance Agent",
            "type": "system",
            "status": "healthy",
            "description": "Enforces policies and compliance",
        },
    ]

    # Domain agents - ONLY from database (Forge visual editor is the source of truth)
    # Deployed agents have .agent.yaml and .py files generated, but those are runtime artifacts
    # The database stores the canonical user agent definitions
    domain_agents = []

    # Get agents from the database (visual graph editor)
    try:
        from backend import db

        db_graphs = db.list_graphs(environment="dev", domain_id=domain_id)

        for graph in db_graphs:
            # Only include user and channel graphs (not system graphs)
            if graph.get("graph_type") in ["user", "channel"]:
                domain_agents.append(
                    {
                        "id": graph["id"],
                        "name": graph.get("display_name", graph["name"]),
                        "type": "domain",
                        "status": "active" if graph.get("status") in ["active", "production"] else "unknown",
                        "description": graph.get("description", ""),
                        "version": graph.get("version", "1.0.0"),
                        "capabilities": [],
                    }
                )
    except Exception as e:
        print(f"⚠️ Failed to load database graphs: {e}")

    return {
        "domain_id": domain_id,
        "timestamp": datetime.utcnow().isoformat(),
        "system_agents": system_agents,
        "domain_agents": domain_agents,
        "total_agents": len(system_agents) + len(domain_agents),
    }


@router.get("/agents/{agent_id}/health")
async def get_agent_health(agent_id: str) -> dict:
    """
    Get detailed health information for a specific agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Detailed health metrics
    """
    # TODO: Implement actual health checks
    # For now, return mock data

    return {
        "agent_id": agent_id,
        "status": "healthy",
        "uptime_seconds": 3600,
        "last_activity": datetime.utcnow().isoformat(),
        "metrics": {"requests_processed": 150, "average_response_time_ms": 250, "error_rate": 0.01},
    }


@router.get("/domains/{domain_id}/health")
async def get_domain_health(domain_id: str) -> dict:
    """
    Get overall health summary for a domain.

    Args:
        domain_id: Domain identifier

    Returns:
        Domain health summary
    """
    agents_status = await get_deployed_agents(domain_id)

    # Count healthy agents
    all_agents = agents_status["system_agents"] + agents_status["domain_agents"]
    healthy_count = sum(1 for agent in all_agents if agent["status"] == "healthy")
    total_count = len(all_agents)

    return {
        "domain_id": domain_id,
        "status": "healthy" if healthy_count == total_count else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {"total": total_count, "healthy": healthy_count, "degraded": total_count - healthy_count},
        "health_percentage": (healthy_count / total_count * 100) if total_count > 0 else 0,
    }


@router.websocket("/ws/agent-activity/{session_id}")
async def agent_activity_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming agent activity in real-time.
    Clients connect with their session_id to receive activity updates.

    Args:
        session_id: Unique session identifier for the conversation/test session
    """
    from backend.agents.system.observability_agent import observability_agent

    await websocket.accept()
    print(f"🔌 WebSocket connected for session: {session_id}")

    # Register this connection
    await observability_agent.register_connection(session_id, websocket)

    try:
        # Keep connection alive and listen for pings
        while True:
            data = await websocket.receive_text()
            # Echo ping/pong for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session: {session_id}")
    except Exception as e:
        print(f"❌ WebSocket error for session {session_id}: {e}")
    finally:
        # Unregister on disconnect
        await observability_agent.unregister_connection(session_id, websocket)


# ============================================================================
# Activity History & Analytics Endpoints (Phase 3)
# These endpoints call MCP observability tools for historical data
# ============================================================================


from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Natural language query request"""

    query: str
    session_id: str | None = None
    agent_id: str | None = None


@router.get("/sessions/recent")
async def get_recent_sessions_endpoint(limit: int = 20) -> dict:
    """
    Get list of recent sessions with summary information.

    Args:
        limit: Maximum number of sessions to return (default: 20)

    Returns:
        List of session summaries with activity counts and duration
    """
    try:
        from mcp.tools.observability_tools import get_recent_sessions

        sessions = get_recent_sessions(limit=limit)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(500, f"Failed to get recent sessions: {e!s}")


@router.get("/sessions/{session_id}/activities")
async def get_session_activities_endpoint(session_id: str, limit: int = 100, offset: int = 0) -> dict:
    """
    Get all activities for a specific session.

    Args:
        session_id: Session identifier
        limit: Maximum activities to return
        offset: Number of activities to skip

    Returns:
        Activities list with pagination info
    """
    try:
        from mcp.tools.observability_tools import get_session_activities

        return get_session_activities(session_id, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(500, f"Failed to get session activities: {e!s}")


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics_endpoint(session_id: str) -> dict:
    """
    Get aggregated metrics for a session.

    Args:
        session_id: Session identifier

    Returns:
        Session metrics including duration, counts, agents involved
    """
    try:
        from mcp.tools.observability_tools import get_session_metrics

        return get_session_metrics(session_id)
    except Exception as e:
        raise HTTPException(500, f"Failed to get session metrics: {e!s}")


@router.get("/activities/search")
async def search_activities_endpoint(
    q: str | None = None,
    event_type: str | None = None,
    agent_id: str | None = None,
    session_id: str | None = None,
    limit: int = 50,
) -> dict:
    """
    Search activities with flexible filters.

    Args:
        q: Text search in message field
        event_type: Filter by event type
        agent_id: Filter by agent
        session_id: Filter by session
        limit: Maximum results

    Returns:
        Matching activities with search metadata
    """
    try:
        from mcp.tools.observability_tools import search_activities

        event_types = [event_type] if event_type else None
        return search_activities(
            query=q, event_types=event_types, agent_id=agent_id, session_id=session_id, limit=limit
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to search activities: {e!s}")


@router.get("/errors")
async def get_error_summary_endpoint(agent_id: str | None = None, hours: int = 24) -> dict:
    """
    Get error statistics and recent errors.

    Args:
        agent_id: Optional filter by agent
        hours: Look back window in hours (default: 24)

    Returns:
        Error counts and recent error details
    """
    try:
        from mcp.tools.observability_tools import get_error_summary

        return get_error_summary(agent_id=agent_id, hours=hours)
    except Exception as e:
        raise HTTPException(500, f"Failed to get error summary: {e!s}")


@router.post("/query")
async def natural_language_query_endpoint(request: QueryRequest) -> dict:
    """
    Natural language query via Observability Agent.

    Args:
        request: Query request with natural language question

    Returns:
        Agent response with formatted answer and raw data
    """
    try:
        from agents.observability_agent_graph import invoke_observability_agent

        result = await invoke_observability_agent(
            query=request.query, session_id=request.session_id, agent_id=request.agent_id
        )
        return result
    except Exception as e:
        raise HTTPException(500, f"Failed to process query: {e!s}")


# ============================================================================
# Agent Metrics Endpoints (Phase 1 - Agent Dashboard)
# Aggregated metrics for deployed agents
# ============================================================================


@router.get("/agents/{agent_id}/metrics")
async def get_agent_metrics_endpoint(agent_id: str, hours: int = 24) -> dict:
    """
    Get aggregated metrics for a specific agent.

    Args:
        agent_id: Agent identifier
        hours: Look back window in hours (default: 24)

    Returns:
        Agent metrics including executions, success rate, latency percentiles
    """
    try:
        from mcp.tools.observability_tools import get_agent_metrics

        return get_agent_metrics(agent_id=agent_id, hours=hours)
    except Exception as e:
        raise HTTPException(500, f"Failed to get agent metrics: {e!s}")


@router.get("/agents/metrics")
async def get_all_agents_metrics_endpoint(hours: int = 24) -> dict:
    """
    Get aggregated metrics for all agents.

    Args:
        hours: Look back window in hours (default: 24)

    Returns:
        Per-agent metrics list with summary totals
    """
    try:
        from mcp.tools.observability_tools import get_all_agents_metrics

        return get_all_agents_metrics(hours=hours)
    except Exception as e:
        raise HTTPException(500, f"Failed to get all agents metrics: {e!s}")


# ============================================================================
# Cost & Token Tracking Endpoints (Phase 2)
# ============================================================================


@router.get("/tools/invocations")
async def get_tool_invocations_endpoint(
    agent_id: str | None = None, session_id: str | None = None, hours: int = 24, limit: int = 100
) -> dict:
    """
    Get tool invocations with optional filtering.

    Args:
        agent_id: Filter by agent
        session_id: Filter by session
        hours: Look back window in hours (default: 24)
        limit: Maximum results (default: 100)

    Returns:
        Tool invocations with aggregates by tool
    """
    try:
        from mcp.tools.observability_tools import get_tool_invocations

        return get_tool_invocations(agent_id=agent_id, session_id=session_id, hours=hours, limit=limit)
    except Exception as e:
        raise HTTPException(500, f"Failed to get tool invocations: {e!s}")


@router.get("/costs/summary")
async def get_cost_summary_endpoint(
    agent_id: str | None = None, session_id: str | None = None, hours: int = 24
) -> dict:
    """
    Get LLM cost summary.

    Args:
        agent_id: Optional filter by agent
        session_id: Optional filter by session
        hours: Look back window in hours (default: 24)

    Returns:
        Cost summary with breakdown by model
    """
    try:
        from mcp.tools.observability_tools import get_cost_summary

        return get_cost_summary(agent_id=agent_id, session_id=session_id, hours=hours)
    except Exception as e:
        raise HTTPException(500, f"Failed to get cost summary: {e!s}")


@router.get("/costs/by-agent")
async def get_cost_by_agent_endpoint(hours: int = 24) -> dict:
    """
    Get cost breakdown by agent.

    Args:
        hours: Look back window in hours (default: 24)

    Returns:
        Per-agent cost summary sorted by cost descending
    """
    try:
        from mcp.tools.observability_tools import get_cost_by_agent

        return get_cost_by_agent(hours=hours)
    except Exception as e:
        raise HTTPException(500, f"Failed to get cost by agent: {e!s}")
