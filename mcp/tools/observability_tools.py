"""
MCP Observability Tools for Activity Persistence and Analytics
Provides activity logging, session history, search, and metrics for agent execution monitoring.
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# SQLITE CONNECTION
# ============================================================================


def get_db_connection():
    """Get SQLite connection for activity storage"""
    import os

    db_path = os.getenv("DATABASE_PATH", "/app/data/foundry.db")

    conn = sqlite3.connect(db_path, timeout=30.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# ============================================================================
# ACTIVITY PERSISTENCE
# ============================================================================


def save_activity(
    session_id: str,
    agent_id: str,
    agent_name: str,
    event_type: str,
    timestamp: float,
    message: str,
    metadata: dict | None = None,
) -> str:
    """
    Persist an activity event to the database.

    Args:
        session_id: Session identifier
        agent_id: Agent identifier
        agent_name: Display name of the agent
        event_type: One of: started, processing, tool_call, completed, error,
                    interrupted, resumed, user_message, agent_message
        timestamp: Unix timestamp (float for millisecond precision)
        message: Activity message/description
        metadata: Optional JSON-serializable metadata dict

    Returns:
        activity_id: UUID of the created activity record
    """
    activity_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO agent_activities
            (id, session_id, agent_id, agent_name, event_type, timestamp, message, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                activity_id,
                session_id,
                agent_id,
                agent_name,
                event_type,
                timestamp,
                message,
                json.dumps(metadata or {}),
                created_at,
            ),
        )

        conn.commit()
        conn.close()

        logger.debug(f"Saved activity {activity_id} for session {session_id}")
        return activity_id

    except Exception as e:
        logger.error(f"Failed to save activity: {e}")
        raise


# ============================================================================
# SESSION QUERIES
# ============================================================================


def get_session_activities(session_id: str, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    """
    Get all activities for a specific session.

    Args:
        session_id: Session identifier
        limit: Maximum number of activities to return
        offset: Number of activities to skip

    Returns:
        Dict with activities list, total count, and pagination info
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get total count
        cur.execute("SELECT COUNT(*) as count FROM agent_activities WHERE session_id = ?", (session_id,))
        total = cur.fetchone()["count"]

        # Get activities
        cur.execute(
            """
            SELECT id, session_id, agent_id, agent_name, event_type,
                   timestamp, message, metadata, created_at
            FROM agent_activities
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ? OFFSET ?
        """,
            (session_id, limit, offset),
        )

        activities = cur.fetchall()
        conn.close()

        # Parse metadata JSON
        for activity in activities:
            if activity.get("metadata"):
                try:
                    activity["metadata"] = json.loads(activity["metadata"])
                except:
                    pass

        return {
            "activities": activities,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(activities) < total,
        }

    except Exception as e:
        logger.error(f"Failed to get session activities: {e}")
        raise


def get_agent_activities(agent_id: str, hours: int = 24, limit: int = 100) -> dict[str, Any]:
    """
    Get recent activities for a specific agent.

    Args:
        agent_id: Agent identifier
        hours: Look back window in hours
        limit: Maximum number of activities to return

    Returns:
        Dict with activities list and metadata
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Calculate cutoff timestamp
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        cur.execute(
            """
            SELECT id, session_id, agent_id, agent_name, event_type,
                   timestamp, message, metadata, created_at
            FROM agent_activities
            WHERE agent_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (agent_id, cutoff, limit),
        )

        activities = cur.fetchall()
        conn.close()

        # Parse metadata JSON
        for activity in activities:
            if activity.get("metadata"):
                try:
                    activity["metadata"] = json.loads(activity["metadata"])
                except:
                    pass

        return {"agent_id": agent_id, "hours": hours, "activities": activities, "count": len(activities)}

    except Exception as e:
        logger.error(f"Failed to get agent activities: {e}")
        raise


# ============================================================================
# SEARCH
# ============================================================================


def search_activities(
    query: str | None = None,
    event_types: list[str] | None = None,
    agent_id: str | None = None,
    session_id: str | None = None,
    start_time: float | None = None,
    end_time: float | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Search activities with flexible filters.

    Args:
        query: Text search in message field
        event_types: Filter by event types
        agent_id: Filter by agent
        session_id: Filter by session
        start_time: Filter by minimum timestamp
        end_time: Filter by maximum timestamp
        limit: Maximum results

    Returns:
        Dict with matching activities and search metadata
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Build dynamic query
        conditions = []
        params = []

        if query:
            conditions.append("message LIKE ?")
            params.append(f"%{query}%")

        if event_types:
            placeholders = ",".join(["?" for _ in event_types])
            conditions.append(f"event_type IN ({placeholders})")
            params.extend(event_types)

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        if start_time:
            conditions.append("timestamp >= ?")
            params.append(start_time)

        if end_time:
            conditions.append("timestamp <= ?")
            params.append(end_time)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cur.execute(
            f"""
            SELECT id, session_id, agent_id, agent_name, event_type,
                   timestamp, message, metadata, created_at
            FROM agent_activities
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (*params, limit),
        )

        activities = cur.fetchall()
        conn.close()

        # Parse metadata JSON
        for activity in activities:
            if activity.get("metadata"):
                try:
                    activity["metadata"] = json.loads(activity["metadata"])
                except:
                    pass

        return {
            "query": query,
            "filters": {
                "event_types": event_types,
                "agent_id": agent_id,
                "session_id": session_id,
                "start_time": start_time,
                "end_time": end_time,
            },
            "activities": activities,
            "count": len(activities),
        }

    except Exception as e:
        logger.error(f"Failed to search activities: {e}")
        raise


# ============================================================================
# METRICS & ANALYTICS
# ============================================================================


def get_session_metrics(session_id: str) -> dict[str, Any]:
    """
    Get aggregated metrics for a session.

    Args:
        session_id: Session identifier

    Returns:
        Dict with session metrics including duration, counts, agents involved
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all activities for session
        cur.execute(
            """
            SELECT event_type, agent_id, agent_name, timestamp, message
            FROM agent_activities
            WHERE session_id = ?
            ORDER BY timestamp ASC
        """,
            (session_id,),
        )

        activities = cur.fetchall()
        conn.close()

        if not activities:
            return {"session_id": session_id, "error": "Session not found"}

        # Calculate metrics
        first_ts = activities[0]["timestamp"]
        last_ts = activities[-1]["timestamp"]
        duration_seconds = last_ts - first_ts

        # Count by event type
        event_counts = {}
        agents_involved = set()
        user_messages = 0
        agent_messages = 0
        errors = 0
        tool_calls = 0

        for activity in activities:
            event_type = activity["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            if activity["agent_id"] != "user":
                agents_involved.add(activity["agent_name"])

            if event_type == "user_message":
                user_messages += 1
            elif event_type == "agent_message":
                agent_messages += 1
            elif event_type == "error":
                errors += 1
            elif event_type == "tool_call":
                tool_calls += 1

        return {
            "session_id": session_id,
            "duration_seconds": round(duration_seconds, 2),
            "activity_count": len(activities),
            "event_counts": event_counts,
            "tool_calls": tool_calls,
            "errors": errors,
            "agents_involved": list(agents_involved),
            "message_count": {"user": user_messages, "agent": agent_messages},
            "first_activity": datetime.fromtimestamp(first_ts).isoformat(),
            "last_activity": datetime.fromtimestamp(last_ts).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get session metrics: {e}")
        raise


def get_recent_sessions(limit: int = 20) -> list[dict[str, Any]]:
    """
    Get list of recent sessions with summary info.

    Args:
        limit: Maximum number of sessions to return

    Returns:
        List of session summaries
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get unique sessions with basic info
        cur.execute(
            """
            SELECT
                session_id,
                MIN(timestamp) as started_at,
                MAX(timestamp) as ended_at,
                COUNT(*) as activity_count,
                COUNT(DISTINCT agent_id) as agent_count,
                SUM(CASE WHEN event_type = 'error' THEN 1 ELSE 0 END) as error_count,
                GROUP_CONCAT(DISTINCT agent_name) as agents
            FROM agent_activities
            GROUP BY session_id
            ORDER BY MAX(timestamp) DESC
            LIMIT ?
        """,
            (limit,),
        )

        sessions = cur.fetchall()
        conn.close()

        # Format results
        result = []
        for session in sessions:
            duration = session["ended_at"] - session["started_at"]
            result.append(
                {
                    "session_id": session["session_id"],
                    "started_at": datetime.fromtimestamp(session["started_at"]).isoformat(),
                    "ended_at": datetime.fromtimestamp(session["ended_at"]).isoformat(),
                    "duration_seconds": round(duration, 2),
                    "activity_count": session["activity_count"],
                    "agent_count": session["agent_count"],
                    "error_count": session["error_count"],
                    "agents": session["agents"].split(",") if session["agents"] else [],
                }
            )

        return result

    except Exception as e:
        logger.error(f"Failed to get recent sessions: {e}")
        raise


def get_error_summary(agent_id: str | None = None, hours: int = 24) -> dict[str, Any]:
    """
    Get error statistics and recent errors.

    Args:
        agent_id: Optional filter by agent
        hours: Look back window in hours

    Returns:
        Dict with error counts and recent error details
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        # Build query
        if agent_id:
            cur.execute(
                """
                SELECT id, session_id, agent_id, agent_name, timestamp, message, metadata
                FROM agent_activities
                WHERE event_type = 'error' AND agent_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 50
            """,
                (agent_id, cutoff),
            )
        else:
            cur.execute(
                """
                SELECT id, session_id, agent_id, agent_name, timestamp, message, metadata
                FROM agent_activities
                WHERE event_type = 'error' AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 50
            """,
                (cutoff,),
            )

        errors = cur.fetchall()

        # Get error counts by agent
        if agent_id:
            cur.execute(
                """
                SELECT agent_name, COUNT(*) as count
                FROM agent_activities
                WHERE event_type = 'error' AND agent_id = ? AND timestamp >= ?
                GROUP BY agent_name
            """,
                (agent_id, cutoff),
            )
        else:
            cur.execute(
                """
                SELECT agent_name, COUNT(*) as count
                FROM agent_activities
                WHERE event_type = 'error' AND timestamp >= ?
                GROUP BY agent_name
            """,
                (cutoff,),
            )

        error_counts = {row["agent_name"]: row["count"] for row in cur.fetchall()}

        conn.close()

        # Parse metadata
        for error in errors:
            if error.get("metadata"):
                try:
                    error["metadata"] = json.loads(error["metadata"])
                except:
                    pass

        return {
            "hours": hours,
            "agent_id": agent_id,
            "total_errors": sum(error_counts.values()),
            "errors_by_agent": error_counts,
            "recent_errors": errors[:20],
        }

    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise


# ============================================================================
# AGENT METRICS (Dashboard)
# ============================================================================


def get_agent_metrics(agent_id: str, hours: int = 24) -> dict[str, Any]:
    """
    Get aggregated metrics for a single agent.

    Args:
        agent_id: Agent identifier
        hours: Look back window in hours

    Returns:
        Dict with execution stats, success rate, latency, etc.
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        # Get execution counts by event type
        cur.execute(
            """
            SELECT
                event_type,
                COUNT(*) as count
            FROM agent_activities
            WHERE agent_id = ? AND timestamp >= ?
            GROUP BY event_type
        """,
            (agent_id, cutoff),
        )

        event_counts = {row["event_type"]: row["count"] for row in cur.fetchall()}

        # Calculate executions (started events)
        executions = event_counts.get("started", 0)
        completions = event_counts.get("completed", 0)
        errors = event_counts.get("error", 0)
        tool_calls = event_counts.get("tool_call", 0)

        # Success rate
        total_outcomes = completions + errors
        success_rate = (completions / total_outcomes * 100) if total_outcomes > 0 else 0

        # Get session-based latency (time from first to last activity per session)
        cur.execute(
            """
            SELECT
                session_id,
                MIN(timestamp) as start_ts,
                MAX(timestamp) as end_ts
            FROM agent_activities
            WHERE agent_id = ? AND timestamp >= ?
            GROUP BY session_id
        """,
            (agent_id, cutoff),
        )

        latencies = []
        for row in cur.fetchall():
            duration_ms = (row["end_ts"] - row["start_ts"]) * 1000
            if duration_ms > 0:  # Only count sessions with some duration
                latencies.append(duration_ms)

        avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0

        # Calculate percentiles if we have data
        p95_latency_ms = 0
        p99_latency_ms = 0
        if latencies:
            sorted_latencies = sorted(latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            p95_latency_ms = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
            p99_latency_ms = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)]

        # Get last active timestamp
        cur.execute(
            """
            SELECT MAX(timestamp) as last_active
            FROM agent_activities
            WHERE agent_id = ?
        """,
            (agent_id,),
        )

        last_active_row = cur.fetchone()
        last_active = None
        if last_active_row and last_active_row["last_active"]:
            last_active = datetime.fromtimestamp(last_active_row["last_active"]).isoformat()

        # Get unique session count
        cur.execute(
            """
            SELECT COUNT(DISTINCT session_id) as session_count
            FROM agent_activities
            WHERE agent_id = ? AND timestamp >= ?
        """,
            (agent_id, cutoff),
        )

        session_count = cur.fetchone()["session_count"]

        conn.close()

        return {
            "agent_id": agent_id,
            "hours": hours,
            "executions": executions,
            "completions": completions,
            "errors": errors,
            "success_rate": round(success_rate, 2),
            "tool_calls": tool_calls,
            "avg_latency_ms": round(avg_latency_ms, 2),
            "p95_latency_ms": round(p95_latency_ms, 2),
            "p99_latency_ms": round(p99_latency_ms, 2),
            "sessions": session_count,
            "last_active": last_active,
        }

    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        raise


def get_all_agents_metrics(hours: int = 24) -> dict[str, Any]:
    """
    Get aggregated metrics for all agents.

    Args:
        hours: Look back window in hours

    Returns:
        Dict with per-agent metrics and summary totals
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        # Get all unique agents with activity in the time window
        cur.execute(
            """
            SELECT DISTINCT agent_id, agent_name
            FROM agent_activities
            WHERE timestamp >= ? AND agent_id != 'user'
        """,
            (cutoff,),
        )

        agents = cur.fetchall()

        # Get metrics per agent
        cur.execute(
            """
            SELECT
                agent_id,
                agent_name,
                event_type,
                COUNT(*) as count
            FROM agent_activities
            WHERE timestamp >= ? AND agent_id != 'user'
            GROUP BY agent_id, agent_name, event_type
        """,
            (cutoff,),
        )

        # Build metrics per agent
        agent_metrics = {}
        for row in cur.fetchall():
            agent_id = row["agent_id"]
            if agent_id not in agent_metrics:
                agent_metrics[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": row["agent_name"],
                    "executions": 0,
                    "completions": 0,
                    "errors": 0,
                    "tool_calls": 0,
                    "success_rate": 0,
                    "avg_latency_ms": 0,
                    "p95_latency_ms": 0,
                    "sessions": 0,
                    "last_active": None,
                }

            event_type = row["event_type"]
            count = row["count"]

            if event_type == "started":
                agent_metrics[agent_id]["executions"] = count
            elif event_type == "completed":
                agent_metrics[agent_id]["completions"] = count
            elif event_type == "error":
                agent_metrics[agent_id]["errors"] = count
            elif event_type == "tool_call":
                agent_metrics[agent_id]["tool_calls"] = count

        # Calculate success rates
        for agent_id, metrics in agent_metrics.items():
            total = metrics["completions"] + metrics["errors"]
            if total > 0:
                metrics["success_rate"] = round((metrics["completions"] / total) * 100, 2)

        # Get session counts and latencies per agent
        cur.execute(
            """
            SELECT
                agent_id,
                session_id,
                MIN(timestamp) as start_ts,
                MAX(timestamp) as end_ts
            FROM agent_activities
            WHERE timestamp >= ? AND agent_id != 'user'
            GROUP BY agent_id, session_id
        """,
            (cutoff,),
        )

        agent_latencies = {}
        agent_sessions = {}
        for row in cur.fetchall():
            agent_id = row["agent_id"]
            if agent_id not in agent_latencies:
                agent_latencies[agent_id] = []
                agent_sessions[agent_id] = 0

            agent_sessions[agent_id] += 1
            duration_ms = (row["end_ts"] - row["start_ts"]) * 1000
            if duration_ms > 0:
                agent_latencies[agent_id].append(duration_ms)

        # Update metrics with latency and session data
        for agent_id, latencies in agent_latencies.items():
            if agent_id in agent_metrics:
                agent_metrics[agent_id]["sessions"] = agent_sessions.get(agent_id, 0)
                if latencies:
                    agent_metrics[agent_id]["avg_latency_ms"] = round(sum(latencies) / len(latencies), 2)
                    sorted_lat = sorted(latencies)
                    p95_idx = int(len(sorted_lat) * 0.95)
                    agent_metrics[agent_id]["p95_latency_ms"] = round(sorted_lat[min(p95_idx, len(sorted_lat) - 1)], 2)

        # Get last active per agent
        cur.execute("""
            SELECT agent_id, MAX(timestamp) as last_active
            FROM agent_activities
            WHERE agent_id != 'user'
            GROUP BY agent_id
        """)

        for row in cur.fetchall():
            if row["agent_id"] in agent_metrics and row["last_active"]:
                agent_metrics[row["agent_id"]]["last_active"] = datetime.fromtimestamp(row["last_active"]).isoformat()

        conn.close()

        # Calculate summary totals
        agents_list = list(agent_metrics.values())
        total_executions = sum(a["executions"] for a in agents_list)
        total_errors = sum(a["errors"] for a in agents_list)
        total_completions = sum(a["completions"] for a in agents_list)
        total_outcomes = total_completions + total_errors
        overall_success_rate = (total_completions / total_outcomes * 100) if total_outcomes > 0 else 0

        return {
            "hours": hours,
            "agents": agents_list,
            "summary": {
                "active_agents": len(agents_list),
                "total_executions": total_executions,
                "total_errors": total_errors,
                "overall_success_rate": round(overall_success_rate, 2),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get all agents metrics: {e}")
        raise


# ============================================================================
# COST & TOKEN TRACKING
# ============================================================================


def get_tool_invocations(
    agent_id: str | None = None, session_id: str | None = None, hours: int = 24, limit: int = 100
) -> dict[str, Any]:
    """
    Get tool invocations with optional filtering.

    Args:
        agent_id: Optional filter by agent
        session_id: Optional filter by session
        hours: Look back window in hours
        limit: Maximum results

    Returns:
        Dict with tool invocations and aggregates
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        # Build dynamic query
        conditions = ["started_at >= ?"]
        params: list = [cutoff]

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        where_clause = " AND ".join(conditions)

        cur.execute(
            f"""
            SELECT id, agent_id, function_id, session_id, status,
                   started_at, completed_at, duration_ms, error_message
            FROM tool_invocations
            WHERE {where_clause}
            ORDER BY started_at DESC
            LIMIT ?
        """,
            (*params, limit),
        )

        invocations = cur.fetchall()

        # Get aggregates
        cur.execute(
            f"""
            SELECT
                function_id,
                COUNT(*) as call_count,
                AVG(duration_ms) as avg_duration_ms,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count
            FROM tool_invocations
            WHERE {where_clause}
            GROUP BY function_id
        """,
            params,
        )

        by_tool = {
            row["function_id"]: {
                "tool": row["function_id"],
                "calls": row["call_count"],
                "avg_duration_ms": round(row["avg_duration_ms"] or 0, 2),
                "success_count": row["success_count"],
                "failed_count": row["failed_count"],
            }
            for row in cur.fetchall()
        }

        conn.close()

        return {
            "hours": hours,
            "agent_id": agent_id,
            "session_id": session_id,
            "invocations": invocations,
            "by_tool": list(by_tool.values()),
            "total_count": len(invocations),
        }

    except Exception as e:
        logger.error(f"Failed to get tool invocations: {e}")
        raise


def get_cost_summary(agent_id: str | None = None, session_id: str | None = None, hours: int = 24) -> dict[str, Any]:
    """
    Get LLM cost summary from activity data.

    Args:
        agent_id: Optional filter by agent
        session_id: Optional filter by session
        hours: Look back window

    Returns:
        Dict with cost breakdown
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        # Build query
        conditions = ["event_type = 'llm_call'", "timestamp >= ?"]
        params: list = [cutoff]

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)

        if session_id:
            conditions.append("session_id = ?")
            params.append(session_id)

        where_clause = " AND ".join(conditions)

        cur.execute(
            f"""
            SELECT metadata FROM agent_activities
            WHERE {where_clause}
        """,
            params,
        )

        rows = cur.fetchall()
        conn.close()

        # Aggregate costs
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        by_model: dict[str, dict] = {}

        for row in rows:
            try:
                metadata = json.loads(row["metadata"]) if row.get("metadata") else {}
                prompt = metadata.get("prompt_tokens", 0)
                completion = metadata.get("completion_tokens", 0)
                cost = metadata.get("total_cost_usd", 0)
                model = metadata.get("model", "unknown")

                total_prompt_tokens += prompt
                total_completion_tokens += completion
                total_cost += cost

                if model not in by_model:
                    by_model[model] = {
                        "model": model,
                        "calls": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost_usd": 0.0,
                    }
                by_model[model]["calls"] += 1
                by_model[model]["prompt_tokens"] += prompt
                by_model[model]["completion_tokens"] += completion
                by_model[model]["cost_usd"] += cost

            except (json.JSONDecodeError, KeyError):
                pass

        return {
            "hours": hours,
            "agent_id": agent_id,
            "session_id": session_id,
            "total_calls": len(rows),
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "total_cost_usd": round(total_cost, 4),
            "by_model": list(by_model.values()),
        }

    except Exception as e:
        logger.error(f"Failed to get cost summary: {e}")
        raise


def get_cost_by_agent(hours: int = 24) -> dict[str, Any]:
    """
    Get cost breakdown by agent.

    Args:
        hours: Look back window

    Returns:
        Dict with per-agent cost summary
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cutoff = (datetime.utcnow() - timedelta(hours=hours)).timestamp()

        cur.execute(
            """
            SELECT agent_id, agent_name, metadata
            FROM agent_activities
            WHERE event_type = 'llm_call' AND timestamp >= ?
        """,
            (cutoff,),
        )

        rows = cur.fetchall()
        conn.close()

        # Aggregate by agent
        by_agent: dict[str, dict] = {}

        for row in rows:
            agent_id = row["agent_id"]
            try:
                metadata = json.loads(row["metadata"]) if row.get("metadata") else {}
                cost = metadata.get("total_cost_usd", 0)
                tokens = metadata.get("total_tokens", 0)

                if agent_id not in by_agent:
                    by_agent[agent_id] = {
                        "agent_id": agent_id,
                        "agent_name": row["agent_name"],
                        "calls": 0,
                        "total_tokens": 0,
                        "cost_usd": 0.0,
                    }
                by_agent[agent_id]["calls"] += 1
                by_agent[agent_id]["total_tokens"] += tokens
                by_agent[agent_id]["cost_usd"] += cost

            except (json.JSONDecodeError, KeyError):
                pass

        # Sort by cost descending
        agents = sorted(by_agent.values(), key=lambda x: x["cost_usd"], reverse=True)

        total_cost = sum(a["cost_usd"] for a in agents)
        total_tokens = sum(a["total_tokens"] for a in agents)

        return {
            "hours": hours,
            "agents": agents,
            "summary": {
                "total_agents": len(agents),
                "total_cost_usd": round(total_cost, 4),
                "total_tokens": total_tokens,
                "total_calls": sum(a["calls"] for a in agents),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get cost by agent: {e}")
        raise


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "get_agent_activities",
    "get_agent_metrics",
    "get_all_agents_metrics",
    "get_cost_by_agent",
    "get_cost_summary",
    "get_error_summary",
    "get_recent_sessions",
    "get_session_activities",
    "get_session_metrics",
    "get_tool_invocations",
    "save_activity",
    "search_activities",
]
