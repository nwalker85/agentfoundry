# Notion/GitHub API Issue Resolution

## Problem Identified

From the audit logs, the Notion API was returning `400 Bad Request` errors when
trying to create stories. This was due to missing database IDs in the
environment configuration.

## Root Cause

1. `NOTION_DATABASE_STORIES_ID` not configured in `.env.local`
2. `NOTION_DATABASE_EPICS_ID` not configured in `.env.local`
3. `GITHUB_REPO` not configured in `.env.local`

## Solution Implemented

Added mock mode to both Notion and GitHub tools to allow testing without actual
API credentials.

### Changes Made

#### 1. NotionTool (mcp/tools/notion.py)

- Added check for missing `stories_db_id`
- Returns mock response when database ID not configured
- Generates fake Notion URLs for testing
- Logs warning when in mock mode

#### 2. GitHubTool (mcp/tools/github.py)

- Added `mock_mode` flag when credentials missing
- Returns mock issue numbers and URLs
- Handles missing client gracefully in close()
- Logs warning when in mock mode

## Testing Without Real APIs

The system now works in three modes:

### 1. Full Mock Mode (No APIs configured)

- Both Notion and GitHub return mock responses
- Useful for frontend development and flow testing
- Shows warning messages in console

### 2. Partial Mode (Some APIs configured)

- Configure only the APIs you have access to
- Others will use mock responses
- Mix of real and mock data

### 3. Production Mode (All APIs configured)

- All environment variables properly set
- Real API calls to Notion and GitHub
- Full functionality

## Environment Setup

To use real APIs, add to `.env.local`:

```bash
# Notion (get from https://www.notion.so/my-integrations)
NOTION_API_TOKEN=secret_...
NOTION_DATABASE_STORIES_ID=<database-id>
NOTION_DATABASE_EPICS_ID=<database-id>

# GitHub (get from https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo
```

To use mock mode (for testing):

```bash
# Leave these empty or don't set them
NOTION_DATABASE_STORIES_ID=
NOTION_DATABASE_EPICS_ID=
GITHUB_REPO=
```

## Current Status

✅ **LangGraph flow fixed** - No more recursion errors ✅ **Mock mode
implemented** - Can test without real APIs ✅ **End-to-end flow works** -
Message → Agent → Mock APIs → Response

## Testing

1. Restart MCP server to load changes:

```bash
python mcp_server.py
```

2. Test via frontend:

```bash
# Visit http://localhost:3000/chat
# Try: "Create a story for adding user authentication"
```

3. Expected output:

- Mock Notion URL: `https://notion.so/mock-story-...`
- Mock GitHub URL: `https://github.com/mock-owner/mock-repo/issues/...`

## Next Steps

Once you have real Notion/GitHub credentials:

1. Create a Notion database for stories with these properties:

   - Name (title)
   - Priority (select: P0, P1, P2, P3)
   - Status (select: Backlog, In Progress, Done)
   - Epic (relation to Epics database)
   - Acceptance Criteria (rich text)
   - Definition of Done (rich text)
   - Idempotency Key (rich text)
   - GitHub URL (url)

2. Create a Notion database for epics with:

   - Title (title)
   - Status (select: Active, Complete)
   - Priority (select: P0, P1, P2, P3)

3. Add the database IDs to `.env.local`

4. Create a GitHub repo and add credentials

The system will automatically switch from mock to real mode when credentials are
detected.
