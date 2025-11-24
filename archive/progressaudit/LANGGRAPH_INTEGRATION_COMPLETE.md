# LangGraph Agent Integration — Changes & Testing Guide

**Date:** November 10, 2025  
**Change Type:** Critical Fix — Switch to LangGraph Agent  
**Files Modified:** 2 files  
**Files Created:** 1 test file

---

## Changes Made

### 1. Modified `mcp_server.py`

**Import Change:**

```python
# OLD (Simple Agent)
from agent.simple_pm import SimplePMAgent

# NEW (LangGraph Agent)
from agent.pm_graph import PMAgent
```

**Type Annotation Change:**

```python
# OLD
pm_agent: Optional[SimplePMAgent] = None

# NEW
pm_agent: Optional[PMAgent] = None
```

**Initialization Change:**

```python
# OLD
pm_agent = SimplePMAgent()
print("✅ PM Agent initialized")

# NEW
pm_agent = PMAgent()
print("✅ LangGraph PM Agent initialized")
```

**Version Bump:**

```python
# OLD
version="0.3.0"

# NEW
version="0.4.0"  # Using LangGraph agent
```

**Changes Summary:**

- Line 23: Import changed from `SimplePMAgent` to `PMAgent`
- Line 32: Type annotation changed
- Line 60-63: Initialization changed with updated log message
- Line 83: Version bumped to 0.4.0
- Line 137: Version in root endpoint updated

---

### 2. Created `test_langgraph_agent.py`

**Purpose:** Comprehensive test suite for LangGraph agent

**Test Coverage:**

1. Import test — Can the agent be imported?
2. Initialization test — Can it be instantiated?
3. Graph structure test — Does it have the expected nodes?
4. Message processing test — Does it work end-to-end?

**Features:**

- Environment variable checks
- Graceful skipping if API keys not set
- Detailed output for debugging
- Full E2E test with actual OpenAI API call

---

## How to Test

### Prerequisites

Ensure your `.env.local` file has:

```bash
OPENAI_API_KEY=sk-...
NOTION_API_TOKEN=secret_...
NOTION_DATABASE_STORIES_ID=...
NOTION_DATABASE_EPICS_ID=...
GITHUB_TOKEN=ghp_...
GITHUB_REPO=username/repo
```

### Test 1: Run the LangGraph Agent Test Suite

```bash
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
source venv/bin/activate
python test_langgraph_agent.py
```

**Expected Output:**

```
============================================================
LangGraph PM Agent Test Suite
============================================================

📋 Environment Check:
   OPENAI_API_KEY: ✓ Set
   NOTION_API_TOKEN: ✓ Set
   GITHUB_TOKEN: ✓ Set

============================================================
Test 1: Import LangGraph PM Agent
============================================================
✅ PMAgent imported successfully

============================================================
Test 2: Initialize LangGraph PM Agent
============================================================
✅ PMAgent initialized successfully
   LLM Model: gpt-4
   MCP Base URL: http://localhost:8001

============================================================
Test 3: Verify LangGraph Structure
============================================================
✅ Agent has graph attribute
   Graph compiled successfully
   Expected nodes:
   - understand
   - clarify
   - validate
   - plan
   - create_story
   - create_issue
   - complete
   - error

============================================================
Test 4: Process Message with LangGraph Agent
============================================================

📝 Test Message:
   Create a story for adding a health check endpoint...

🤖 Processing with LangGraph agent...
   (This will call OpenAI API and may take 10-30 seconds)

✅ Agent completed processing!

📊 Result:
   Status: completed
   Error: None

💬 Agent Messages (5 messages):
   1. HumanMessage: Create a story for adding a health check endpoint...
   2. AIMessage: I'll create the story with these details:...
   3. AIMessage: ✅ Story created in Notion: https://notion.so/...
   4. AIMessage: ✅ GitHub issue created: https://github.com/...
   5. AIMessage: ✨ Story successfully created!...

🎯 Story Created: https://notion.so/...
🎯 Issue Created: https://github.com/...

✅ Message processing SUCCESSFUL

============================================================
Test Summary
============================================================
Passed: 4/4
✅ ALL TESTS PASSED - LangGraph agent is operational!
```

---

### Test 2: Start MCP Server with LangGraph Agent

```bash
cd "/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
source venv/bin/activate
python mcp_server.py
```

**Expected Startup Output:**

```
🚀 Starting Engineering Department MCP Server...
📊 Environment: development
🏢 Tenant ID: local-dev
✅ Notion tool initialized
✅ GitHub tool initialized
✅ Audit tool initialized
✅ LangGraph PM Agent initialized  ← CONFIRM THIS LINE

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**If you see this error:**

```
⚠️ PM Agent initialization failed: No module named 'langgraph'
```

**Fix:**

```bash
pip install langgraph langchain-openai langchain-core
```

---

### Test 3: Test Chat Endpoint with LangGraph Agent

**In a separate terminal:**

```bash
curl -X POST http://localhost:8001/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a story for adding rate limiting to the API. This should be under Infrastructure epic with P1 priority."
  }' | jq
```

**Expected Response:**

```json
{
  "messages": [
    {
      "type": "human",
      "content": "Create a story for adding rate limiting..."
    },
    {
      "type": "ai",
      "content": "I'll create the story with these details:\n- Epic: Infrastructure\n- Title: Add rate limiting to the API\n- Priority: P1\n..."
    },
    {
      "type": "ai",
      "content": "✅ Story created in Notion: https://notion.so/..."
    },
    {
      "type": "ai",
      "content": "✅ GitHub issue created: https://github.com/..."
    },
    {
      "type": "ai",
      "content": "✨ Story successfully created!\n\n**Notion Story:** ...\n**GitHub Issue:** ..."
    }
  ],
  "story_url": "https://notion.so/...",
  "issue_url": "https://github.com/...",
  "status": "completed"
}
```

---

### Test 4: Verify Server Status Shows LangGraph

```bash
curl http://localhost:8001/ | jq
```

**Expected Response:**

```json
{
  "service": "Engineering Department MCP Server",
  "version": "0.4.0",  ← CONFIRM VERSION BUMP
  "status": "healthy",
  "environment": "development",
  "tenant_id": "local-dev",
  "tools": {
    "notion": true,
    "github": true,
    "audit": true,
    "agent": true  ← CONFIRM AGENT AVAILABLE
  }
}
```

---

## What's Different Now?

### Before (Simple Agent)

- **Regex-based parsing** — Fragile, limited patterns
- **No clarification loop** — Can't ask follow-up questions
- **No validation** — Proceeds with incomplete data
- **Direct execution** — No planning phase
- **200 LOC** — Basic implementation

### After (LangGraph Agent)

- **LLM-powered understanding** — GPT-4 extracts task details
- **Multi-step clarification** — Up to 2 rounds of questions
- **Validation pipeline** — Checks requirements before proceeding
- **Planning phase** — Reviews task before execution
- **400 LOC** — Sophisticated state machine
- **Conditional routing** — Error handling, retry logic
- **Message history** — Full conversation context

---

## LangGraph Flow (What Happens Now)

1. **Understand** — LLM extracts epic, story, priority, AC, DoD
2. **Route** — If missing critical info → Clarify; else → Validate
3. **Clarify** — Ask user for missing details (max 2 rounds)
4. **Validate** — Confirm all required fields present
5. **Plan** — Review task, prepare for execution
6. **Create Story** — Call MCP Notion tool
7. **Create Issue** — Call MCP GitHub tool
8. **Complete** — Return summary with URLs

**Error handling at every step** — If anything fails, goes to error node and
reports back

---

## Troubleshooting

### "No module named 'langgraph'"

**Cause:** LangGraph not installed in venv

**Fix:**

```bash
source venv/bin/activate
pip install langgraph langchain-openai langchain-core
```

### "OPENAI_API_KEY not set"

**Cause:** Missing OpenAI API key

**Fix:** Add to `.env.local`:

```bash
OPENAI_API_KEY=sk-proj-...
```

### "PM Agent initialization failed: 401 Unauthorized"

**Cause:** Invalid OpenAI API key

**Fix:** Get valid key from https://platform.openai.com/api-keys

### Agent returns "awaiting_clarification"

**This is normal!** The LangGraph agent will ask for clarification if:

- Epic not specified
- Story title unclear
- No acceptance criteria mentioned

**Example clarification message:**

```
I need some clarification:
- Which epic should this story belong to?
- What are the acceptance criteria for this story?
```

You can then send another message with the details.

---

## Performance Expectations

### Response Times

**Simple Agent (Old):**

- Parsing: <10ms (regex)
- Total: 2-3 seconds (API calls only)

**LangGraph Agent (New):**

- Understanding: 2-5 seconds (LLM call)
- Validation: 1-2 seconds (LLM call if needed)
- Execution: 2-3 seconds (API calls)
- **Total: 5-10 seconds** (more intelligent, slower)

### API Costs

**Per Story Creation:**

- Understanding: ~500 tokens (input) + ~200 tokens (output)
- Validation: ~300 tokens (input) + ~100 tokens (output)
- **Total: ~1,100 tokens ≈ $0.01-0.02 per story** (GPT-4 pricing)

---

## Next Steps

### After Testing Confirms Working

1. **Update Current State.md**

   - Change status to "LangGraph agent operational"
   - Remove mention of "compatibility issues"

2. **Deprecate simple_pm.py**

   - Move to `archive/` or `tests/fixtures/`
   - Add comment: "Legacy testing scaffold - use pm_graph.py"

3. **Update documentation**

   - POC_SCOPE.md — Check off "LangGraph integration"
   - PROJECT_PLAN.md — Mark Phase 2 as complete

4. **Wire into Frontend** (Next sprint)
   - Create `/app/chat/page.tsx`
   - Connect to `/api/agent/chat` endpoint
   - Handle streaming responses
   - Display clarification prompts

---

## Summary

**Changed:** 5 lines of code in `mcp_server.py`  
**Result:** Now using sophisticated LangGraph agent instead of basic regex
agent  
**Benefit:**

- Conversational clarification loops
- LLM-powered parsing
- Validation pipeline
- Error handling
- Planning phase

**Cost:** 5-10 seconds per request instead of 2-3 seconds (due to LLM calls)

**Trade-off worth it?** YES — This was the entire point of the project.

---

**Changes Complete**  
**Ready for Testing**  
**Run:** `python test_langgraph_agent.py`
