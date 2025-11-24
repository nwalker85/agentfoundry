"""
Structured Logging Module for Agent Foundry
============================================
Provides JSON-formatted structured logging with correlation IDs and context propagation.

Features:
- JSON log output for production environments
- Correlation ID support (trace_id, span_id, session_id)
- Contextual logging with automatic field injection
- Integration with OpenTelemetry spans
- Log level configuration via environment variables

Environment Variables:
    LOG_LEVEL: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - default: INFO
    LOG_FORMAT: Output format (json, text) - default: json in production, text in development
    ENVIRONMENT: Deployment environment (development, staging, production)

Usage:
    from backend.observability.logger import get_logger, with_context

    # Basic usage
    logger = get_logger(__name__)
    logger.info("Processing request", request_id="req-123", user_id="usr-456")

    # With context propagation
    with with_context(session_id="sess-123", agent_id="cibc-card-activation"):
        logger.info("Starting agent execution")
        # All logs within this context will include session_id and agent_id
        logger.info("Tool invoked", tool_name="verify_card")

    # With OpenTelemetry span correlation
    from backend.observability import create_span
    with create_span("my_operation") as span:
        logger.info("Inside traced operation")  # Automatically includes trace_id/span_id
"""

import contextvars
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any

# Context variable for storing log context
_log_context: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("log_context", default={})


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format with standardized fields:
    - timestamp: ISO 8601 format
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - context: Additional context fields
    - trace_id/span_id: OpenTelemetry correlation (if available)
    - error: Exception details (if present)
    """

    def __init__(self, include_trace: bool = True):
        """
        Initialize formatter.

        Args:
            include_trace: Whether to include OpenTelemetry trace/span IDs
        """
        super().__init__()
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base log entry
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add file location for DEBUG and ERROR levels
        if record.levelno in (logging.DEBUG, logging.ERROR, logging.CRITICAL):
            log_entry["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add context from context variable
        context = _log_context.get()
        if context:
            log_entry["context"] = context.copy()

        # Add extra fields passed to log call
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                extra_fields[key] = value

        if extra_fields:
            if "context" not in log_entry:
                log_entry["context"] = {}
            log_entry["context"].update(extra_fields)

        # Add OpenTelemetry trace correlation
        if self.include_trace:
            trace_info = self._get_trace_context()
            if trace_info:
                log_entry.update(trace_info)

        # Add exception info if present
        if record.exc_info:
            log_entry["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else "Unknown",
                "message": str(record.exc_info[1]) if record.exc_info[1] else "",
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, default=str, ensure_ascii=False)

    def _get_trace_context(self) -> dict[str, str] | None:
        """Extract OpenTelemetry trace context if available."""
        try:
            from opentelemetry import trace

            span = trace.get_current_span()
            if span and span.is_recording():
                ctx = span.get_span_context()
                return {
                    "trace_id": format(ctx.trace_id, "032x"),
                    "span_id": format(ctx.span_id, "016x"),
                }
        except ImportError:
            pass
        except Exception:
            pass
        return None


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Format: [TIMESTAMP] LEVEL    logger: message {key=value, ...}
    """

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        """
        Initialize formatter.

        Args:
            use_colors: Whether to use ANSI colors in output
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as human-readable text."""
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Level with optional color
        level = record.levelname.ljust(8)
        if self.use_colors and record.levelname in self.COLORS:
            level = f"{self.COLORS[record.levelname]}{level}{self.RESET}"

        # Logger name (truncated if too long)
        logger_name = record.name
        if len(logger_name) > 30:
            logger_name = "..." + logger_name[-27:]

        # Message
        message = record.getMessage()

        # Build output
        output = f"[{timestamp}] {level} {logger_name}: {message}"

        # Add context from context variable
        context = _log_context.get()
        extra_fields = {}

        # Collect extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "message",
                "taskName",
            ):
                extra_fields[key] = value

        # Merge context and extra fields
        all_context = {**context, **extra_fields}
        if all_context:
            context_str = ", ".join(f"{k}={v}" for k, v in all_context.items())
            output += f" {{{context_str}}}"

        # Add exception if present
        if record.exc_info:
            output += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return output


class ContextualLogger(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes context fields.

    Allows passing extra fields directly to log methods:
        logger.info("Processing", request_id="123", user_id="456")
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process log message and add extra fields."""
        # Get extra dict, creating if needed
        extra = kwargs.get("extra", {})

        # Add any keyword arguments as extra fields
        for key, value in list(kwargs.items()):
            if key not in ("exc_info", "stack_info", "stacklevel", "extra"):
                extra[key] = value
                del kwargs[key]

        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(name: str) -> ContextualLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        ContextualLogger instance with structured output

    Example:
        logger = get_logger(__name__)
        logger.info("User logged in", user_id="usr-123", ip_address="192.168.1.1")
    """
    logger = logging.getLogger(name)
    return ContextualLogger(logger, {})


class with_context:
    """
    Context manager for adding fields to all logs within a scope.

    Usage:
        with with_context(session_id="sess-123", agent_id="my-agent"):
            logger.info("Starting execution")  # Includes session_id and agent_id
            do_work()
            logger.info("Completed")  # Also includes session_id and agent_id
    """

    def __init__(self, **fields):
        """
        Initialize context with fields.

        Args:
            **fields: Key-value pairs to include in all logs within this context
        """
        self.fields = fields
        self.token = None

    def __enter__(self):
        """Enter context and set fields."""
        # Merge with existing context
        current = _log_context.get()
        new_context = {**current, **self.fields}
        self.token = _log_context.set(new_context)
        return self

    def __exit__(self, *args):
        """Exit context and restore previous state."""
        if self.token:
            _log_context.reset(self.token)


def configure_logging(
    level: str | None = None,
    format_type: str | None = None,
    include_trace: bool = True,
) -> None:
    """
    Configure the root logger with structured output.

    This should be called once at application startup.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format ('json' or 'text')
        include_trace: Whether to include OpenTelemetry trace IDs

    Example:
        # In main.py startup
        from backend.observability.logger import configure_logging
        configure_logging(level="INFO", format_type="json")
    """
    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    log_level = getattr(logging, level, logging.INFO)

    # Determine format type
    if format_type is None:
        env = os.getenv("ENVIRONMENT", "development").lower()
        format_type = os.getenv("LOG_FORMAT", "json" if env == "production" else "text")

    # Create handler with appropriate formatter
    handler = logging.StreamHandler(sys.stdout)

    if format_type == "json":
        handler.setFormatter(StructuredFormatter(include_trace=include_trace))
    else:
        handler.setFormatter(TextFormatter(use_colors=True))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers and add our configured one
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


# Pre-configured loggers for common use cases
def get_agent_logger(agent_id: str, agent_name: str | None = None) -> ContextualLogger:
    """
    Get a logger pre-configured for agent execution.

    Args:
        agent_id: Agent identifier
        agent_name: Optional human-readable agent name

    Returns:
        Logger with agent context
    """
    logger = get_logger(f"agent.{agent_id}")
    # Note: These won't be automatically included, but the logger is namespaced
    return logger


def get_request_logger(request_id: str, method: str, path: str) -> ContextualLogger:
    """
    Get a logger pre-configured for HTTP request handling.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path

    Returns:
        Logger with request context
    """
    return get_logger(f"http.{method.lower()}")
