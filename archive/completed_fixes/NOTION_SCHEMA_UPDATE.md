# Notion Schema Update Implementation

## Overview

Updated the MCP Notion integration to align with the new database schemas
defined in the CSV imports.

## Changes Made

### 1. Updated Story Schema (`notion_import_stories.csv`)

**New Fields Supported:**

- `Title` - Story title (was "Name")
- `Epic` - Relation to epics database
- `User Story` - Standard user story format
- `Description` - Detailed description
- `Acceptance Criteria` - Success criteria
- `Status` - Ready/Backlog/In Progress/In Review/Done
- `Priority` - P0/P1/P2/P3
- `Story Points` - Numeric estimation (changed from select)
- `Sprint` - Sprint assignment
- `Technical Type` - Feature/Bug Fix/Tech Debt/Documentation
- `GitHub Issue` - URL field for issue link
- `GitHub PR` - URL field for PR link
- `Assignee` - Text field for assignment
- `AI Generated` - Checkbox for AI-created stories

**Status Mapping:**

- Removed: TODO, In QA
- Added: Ready (stories ready to start)
- Kept: Backlog, In Progress, In Review, Done

### 2. Updated Epic Schema (`notion_import_epics.csv`)

**New Fields Supported:**

- `Title` - Epic title
- `Description` - Epic description
- `Status` - Active/Planning/On Hold
- `Priority` - P0/P1/P2/P3
- `Target Quarter` - Q1 2025, Q2 2025, etc.
- `Business Value` - High/Medium/Low
- `Technical Area` - Backend/Frontend/Security/etc.
- `Created By` - PM Agent/Human

### 3. Implementation Enhancements

**Added Helper Methods:**

- `_determine_technical_type()` - Auto-categorizes stories
- `_estimate_story_points()` - Estimates based on complexity
- `_format_user_story()` - Generates standard user story format
- `_find_or_create_epic()` - Handles epic creation/lookup
- `update_story_github_url()` - Updates GitHub integration fields

**Improved Content Generation:**

- Stories now use to-do blocks for acceptance criteria
- Callout blocks for epic context
- Better structured page content
- Technical implementation sections

### 4. Schema File Updates

**Updated `mcp/schemas.py`:**

- Removed `TODO` and `IN_QA` statuses
- Added `READY` status
- Comments clarify Notion alignment

## Testing

Created `test_notion_schema.py` to validate:

1. Story creation with full schema
2. Epic creation/lookup
3. GitHub URL updates
4. Story retrieval and filtering

## Migration Steps

1. **Import CSVs to Notion:**

   - Import `notion_import_epics.csv` to Epics database
   - Import `notion_import_stories.csv` to Stories database
   - This will create proper field types and options

2. **Verify Database IDs:**

   - Stories: `2a6517b8b98e808bbe23f3c7ce5ac6fd`
   - Epics: `2a6517b8b98e80b99c13fb8d933e44cc`

3. **Test Integration:**
   ```bash
   python test_notion_schema.py
   ```

## Benefits

1. **Richer Data Model:** Supports sprint planning, technical categorization,
   and GitHub integration
2. **Better Tracking:** AI-generated flag, assignees, story points
3. **Improved Workflow:** Ready status for sprint planning
4. **Epic Management:** Full epic lifecycle with business value and technical
   areas
5. **GitHub Integration:** Direct links to issues and PRs

## Next Steps

1. Import CSV data to Notion databases
2. Run test suite to verify integration
3. Update PM agent to leverage new fields
4. Implement GitHub webhook for automatic URL updates
5. Add sprint planning capabilities

## Backward Compatibility

The implementation gracefully handles:

- Missing epic relations (creates new epics as needed)
- Empty GitHub fields (populated when issues created)
- Unassigned stories (for AI-generated content)
- Default values for all new fields

## Files Modified

- `/mcp/tools/notion.py` - Complete rewrite with new schema support
- `/mcp/schemas.py` - Updated status enum
- Created `/test_notion_schema.py` - Comprehensive test suite
- Created `/NOTION_SCHEMA_UPDATE.md` - This document
