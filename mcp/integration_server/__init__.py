"""
Integration Gateway MCP server package.

Exposes the FastAPI application instance so `uvicorn mcp.integration_server:app`
works both locally and inside Docker.
"""

from .main import app

__all__ = ["app"]
