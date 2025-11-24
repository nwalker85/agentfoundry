"""
FastAPI application entrypoint for the MCP ↔ n8n integration gateway.

This module keeps the app wiring thin: request lifecycle management,
root/health routes, and dependency injection for the manifest loader
and integration client live here, while the heavy lifting sits in
`manifest_loader.py`, `client.py`, and future routers.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import Body, FastAPI, HTTPException, Request, status

from .client import IntegrationClient
from .manifest_loader import ManifestLoader
from .validation import validate_payload

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load the manifest once at startup and keep it cached."""
    manifest_path = os.getenv(
        "INTEGRATIONS_MANIFEST",
        os.path.join(
            os.path.dirname(__file__),
            "config",
            "integrations.manifest.json",
        ),
    )

    manifest_loader = ManifestLoader(manifest_path)
    manifest_loader.load()

    app.state.manifest_loader = manifest_loader
    app.state.integration_client = IntegrationClient()
    app.state.tool_metrics: dict[str, dict[str, Any]] = {}

    logger.info(
        "Integration manifest loaded: %s (%d tools)",
        manifest_path,
        len(app.state.manifest_loader.tools),
    )

    try:
        yield
    finally:
        # Close httpx connection pool
        client: IntegrationClient = app.state.integration_client
        await client.close()


app = FastAPI(
    title="Foundry MCP Integration Gateway",
    version="0.1.0",
    description="Bridges MCP tool calls to n8n workflows via a manifest contract.",
    lifespan=lifespan,
)


def _serialize_tool(tool) -> dict[str, Any]:
    return {
        "toolName": tool.toolName,
        "displayName": tool.displayName,
        "description": tool.description,
        "category": tool.category,
        "logo": tool.logo,
        "tags": tool.tags,
        "metadata": tool.metadata.model_dump(exclude_none=True),
    }


def _get_metrics(app_state, tool_name: str) -> dict[str, Any]:
    metrics = app_state.tool_metrics.setdefault(tool_name, {"success": 0, "failure": 0, "last_error": None})
    return metrics


@app.get("/health")
async def health(request: Request) -> dict[str, Any]:
    """Simple health probe for Docker/K8s."""
    loader: ManifestLoader = request.app.state.manifest_loader
    metrics: dict[str, Any] = request.app.state.tool_metrics
    return {
        "service": "mcp-integration",
        "status": "ok",
        "tool_count": len(loader.tools),
        "manifest_path": loader.manifest_path,
        "tools": metrics,
    }


@app.get("/tools")
async def list_tools(request: Request) -> dict[str, Any]:
    loader: ManifestLoader = request.app.state.manifest_loader
    return {"items": [_serialize_tool(tool) for tool in loader.tools.values()]}


@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str, request: Request) -> dict[str, Any]:
    loader: ManifestLoader = request.app.state.manifest_loader
    try:
        tool = loader.get(tool_name)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _serialize_tool(tool) | {
        "inputSchema": tool.inputSchema.model_dump(),
        "outputSchema": tool.outputSchema.model_dump(),
        "examples": [example.model_dump() for example in tool.examples],
    }


@app.post("/tools/{tool_name}/invoke")
async def invoke_tool(
    tool_name: str,
    request: Request,
    payload: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    loader: ManifestLoader = request.app.state.manifest_loader
    client: IntegrationClient = request.app.state.integration_client

    try:
        manifest = loader.get(tool_name)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    try:
        validate_payload(payload, manifest.inputSchema)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_INPUT", "detail": str(exc)},
        )

    try:
        response = await client.invoke(manifest, payload)
    except httpx.HTTPError as exc:
        metrics = _get_metrics(request.app.state, manifest.toolName)
        metrics["failure"] += 1
        metrics["last_error"] = str(exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "N8N_UNAVAILABLE", "detail": str(exc)},
        )

    if response.status_code >= 400:
        metrics = _get_metrics(request.app.state, manifest.toolName)
        metrics["failure"] += 1
        metrics["last_error"] = response.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "N8N_ERROR",
                "status": response.status_code,
                "detail": response.text,
            },
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "N8N_INVALID_JSON", "detail": str(exc)},
        )

    try:
        validate_payload(data, manifest.outputSchema)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "INVALID_OUTPUT", "detail": str(exc)},
        )

    metrics = _get_metrics(request.app.state, manifest.toolName)
    metrics["success"] += 1
    metrics["last_error"] = None

    return {"tool": manifest.toolName, "data": data}
