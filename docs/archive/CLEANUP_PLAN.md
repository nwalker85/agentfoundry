# Documentation Cleanup Plan

## Safe Cleanup Strategy

Only touching documentation and debug scripts - NO changes to working code.

## 📦 Files to Archive

### Debug/Test Scripts (22 files)

Move to `archive/debug_scripts/`:

```bash
# Notion debugging
- check_field_types.py
- check_notion_actual.py
- debug_notion_errors.py
- debug_notion_schema.py
- test_actual_types.py
- test_field_types.py
- test_fixed_schema.py
- test_notion_api.py
- test_notion_schema.py
- test_notion_tool.py
- query_notion_dbs.py

# GitHub debugging
- debug_github.py
- find_repo_name.py
- test_github_corrected.py
- test_github_issue.py
- test_github_repo_ops.py
- test_private_repo.py

# PM Agent testing
- test_pm_agent.py
- test_pm_init.py
- test_pm_recursion.py
- test_backend.py
- test_complete_flow.py
```

### Completed Fix Documentation (7 files)

Move to `archive/completed_fixes/`:

```bash
- ALL_FIXES_COMPLETE.md
- ERROR_FIXES.md
- FIELD_TYPE_FIXES.md
- FINAL_FIELD_FIXES.md
- NOTION_IMPLEMENTATION_COMPLETE.md
- NOTION_SCHEMA_UPDATE.md
- ARCHITECTURE_UPDATE.md
```

### Data Import Files (2 files)

Move to `archive/data_imports/`:

```bash
- notion_import_epics.csv
- notion_import_stories.csv
```

## 📄 Documentation Consolidation

### Current Documentation Structure

```
docs/
├── Core Documentation (KEEP AS-IS)
│   ├── ARCHITECTURE.md          # System design
│   ├── PROJECT_STATUS.md        # Current status
│   ├── TESTING_GUIDE.md         # Testing approach
│   ├── CODE_INVENTORY.md        # Codebase structure
│   └── README.md                # Doc index
│
├── Requirements Docs (CONSIDER MERGING)
│   ├── POC_SCOPE.md             ┐
│   ├── POC_PERSONAS_USE_CASES.md├─→ POC_REQUIREMENTS.md
│   └── POC_TO_PROD_DELTA.md     ┘
│
│   ├── PROD_IMPLEMENTATION_REQUIREMENTS.md ┐
│   └── PROD_PERSONAS_USE_CASES.md         ├─→ PROD_REQUIREMENTS.md
│
├── Planning Docs (REVIEW)
│   ├── FRONTEND_DEVELOPMENT_PLAN.md  # May be complete now?
│   ├── CONSOLIDATION_PLAN.md         # This doc - can archive after
│   └── NOTION_SCHEMA_DESIGN.md       # Keep as reference
│
└── Unknown (CHECK)
    └── Environment C.md              # Fragment? Review content

progressaudit/
├── Recent (KEEP)
│   ├── LANGGRAPH_INTEGRATION_COMPLETE.md
│   ├── DAY1_FRONTEND_COMPLETE.md
│   └── AUDIT_20251110.md
│
└── Older (ARCHIVE AFTER EXTRACTING KEY INFO)
    ├── API_MOCK_MODE_IMPLEMENTED.md
    ├── CRITICAL_CORRECTION_20251110.md
    ├── LANGGRAPH_FIXES_APPLIED.md
    ├── NOTION_API_FIXED.md
    └── TEST_RESULTS_ANALYSIS.md
```

## 🎯 Manual Cleanup Commands

### Step 1: Create Archive Structure

```bash
mkdir -p archive/debug_scripts
mkdir -p archive/completed_fixes
mkdir -p archive/data_imports
mkdir -p archive/progressaudit
```

### Step 2: Move Debug Scripts

```bash
# Move all test and debug scripts
mv test_*.py debug_*.py check_*.py query_*.py find_*.py archive/debug_scripts/
```

### Step 3: Move Completed Documentation

```bash
# Move fix documentation
mv *_COMPLETE.md *_FIXES.md *_UPDATE.md archive/completed_fixes/
```

### Step 4: Move Data Files

```bash
# Move CSV imports
mv *.csv archive/data_imports/
```

## ✅ What We're NOT Touching

- ❌ mcp_server.py (main server)
- ❌ agent/ directory (working agents)
- ❌ mcp/ directory (MCP tools)
- ❌ app/ directory (frontend)
- ❌ tests/ directory (official test suites)
- ❌ Any .sh scripts (setup, start, run_tests)
- ❌ Configuration files (.env, package.json, requirements.txt)
- ❌ Git files
- ❌ Node/Python environments

## 📊 Expected Results

- **Root directory**: From ~50 files → ~20 files
- **Cleaner structure**: Debug scripts separated from production code
- **Documentation**: Historical fixes archived but accessible
- **Zero risk**: No working code modified

## 🔄 Rollback Plan

If anything goes wrong:

```bash
# Move everything back from archive
mv archive/debug_scripts/* .
mv archive/completed_fixes/* .
mv archive/data_imports/* .
rm -rf archive/
```

## Next Steps After Cleanup

1. Update README.md to reflect E2E test success
2. Consider merging POC docs into single POC_REQUIREMENTS.md
3. Consider merging PROD docs into single PROD_REQUIREMENTS.md
4. Update docs/README.md index after consolidation
5. Commit changes:
   `git commit -m "chore: archive debug scripts and completed documentation"`
