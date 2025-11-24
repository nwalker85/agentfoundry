# Engineering Department - Consolidation Action Plan

## Executive Summary

This plan reduces ~10,650 lines across 44 files to a more maintainable structure
while closing critical gaps.

## Risk Assessment

### Critical Blockers

1. **No Chat UI** - POC cannot demonstrate without conversational interface
2. **No WebSocket/SSE** - Real-time feedback impossible
3. **No Docker** - Deployment friction high

### Technical Debt

- Documentation redundancy (~40% overlap)
- Duplicate utilities (Python + Shell versions)
- Test files scattered in root directory
- ~~LangGraph compatibility issues~~ ✅ Resolved (PMAgent operational v0.4.0)

## Consolidation Actions

### Phase 1: Documentation Consolidation (2 hours)

Run the consolidation script:

```bash
cd /Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment
python scripts/consolidate_docs.py
```

**Manual Steps After Script:**

1. Review consolidated files in `docs/` directory
2. Verify no information lost
3. Archive originals:

   ```bash
   mkdir -p archive/docs_backup_$(date +%Y%m%d)
   mv "Current State.md" "PROJECT_PLAN.md" "PROJECT_INVENTORY.md" archive/docs_backup_$(date +%Y%m%d)/
   mv "UAT_GUIDE.md" "TEST_README.md" "QUICK_TEST.md" archive/docs_backup_$(date +%Y%m%d)/
   ```

4. Fix `Environment C.md` corruption manually (remove duplicate blocks)

### Phase 2: Test Organization (1 hour)

```bash
# Create test structure
mkdir -p tests/{unit,integration,e2e,uat}

# Move test files
mv test_notion.py tests/integration/
mv test_langgraph_agent.py tests/integration/
mv test_mcp_langgraph.py tests/integration/
mv test_e2e.py tests/e2e/
mv test_agent_detailed.py tests/e2e/
mv uat_runner.py tests/uat/

# Update imports in moved files
find tests/ -name "*.py" -exec sed -i '' 's/from mcp/from ..mcp/g' {} \;
```

### Phase 3: Frontend Implementation (4 hours)

Run the frontend generator:

```bash
python scripts/create_frontend.py
```

Then update the MCP server with the new endpoint:

```python
# Add to mcp_server.py

@app.post("/api/agent/process")
async def process_agent_message(
    message: str = Body(...),
    session_id: str = Body(default="default")
) -> Dict:
    """Process message through PM agent"""
    from agent.pm_graph import PMAgent

    agent = PMAgent()
    result = await agent.process_message(message)

    return {
        "response": result.get("response", "Processing your request..."),
        "artifacts": result.get("artifacts", []),
        "session_id": session_id
    }
```

### Phase 4: Infrastructure Setup (2 hours)

```bash
# Build and run with Docker
docker-compose up --build

# Or run locally for development
# Terminal 1
python mcp_server.py

# Terminal 2
npm run dev
```

### Phase 5: Cleanup (30 minutes)

```bash
# Remove duplicates
rm check_git_status.sh  # Keep Python version

# Move utilities to scripts/
mv check_git_status.py scripts/
mv commit_helper.sh scripts/
mv start_server.sh scripts/
mv run_tests.sh scripts/

# Archive deprecated content
mv archive/ .archive_deprecated/
echo ".archive_deprecated/" >> .gitignore
```

## Validation Checklist

### After Documentation Consolidation

- [ ] `docs/PROJECT_STATUS.md` contains all key information
- [ ] `docs/TESTING_GUIDE.md` has all test procedures
- [ ] No duplicate information across documents
- [ ] Originals backed up before deletion

### After Test Organization

- [ ] All tests run from new locations
- [ ] Import paths updated correctly
- [ ] Test runner scripts updated

### After Frontend Implementation

- [ ] Chat page loads at http://localhost:3000/chat
- [ ] Messages send to MCP server
- [ ] Responses display in UI
- [ ] Artifacts (stories/issues) shown

### After Infrastructure Setup

- [ ] Docker image builds successfully
- [ ] Services start without errors
- [ ] Ports accessible (3000, 8001)
- [ ] Environment variables loaded

## Success Metrics

### Before Consolidation

- Files: 44 active
- Documentation: 16 files, ~5,700 lines
- Test files: Scattered in root
- Frontend: 20% complete
- Docker: Not implemented

### After Consolidation

- Files: ~35 active (-20%)
- Documentation: 6 files, ~3,000 lines (-48%)
- Test files: Organized in tests/
- Frontend: 60% complete (chat working)
- Docker: Fully containerized

## Time Estimate

| Phase             | Duration      | Priority     |
| ----------------- | ------------- | ------------ |
| Documentation     | 2 hours       | Medium       |
| Test Organization | 1 hour        | Low          |
| Frontend          | 4 hours       | **CRITICAL** |
| Infrastructure    | 2 hours       | High         |
| Cleanup           | 30 minutes    | Low          |
| **Total**         | **~10 hours** | -            |

## Immediate Next Steps (Do These First)

1. **Run frontend generator** (Critical for POC demo):

   ```bash
   python scripts/create_frontend.py
   ```

2. **Update MCP server** with agent endpoint

3. **Test the chat interface**:

   ```bash
   python mcp_server.py  # Terminal 1
   npm run dev          # Terminal 2
   # Visit http://localhost:3000/chat
   ```

4. **Only then** proceed with documentation consolidation

## Risk Mitigation

- **All changes reversible** - Backups created before modifications
- **Incremental approach** - Each phase independently executable
- **Validation steps** - Checklist ensures nothing breaks
- **Git safety** - Commit before each phase:
  ```bash
  git add -A && git commit -m "Pre-consolidation checkpoint"
  ```

## Notes

- ✅ LangGraph PMAgent is now operational (v0.4.0) - compatibility issues
  resolved
- Focus on user experience and frontend integration
- Documentation consolidation can wait if frontend is urgent
- Consider keeping some redundancy if it aids different audiences

---

_Generated: 2025-11-10_ _Priority: Frontend > Docker > Docs > Tests > Cleanup_
