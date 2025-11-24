"""
Usage and Cost Tracking Service
================================
Tracks LLM token usage and calculates costs based on model pricing.

Pricing data sourced from public API documentation (as of Jan 2025).
Prices are in USD per 1M tokens unless otherwise noted.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# Model Pricing Configuration
# ============================================================================


@dataclass
class ModelPricing:
    """Pricing for a single model"""

    input_per_1m: float  # USD per 1M input tokens
    output_per_1m: float  # USD per 1M output tokens
    provider: str
    context_window: int = 128000


# Pricing table - prices per 1M tokens (USD)
# Source: Public API documentation as of Jan 2025
MODEL_PRICING: dict[str, ModelPricing] = {
    # OpenAI Models
    "gpt-4o": ModelPricing(2.50, 10.00, "openai", 128000),
    "gpt-4o-2024-11-20": ModelPricing(2.50, 10.00, "openai", 128000),
    "gpt-4o-mini": ModelPricing(0.15, 0.60, "openai", 128000),
    "gpt-4o-mini-2024-07-18": ModelPricing(0.15, 0.60, "openai", 128000),
    "gpt-4-turbo": ModelPricing(10.00, 30.00, "openai", 128000),
    "gpt-4-turbo-preview": ModelPricing(10.00, 30.00, "openai", 128000),
    "gpt-4": ModelPricing(30.00, 60.00, "openai", 8192),
    "gpt-3.5-turbo": ModelPricing(0.50, 1.50, "openai", 16385),
    "gpt-3.5-turbo-0125": ModelPricing(0.50, 1.50, "openai", 16385),
    "o1": ModelPricing(15.00, 60.00, "openai", 200000),
    "o1-mini": ModelPricing(3.00, 12.00, "openai", 128000),
    "o1-preview": ModelPricing(15.00, 60.00, "openai", 128000),
    # Anthropic Models
    "claude-3-5-sonnet-20241022": ModelPricing(3.00, 15.00, "anthropic", 200000),
    "claude-3-5-sonnet-latest": ModelPricing(3.00, 15.00, "anthropic", 200000),
    "claude-sonnet-4-5-20250929": ModelPricing(3.00, 15.00, "anthropic", 200000),
    "claude-3-5-haiku-20241022": ModelPricing(0.80, 4.00, "anthropic", 200000),
    "claude-3-opus-20240229": ModelPricing(15.00, 75.00, "anthropic", 200000),
    "claude-3-sonnet-20240229": ModelPricing(3.00, 15.00, "anthropic", 200000),
    "claude-3-haiku-20240307": ModelPricing(0.25, 1.25, "anthropic", 200000),
    # Google Models
    "gemini-1.5-pro": ModelPricing(1.25, 5.00, "google", 2000000),
    "gemini-1.5-flash": ModelPricing(0.075, 0.30, "google", 1000000),
    "gemini-2.0-flash": ModelPricing(0.10, 0.40, "google", 1000000),
    # Default fallback
    "unknown": ModelPricing(1.00, 3.00, "unknown", 128000),
}


def get_model_pricing(model_name: str) -> ModelPricing:
    """Get pricing for a model, with fuzzy matching and fallback"""
    # Exact match
    if model_name in MODEL_PRICING:
        return MODEL_PRICING[model_name]

    # Fuzzy match (contains)
    model_lower = model_name.lower()
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower or model_lower in key:
            return pricing

    # Provider-based fallback
    if "gpt" in model_lower:
        return MODEL_PRICING.get("gpt-4o-mini", MODEL_PRICING["unknown"])
    if "claude" in model_lower:
        return MODEL_PRICING.get("claude-3-5-haiku-20241022", MODEL_PRICING["unknown"])
    if "gemini" in model_lower:
        return MODEL_PRICING.get("gemini-1.5-flash", MODEL_PRICING["unknown"])

    return MODEL_PRICING["unknown"]


def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
    """
    Calculate cost for a single LLM call.

    Args:
        model_name: The model used
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Dict with cost breakdown
    """
    pricing = get_model_pricing(model_name)

    input_cost = (prompt_tokens / 1_000_000) * pricing.input_per_1m
    output_cost = (completion_tokens / 1_000_000) * pricing.output_per_1m
    total_cost = input_cost + output_cost

    return {
        "model": model_name,
        "provider": pricing.provider,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "pricing_used": {
            "input_per_1m": pricing.input_per_1m,
            "output_per_1m": pricing.output_per_1m,
        },
    }


# ============================================================================
# Database Operations
# ============================================================================


def save_llm_usage(
    session_id: str,
    agent_id: str,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Save LLM usage record to the database.

    Args:
        session_id: Session identifier
        agent_id: Agent that made the call
        model_name: LLM model used
        prompt_tokens: Input tokens
        completion_tokens: Output tokens
        duration_ms: Call duration in milliseconds
        metadata: Additional metadata

    Returns:
        Usage record with calculated cost
    """
    from uuid import uuid4

    from backend.db import get_db_connection

    cost_data = calculate_cost(model_name, prompt_tokens, completion_tokens)

    record_id = str(uuid4())
    timestamp = datetime.utcnow().isoformat()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Save to agent_activities with llm_call event type
        cursor.execute(
            """
            INSERT INTO agent_activities (
                id, session_id, agent_id, agent_name, event_type,
                timestamp, message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record_id,
                session_id,
                agent_id,
                agent_id,  # Use agent_id as name
                "llm_call",
                timestamp,
                f"LLM call to {model_name}: {prompt_tokens} in / {completion_tokens} out tokens",
                json.dumps({**cost_data, "duration_ms": duration_ms, **(metadata or {})}),
            ),
        )

        conn.commit()

        return {
            "id": record_id,
            "session_id": session_id,
            "agent_id": agent_id,
            "timestamp": timestamp,
            **cost_data,
            "duration_ms": duration_ms,
        }

    except Exception as e:
        logger.error(f"Failed to save LLM usage: {e}")
        raise


def get_usage_summary(agent_id: str | None = None, session_id: str | None = None, hours: int = 24) -> dict[str, Any]:
    """
    Get aggregated usage summary.

    Args:
        agent_id: Optional filter by agent
        session_id: Optional filter by session
        hours: Look back window

    Returns:
        Aggregated usage statistics
    """
    from backend.db import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    # Build query
    where_clauses = ["event_type = 'llm_call'", "timestamp > ?"]
    params: list[Any] = [cutoff]

    if agent_id:
        where_clauses.append("agent_id = ?")
        params.append(agent_id)

    if session_id:
        where_clauses.append("session_id = ?")
        params.append(session_id)

    where_sql = " AND ".join(where_clauses)

    # Get all LLM call records
    cursor.execute(
        f"""
        SELECT metadata FROM agent_activities
        WHERE {where_sql}
        ORDER BY timestamp DESC
    """,
        params,
    )

    rows = cursor.fetchall()

    # Aggregate
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_cost = 0.0
    by_model: dict[str, dict[str, Any]] = {}

    for row in rows:
        try:
            metadata = json.loads(row[0]) if row[0] else {}
            prompt = metadata.get("prompt_tokens", 0)
            completion = metadata.get("completion_tokens", 0)
            cost = metadata.get("total_cost_usd", 0)
            model = metadata.get("model", "unknown")

            total_prompt_tokens += prompt
            total_completion_tokens += completion
            total_cost += cost

            if model not in by_model:
                by_model[model] = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}
            by_model[model]["calls"] += 1
            by_model[model]["prompt_tokens"] += prompt
            by_model[model]["completion_tokens"] += completion
            by_model[model]["cost_usd"] += cost

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse usage metadata: {e}")

    return {
        "hours": hours,
        "agent_id": agent_id,
        "session_id": session_id,
        "total_calls": len(rows),
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "total_cost_usd": round(total_cost, 4),
        "by_model": by_model,
    }


def get_cost_by_agent(hours: int = 24) -> list[dict[str, Any]]:
    """
    Get cost breakdown by agent.

    Args:
        hours: Look back window

    Returns:
        List of agent cost summaries
    """
    from backend.db import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()

    cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    cursor.execute(
        """
        SELECT agent_id, metadata FROM agent_activities
        WHERE event_type = 'llm_call' AND timestamp > ?
        ORDER BY agent_id
    """,
        (cutoff,),
    )

    rows = cursor.fetchall()

    # Aggregate by agent
    by_agent: dict[str, dict[str, Any]] = {}

    for row in rows:
        agent_id = row[0]
        try:
            metadata = json.loads(row[1]) if row[1] else {}
            cost = metadata.get("total_cost_usd", 0)
            tokens = metadata.get("total_tokens", 0)

            if agent_id not in by_agent:
                by_agent[agent_id] = {"agent_id": agent_id, "calls": 0, "total_tokens": 0, "cost_usd": 0.0}
            by_agent[agent_id]["calls"] += 1
            by_agent[agent_id]["total_tokens"] += tokens
            by_agent[agent_id]["cost_usd"] += cost

        except (json.JSONDecodeError, KeyError):
            pass

    # Sort by cost descending
    agents = sorted(by_agent.values(), key=lambda x: x["cost_usd"], reverse=True)

    return agents
