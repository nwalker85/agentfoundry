"""Shared pytest fixtures for Engineering Department tests."""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any
from pathlib import Path


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """MCP server base URL."""
    return os.getenv("MCP_SERVER_URL", "http://localhost:8001")


@pytest.fixture
async def mcp_client(base_url: str) -> AsyncGenerator:
    """HTTP client for MCP server tests."""
    import httpx
    
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=30.0,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture
def sample_story_data() -> Dict[str, Any]:
    """Sample story data for tests."""
    return {
        "epic_title": "Test Epic",
        "story_title": "Test Story",
        "priority": "P2",
        "description": "Test description",
        "acceptance_criteria": [
            "Acceptance criterion 1",
            "Acceptance criterion 2"
        ],
        "definition_of_done": [
            "Definition of done 1",
            "Definition of done 2"
        ]
    }


@pytest.fixture
def sample_issue_data() -> Dict[str, Any]:
    """Sample GitHub issue data for tests."""
    return {
        "title": "[P2] Test Issue",
        "body": "Test issue body",
        "labels": ["test", "automated"],
        "story_url": "https://notion.so/test-story"
    }


@pytest.fixture
def project_root() -> Path:
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def env_vars() -> Dict[str, str]:
    """Environment variables for tests."""
    return {
        "NOTION_API_TOKEN": os.getenv("NOTION_API_TOKEN", ""),
        "NOTION_DATABASE_STORIES_ID": os.getenv("NOTION_DATABASE_STORIES_ID", ""),
        "NOTION_DATABASE_EPICS_ID": os.getenv("NOTION_DATABASE_EPICS_ID", ""),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN", ""),
        "GITHUB_REPO": os.getenv("GITHUB_REPO", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
    }


@pytest.fixture
def check_env_vars(env_vars: Dict[str, str]) -> None:
    """Check that required environment variables are set."""
    missing = [key for key, value in env_vars.items() if not value]
    
    if missing:
        pytest.skip(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Check .env.local configuration."
        )


@pytest.fixture
def clean_test_data():
    """Fixture to clean up test data after tests."""
    # Setup: nothing needed
    yield
    # Teardown: clean up any test data
    # This would implement cleanup logic for test stories/issues
    pass


# Markers for categorizing tests
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "requires_server: mark test as requiring MCP server to be running"
    )
    config.addinivalue_line(
        "markers", "requires_notion: mark test as requiring Notion API access"
    )
    config.addinivalue_line(
        "markers", "requires_github: mark test as requiring GitHub API access"
    )
    config.addinivalue_line(
        "markers", "requires_openai: mark test as requiring OpenAI API access"
    )

