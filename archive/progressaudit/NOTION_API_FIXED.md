# Notion API Integration Fixed

## Problem

The Notion API was returning `400 Bad Request` when trying to create stories.
The error logs showed:

```
HTTPStatusError: Client error '400 Bad Request' for url 'https://api.notion.com/v1/pages'
```

## Root Cause

The Notion tool was trying to use database properties that don't exist in the
actual databases. The code assumed certain fields like "Epic" (relation),
"Definition of Done", and "Idempotency Key" that weren't configured in the
actual Notion databases.

## Solution Applied

### 1. Updated Property Mapping

Changed from assumed schema to actual schema:

- Removed: `Epic` (relation), `Definition of Done`, `Idempotency Key`
- Updated: `User Story` for description field
- Kept: `Name`, `Priority`, `Status`, `Acceptance Criteria`

### 2. Simplified Epic Handling

- Temporarily disabled epic relation creation
- Epic title now shown in page content instead of as a relation
- This avoids errors from missing relation fields

### 3. Added Error Logging

- Added detailed error logging to show actual API responses
- Logs the properties being sent for debugging
- Shows the exact error from Notion API

## Database IDs from URLs

From your provided URLs:

- **Stories Database ID**: `2a6517b8b98e808bbe23f3c7ce5ac6fd`
- **Epics Database ID**: `2a6517b8b98e80b99c13fb8d933e44cc`

These are correctly configured in `.env.local`.

## Current Status

The Notion integration should now work with the actual database schema. The tool
will:

1. Create stories with Name, Priority, Status
2. Add User Story and Acceptance Criteria as rich text fields
3. Include Epic title in the page content
4. Skip fields that don't exist in the database

## Testing

To test the fixes:

```bash
# Test Notion tool directly
python test_notion_tool.py

# Or test through the full system
python mcp_server.py
# Then use the chat interface or test_backend.py
```

## Next Steps

To fully utilize the Notion integration, you may want to:

1. **Update Notion Database Schema** - Add missing fields if needed:

   - Definition of Done (rich text)
   - GitHub URL (url)
   - Epic (relation to Epics database)

2. **Or Keep Current Schema** - The tool now works with existing fields

3. **Verify GitHub Integration** - The GitHub token and repo are configured
   correctly

## Files Modified

- `/mcp/tools/notion.py` - Fixed property mapping and error handling
- `/mcp/tools/github.py` - Reverted mock mode changes
- Created `/test_notion_tool.py` - Direct API test script

The integration should now work with real Notion and GitHub APIs.
