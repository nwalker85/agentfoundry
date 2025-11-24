import sys
import types

import pytest
from fastapi.testclient import TestClient

if "psycopg" not in sys.modules:
    psycopg_module = types.ModuleType("psycopg")
    psycopg_module.connect = lambda *args, **kwargs: None  # type: ignore
    psycopg_module.Connection = object  # type: ignore

    rows_module = types.ModuleType("psycopg.rows")
    rows_module.dict_row = lambda *args, **kwargs: None  # type: ignore

    psycopg_module.rows = rows_module  # type: ignore[attr-defined]

    sys.modules["psycopg"] = psycopg_module
    sys.modules["psycopg.rows"] = rows_module

import backend.main as main


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    async def fake_integration_request(method: str, path: str, **kwargs):
        if path == "/tools":
            return {
                "items": [
                    {
                        "toolName": "slack.postMessage",
                        "displayName": "Slack · Post Message",
                        "description": "Send a message in Slack",
                        "category": "messaging",
                        "logo": "slack",
                        "tags": ["messaging"],
                        "metadata": {"docsUrl": "https://api.slack.com"},
                    }
                ]
            }
        if path == "/health":
            return {
                "tools": {
                    "slack.postMessage": {"success": 5, "failure": 0, "last_error": None}
                }
            }
        raise AssertionError(f"Unexpected integration request {method} {path}")

    monkeypatch.setattr(main, "_integration_request", fake_integration_request)
    return TestClient(main.app)


def test_catalog_merges_health(client: TestClient):
    response = client.get("/api/integrations/tools")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["toolName"] == "slack.postMessage"
    assert item["health"]["success"] == 5
    assert item["health"]["failure"] == 0

