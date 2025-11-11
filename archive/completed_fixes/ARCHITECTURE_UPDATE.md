# Engineering Department - Architecture Update

## Critical Change: GitHub is for Code, Not Issues

### Previous Architecture (INCORRECT)
```
Notion (Stories) → GitHub Issues → Code Development
```

### Corrected Architecture (CORRECT)
```
Notion (Complete Project Management) 
    ↓
Developer picks up story
    ↓
GitHub (Code Management Only)
```

## Tool Responsibilities

### ✅ Notion - Complete Project Management
- **Epics** - High-level feature organization
- **Stories** - Detailed work items
- **Issue Tracking** - All issues stay in Notion
- **Sprint Planning** - Backlog management
- **Status Tracking** - Ready, In Progress, Done
- **Acceptance Criteria** - Definition of done
- **Story Points** - Estimation
- **Assignment** - Who's working on what

### ✅ GitHub - Code Management Only
- **Repository Operations**
  - Clone repository
  - Pull latest changes
  - Create feature branches
  - Commit code changes
  - Push to remote
  - Create pull requests
- **Code Review** - Via PRs
- **Version Control** - Git history
- **CI/CD** - Actions/workflows

### ❌ What GitHub Does NOT Do
- **No Issue Creation** - Issues stay in Notion
- **No Project Management** - That's Notion's job
- **No Sprint Planning** - Handled in Notion
- **No Story Tracking** - All in Notion

## Updated PM Agent Workflow

```python
1. Understand user request
2. Create/find epic in Notion
3. Create story in Notion
4. ✅ STOP - No GitHub issue creation
5. Story ready for development in Notion backlog
```

## Developer Workflow

```python
1. Check Notion backlog for stories
2. Pick up a story (mark "In Progress")
3. Use GitHub for code:
   - Clone/pull repo
   - Create feature branch
   - Write code
   - Commit and push
   - Create PR
4. Update story status in Notion
5. Link PR in Notion (optional)
```

## Implementation Changes

### Files Updated
1. **`github_repo.py`** - New tool for repository operations
2. **`pm_graph.py`** - Removed GitHub issue creation
3. **Workflow removed**: `create_story` → ~~`create_issue`~~ → `complete`

### Files Deprecated
- `github.py` - Issue management tool (not needed)

## Benefits of This Architecture

1. **Single Source of Truth** - Notion is the only place for project management
2. **Clear Separation** - Project management vs code management
3. **No Duplication** - No sync issues between Notion and GitHub Issues
4. **Simpler Workflow** - Fewer integration points
5. **Better for POC** - Focus on core value proposition

## Testing

```bash
# Test repository operations (not issues)
python test_github_repo_ops.py

# Test PM Agent (creates stories in Notion only)
python test_pm_agent.py
```

## Environment Variables

```bash
# GitHub configuration (for code operations)
GITHUB_TOKEN=<your_token>
GITHUB_REPO=nwalker85/engineeringdepartment  # Fixed repo name
GITHUB_DEFAULT_BRANCH=main
GITHUB_WORKSPACE_DIR=/tmp/github_workspace  # Local clone location

# Notion configuration (for all project management)
NOTION_API_TOKEN=<your_token>
NOTION_DATABASE_STORIES_ID=<stories_db_id>
NOTION_DATABASE_EPICS_ID=<epics_db_id>
```

## Summary

The Engineering Department system now correctly separates concerns:
- **Notion** = Where work is planned, tracked, and managed
- **GitHub** = Where code is stored, versioned, and reviewed

This is a cleaner, more maintainable architecture that aligns with industry best practices.
