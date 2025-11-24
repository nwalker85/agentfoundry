from pathlib import Path

import pytest

from mcp.integration_server.manifest_loader import ManifestLoader


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.name == "agentfoundry":
            return parent
    raise RuntimeError("Could not locate repo root")


def fixture_manifest_path() -> Path:
    return repo_root() / "mcp" / "integration_server" / "config" / "integrations.manifest.json"


def test_manifest_loader_reads_tools():
    loader = ManifestLoader(str(fixture_manifest_path()))
    loader.load()

    assert len(loader.tools) == 3
    assert "slack.postmessage" in loader.tools


def test_manifest_loader_missing_file():
    loader = ManifestLoader("/does/not/exist.json")
    with pytest.raises(FileNotFoundError):
        loader.load()

