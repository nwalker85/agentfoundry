"""
Service Discovery Configuration
---------------------------------
Infrastructure-as-Registry pattern: Service names resolve via Docker DNS.

Philosophy:
- Internal services ALWAYS use port 8080 (standardized)
- Service names are DNS-resolvable (foundry-backend, livekit, redis, etc.)
- Override with env vars ONLY for external/testing scenarios
- NO port configuration needed in application code

Production Note:
- In Kubernetes, these same service names work via K8s Service discovery
- No code changes needed when moving to production
"""

import os


class ServiceConfig:
    """
    Centralized service discovery configuration.

    Usage:
        from backend.config.services import SERVICES

        # Make internal API call
        url = f"http://{SERVICES.COMPILER}:{SERVICES.PORT}/api/compile"

        # Call integration gateway
        url = f"http://{SERVICES.MCP_INTEGRATION}:{SERVICES.PORT}/tools"
    """

    # ============================================================================
    # STANDARD INTERNAL PORT - All services listen on 8080 inside containers
    # ============================================================================
    PORT = 8080

    # ============================================================================
    # SERVICE NAMES (DNS-resolvable in Docker/K8s)
    # ============================================================================

    # Core Backend Services
    BACKEND = os.getenv("SVC_BACKEND_HOST", "foundry-backend")
    COMPILER = os.getenv("SVC_COMPILER_HOST", "foundry-compiler")

    # Integration & Workflow
    MCP_INTEGRATION = os.getenv("SVC_MCP_HOST", "mcp-integration")
    N8N = os.getenv("SVC_N8N_HOST", "n8n")

    # Infrastructure
    # Use localhost when running from host machine, service name when in Docker
    REDIS = os.getenv("SVC_REDIS_HOST", "redis")
    POSTGRES = os.getenv("SVC_POSTGRES_HOST", "postgres")
    LIVEKIT = os.getenv("SVC_LIVEKIT_HOST", "livekit")
    LOCALSTACK = os.getenv("SVC_LOCALSTACK_HOST", "localhost")  # Default localhost for host machine

    # Authorization
    # Use localhost when running from host machine, openfga when in Docker
    OPENFGA = os.getenv("SVC_OPENFGA_HOST", "localhost")

    # Observability
    PROMETHEUS = os.getenv("SVC_PROMETHEUS_HOST", "prometheus")
    GRAFANA = os.getenv("SVC_GRAFANA_HOST", "grafana")
    TEMPO = os.getenv("SVC_TEMPO_HOST", "tempo")

    # Email Testing
    MAILPIT = os.getenv("SVC_MAILPIT_HOST", "mailpit")

    # ============================================================================
    # SERVICE-SPECIFIC PORTS (for services that DON'T use 8080)
    # ============================================================================

    # LiveKit uses its own port scheme
    LIVEKIT_HTTP_PORT = int(os.getenv("LIVEKIT_HTTP_PORT", "7880"))

    # Redis standard port
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

    # PostgreSQL standard port
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

    # LocalStack gateway
    LOCALSTACK_PORT = int(os.getenv("LOCALSTACK_PORT", "4566"))

    # OpenFGA authorization
    # When running from host: use localhost:9080 (HTTP) or localhost:8081 (gRPC)
    # When running in Docker: use openfga:8080 (HTTP internal) or openfga:8081 (gRPC)
    OPENFGA_HTTP_PORT = int(os.getenv("OPENFGA_HTTP_PORT", "9080"))  # External HTTP port
    OPENFGA_GRPC_PORT = int(os.getenv("OPENFGA_GRPC_PORT", "8081"))  # External gRPC port

    # n8n uses 5678
    N8N_PORT = int(os.getenv("N8N_PORT", "5678"))

    # Prometheus/Grafana
    PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9090"))
    GRAFANA_PORT = int(os.getenv("GRAFANA_PORT", "3000"))

    # Tempo (distributed tracing)
    TEMPO_OTLP_HTTP_PORT = int(os.getenv("TEMPO_OTLP_HTTP_PORT", "4318"))
    TEMPO_OTLP_GRPC_PORT = int(os.getenv("TEMPO_OTLP_GRPC_PORT", "4317"))
    TEMPO_QUERY_PORT = int(os.getenv("TEMPO_QUERY_PORT", "3200"))

    # Mailpit (email testing)
    MAILPIT_SMTP_PORT = int(os.getenv("MAILPIT_SMTP_PORT", "1025"))
    MAILPIT_UI_PORT = int(os.getenv("MAILPIT_UI_PORT", "8025"))

    # ============================================================================
    # PUBLIC URLS (for browser/external access)
    # ============================================================================

    @staticmethod
    def get_public_backend_url() -> str:
        """URL for frontend browser to reach backend (localhost in dev)"""
        return os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")

    @staticmethod
    def get_public_livekit_url() -> str:
        """URL for frontend browser to reach LiveKit (localhost in dev)"""
        port = os.getenv("LIVEKIT_PUBLIC_PORT", "7880")
        return os.getenv("PUBLIC_LIVEKIT_URL", f"ws://localhost:{port}")

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    @classmethod
    def get_service_url(cls, service_name: str) -> str:
        """
        Get full URL for an internal service.

        Args:
            service_name: Service attribute name (e.g., "BACKEND", "COMPILER")

        Returns:
            Full HTTP URL (e.g., "http://foundry-backend:8080")

        Example:
            >>> SERVICES.get_service_url("COMPILER")
            'http://foundry-compiler:8080'
        """
        host = getattr(cls, service_name)

        # Special case for services with non-standard ports
        if service_name == "LIVEKIT":
            return f"ws://{host}:{cls.LIVEKIT_HTTP_PORT}"
        elif service_name == "REDIS":
            return f"redis://{host}:{cls.REDIS_PORT}"
        elif service_name == "POSTGRES":
            return f"postgresql://{host}:{cls.POSTGRES_PORT}"
        elif service_name == "LOCALSTACK":
            return f"http://{host}:{cls.LOCALSTACK_PORT}"
        elif service_name == "OPENFGA":
            # In Docker: use internal HTTP port 8080
            # From host: use external mapped port 9080
            port = 8080 if host != "localhost" else cls.OPENFGA_HTTP_PORT
            return f"http://{host}:{port}"
        elif service_name == "N8N":
            return f"http://{host}:{cls.N8N_PORT}"
        elif service_name == "PROMETHEUS":
            return f"http://{host}:{cls.PROMETHEUS_PORT}"
        elif service_name == "GRAFANA":
            return f"http://{host}:{cls.GRAFANA_PORT}"
        elif service_name == "TEMPO":
            # Returns OTLP HTTP endpoint for sending traces
            return f"http://{host}:{cls.TEMPO_OTLP_HTTP_PORT}"
        elif service_name == "TEMPO_QUERY":
            # Returns query API endpoint for Grafana datasource
            host = cls.TEMPO
            return f"http://{host}:{cls.TEMPO_QUERY_PORT}"
        elif service_name == "MAILPIT":
            # Returns SMTP endpoint for sending email
            return f"smtp://{host}:{cls.MAILPIT_SMTP_PORT}"
        elif service_name == "MAILPIT_UI":
            # Returns web UI endpoint
            host = cls.MAILPIT
            return f"http://{host}:{cls.MAILPIT_UI_PORT}"
        else:
            # Standard 8080 services
            return f"http://{host}:{cls.PORT}"

    @classmethod
    def to_dict(cls) -> dict[str, str]:
        """Export all service URLs as dictionary"""
        return {
            "backend": cls.get_service_url("BACKEND"),
            "compiler": cls.get_service_url("COMPILER"),
            "mcp_integration": cls.get_service_url("MCP_INTEGRATION"),
            "n8n": cls.get_service_url("N8N"),
            "redis": cls.get_service_url("REDIS"),
            "postgres": cls.get_service_url("POSTGRES"),
            "livekit": cls.get_service_url("LIVEKIT"),
            "localstack": cls.get_service_url("LOCALSTACK"),
            "openfga": cls.get_service_url("OPENFGA"),
            "prometheus": cls.get_service_url("PROMETHEUS"),
            "grafana": cls.get_service_url("GRAFANA"),
            "tempo": cls.get_service_url("TEMPO"),
            "tempo_query": cls.get_service_url("TEMPO_QUERY"),
            "mailpit": cls.get_service_url("MAILPIT"),
            "mailpit_ui": cls.get_service_url("MAILPIT_UI"),
        }


# Singleton instance
SERVICES = ServiceConfig()


# ============================================================================
# OBSERVABILITY NAMING
# ============================================================================


def get_otel_service_name() -> str:
    """
    Get OpenTelemetry service name for this service.

    Aligns with service discovery names for consistent tracing.
    """
    return os.getenv("OTEL_SERVICE_NAME", "foundry-backend")


def get_service_version() -> str:
    """Get service version for telemetry"""
    return os.getenv("SERVICE_VERSION", "0.8.1-dev")
