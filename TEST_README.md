# Running E2E Tests

## Quick Start

The MCP server is already running on port 8001. To run the E2E tests:

```bash
# In a new terminal, navigate to the project directory
cd "/Users/nate/Development/1. Projects/Engineering Department"

# Activate the virtual environment
source venv/bin/activate

# Run the E2E test suite
python test_e2e.py
```

## What the Tests Do

1. **MCP Server Status Check** - Verifies server is running and tools are available
2. **Notion Story Creation** - Creates a test story with idempotency protection
3. **GitHub Issue Creation** - Creates corresponding GitHub issue
4. **Idempotency Test** - Verifies duplicate requests return same results
5. **Story Listing** - Queries top priority stories
6. **Audit Log Query** - Verifies all actions are logged
7. **PM Agent Test** - Tests the simplified PM agent workflow

## Troubleshooting

### If you see "Cannot connect to MCP server"
The server needs to be running in a separate terminal. It's currently running on PID 36264.

### If you see Pydantic/LangGraph errors
We've created a simplified PM agent (`agent/simple_pm.py`) that doesn't use LangGraph to avoid compatibility issues.

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### Missing Environment Variables
Check `.env.local` has:
- `NOTION_API_TOKEN`
- `NOTION_DATABASE_STORIES_ID`
- `NOTION_DATABASE_EPICS_ID`
- `GITHUB_TOKEN`
- `GITHUB_REPO`

## Current Server Status

The MCP server (v0.2.0) is running and provides:
- `/api/tools/notion/create-story` - Create Notion stories
- `/api/tools/notion/list-stories` - List top stories
- `/api/tools/github/create-issue` - Create GitHub issues
- `/api/tools/audit/query` - Query audit logs
- `/api/tools/schema` - Get tool schemas

## Architecture Notes

The implementation now includes:
- **Idempotency protection** via content-based hashing
- **Full audit trail** in JSONL format
- **Schema validation** with Pydantic models
- **Simplified PM agent** for immediate testing
- **RESTful MCP endpoints** with OpenAPI compatibility
