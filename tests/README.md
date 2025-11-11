# Engineering Department Test Suite

**Last Updated:** November 10, 2025  
**Test Coverage:** Phase 3 - MCP Tools & Agent Integration

---

## Test Directory Structure

```
tests/
├── README.md                      # This file
├── unit/                          # Unit tests for individual components
│   └── (to be created)
├── integration/                   # Integration tests for service interactions
│   ├── test_notion.py            # Notion API integration tests
│   ├── test_langgraph_agent.py   # LangGraph agent integration tests
│   └── test_mcp_langgraph.py     # MCP + LangGraph integration tests
├── e2e/                           # End-to-end workflow tests
│   ├── test_e2e.py               # Full MCP server E2E tests
│   └── test_agent_detailed.py    # Detailed agent workflow tests
└── uat/                           # User Acceptance Testing
    └── uat_runner.py             # UAT test runner and automation
```

---

## Quick Start

### Prerequisites

```bash
# Ensure virtual environment is activated
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
source venv/bin/activate

# Ensure .env.local is configured with:
# - NOTION_API_TOKEN
# - NOTION_DATABASE_STORIES_ID
# - NOTION_DATABASE_EPICS_ID
# - GITHUB_TOKEN
# - GITHUB_REPO
# - OPENAI_API_KEY
```

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=agent --cov=mcp --cov-report=html

# Run specific test suite
pytest tests/integration/ -v
pytest tests/e2e/ -v
pytest tests/uat/ -v
```

---

## Test Suites

### Unit Tests (`tests/unit/`)

**Purpose:** Test individual functions and classes in isolation  
**Status:** Not yet created  
**Planned Coverage:**
- Agent message parsing
- Schema validation
- Idempotency key generation
- Audit log formatting

**Run:**
```bash
pytest tests/unit/ -v
```

---

### Integration Tests (`tests/integration/`)

**Purpose:** Test interactions between components and external services  
**Current Tests:**
- `test_notion.py` - Notion API integration (63 lines)
- `test_langgraph_agent.py` - LangGraph agent integration (218 lines)
- `test_mcp_langgraph.py` - MCP + LangGraph integration (13,242 lines)

**What they test:**
- Notion API connectivity and story creation
- LangGraph agent initialization and message processing
- MCP server endpoints with agent integration
- External API authentication and error handling

**Run:**
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/integration/test_notion.py -v

# Run with specific markers
pytest tests/integration/ -v -m "notion"
```

**Prerequisites:**
- MCP server must be running on port 8001
- Valid API credentials in `.env.local`
- Network access to external services

---

### End-to-End Tests (`tests/e2e/`)

**Purpose:** Test complete workflows from user input to final output  
**Current Tests:**
- `test_e2e.py` - Full MCP server workflow (9,453 lines)
- `test_agent_detailed.py` - Detailed agent workflows (1,997 lines)

**What they test:**
1. Server health and tool availability
2. Story creation with idempotency
3. GitHub issue creation with linking
4. Idempotency protection verification
5. Story listing with filters
6. Audit trail validation
7. PM agent end-to-end workflow

**Run:**
```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific test
pytest tests/e2e/test_e2e.py -v

# With detailed output
pytest tests/e2e/ -v -s
```

**Prerequisites:**
- MCP server must be running on port 8001
- All external services accessible
- Clean test data state

**Expected Output:**
```
✅ Test 1: MCP server is running
✅ Test 2: Notion story creation
✅ Test 3: GitHub issue creation
✅ Test 4: Idempotency protection
✅ Test 5: Story listing
✅ Test 6: Audit log query
✅ Test 7: PM agent workflow

🎉 ALL TESTS PASSED!
```

---

### User Acceptance Tests (`tests/uat/`)

**Purpose:** Validate system meets business requirements  
**Current Tests:**
- `uat_runner.py` - Automated UAT execution (611 lines)

**What it tests:**
- Business workflows from user perspective
- Acceptance criteria validation
- User experience validation
- Production readiness verification

**Run:**
```bash
# Run UAT suite
python tests/uat/uat_runner.py

# Or with pytest
pytest tests/uat/ -v
```

**See also:** `docs/TESTING_GUIDE.md` for detailed UAT test cases

---

## Test Configuration

### pytest.ini

Create `pytest.ini` in the project root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    uat: User acceptance tests
    slow: Slow tests (>5 seconds)
    notion: Tests that interact with Notion API
    github: Tests that interact with GitHub API
    agent: Tests for agent functionality
```

### conftest.py

Create `tests/conftest.py` for shared fixtures:

```python
import pytest
import asyncio
from typing import AsyncGenerator

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mcp_client() -> AsyncGenerator:
    """HTTP client for MCP server tests."""
    import httpx
    async with httpx.AsyncClient(base_url="http://localhost:8001") as client:
        yield client

@pytest.fixture
def sample_story_data():
    """Sample story data for tests."""
    return {
        "epic_title": "Test Epic",
        "story_title": "Test Story",
        "priority": "P2",
        "acceptance_criteria": ["AC 1", "AC 2"],
        "definition_of_done": ["DoD 1", "DoD 2"]
    }
```

---

## Test Execution Strategies

### Local Development

```bash
# Watch mode for TDD
ptw tests/ --clear

# Run specific markers
pytest tests/ -v -m "unit and not slow"

# Run failed tests only
pytest tests/ --lf

# Run tests in parallel
pytest tests/ -n auto
```

### Pre-Commit

```bash
# Run quick tests before commit
pytest tests/unit/ tests/integration/test_notion.py -v
```

### CI/CD Pipeline

```bash
# Full test suite with coverage
pytest tests/ -v \
  --cov=agent \
  --cov=mcp \
  --cov-report=xml \
  --cov-report=html \
  --junitxml=test-results.xml
```

---

## Writing New Tests

### Unit Test Template

```python
# tests/unit/test_example.py

import pytest
from agent.simple_pm import SimplePMAgent

class TestMessageParsing:
    """Test message parsing functionality."""
    
    def test_extract_epic_from_message(self):
        """Should extract epic name from user message."""
        agent = SimplePMAgent()
        message = "Create story in Auth epic"
        
        result = agent.parse_message(message)
        
        assert result["epic"] == "Auth"
    
    def test_extract_priority_from_message(self):
        """Should extract priority from user message."""
        agent = SimplePMAgent()
        message = "Create P1 story for login"
        
        result = agent.parse_message(message)
        
        assert result["priority"] == "P1"
```

### Integration Test Template

```python
# tests/integration/test_example.py

import pytest
import httpx

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_server_health():
    """Should return healthy status."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8001/")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### E2E Test Template

```python
# tests/e2e/test_example.py

import pytest
import httpx

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_story_workflow():
    """Should create story and issue end-to-end."""
    async with httpx.AsyncClient() as client:
        # Step 1: Create story
        story_response = await client.post(
            "http://localhost:8001/api/tools/notion/create-story",
            json={"epic_title": "Test", "story_title": "E2E Test"}
        )
        assert story_response.status_code == 200
        story_url = story_response.json()["story_url"]
        
        # Step 2: Create issue
        issue_response = await client.post(
            "http://localhost:8001/api/tools/github/create-issue",
            json={"title": "E2E Test", "story_url": story_url}
        )
        assert issue_response.status_code == 200
        
        # Step 3: Verify audit trail
        audit_response = await client.get(
            "http://localhost:8001/api/tools/audit/query?limit=1"
        )
        assert audit_response.status_code == 200
```

---

## Test Best Practices

### General Principles
1. **Isolation:** Each test should be independent
2. **Clarity:** Test names should describe what is being tested
3. **Speed:** Keep unit tests fast (<100ms), integration tests reasonable (<5s)
4. **Reliability:** Tests should be deterministic, not flaky
5. **Coverage:** Aim for >80% code coverage

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Use descriptive names: `test_should_return_error_when_missing_required_field`

### Assertions
- Use descriptive assertion messages
- Prefer specific assertions over generic ones
- Test one concept per test

### Fixtures
- Use fixtures for common setup
- Keep fixtures focused and composable
- Document fixture scope and purpose

### Mocking
- Mock external services in unit/integration tests
- Use real services in E2E tests
- Document what is mocked and why

---

## Troubleshooting Tests

### Common Issues

| Issue | Solution |
|-------|----------|
| Import errors | Ensure PYTHONPATH includes project root |
| Server not available | Start MCP server before running tests |
| Authentication errors | Check .env.local credentials |
| Timeout errors | Increase timeout or check service health |
| Flaky tests | Add retry logic or fix race conditions |

### Debug Commands

```bash
# Run with print statements visible
pytest tests/ -v -s

# Run with pdb on failure
pytest tests/ --pdb

# Run with detailed traceback
pytest tests/ --tb=long

# Run with warnings
pytest tests/ -v -W all
```

---

## Test Metrics

### Current Coverage
- **Integration Tests:** 3 files
- **E2E Tests:** 2 files
- **UAT Tests:** 1 file
- **Unit Tests:** 0 files (planned)

### Target Metrics
- **Code Coverage:** >80%
- **Test Pass Rate:** 100%
- **Test Execution Time:** <60 seconds (all tests)
- **Flakiness Rate:** <1%

---

## Next Steps

### Immediate
- [ ] Create unit tests for core functions
- [ ] Add pytest.ini configuration
- [ ] Create conftest.py with shared fixtures
- [ ] Add test markers for categorization

### Short-term
- [ ] Implement test data factories
- [ ] Add contract tests for APIs
- [ ] Create performance benchmarks
- [ ] Set up test coverage reporting

### Long-term
- [ ] Add BDD/Gherkin conversational tests
- [ ] Implement chaos engineering tests
- [ ] Add load testing with Locust
- [ ] Create self-validating test suite

---

## References

- [Testing Guide](../docs/TESTING_GUIDE.md) - Complete testing documentation
- [Project Status](../docs/PROJECT_STATUS.md) - Current implementation status
- [Architecture](../docs/ARCHITECTURE.md) - System architecture and design

---

*Test Suite Documentation - Engineering Department*  
*Last Updated: November 10, 2025*

