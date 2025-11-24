"""
Prometheus Metrics Module
=========================
Defines and exposes Prometheus metrics for Agent Foundry.

Metrics Categories:
- HTTP request metrics (latency, count, errors)
- Agent execution metrics (invocations, duration, success/failure)
- Tool invocation metrics (calls, duration, errors)
- LLM usage metrics (tokens, cost, latency)

Usage:
    from backend.observability.metrics import (
        request_latency,
        agent_invocations,
        record_agent_execution,
        get_metrics_endpoint
    )

    # Record metrics
    agent_invocations.labels(agent_id="my-agent", status="success").inc()

    # Get Prometheus endpoint handler
    from fastapi import Response
    @app.get("/metrics")
    async def metrics():
        return get_metrics_endpoint()
"""

import logging
import time
from collections.abc import Callable
from functools import wraps

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)

# ============================================================================
# HTTP REQUEST METRICS
# ============================================================================

# Request latency histogram with common buckets
REQUEST_LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code"],
    buckets=REQUEST_LATENCY_BUCKETS,
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# ============================================================================
# AGENT EXECUTION METRICS
# ============================================================================

agent_invocations_total = Counter(
    "agent_invocations_total",
    "Total agent invocations",
    ["agent_id", "status"],  # status: success, error, interrupted
)

agent_execution_duration_seconds = Histogram(
    "agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_id"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

agents_active = Gauge(
    "agents_active",
    "Number of agents currently executing",
    ["agent_id"],
)

# ============================================================================
# TOOL INVOCATION METRICS
# ============================================================================

tool_invocations_total = Counter(
    "tool_invocations_total",
    "Total tool invocations",
    ["tool_name", "agent_id", "status"],  # status: success, error
)

tool_execution_duration_seconds = Histogram(
    "tool_execution_duration_seconds",
    "Tool execution duration in seconds",
    ["tool_name"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ============================================================================
# LLM USAGE METRICS
# ============================================================================

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["model", "token_type"],  # token_type: prompt, completion
)

llm_cost_usd_total = Counter(
    "llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model", "agent_id"],
)

llm_request_duration_seconds = Histogram(
    "llm_request_duration_seconds",
    "LLM request duration in seconds",
    ["model"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

llm_requests_total = Counter(
    "llm_requests_total",
    "Total LLM requests",
    ["model", "status"],
)

# ============================================================================
# SESSION METRICS
# ============================================================================

sessions_active = Gauge(
    "sessions_active",
    "Number of active sessions",
)

session_duration_seconds = Histogram(
    "session_duration_seconds",
    "Session duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1800.0),
)

# ============================================================================
# SYSTEM METRICS
# ============================================================================

app_info = Gauge(
    "app_info",
    "Application information",
    ["version", "environment"],
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request path
        status_code: Response status code
        duration: Request duration in seconds
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint, status_code=str(status_code)).observe(
        duration
    )


def record_agent_execution(agent_id: str, status: str, duration_seconds: float):
    """
    Record agent execution metrics.

    Args:
        agent_id: Agent identifier
        status: Execution status (success, error, interrupted)
        duration_seconds: Execution duration
    """
    agent_invocations_total.labels(agent_id=agent_id, status=status).inc()
    agent_execution_duration_seconds.labels(agent_id=agent_id).observe(duration_seconds)


def record_tool_invocation(tool_name: str, agent_id: str, status: str, duration_seconds: float):
    """
    Record tool invocation metrics.

    Args:
        tool_name: Name of the tool
        agent_id: Agent that invoked the tool
        status: Invocation status (success, error)
        duration_seconds: Invocation duration
    """
    tool_invocations_total.labels(tool_name=tool_name, agent_id=agent_id, status=status).inc()
    tool_execution_duration_seconds.labels(tool_name=tool_name).observe(duration_seconds)


def record_llm_usage(
    model: str,
    agent_id: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    duration_seconds: float | None = None,
    status: str = "success",
):
    """
    Record LLM usage metrics.

    Args:
        model: Model name
        agent_id: Agent that made the call
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
        cost_usd: Cost in USD
        duration_seconds: Optional request duration
        status: Request status (success, error)
    """
    llm_tokens_total.labels(model=model, token_type="prompt").inc(prompt_tokens)
    llm_tokens_total.labels(model=model, token_type="completion").inc(completion_tokens)
    llm_cost_usd_total.labels(model=model, agent_id=agent_id).inc(cost_usd)
    llm_requests_total.labels(model=model, status=status).inc()

    if duration_seconds is not None:
        llm_request_duration_seconds.labels(model=model).observe(duration_seconds)


def set_app_info(version: str, environment: str):
    """Set application info gauge"""
    app_info.labels(version=version, environment=environment).set(1)


# ============================================================================
# PROMETHEUS ENDPOINT
# ============================================================================


def get_metrics_response():
    """
    Generate Prometheus metrics response.

    Returns:
        Tuple of (content, content_type)
    """
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST


def metrics_endpoint_handler():
    """
    FastAPI-compatible metrics endpoint handler.

    Usage:
        from fastapi import Response
        from backend.observability.metrics import metrics_endpoint_handler

        @app.get("/metrics")
        async def metrics():
            content, content_type = metrics_endpoint_handler()
            return Response(content=content, media_type=content_type)
    """
    return get_metrics_response()


# ============================================================================
# DECORATORS
# ============================================================================


def track_execution_time(metric: Histogram, labels: dict | None = None):
    """
    Decorator to track function execution time.

    Usage:
        @track_execution_time(agent_execution_duration_seconds, {"agent_id": "my-agent"})
        async def my_function():
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)

        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is async"""
    import asyncio

    return asyncio.iscoroutinefunction(func)
