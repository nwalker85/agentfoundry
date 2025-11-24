# Engineering Department — Testing Guide

**Version:** 2.1 (v0.7.0 Update)  
**Last Updated:** November 12, 2025  
**System:** Engineering Department MCP Server v0.7.0  
**Test Environment:** http://localhost:8001 (backend), http://localhost:3000
(frontend)

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Quick Validation Commands](#quick-validation-commands)
3. [Test Suites](#test-suites)
4. [User Acceptance Testing (UAT)](#user-acceptance-testing-uat)
5. [Testing Strategy & Framework](#testing-strategy--framework)
6. [Troubleshooting](#troubleshooting)
7. [Test Automation & CI/CD](#test-automation--cicd)

---

## Quick Start

### Prerequisites

Ensure your `.env.local` has:

- `OPENAI_API_KEY` (required for LangGraph agent)
- `NOTION_API_TOKEN` (required for story creation)
- `GITHUB_TOKEN` (required for issue creation)
- `NOTION_DATABASE_STORIES_ID`
- `NOTION_DATABASE_EPICS_ID`
- `GITHUB_REPO` (format: `owner/repo`)

### Start the MCP Server

```bash
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
source venv/bin/activate
python mcp_server.py
```

Expected output:

```
🚀 Starting Engineering Department MCP Server...
✅ Notion tool initialized
✅ GitHub tool initialized
✅ Audit tool initialized
INFO: Uvicorn running on http://0.0.0.0:8001
```

---

## Quick Validation Commands

### Health Checks

```bash
# Check server health
curl http://localhost:8001/

# Expected: {"status": "healthy", "version": "v0.2.0"}
```

```bash
# Check tool availability
curl http://localhost:8001/api/status

# Expected: {"api_version": "v1", "status": "operational", "tools_available": {...}}
```

```bash
# Get tool schemas
curl http://localhost:8001/api/tools/schema
```

### Quick Story Creation Test

```bash
# Create a test story
curl -X POST http://localhost:8001/api/tools/notion/create-story \
  -H "Content-Type: application/json" \
  -d '{
    "epic_title": "Test Epic",
    "story_title": "Test Story",
    "priority": "P2",
    "acceptance_criteria": ["AC 1", "AC 2"],
    "definition_of_done": ["DoD 1", "DoD 2"]
  }'
```

### Quick Story List Test

```bash
# List top priority stories
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "priorities": ["P0", "P1"]}'
```

### Quick Audit Query Test

```bash
# Query recent audit logs
curl "http://localhost:8001/api/tools/audit/query?tool=notion&limit=10"
```

### Quick Agent Test

```bash
# Test LangGraph PMAgent
python -c "
from agent.pm_graph import PMAgent
import asyncio

async def test():
    agent = PMAgent()
    result = await agent.process_message('Create P1 story for health check endpoint in Monitoring epic')
    print('Status:', result['status'])
    print('Messages:', len(result.get('messages', [])))
    print('Story URL:', result.get('story_url'))
    await agent.close()

asyncio.run(test())
"
```

---

## Test Suites

### Suite 1: E2E Integration Test (Recommended)

Tests the full MCP server stack via HTTP.

```bash
# In a new terminal
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
source venv/bin/activate

# Run E2E tests
pytest tests/e2e/ -v

# Or use the test runner
./run_tests.sh e2e
```

**What it tests:**

1. Server health and tool availability
2. Story creation with idempotency
3. GitHub issue creation
4. Idempotency protection verification
5. Story listing with filters
6. Audit trail validation
7. PM agent workflow

**Expected output:**

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

### Suite 2: Integration Tests

Tests component interactions and external services.

```bash
# Run all integration tests
pytest tests/integration/ -v

# Or use the test runner
./run_tests.sh integration

# Run specific integration test
pytest tests/integration/test_notion.py -v
pytest tests/integration/test_langgraph_agent.py -v
```

### Suite 3: Unit Tests

Tests individual functions and classes (planned).

```bash
# Run unit tests
pytest tests/unit/ -v

# Or use the test runner
./run_tests.sh unit
```

### Suite 4: UAT Tests

User acceptance testing suite.

```bash
# Run UAT
pytest tests/uat/ -v

# Or use the test runner
./run_tests.sh uat

# Or run directly
python tests/uat/uat_runner.py
```

### Suite 5: Run All Tests

```bash
# Run all tests with pytest
pytest tests/ -v

# Or use the test runner
./run_tests.sh all

# With coverage
pytest tests/ -v --cov=agent --cov=mcp --cov-report=html

# Or use test runner with coverage
./run_tests.sh all --cov
```

---

## User Acceptance Testing (UAT)

### UAT Overview

**Purpose:** Validate that the Engineering Department system meets business
requirements for story creation, task management, and automated GitHub
integration.

**Duration:** ~30 minutes  
**Environment:** http://localhost:8001

**Scope:**

- Story creation in Notion
- GitHub issue generation
- Idempotency protection
- Audit trail functionality
- PM Agent automation

**Out of Scope:**

- WebSocket real-time features (Phase 4)
- Multi-agent orchestration (Phase 5)
- Production performance testing

---

### Test Cases

#### TC-001: Basic Story Creation

**Priority:** P0 - Critical  
**Time:** 3 minutes

**Steps:**

1. Send POST to `/api/tools/notion/create-story`
2. Use payload:

```json
{
  "epic_title": "Q4 Platform Goals",
  "story_title": "Implement user authentication",
  "priority": "P1",
  "description": "Add OAuth2 authentication for users",
  "acceptance_criteria": [
    "Users can sign in with Google",
    "Sessions persist for 24 hours",
    "Logout invalidates tokens"
  ],
  "definition_of_done": [
    "Code reviewed",
    "Tests passing",
    "Documentation updated"
  ]
}
```

**Expected Results:**

- [ ] HTTP 200 response
- [ ] Response contains `story_id`
- [ ] Response contains `story_url`
- [ ] Response contains `idempotency_key`
- [ ] Story visible in Notion workspace

**cURL Command:**

```bash
curl -X POST http://localhost:8001/api/tools/notion/create-story \
  -H "Content-Type: application/json" \
  -d '{
    "epic_title": "Q4 Platform Goals",
    "story_title": "Implement user authentication",
    "priority": "P1",
    "description": "Add OAuth2 authentication for users",
    "acceptance_criteria": ["Users can sign in with Google", "Sessions persist for 24 hours"],
    "definition_of_done": ["Code reviewed", "Tests passing"]
  }'
```

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-002: Idempotency Protection

**Priority:** P0 - Critical  
**Time:** 2 minutes

**Steps:**

1. Repeat exact same request from TC-001
2. Compare response with TC-001

**Expected Results:**

- [ ] Same `story_id` as TC-001
- [ ] Same `idempotency_key` as TC-001
- [ ] No new story created in Notion
- [ ] Response time < 500ms (cached)

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-003: GitHub Issue Creation

**Priority:** P0 - Critical  
**Time:** 3 minutes

**Steps:**

1. Copy `story_url` from TC-001
2. Send POST to `/api/tools/github/create-issue`
3. Use payload:

```json
{
  "title": "[P1] Implement user authentication",
  "body": "## Description\nAdd OAuth2 authentication for users\n\n## Acceptance Criteria\n- [ ] Users can sign in with Google\n- [ ] Sessions persist for 24 hours\n- [ ] Logout invalidates tokens\n\n## Definition of Done\n- [ ] Code reviewed\n- [ ] Tests passing\n- [ ] Documentation updated",
  "labels": ["priority/P1", "source/agent-pm"],
  "story_url": "<INSERT_STORY_URL_FROM_TC-001>"
}
```

**Expected Results:**

- [ ] HTTP 200 response
- [ ] Response contains `issue_number`
- [ ] Response contains `issue_url`
- [ ] Issue visible in GitHub repository
- [ ] Issue contains link to Notion story

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-004: Story Listing and Filtering

**Priority:** P1 - High  
**Time:** 2 minutes

**Steps:**

1. Send POST to `/api/tools/notion/list-stories`
2. Filter by P0/P1 priorities

**cURL Command:**

```bash
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "priorities": ["P0", "P1"]}'
```

**Expected Results:**

- [ ] HTTP 200 response
- [ ] Returns array of stories
- [ ] All stories have P0 or P1 priority
- [ ] Story from TC-001 appears in list

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-005: Audit Trail Verification

**Priority:** P1 - High  
**Time:** 2 minutes

**Steps:**

1. Query audit logs for Notion tool

**cURL Command:**

```bash
curl "http://localhost:8001/api/tools/audit/query?tool=notion&limit=10"
```

**Expected Results:**

- [ ] HTTP 200 response
- [ ] Contains entries for TC-001 story creation
- [ ] Each entry has timestamp
- [ ] Each entry has request_id
- [ ] Input/output hashes present

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-006: PM Agent End-to-End

**Priority:** P1 - High  
**Time:** 5 minutes

**Steps:**

```bash
python -c "
from agent.pm_graph import PMAgent
import asyncio

async def test():
    agent = PMAgent()
    result = await agent.process_message(
        'Create a story for adding monitoring dashboard. '
        'This is part of the Observability epic with P2 priority.'
    )
    print('Status:', result['status'])
    print('Messages:', len(result.get('messages', [])))
    print('Story URL:', result.get('story_url'))
    print('Issue URL:', result.get('issue_url'))
    await agent.close()

asyncio.run(test())
"
```

**Expected Results:**

- [ ] LangGraph agent processes request with GPT-4
- [ ] Story created in Notion
- [ ] Issue created in GitHub
- [ ] Both URLs returned
- [ ] Conversation messages logged
- [ ] Status shows "completed"

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-007: Error Handling

**Priority:** P2 - Medium  
**Time:** 3 minutes

**Steps:**

1. Send invalid payload (missing required fields)

```json
{
  "story_title": "Test story without epic"
}
```

**Expected Results:**

- [ ] HTTP 422 or 400 response
- [ ] Error message describes missing fields
- [ ] No story created
- [ ] Error logged in audit trail

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-008: Backlog View UI

**Priority:** P1 - High  
**Time:** 5 minutes

**Steps:**

1. Navigate to http://localhost:3000/backlog
2. Verify stories load from Notion
3. Test priority filters (P0, P1, P2, P3)
4. Test status filters (Backlog, Ready, In Progress, etc.)
5. Test search functionality
6. Verify story cards display correctly
7. Test external links to Notion and GitHub
8. Test mobile responsive behavior

**Expected Results:**

- [ ] Backlog page loads without errors
- [ ] Stories display in card format
- [ ] Filters work correctly (priority, status, epic)
- [ ] Search filters stories in real-time
- [ ] Story cards show:
  - [ ] Title
  - [ ] Epic (if assigned)
  - [ ] Priority badge
  - [ ] Status badge
  - [ ] Created date
  - [ ] Links to Notion and GitHub (if available)
- [ ] Mobile view collapses filters appropriately
- [ ] Dark mode renders correctly

**Manual Test Commands:**

```bash
# Start frontend
npm run dev

# Navigate to:
http://localhost:3000/backlog

# Test filtering:
# 1. Click P0 checkbox
# 2. Verify only P0 stories shown
# 3. Click "Ready" status
# 4. Verify only Ready + P0 stories shown
# 5. Clear filters and search "auth"
# 6. Verify only stories with "auth" in title/epic shown
```

**Status:** ⬜ PASS / ⬜ FAIL

---

#### TC-009: Concurrent Requests

**Priority:** P2 - Medium  
**Time:** 3 minutes

**Steps:**

1. Send 3 different story creation requests simultaneously
2. Verify all complete successfully

**Expected Results:**

- [ ] All 3 requests succeed
- [ ] 3 different stories created
- [ ] 3 different idempotency keys
- [ ] All appear in audit log

**Status:** ⬜ PASS / ⬜ FAIL

---

### Acceptance Criteria Summary

**Critical (Must Pass):**

- [ ] TC-001: Basic Story Creation
- [ ] TC-002: Idempotency Protection
- [ ] TC-003: GitHub Issue Creation

**Important (Should Pass):**

- [ ] TC-004: Story Listing
- [ ] TC-005: Audit Trail
- [ ] TC-006: PM Agent E2E

**Nice to Have:**

- [ ] TC-007: Error Handling
- [ ] TC-008: Concurrent Requests

---

### UAT Completion Criteria

- [ ] All P0 tests passed
- [ ] At least 75% of P1 tests passed
- [ ] No critical defects remain open
- [ ] Audit trail functioning
- [ ] Idempotency verified

---

### Test Execution Report Template

**Test Session Information:**

- Tester Name: **********\_\_\_**********
- Test Date: **********\_\_\_**********
- Start Time: **********\_\_\_**********
- End Time: **********\_\_\_**********
- Environment: ⬜ Local / ⬜ Staging / ⬜ Other

**Test Results:**

| Test Case | Priority | Status            | Notes |
| --------- | -------- | ----------------- | ----- |
| TC-001    | P0       | ⬜ PASS / ⬜ FAIL |       |
| TC-002    | P0       | ⬜ PASS / ⬜ FAIL |       |
| TC-003    | P0       | ⬜ PASS / ⬜ FAIL |       |
| TC-004    | P1       | ⬜ PASS / ⬜ FAIL |       |
| TC-005    | P1       | ⬜ PASS / ⬜ FAIL |       |
| TC-006    | P1       | ⬜ PASS / ⬜ FAIL |       |
| TC-007    | P2       | ⬜ PASS / ⬜ FAIL |       |
| TC-008    | P1       | ⬜ PASS / ⬜ FAIL |       |
| TC-009    | P2       | ⬜ PASS / ⬜ FAIL |       |

**Statistics:**

- Total Tests: 9
- Passed: **\_**
- Failed: **\_**
- Pass Rate: **\_**%

---

## Testing Strategy & Framework

### Testing Philosophy

**POC Phase:** "Test the conversation, not the plumbing"

- Focus on conversational quality
- Validate user satisfaction
- Prioritize user experience over technical details

**Production Phase:** "Test autonomous decisions and business outcomes"

- Validate autonomous operation
- Test business value delivery
- Ensure compliance and governance

---

### Test Architecture

#### Current (Phase 3)

```
Level 1: Integration Tests (pytest + httpx)
           ↓ Validates agent-MCP flow
Level 2: Unit Tests (pytest)
           ↓ Validates components
Level 3: Contract Tests (JSON Schema)
           ↓ Validates API contracts
```

#### Planned (Phase 4+)

```
Level 0: Business Outcome Tests
           ↓ Validates business value delivery
Level 1: Multi-Agent Orchestration Tests
           ↓ Validates agent coordination
Level 2: Agent Decision Tests (LangChain Evals)
           ↓ Validates individual agent quality
Level 3: Integration Tests (pytest + Testcontainers)
           ↓ Validates system integration
Level 4: Chaos Engineering (Chaos Monkey)
           ↓ Validates resilience
Level 5: Load Tests (Locust)
           ↓ Validates scale
```

---

### Test Frameworks & Tools

**Current Stack:**

- **pytest** - Unit and integration testing
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for integration tests
- **JSON Schema** - Contract validation

**Planned Additions:**

- **Behave** - BDD / Gherkin for conversational tests
- **Playwright** - UI testing
- **Locust** - Load testing
- **LangChain Evals** - Agent quality testing
- **Chaos Monkey** - Resilience testing

---

### Testing Best Practices

#### POC Testing Principles

1. **User-first:** Test what users experience, not implementation
2. **Conversation corpus:** Build from real examples
3. **Fast feedback:** Sub-second unit tests, <5s integration tests
4. **Persona-based:** Separate tests for different user types
5. **Forgiveness:** Allow multiple valid responses

#### Production Testing Principles

1. **Business outcomes:** Test value delivery, not just functionality
2. **Autonomous operation:** Test decisions without human input
3. **Chaos engineering:** Regularly break things in staging
4. **Compliance-first:** Every test validates governance
5. **Scale assumptions:** Test at 10x expected load

---

### Test Metrics

#### POC Targets

- **Conversation Success Rate:** >85%
- **Average Clarifications:** <2
- **Response Time P95:** <3s
- **Test Coverage:** >80%

#### Production Targets

- **System Availability:** 99.99%
- **Autonomous Success Rate:** >90%
- **MTTR:** <15 minutes
- **Compliance Score:** 100%
- **Cost per Feature:** <$5000

---

## Troubleshooting

### Common Issues

| Symptom                  | Possible Cause             | Solution              |
| ------------------------ | -------------------------- | --------------------- |
| Connection refused       | Server not running         | Start MCP server      |
| 401 Unauthorized         | Missing auth header        | Check .env.local      |
| 500 Server Error         | Tool initialization failed | Check API tokens      |
| Notion story not visible | Wrong workspace            | Verify database IDs   |
| GitHub issue not created | Invalid repo               | Check GITHUB_REPO env |
| Agent not initialized    | Missing OpenAI key         | Check OPENAI_API_KEY  |

### Debug Commands

```bash
# Check server logs
tail -f audit/actions_*.jsonl

# Verify environment variables
python -c "import os; print(os.getenv('NOTION_API_TOKEN', 'NOT SET'))"
python -c "import os; print(os.getenv('OPENAI_API_KEY', 'NOT SET'))"

# Test Notion connection
python test_notion.py

# Check Python dependencies
pip list | grep -E '(fastapi|langchain|openai)'
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Check for version conflicts
pip check
```

### Server Won't Start

```bash
# Check if port 8001 is in use
lsof -i :8001

# Kill existing process
kill -9 <PID>

# Or use a different port
uvicorn mcp_server:app --port 8002
```

### Tests Timing Out

```bash
# Increase timeout in test
pytest test_e2e.py --timeout=120

# Check OpenAI API status
curl https://status.openai.com/

# Verify OpenAI API key is set
echo $OPENAI_API_KEY

# Test LangGraph agent directly
python test_langgraph_agent.py
```

---

## Test Automation & CI/CD

### Local Development

```bash
# Run all tests
make test

# Run specific test file
pytest test_e2e.py -v

# Run with coverage
pytest --cov=agent --cov=mcp --cov-report=html

# Watch mode for TDD
ptw tests/ --clear

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

### Continuous Integration

**GitHub Actions workflow** (planned):

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run integration tests
        run: pytest test_e2e.py -v
        env:
          NOTION_API_TOKEN: ${{ secrets.NOTION_API_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Test Data Management

```
/tests/fixtures/
├── conversations/
│   ├── pm_examples.json        # PM language patterns
│   ├── dev_examples.json       # Developer patterns
│   └── ba_examples.json        # BA patterns
├── stories/
│   ├── valid_stories.json      # Expected to succeed
│   └── invalid_stories.json    # Expected to fail
└── responses/
    └── expected_responses.json  # Golden responses
```

---

## Success Criteria

All tests should show:

```
✅ Server Health Check
✅ API Status Check
✅ Basic Story Creation
✅ Idempotency Protection
✅ GitHub Issue Creation
✅ Agent E2E Workflow

🎉 ALL TESTS PASSED!
   The MCP Server with PM Agent is fully operational!
```

---

## Next Steps

### Phase 4 Testing Enhancements

- [ ] Add Behave for BDD conversational tests
- [ ] Implement Playwright for UI testing
- [ ] Add performance benchmarking
- [ ] Set up CI/CD pipeline
- [ ] Create test dashboard

### Phase 5 Advanced Testing

- [ ] Multi-agent orchestration tests
- [ ] Chaos engineering in staging
- [ ] Load testing with Locust
- [ ] Compliance test suite
- [ ] Autonomous test generation

---

_Testing Guide Version 2.1 - v0.7.0 Update_  
_Last Updated: November 12, 2025_  
_Includes: Backlog View UI Testing (TC-008)_
