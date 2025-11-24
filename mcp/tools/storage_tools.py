"""
MCP Storage Tools for Agent Design Persistence
Provides autosave, versioning, and import/export capabilities for LangGraph agents.
"""

import hashlib
import json
import sqlite3
from datetime import datetime

import redis

# ============================================================================
# REDIS CONNECTION (Drafts)
# ============================================================================


def get_redis_client():
    """Get Redis client for draft storage"""
    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    # Parse redis://host:port format
    if redis_url.startswith("redis://"):
        parts = redis_url.replace("redis://", "").split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 6379
    else:
        host = "localhost"
        port = 6379

    return redis.Redis(host=host, port=port, db=0, decode_responses=True)


# ============================================================================
# SQLITE CONNECTION (Versions)
# ============================================================================


def get_sqlite_conn():
    """Get SQLite connection for version storage"""
    import os

    # Use a dedicated SQLite database for versioning
    # (separate from the main DATABASE_URL which might be PostgreSQL)
    db_path = os.getenv("VERSIONS_DB_PATH", "/app/data/agent_versions.db")

    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# ============================================================================
# SCHEMA INITIALIZATION
# ============================================================================


def init_agent_versions_table():
    """Initialize agent_versions table if not exists"""
    conn = get_sqlite_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            graph_data TEXT NOT NULL,
            commit_message TEXT,
            commit_hash TEXT NOT NULL,
            user_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
            UNIQUE(agent_id, version)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_versions_agent_id
        ON agent_versions(agent_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_versions_commit_hash
        ON agent_versions(commit_hash)
    """)
    conn.commit()
    conn.close()


# Initialize on import
init_agent_versions_table()


# ============================================================================
# MCP TOOL: Save Agent Draft (Autosave to Redis)
# ============================================================================


def save_agent_draft(agent_id: str, user_id: str, graph_data: dict) -> str:
    """
    Autosave agent design draft to Redis (ephemeral storage).
    Used for real-time autosave every 3 seconds.

    Args:
        agent_id: Unique identifier for the agent
        user_id: ID of the user editing the agent
        graph_data: ReactFlow graph structure (nodes, edges, metadata)

    Returns:
        Success message with timestamp
    """
    try:
        redis_client = get_redis_client()

        # Store draft data
        draft_key = f"agent_draft:{agent_id}"
        draft_payload = {
            "agent_id": agent_id,
            "user_id": user_id,
            "graph_data": graph_data,
            "last_saved": datetime.utcnow().isoformat(),
        }

        # Save to Redis with 24 hour TTL
        redis_client.setex(
            draft_key,
            86400,  # 24 hours
            json.dumps(draft_payload),
        )

        # Track user's active drafts
        user_drafts_key = f"user_drafts:{user_id}"
        redis_client.sadd(user_drafts_key, agent_id)
        redis_client.expire(user_drafts_key, 86400)

        return f"Draft saved for agent {agent_id} at {draft_payload['last_saved']}"

    except Exception as e:
        return f"Error saving draft: {e!s}"


# ============================================================================
# MCP TOOL: Commit Agent Version (Git-like versioning)
# ============================================================================


def commit_agent_version(agent_id: str, graph_data: dict, message: str, user_id: str | None = None) -> str:
    """
    Commit agent version to SQLite with message (git-like versioning).
    Creates a new immutable version snapshot.

    Args:
        agent_id: Unique identifier for the agent
        graph_data: ReactFlow graph structure to commit
        message: Commit message describing changes
        user_id: Optional user ID who created this commit

    Returns:
        Success message with version number and commit hash
    """
    try:
        conn = get_sqlite_conn()
        conn.row_factory = dict_factory

        # Get next version number
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 as next_version FROM agent_versions WHERE agent_id = ?", (agent_id,)
        )
        next_version = cursor.fetchone()["next_version"]

        # Generate commit hash (SHA-256 of graph_data + timestamp)
        graph_json = json.dumps(graph_data, sort_keys=True)
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{agent_id}:{next_version}:{graph_json}:{timestamp}"
        commit_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]

        # Insert new version
        cursor.execute(
            """
            INSERT INTO agent_versions (agent_id, version, graph_data, commit_message, commit_hash, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (agent_id, next_version, graph_json, message, commit_hash, user_id, timestamp),
        )

        conn.commit()
        conn.close()

        # Clear draft from Redis after successful commit
        try:
            redis_client = get_redis_client()
            redis_client.delete(f"agent_draft:{agent_id}")
        except:
            pass  # Don't fail commit if Redis cleanup fails

        return f"Committed version {next_version} for agent {agent_id} (hash: {commit_hash})"

    except Exception as e:
        return f"Error committing version: {e!s}"


# ============================================================================
# MCP TOOL: Get Agent History
# ============================================================================


def get_agent_history(agent_id: str, limit: int = 50) -> list:
    """
    Retrieve version history for an agent (git log style).

    Args:
        agent_id: Unique identifier for the agent
        limit: Maximum number of versions to return

    Returns:
        List of version objects with metadata (newest first)
    """
    try:
        conn = get_sqlite_conn()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                version,
                commit_message,
                commit_hash,
                user_id,
                created_at
            FROM agent_versions
            WHERE agent_id = ?
            ORDER BY version DESC
            LIMIT ?
        """,
            (agent_id, limit),
        )

        versions = cursor.fetchall()
        conn.close()

        return versions

    except Exception as e:
        return [{"error": str(e)}]


# ============================================================================
# MCP TOOL: Restore Agent Version (Checkout)
# ============================================================================


def restore_agent_version(agent_id: str, version: int) -> dict:
    """
    Rollback to specific version and return graph_data (git checkout).

    Args:
        agent_id: Unique identifier for the agent
        version: Version number to restore

    Returns:
        Graph data dictionary from the specified version
    """
    try:
        conn = get_sqlite_conn()
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT graph_data, commit_hash, created_at
            FROM agent_versions
            WHERE agent_id = ? AND version = ?
        """,
            (agent_id, version),
        )

        result = cursor.fetchone()
        conn.close()

        if not result:
            return {"error": f"Version {version} not found for agent {agent_id}"}

        # Parse JSON graph_data
        graph_data = json.loads(result["graph_data"])

        return {
            "graph_data": graph_data,
            "version": version,
            "commit_hash": result["commit_hash"],
            "restored_from": result["created_at"],
        }

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# MCP TOOL: Get Agent Draft (Load from Redis)
# ============================================================================


def get_agent_draft(agent_id: str) -> dict | None:
    """
    Retrieve the latest draft from Redis for an agent.

    Args:
        agent_id: Unique identifier for the agent

    Returns:
        Draft data or None if no draft exists
    """
    try:
        redis_client = get_redis_client()
        draft_key = f"agent_draft:{agent_id}"

        draft_json = redis_client.get(draft_key)
        if not draft_json:
            return None

        return json.loads(draft_json)

    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# MCP TOOL: Import Python Code (LangGraph → ReactFlow)
# ============================================================================


def import_python_code(python_code: str) -> dict:
    """
    Parse Python LangGraph code and convert to ReactFlow graph structure.

    Args:
        python_code: Python code string containing LangGraph definition

    Returns:
        ReactFlow graph structure with nodes and edges
    """
    try:
        from mcp.converters.python_to_reactflow import parse_langgraph_code

        graph_data = parse_langgraph_code(python_code)
        return graph_data

    except Exception as e:
        return {"error": str(e), "nodes": [], "edges": []}


# ============================================================================
# MCP TOOL: Export to Python (ReactFlow → LangGraph)
# ============================================================================


def export_to_python(graph_data: dict, agent_name: str = "agent") -> str:
    """
    Convert ReactFlow graph structure to Python LangGraph code.

    Args:
        graph_data: ReactFlow graph with nodes and edges
        agent_name: Name for the generated agent class

    Returns:
        Python code string for LangGraph agent
    """
    try:
        from mcp.converters.reactflow_to_python import generate_langgraph_code

        python_code = generate_langgraph_code(graph_data, agent_name)
        return python_code

    except Exception as e:
        return f"# Error generating Python code: {e!s}\n"


# ============================================================================
# MCP TOOL: List User Drafts
# ============================================================================


def list_user_drafts(user_id: str) -> list:
    """
    List all active drafts for a user.

    Args:
        user_id: User identifier

    Returns:
        List of agent IDs with active drafts
    """
    try:
        redis_client = get_redis_client()
        user_drafts_key = f"user_drafts:{user_id}"

        agent_ids = redis_client.smembers(user_drafts_key)

        drafts = []
        for agent_id in agent_ids:
            draft = get_agent_draft(agent_id)
            if draft:
                drafts.append(
                    {"agent_id": agent_id, "last_saved": draft.get("last_saved"), "user_id": draft.get("user_id")}
                )

        return drafts

    except Exception as e:
        return [{"error": str(e)}]


# ============================================================================
# EXPORT MCP TOOLS
# ============================================================================

__all__ = [
    "commit_agent_version",
    "export_to_python",
    "get_agent_draft",
    "get_agent_history",
    "import_python_code",
    "list_user_drafts",
    "restore_agent_version",
    "save_agent_draft",
]
