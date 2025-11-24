# Error Fixes Applied

## Issues Identified from Logs

### 1. ❌ LangGraph Recursion Limit Error

**Problem:** PM Agent hitting recursion limit of 50 **Cause:** Infinite loop
between `understand` → `clarify` → `understand` nodes **Fix Applied:**

- Changed clarify node to go to `validate` instead of back to `understand`
- Added explicit clarification count limit (max 2)
- Ensure clarifications_needed is cleared after processing
- Added debug logging to trace node transitions

### 2. ❌ Notion API 400 Bad Request

**Potential Causes:**

- Field mismatch (fixed with Title rename)
- Select option doesn't exist
- URL fields cannot be null (should be empty string or omitted)

**Debug Steps Created:**

1. `debug_notion_errors.py` - Captures detailed error responses
2. `test_pm_recursion.py` - Tests PM agent recursion fix
3. Enhanced error logging in notion.py

## Files Modified

### `/agent/pm_graph.py`

```python
# Key changes:
# 1. Changed edge from clarify → validate (not back to understand)
workflow.add_edge("clarify", "validate")  # Was: workflow.add_edge("clarify", "understand")

# 2. Enhanced clarification handling with defaults
if state["clarification_count"] > 2:
    state["clarifications_needed"] = []
    # Set defaults if still missing
    if not state.get("story_title"):
        state["story_title"] = "New Story Task"
```

### `/mcp/tools/notion.py`

```python
# Fixed GitHub URL fields - remove null URLs
# OLD:
properties["GitHub Issue"] = {
    "url": None  # This causes 400 error
}

# NEW - just omit the field if no URL:
# Don't set GitHub Issue/PR fields initially
# They'll be added later via update_story_github_url()
```

## Testing Commands

```bash
# Test Notion integration alone
python debug_notion_errors.py

# Test PM Agent recursion fix
python test_pm_recursion.py

# Test full flow
python test_pm_agent.py
```

## Next Steps

1. **Run debug_notion_errors.py** to see exact Notion API error
2. **Remove null URL fields** from story creation
3. **Test PM agent** with recursion fix
4. **Monitor logs** for any remaining issues

## Expected Resolution

After these fixes:

- PM Agent should complete without recursion errors
- Notion story creation should succeed
- GitHub issue creation should follow
- Full workflow should complete end-to-end
