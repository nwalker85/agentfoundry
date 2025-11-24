import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from mcp.integration_server.client import IntegrationClient
from mcp.integration_server.main import app


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if parent.name == "agentfoundry":
            return parent
    raise RuntimeError("Could not locate repo root")


@pytest.fixture(scope="module")
def manifest_path() -> str:
    return str(repo_root() / "mcp" / "integration_server" / "config" / "integrations.manifest.json")


@pytest.fixture()
def test_client(monkeypatch: pytest.MonkeyPatch, manifest_path: str):
    previous = os.environ.get("INTEGRATIONS_MANIFEST")
    os.environ["INTEGRATIONS_MANIFEST"] = manifest_path
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if previous is None:
            os.environ.pop("INTEGRATIONS_MANIFEST", None)
        else:
            os.environ["INTEGRATIONS_MANIFEST"] = previous


def test_list_tools(test_client: TestClient):
    res = test_client.get("/tools")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 3


def test_invoke_tool_success(monkeypatch: pytest.MonkeyPatch, test_client: TestClient):
    async def fake_invoke(self, manifest, payload):
        return httpx.Response(
            status_code=200,
            json={"incidentId": "INC-1", "url": "https://snow.example.com/INC-1"},
        )

    monkeypatch.setattr(IntegrationClient, "invoke", fake_invoke, raising=False)

    payload = {"shortDescription": "VPN down", "priority": "P1"}
    res = test_client.post("/tools/servicenow.createIncident/invoke", json=payload)
    assert res.status_code == 200
    assert res.json()["tool"] == "servicenow.createIncident"


def test_invoke_tool_validation_error(test_client: TestClient):
    res = test_client.post("/tools/servicenow.createIncident/invoke", json={})
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["code"] == "INVALID_INPUT"

