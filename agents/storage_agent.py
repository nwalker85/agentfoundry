"""
Storage Agent - LangGraph Agent for Agent Design Persistence
Handles all storage operations for agent designs: autosave, versioning, import/export.
"""

import sys
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.tools.storage_tools import (
    commit_agent_version,
    export_to_python,
    get_agent_draft,
    get_agent_history,
    import_python_code,
    list_user_drafts,
    restore_agent_version,
    save_agent_draft,
)

# ============================================================================
# STATE DEFINITION
# ============================================================================


class StorageAgentState(TypedDict, total=False):
    """State for storage agent operations"""

    # Input
    action: Literal[
        "save_draft",
        "commit_version",
        "get_history",
        "restore_version",
        "get_draft",
        "import_python",
        "export_python",
        "list_drafts",
    ]
    agent_id: str
    user_id: str | None
    graph_data: dict | None
    commit_message: str | None
    version: int | None
    python_code: str | None
    agent_name: str | None

    # Output
    result: Any
    error: str | None
    success: bool


# ============================================================================
# NODE FUNCTIONS
# ============================================================================


def route_action(state: StorageAgentState) -> str:
    """
    Route to the appropriate storage operation based on action.
    """
    action = state.get("action")

    if action == "save_draft":
        return "save_draft"
    elif action == "commit_version":
        return "commit_version"
    elif action == "get_history":
        return "get_history"
    elif action == "restore_version":
        return "restore_version"
    elif action == "get_draft":
        return "get_draft"
    elif action == "import_python":
        return "import_python"
    elif action == "export_python":
        return "export_python"
    elif action == "list_drafts":
        return "list_drafts"
    else:
        return "error"


def handle_save_draft(state: StorageAgentState) -> StorageAgentState:
    """
    Save agent draft to Redis (autosave).
    """
    agent_id = state.get("agent_id")
    user_id = state.get("user_id")
    graph_data = state.get("graph_data")

    if not agent_id or not user_id or not graph_data:
        state["error"] = "Missing required fields: agent_id, user_id, graph_data"
        state["success"] = False
        return state

    try:
        result = save_agent_draft(agent_id, user_id, graph_data)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_commit_version(state: StorageAgentState) -> StorageAgentState:
    """
    Commit agent version to SQLite with message.
    """
    agent_id = state.get("agent_id")
    graph_data = state.get("graph_data")
    commit_message = state.get("commit_message", "Committed version")
    user_id = state.get("user_id")

    if not agent_id or not graph_data:
        state["error"] = "Missing required fields: agent_id, graph_data"
        state["success"] = False
        return state

    try:
        result = commit_agent_version(agent_id, graph_data, commit_message, user_id)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_get_history(state: StorageAgentState) -> StorageAgentState:
    """
    Get version history for an agent.
    """
    agent_id = state.get("agent_id")

    if not agent_id:
        state["error"] = "Missing required field: agent_id"
        state["success"] = False
        return state

    try:
        result = get_agent_history(agent_id)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_restore_version(state: StorageAgentState) -> StorageAgentState:
    """
    Restore agent to a specific version.
    """
    agent_id = state.get("agent_id")
    version = state.get("version")

    if not agent_id or version is None:
        state["error"] = "Missing required fields: agent_id, version"
        state["success"] = False
        return state

    try:
        result = restore_agent_version(agent_id, version)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_get_draft(state: StorageAgentState) -> StorageAgentState:
    """
    Get the latest draft for an agent from Redis.
    """
    agent_id = state.get("agent_id")

    if not agent_id:
        state["error"] = "Missing required field: agent_id"
        state["success"] = False
        return state

    try:
        result = get_agent_draft(agent_id)
        if result is None:
            state["result"] = {"message": "No draft found"}
        else:
            state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_import_python(state: StorageAgentState) -> StorageAgentState:
    """
    Import Python LangGraph code and convert to ReactFlow graph.
    """
    python_code = state.get("python_code")

    if not python_code:
        state["error"] = "Missing required field: python_code"
        state["success"] = False
        return state

    try:
        result = import_python_code(python_code)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_export_python(state: StorageAgentState) -> StorageAgentState:
    """
    Export ReactFlow graph to Python LangGraph code.
    """
    graph_data = state.get("graph_data")
    agent_name = state.get("agent_name", "agent")

    if not graph_data:
        state["error"] = "Missing required field: graph_data"
        state["success"] = False
        return state

    try:
        result = export_to_python(graph_data, agent_name)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_list_drafts(state: StorageAgentState) -> StorageAgentState:
    """
    List all drafts for a user.
    """
    user_id = state.get("user_id")

    if not user_id:
        state["error"] = "Missing required field: user_id"
        state["success"] = False
        return state

    try:
        result = list_user_drafts(user_id)
        state["result"] = result
        state["success"] = True
        state["error"] = None
    except Exception as e:
        state["error"] = str(e)
        state["success"] = False

    return state


def handle_error(state: StorageAgentState) -> StorageAgentState:
    """
    Handle unknown action.
    """
    state["error"] = f"Unknown action: {state.get('action')}"
    state["success"] = False
    return state


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================


def create_storage_agent():
    """
    Create the storage agent graph.
    """
    # Build the graph
    builder = StateGraph(StorageAgentState)

    # Add nodes for each operation
    builder.add_node("save_draft", handle_save_draft)
    builder.add_node("commit_version", handle_commit_version)
    builder.add_node("get_history", handle_get_history)
    builder.add_node("restore_version", handle_restore_version)
    builder.add_node("get_draft", handle_get_draft)
    builder.add_node("import_python", handle_import_python)
    builder.add_node("export_python", handle_export_python)
    builder.add_node("list_drafts", handle_list_drafts)
    builder.add_node("error", handle_error)

    # Add conditional routing from START
    builder.add_conditional_edges(
        START,
        route_action,
        {
            "save_draft": "save_draft",
            "commit_version": "commit_version",
            "get_history": "get_history",
            "restore_version": "restore_version",
            "get_draft": "get_draft",
            "import_python": "import_python",
            "export_python": "export_python",
            "list_drafts": "list_drafts",
            "error": "error",
        },
    )

    # All nodes go to END
    builder.add_edge("save_draft", END)
    builder.add_edge("commit_version", END)
    builder.add_edge("get_history", END)
    builder.add_edge("restore_version", END)
    builder.add_edge("get_draft", END)
    builder.add_edge("import_python", END)
    builder.add_edge("export_python", END)
    builder.add_edge("list_drafts", END)
    builder.add_edge("error", END)

    # Compile the graph
    return builder.compile()


# ============================================================================
# AGENT INSTANCE
# ============================================================================

# Create the compiled graph
storage_agent = create_storage_agent()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def invoke_storage_agent(action: str, **kwargs) -> dict:
    """
    Helper function to invoke the storage agent.

    Args:
        action: Storage operation to perform
        **kwargs: Additional parameters for the operation

    Returns:
        Result dictionary with success status and data
    """
    initial_state = {"action": action, **kwargs}

    result = await storage_agent.ainvoke(initial_state)

    return {"success": result.get("success", False), "result": result.get("result"), "error": result.get("error")}


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    import asyncio

    async def test_storage_agent():
        """Test the storage agent with various operations"""

        # Test save draft
        print("Testing save draft...")
        result = await invoke_storage_agent(
            "save_draft",
            agent_id="test-agent-1",
            user_id="user-123",
            graph_data={
                "nodes": [
                    {"id": "1", "type": "entry", "data": {"label": "start"}},
                    {"id": "2", "type": "process", "data": {"label": "process"}},
                    {"id": "3", "type": "end", "data": {"label": "end"}},
                ],
                "edges": [
                    {"id": "e1", "source": "1", "target": "2"},
                    {"id": "e2", "source": "2", "target": "3"},
                ],
            },
        )
        print(f"Save draft result: {result}\n")

        # Test commit version
        print("Testing commit version...")
        result = await invoke_storage_agent(
            "commit_version",
            agent_id="test-agent-1",
            user_id="user-123",
            graph_data={"nodes": [{"id": "1", "type": "entry", "data": {"label": "start"}}], "edges": []},
            commit_message="Initial commit",
        )
        print(f"Commit result: {result}\n")

        # Test get history
        print("Testing get history...")
        result = await invoke_storage_agent("get_history", agent_id="test-agent-1")
        print(f"History result: {result}\n")

        # Test export to Python
        print("Testing export to Python...")
        result = await invoke_storage_agent(
            "export_python",
            graph_data={
                "nodes": [
                    {"id": "1", "type": "entry", "data": {"label": "start", "function": "start_node"}},
                    {"id": "2", "type": "process", "data": {"label": "process", "function": "process_node"}},
                    {"id": "3", "type": "end", "data": {"label": "end", "function": "end_node"}},
                ],
                "edges": [
                    {"id": "e1", "source": "1", "target": "2", "type": "default"},
                    {"id": "e2", "source": "2", "target": "3", "type": "default"},
                ],
            },
            agent_name="test_agent",
        )
        print(f"Export result:\n{result.get('result')}\n")

    # Run tests
    asyncio.run(test_storage_agent())
