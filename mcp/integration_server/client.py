"""HTTP client for proxying MCP tool calls to n8n workflows."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .models import ToolManifest


class IntegrationClient:
    """Thin wrapper around httpx for calling n8n webhooks."""

    def __init__(self, base_timeout: float = 30.0) -> None:
        self.n8n_base_url = os.getenv("N8N_BASE_URL", "http://n8n:5678")
        self.timeout = base_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def invoke(self, manifest: ToolManifest, payload: dict[str, Any]) -> httpx.Response:
        """POST the payload to the manifest's configured webhook."""
        client = await self._get_client()
        return await client.post(
            manifest.n8n.url,
            json=payload,
            headers={
                "x-tool-name": manifest.toolName,
            },
            timeout=manifest.n8n.timeoutSeconds,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
