"""
Backend Configuration Module
"""

from .services import SERVICES, get_otel_service_name, get_service_version

__all__ = ["SERVICES", "get_otel_service_name", "get_service_version"]
