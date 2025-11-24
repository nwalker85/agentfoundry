"""
Integration gateway routes for the MCP ↔ n8n tool catalog.

This module provides FastAPI routes that serve tool catalog data
from the integrations manifest file.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Cached manifest data
_manifest_cache: dict[str, Any] | None = None


def _get_manifest_path() -> str:
    """Get the path to the integrations manifest file."""
    return os.getenv(
        "INTEGRATIONS_MANIFEST",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "mcp",
            "integration_server",
            "config",
            "integrations.manifest.json",
        ),
    )


def _load_manifest() -> list[dict[str, Any]]:
    """Load the integrations manifest file."""
    global _manifest_cache

    if _manifest_cache is not None:
        return _manifest_cache.get("tools", [])

    manifest_path = _get_manifest_path()
    path = Path(manifest_path)

    if not path.exists():
        logger.warning(f"Integrations manifest not found: {path}")
        return []

    try:
        raw = json.loads(path.read_text())
        _manifest_cache = {"tools": raw}
        logger.info(f"Loaded {len(raw)} tools from integrations manifest")
        return raw
    except Exception as e:
        logger.error(f"Failed to load integrations manifest: {e}")
        return []


def _serialize_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Serialize a tool manifest to the API response format."""
    metadata = tool.get("metadata", {})
    return {
        "toolName": tool.get("toolName", ""),
        "displayName": tool.get("displayName", ""),
        "description": tool.get("description", ""),
        "category": tool.get("category", ""),
        "logo": tool.get("logo", ""),
        "tags": tool.get("tags", []),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "health": None,  # Health metrics not tracked in simple mode
    }


@router.get("/tools")
async def list_tools() -> dict[str, Any]:
    """List all available integration tools from the manifest."""
    try:
        tools = _load_manifest()
        return {"items": [_serialize_tool(tool) for tool in tools]}
    except Exception as e:
        logger.error(f"Failed to list integration tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}")
async def get_tool(tool_name: str) -> dict[str, Any]:
    """Get details for a specific integration tool."""
    tools = _load_manifest()

    # Find tool by name (case-insensitive)
    tool_name_lower = tool_name.lower()
    for tool in tools:
        if tool.get("toolName", "").lower() == tool_name_lower:
            return _serialize_tool(tool) | {
                "inputSchema": tool.get("inputSchema", {}),
                "outputSchema": tool.get("outputSchema", {}),
                "examples": tool.get("examples", []),
            }

    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.get("/configs")
async def list_configs() -> list[dict[str, Any]]:
    """List integration configurations (stub for now)."""
    # TODO: Implement configuration storage
    return []


@router.get("/health")
async def health() -> dict[str, Any]:
    """Health check for the integration gateway."""
    tools = _load_manifest()
    return {
        "service": "integration-gateway",
        "status": "ok",
        "tool_count": len(tools),
        "manifest_path": _get_manifest_path(),
    }


@router.post("/reload")
async def reload_manifest() -> dict[str, Any]:
    """Reload the integrations manifest from disk."""
    global _manifest_cache
    _manifest_cache = None
    tools = _load_manifest()
    return {
        "status": "reloaded",
        "tool_count": len(tools),
    }
