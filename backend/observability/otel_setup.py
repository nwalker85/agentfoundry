"""
OpenTelemetry Setup Module
==========================
Initializes OpenTelemetry tracing, metrics, and logging for Agent Foundry.

Uses the Infrastructure-as-Registry pattern for service discovery:
- Default endpoint is Tempo via service discovery (http://tempo:4318)
- Falls back to environment variable if set

Environment Variables:
    OTEL_EXPORTER_OTLP_ENDPOINT: OTLP collector endpoint (default: uses service discovery → http://tempo:4318)
    OTEL_SERVICE_NAME: Service name for traces (default: foundry-backend)
    OTEL_TRACES_EXPORTER: Exporter type (otlp, console, none)
    OTEL_METRICS_EXPORTER: Exporter type (otlp, prometheus, none)
    OTEL_ENVIRONMENT: Deployment environment (dev, staging, prod)

Usage:
    from backend.observability.otel_setup import setup_telemetry, get_tracer, get_meter

    # Initialize on app startup
    setup_telemetry()

    # Get tracer for manual instrumentation
    tracer = get_tracer(__name__)
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("custom.key", "value")
        # ... do work

    # Get meter for custom metrics
    meter = get_meter(__name__)
    counter = meter.create_counter("my_counter")
    counter.add(1, {"label": "value"})
"""

import logging
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global state
_tracer_provider = None
_meter_provider = None
_initialized = False


def is_otel_enabled() -> bool:
    """Check if OTEL should be enabled based on environment"""
    exporter = os.getenv("OTEL_TRACES_EXPORTER", "otlp").lower()
    return exporter not in ("none", "disabled", "")


def setup_telemetry(
    service_name: str | None = None, otlp_endpoint: str | None = None, environment: str | None = None
) -> bool:
    """
    Initialize OpenTelemetry tracing and metrics.

    Args:
        service_name: Override service name (default: from env or 'agent-foundry')
        otlp_endpoint: Override OTLP endpoint (default: from env)
        environment: Override environment (default: from env or 'development')

    Returns:
        True if initialization succeeded, False otherwise
    """
    global _tracer_provider, _meter_provider, _initialized

    if _initialized:
        logger.debug("OpenTelemetry already initialized")
        return True

    if not is_otel_enabled():
        logger.info("OpenTelemetry disabled via OTEL_TRACES_EXPORTER=none")
        _initialized = True
        return False

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import DEPLOYMENT_ENVIRONMENT, SERVICE_NAME, SERVICE_VERSION, Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

        # Configuration - uses service discovery for default endpoint
        _service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "foundry-backend")

        # Use service discovery for OTLP endpoint (Tempo)
        # Priority: 1. Function arg, 2. Env var, 3. Service discovery
        if otlp_endpoint:
            _otlp_endpoint = otlp_endpoint
        elif os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
            _otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        else:
            # Service discovery: use Tempo service
            try:
                from backend.config.services import SERVICES

                _otlp_endpoint = SERVICES.get_service_url("TEMPO")
            except ImportError:
                # Fallback if service config not available
                _otlp_endpoint = "http://tempo:4318"

        _environment = environment or os.getenv("OTEL_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))
        _version = os.getenv("APP_VERSION", "0.8.1")

        # Create resource with service info
        resource = Resource.create(
            {
                SERVICE_NAME: _service_name,
                SERVICE_VERSION: _version,
                DEPLOYMENT_ENVIRONMENT: _environment,
                "service.namespace": "agent-foundry",
            }
        )

        # =====================================================================
        # TRACING SETUP
        # =====================================================================
        trace_exporter_type = os.getenv("OTEL_TRACES_EXPORTER", "otlp").lower()

        _tracer_provider = TracerProvider(resource=resource)

        if trace_exporter_type == "console":
            span_processor = BatchSpanProcessor(ConsoleSpanExporter())
        elif trace_exporter_type == "otlp":
            otlp_trace_exporter = OTLPSpanExporter(endpoint=f"{_otlp_endpoint}/v1/traces")
            span_processor = BatchSpanProcessor(otlp_trace_exporter)
        else:
            span_processor = None

        if span_processor:
            _tracer_provider.add_span_processor(span_processor)

        trace.set_tracer_provider(_tracer_provider)

        # =====================================================================
        # METRICS SETUP
        # =====================================================================
        metrics_exporter_type = os.getenv("OTEL_METRICS_EXPORTER", "otlp").lower()

        if metrics_exporter_type == "console":
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=60000,  # Export every 60 seconds
            )
        elif metrics_exporter_type == "otlp":
            otlp_metric_exporter = OTLPMetricExporter(endpoint=f"{_otlp_endpoint}/v1/metrics")
            metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=60000)
        elif metrics_exporter_type == "prometheus":
            # Prometheus exporter is pull-based, handled separately
            metric_reader = None
        else:
            metric_reader = None

        if metric_reader:
            _meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        else:
            _meter_provider = MeterProvider(resource=resource)

        metrics.set_meter_provider(_meter_provider)

        _initialized = True
        logger.info(
            f"OpenTelemetry initialized: service={_service_name}, env={_environment}, traces={trace_exporter_type}, metrics={metrics_exporter_type}, endpoint={_otlp_endpoint}"
        )
        return True

    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not fully installed: {e}")
        _initialized = True
        return False
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        _initialized = True
        return False


def get_tracer(name: str = __name__):
    """
    Get a tracer for creating spans.

    Args:
        name: Instrumentation name (typically __name__)

    Returns:
        OpenTelemetry tracer or no-op tracer if OTEL disabled
    """
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        return _NoOpTracer()


def get_meter(name: str = __name__):
    """
    Get a meter for creating metrics.

    Args:
        name: Instrumentation name (typically __name__)

    Returns:
        OpenTelemetry meter or no-op meter if OTEL disabled
    """
    try:
        from opentelemetry import metrics

        return metrics.get_meter(name)
    except ImportError:
        return _NoOpMeter()


@contextmanager
def create_span(name: str, attributes: dict | None = None):
    """
    Convenience context manager for creating spans.

    Usage:
        with create_span("my_operation", {"key": "value"}) as span:
            # ... do work
            span.set_attribute("result", "success")
    """
    tracer = get_tracer("agent-foundry")
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def record_exception(span, exception: Exception, attributes: dict | None = None):
    """
    Record an exception on a span.

    Args:
        span: The span to record on
        exception: The exception to record
        attributes: Additional attributes
    """
    try:
        from opentelemetry.trace import Status, StatusCode

        span.set_status(Status(StatusCode.ERROR, str(exception)))
        span.record_exception(exception, attributes=attributes)
    except Exception:
        pass  # Fail silently if OTEL not available


def shutdown_telemetry():
    """Shutdown telemetry providers gracefully"""
    global _tracer_provider, _meter_provider, _initialized

    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down tracer provider: {e}")

    if _meter_provider:
        try:
            _meter_provider.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down meter provider: {e}")

    _initialized = False
    logger.info("OpenTelemetry shutdown complete")


# ============================================================================
# NO-OP IMPLEMENTATIONS (when OTEL is disabled/not installed)
# ============================================================================


class _NoOpSpan:
    """No-op span for when OTEL is disabled"""

    def set_attribute(self, key, value):
        pass

    def set_attributes(self, attributes):
        pass

    def add_event(self, name, attributes=None):
        pass

    def record_exception(self, exception, attributes=None):
        pass

    def set_status(self, status):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoOpTracer:
    """No-op tracer for when OTEL is disabled"""

    def start_span(self, name, **kwargs):
        return _NoOpSpan()

    def start_as_current_span(self, name, **kwargs):
        return _NoOpSpan()


class _NoOpCounter:
    """No-op counter for when OTEL is disabled"""

    def add(self, amount, attributes=None):
        pass


class _NoOpHistogram:
    """No-op histogram for when OTEL is disabled"""

    def record(self, amount, attributes=None):
        pass


class _NoOpMeter:
    """No-op meter for when OTEL is disabled"""

    def create_counter(self, name, **kwargs):
        return _NoOpCounter()

    def create_histogram(self, name, **kwargs):
        return _NoOpHistogram()

    def create_up_down_counter(self, name, **kwargs):
        return _NoOpCounter()

    def create_observable_gauge(self, name, callbacks, **kwargs):
        pass
