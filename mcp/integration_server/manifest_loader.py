"""Utilities for loading and caching the integrations manifest."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ToolManifest


class ManifestLoader:
    """Reads and validates the manifest file declared in docs."""

    def __init__(self, manifest_path: str) -> None:
        self.manifest_path = manifest_path
        self.tools: dict[str, ToolManifest] = {}

    def load(self) -> None:
        """(Re)load manifest into memory."""
        path = Path(self.manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Integrations manifest not found: {path}")

        raw = json.loads(path.read_text())
        manifests: list[ToolManifest] = [ToolManifest.model_validate(obj) for obj in raw]

        self.tools = {manifest.normalized_name(): manifest for manifest in manifests}

    def get(self, tool_name: str) -> ToolManifest:
        """Fetch a tool, raising KeyError if missing."""
        key = tool_name.lower()
        if key not in self.tools:
            raise KeyError(f"Unknown tool '{tool_name}' in integrations manifest")
        return self.tools[key]
