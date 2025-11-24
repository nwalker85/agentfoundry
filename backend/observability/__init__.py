"""
Backend Observability Module
============================
Provides tracing, metrics, and logging infrastructure for Agent Foundry.

Components:
- LangSmith integration for LangGraph agent tracing
- OpenTelemetry instrumentation for distributed tracing
- Prometheus metrics collection
- Structured JSON logging with correlation IDs
- Token/cost tracking

Usage:
    from backend.observability import (
        setup_observability,
        get_langsmith_callbacks,
        get_tracer,
        get_meter,
        get_logger,
        with_context,
    )

    # Initialize on startup
    setup_observability()

    # Get callbacks for agent execution
    callbacks = get_langsmith_callbacks(session_id="...")

    # Create spans for tracing
    with create_span("my_operation") as span:
        span.set_attribute("key", "value")

    # Structured logging with context
    logger = get_logger(__name__)
    with with_context(session_id="sess-123"):
        logger.info("Processing request", user_id="usr-456")
"""

from .langsmith_tracer import (
    LangSmithTokenCallback,
    get_langchain_config,
    get_langsmith_callbacks,
    langsmith_enabled,
)
from .metrics import (
    agent_execution_duration_seconds,
    # Agent metrics
    agent_invocations_total,
    agents_active,
    get_metrics_response,
    # HTTP metrics
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
    llm_cost_usd_total,
    llm_request_duration_seconds,
    llm_requests_total,
    # LLM metrics
    llm_tokens_total,
    metrics_endpoint_handler,
    record_agent_execution,
    record_http_request,
    record_llm_usage,
    record_tool_invocation,
    session_duration_seconds,
    # Session metrics
    sessions_active,
    # Helpers
    set_app_info,
    tool_execution_duration_seconds,
    # Tool metrics
    tool_invocations_total,
)
from .otel_setup import (
    create_span,
    get_meter,
    get_tracer,
    is_otel_enabled,
    record_exception,
    setup_telemetry,
    shutdown_telemetry,
)
from .logger import (
    configure_logging,
    get_agent_logger,
    get_logger,
    get_request_logger,
    with_context,
)


def setup_observability():
    """
    Initialize all observability components.
    Call this on application startup.
    """
    import os

    # Setup OpenTelemetry
    setup_telemetry()

    # Set app info metric
    version = os.getenv("APP_VERSION", "0.8.1")
    environment = os.getenv("ENVIRONMENT", "development")
    set_app_info(version, environment)


__all__ = [
    # LangSmith
    "get_langsmith_callbacks",
    "langsmith_enabled",
    "LangSmithTokenCallback",
    "get_langchain_config",
    # OpenTelemetry
    "setup_telemetry",
    "shutdown_telemetry",
    "get_tracer",
    "get_meter",
    "create_span",
    "record_exception",
    "is_otel_enabled",
    # Structured Logging
    "get_logger",
    "get_agent_logger",
    "get_request_logger",
    "with_context",
    "configure_logging",
    # Prometheus metrics
    "http_request_duration_seconds",
    "http_requests_total",
    "http_requests_in_progress",
    "record_http_request",
    "agent_invocations_total",
    "agent_execution_duration_seconds",
    "agents_active",
    "record_agent_execution",
    "tool_invocations_total",
    "tool_execution_duration_seconds",
    "record_tool_invocation",
    "llm_tokens_total",
    "llm_cost_usd_total",
    "llm_request_duration_seconds",
    "llm_requests_total",
    "record_llm_usage",
    "sessions_active",
    "session_duration_seconds",
    "set_app_info",
    "metrics_endpoint_handler",
    "get_metrics_response",
    # Main setup
    "setup_observability",
]
