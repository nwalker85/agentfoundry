"""
LangGraph Observability Agent
Handles activity queries, session history, and analytics via natural language or structured requests.

This agent uses MCP tools to query the activity database and can respond to:
- "What happened in session X?"
- "Show me recent errors"
- "How long did session Y take?"
- Structured API calls for programmatic access
"""

import json
import logging
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from mcp.tools.observability_tools import (
    get_agent_activities,
    get_error_summary,
    get_recent_sessions,
    get_session_activities,
    get_session_metrics,
    search_activities,
)

logger = logging.getLogger(__name__)


# ============================================================================
# STATE DEFINITION
# ============================================================================


class ObservabilityState(TypedDict, total=False):
    """State for the observability agent"""

    # Input
    query: str  # Natural language query
    action: str | None  # Explicit action (bypasses intent classification)
    session_id: str | None  # Session to query
    agent_id: str | None  # Agent to query
    hours: int | None  # Time window for queries
    limit: int | None  # Result limit

    # Processing
    intent: str  # Classified intent
    tool_results: Any  # Raw tool outputs

    # Output
    response: str  # Final formatted response
    data: Any  # Structured data for API consumers
    error: str | None  # Error message if failed


# Intent types
INTENTS = Literal[
    "session_history",  # Get activities for a session
    "agent_history",  # Get activities for an agent
    "session_metrics",  # Get metrics for a session
    "recent_sessions",  # List recent sessions
    "search",  # Search activities
    "errors",  # Get error summary
    "unknown",  # Could not classify
]


# ============================================================================
# LLM SETUP
# ============================================================================


def get_llm():
    """Get LLM for intent classification and response formatting"""
    import os

    return ChatOpenAI(model=os.getenv("OBSERVABILITY_LLM_MODEL", "gpt-4o-mini"), temperature=0.1)


# ============================================================================
# NODE HANDLERS
# ============================================================================


def classify_intent(state: ObservabilityState) -> ObservabilityState:
    """
    Classify user intent using LLM or explicit action.
    """
    # If action is explicitly provided, use it directly
    if state.get("action"):
        state["intent"] = state["action"]
        logger.info(f"Using explicit action: {state['action']}")
        return state

    # If no query, default to recent sessions
    if not state.get("query"):
        state["intent"] = "recent_sessions"
        return state

    query = state["query"].lower()

    # Simple keyword-based classification (can be enhanced with LLM)
    if any(word in query for word in ["session", "what happened", "history"]):
        if state.get("session_id"):
            state["intent"] = "session_history"
        else:
            state["intent"] = "recent_sessions"
    elif any(word in query for word in ["error", "fail", "problem", "issue"]):
        state["intent"] = "errors"
    elif any(word in query for word in ["metric", "duration", "how long", "stats"]):
        state["intent"] = "session_metrics"
    elif any(word in query for word in ["search", "find", "look for"]):
        state["intent"] = "search"
    elif any(word in query for word in ["agent", "which agent"]):
        state["intent"] = "agent_history"
    elif any(word in query for word in ["recent", "latest", "last"]):
        state["intent"] = "recent_sessions"
    else:
        # Use LLM for complex classification
        try:
            llm = get_llm()
            response = llm.invoke(
                [
                    SystemMessage(
                        content="""You are an intent classifier for an observability system.
                Classify the user's query into one of these intents:
                - session_history: User wants to see activities for a specific session
                - agent_history: User wants to see activities for a specific agent
                - session_metrics: User wants metrics/stats about a session
                - recent_sessions: User wants to see recent sessions
                - search: User wants to search for specific activities
                - errors: User wants to see error information
                - unknown: Cannot determine intent

                Respond with ONLY the intent name, nothing else."""
                    ),
                    HumanMessage(content=query),
                ]
            )
            intent = response.content.strip().lower()
            if intent in ["session_history", "agent_history", "session_metrics", "recent_sessions", "search", "errors"]:
                state["intent"] = intent
            else:
                state["intent"] = "unknown"
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            state["intent"] = "unknown"

    logger.info(f"Classified intent: {state['intent']} for query: {state.get('query', 'N/A')[:50]}")
    return state


def route_by_intent(state: ObservabilityState) -> str:
    """Route to appropriate handler based on intent"""
    intent = state.get("intent", "unknown")
    if intent in ["session_history", "agent_history", "session_metrics", "recent_sessions", "search", "errors"]:
        return intent
    return "unknown"


def handle_session_history(state: ObservabilityState) -> ObservabilityState:
    """Fetch and format session activities"""
    try:
        session_id = state.get("session_id")
        if not session_id:
            state["error"] = "Session ID is required for session history"
            state["response"] = "I need a session ID to look up the history. Please provide one."
            return state

        limit = state.get("limit", 100)
        result = get_session_activities(session_id, limit=limit)
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching session history: {e}")
    return state


def handle_agent_history(state: ObservabilityState) -> ObservabilityState:
    """Fetch activities for a specific agent"""
    try:
        agent_id = state.get("agent_id")
        if not agent_id:
            state["error"] = "Agent ID is required for agent history"
            state["response"] = "I need an agent ID to look up the history. Please provide one."
            return state

        hours = state.get("hours", 24)
        limit = state.get("limit", 100)
        result = get_agent_activities(agent_id, hours=hours, limit=limit)
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching agent history: {e}")
    return state


def handle_session_metrics(state: ObservabilityState) -> ObservabilityState:
    """Get session metrics"""
    try:
        session_id = state.get("session_id")
        if not session_id:
            state["error"] = "Session ID is required for metrics"
            state["response"] = "I need a session ID to get metrics. Please provide one."
            return state

        result = get_session_metrics(session_id)
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching session metrics: {e}")
    return state


def handle_recent_sessions(state: ObservabilityState) -> ObservabilityState:
    """Get list of recent sessions"""
    try:
        limit = state.get("limit", 20)
        result = get_recent_sessions(limit=limit)
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching recent sessions: {e}")
    return state


def handle_search(state: ObservabilityState) -> ObservabilityState:
    """Search activities"""
    try:
        query = state.get("query", "")
        limit = state.get("limit", 50)
        result = search_activities(
            query=query, agent_id=state.get("agent_id"), session_id=state.get("session_id"), limit=limit
        )
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error searching activities: {e}")
    return state


def handle_errors(state: ObservabilityState) -> ObservabilityState:
    """Get error summary"""
    try:
        hours = state.get("hours", 24)
        result = get_error_summary(agent_id=state.get("agent_id"), hours=hours)
        state["tool_results"] = result
        state["data"] = result
    except Exception as e:
        state["error"] = str(e)
        logger.error(f"Error fetching error summary: {e}")
    return state


def handle_unknown(state: ObservabilityState) -> ObservabilityState:
    """Handle unknown intents"""
    state["response"] = """I can help you with:
- Session history: "What happened in session <id>?"
- Recent sessions: "Show me recent sessions"
- Error summary: "Show me recent errors"
- Session metrics: "How long did session <id> take?"
- Search: "Search for activities with <keyword>"

What would you like to know?"""
    state["data"] = {"help": True}
    return state


def format_response(state: ObservabilityState) -> ObservabilityState:
    """Format tool results into human-readable response"""

    # If already has a response (error or help), keep it
    if state.get("response"):
        return state

    if state.get("error"):
        state["response"] = f"Sorry, I encountered an error: {state['error']}"
        return state

    results = state.get("tool_results")
    intent = state.get("intent")

    if not results:
        state["response"] = "No results found."
        return state

    # Format based on intent
    if intent == "session_history":
        activities = results.get("activities", [])
        total = results.get("total", 0)
        if activities:
            state["response"] = f"Found {total} activities in this session:\n\n"
            for act in activities[:10]:  # Show first 10
                ts = act.get("timestamp", 0)
                from datetime import datetime

                time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                state["response"] += f"[{time_str}] {act['agent_name']}: {act['message'][:100]}\n"
            if total > 10:
                state["response"] += f"\n... and {total - 10} more activities"
        else:
            state["response"] = "No activities found for this session."

    elif intent == "recent_sessions":
        if isinstance(results, list):
            state["response"] = f"Found {len(results)} recent sessions:\n\n"
            for session in results[:10]:
                state["response"] += (
                    f"- {session['session_id'][:20]}... ({session['activity_count']} activities, {session['duration_seconds']:.1f}s)\n"
                )
        else:
            state["response"] = "No recent sessions found."

    elif intent == "session_metrics":
        state["response"] = f"""Session Metrics:
- Duration: {results.get("duration_seconds", 0):.1f} seconds
- Total activities: {results.get("activity_count", 0)}
- Tool calls: {results.get("tool_calls", 0)}
- Errors: {results.get("errors", 0)}
- Agents involved: {", ".join(results.get("agents_involved", []))}
- Messages: {results.get("message_count", {}).get("user", 0)} user, {results.get("message_count", {}).get("agent", 0)} agent"""

    elif intent == "errors":
        total = results.get("total_errors", 0)
        state["response"] = f"Error Summary (last {results.get('hours', 24)} hours):\n"
        state["response"] += f"Total errors: {total}\n\n"
        if results.get("errors_by_agent"):
            state["response"] += "By agent:\n"
            for agent, count in results["errors_by_agent"].items():
                state["response"] += f"  - {agent}: {count}\n"

    elif intent == "search":
        activities = results.get("activities", [])
        state["response"] = f"Found {len(activities)} matching activities:\n\n"
        for act in activities[:10]:
            state["response"] += f"- [{act['event_type']}] {act['agent_name']}: {act['message'][:80]}\n"

    elif intent == "agent_history":
        activities = results.get("activities", [])
        state["response"] = f"Found {len(activities)} activities for agent {state.get('agent_id')}:\n\n"
        for act in activities[:10]:
            state["response"] += f"- [{act['event_type']}] {act['message'][:80]}\n"

    else:
        state["response"] = json.dumps(results, indent=2, default=str)

    return state


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================


def create_observability_agent():
    """Create and compile the observability agent graph"""
    builder = StateGraph(ObservabilityState)

    # Add nodes
    builder.add_node("classify", classify_intent)
    builder.add_node("session_history", handle_session_history)
    builder.add_node("agent_history", handle_agent_history)
    builder.add_node("session_metrics", handle_session_metrics)
    builder.add_node("recent_sessions", handle_recent_sessions)
    builder.add_node("search", handle_search)
    builder.add_node("errors", handle_errors)
    builder.add_node("unknown", handle_unknown)
    builder.add_node("format", format_response)

    # Add edges
    builder.add_edge(START, "classify")

    # Conditional routing from classify
    builder.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "session_history": "session_history",
            "agent_history": "agent_history",
            "session_metrics": "session_metrics",
            "recent_sessions": "recent_sessions",
            "search": "search",
            "errors": "errors",
            "unknown": "unknown",
        },
    )

    # All handlers -> format -> END
    for node in [
        "session_history",
        "agent_history",
        "session_metrics",
        "recent_sessions",
        "search",
        "errors",
        "unknown",
    ]:
        builder.add_edge(node, "format")

    builder.add_edge("format", END)

    return builder.compile()


# Singleton instance
observability_agent = create_observability_agent()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def invoke_observability_agent(
    query: str | None = None,
    action: str | None = None,
    session_id: str | None = None,
    agent_id: str | None = None,
    hours: int | None = None,
    limit: int | None = None,
) -> dict:
    """
    Convenience function to invoke the observability agent.

    Args:
        query: Natural language query
        action: Explicit action (bypasses intent classification)
        session_id: Session to query
        agent_id: Agent to query
        hours: Time window for queries
        limit: Result limit

    Returns:
        Dict with response, data, and any errors
    """
    input_state = {}

    if query:
        input_state["query"] = query
    if action:
        input_state["action"] = action
    if session_id:
        input_state["session_id"] = session_id
    if agent_id:
        input_state["agent_id"] = agent_id
    if hours:
        input_state["hours"] = hours
    if limit:
        input_state["limit"] = limit

    result = await observability_agent.ainvoke(input_state)

    return {"response": result.get("response", ""), "data": result.get("data"), "error": result.get("error")}
