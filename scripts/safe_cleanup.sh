#!/bin/bash
# Safe cleanup script - only moves debug scripts and completed documentation
# Does NOT touch any working project files

echo "🧹 Safe Project Cleanup - Documentation & Debug Scripts Only"
echo "============================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
BASE_DIR="/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
cd "$BASE_DIR"

# Create archive directories if they don't exist
echo "📁 Creating archive directories..."
mkdir -p archive/debug_scripts
mkdir -p archive/completed_fixes
mkdir -p archive/data_imports

echo ""
echo "📦 Moving debug/test scripts to archive..."
echo "-------------------------------------------"

# Move debug scripts (safe - these are not used by the running system)
DEBUG_SCRIPTS=(
    "check_field_types.py"
    "check_notion_actual.py"
    "debug_github.py"
    "debug_notion_errors.py"
    "debug_notion_schema.py"
    "find_repo_name.py"
    "query_notion_dbs.py"
    "test_actual_types.py"
    "test_backend.py"
    "test_complete_flow.py"
    "test_field_types.py"
    "test_fixed_schema.py"
    "test_github_corrected.py"
    "test_github_issue.py"
    "test_github_repo_ops.py"
    "test_notion_api.py"
    "test_notion_schema.py"
    "test_notion_tool.py"
    "test_pm_agent.py"
    "test_pm_init.py"
    "test_pm_recursion.py"
    "test_private_repo.py"
)

for script in "${DEBUG_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" archive/debug_scripts/
        echo -e "${GREEN}✓${NC} Moved $script"
    fi
done

echo ""
echo "📄 Moving completed fix documentation..."
echo "----------------------------------------"

# Move completed fix documentation (safe - these document past work)
FIX_DOCS=(
    "ALL_FIXES_COMPLETE.md"
    "ERROR_FIXES.md"
    "FIELD_TYPE_FIXES.md"
    "FINAL_FIELD_FIXES.md"
    "NOTION_IMPLEMENTATION_COMPLETE.md"
    "NOTION_SCHEMA_UPDATE.md"
    "ARCHITECTURE_UPDATE.md"
)

for doc in "${FIX_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" archive/completed_fixes/
        echo -e "${GREEN}✓${NC} Moved $doc"
    fi
done

echo ""
echo "💾 Moving data import files..."
echo "------------------------------"

# Move CSV import files (safe - these were for initial data loading)
CSV_FILES=(
    "notion_import_epics.csv"
    "notion_import_stories.csv"
)

for csv in "${CSV_FILES[@]}"; do
    if [ -f "$csv" ]; then
        mv "$csv" archive/data_imports/
        echo -e "${GREEN}✓${NC} Moved $csv"
    fi
done

echo ""
echo "📊 Cleanup Summary"
echo "=================="
echo -e "${GREEN}✓${NC} Debug scripts archived: $(ls -1 archive/debug_scripts 2>/dev/null | wc -l) files"
echo -e "${GREEN}✓${NC} Fix documentation archived: $(ls -1 archive/completed_fixes 2>/dev/null | wc -l) files"
echo -e "${GREEN}✓${NC} Data imports archived: $(ls -1 archive/data_imports 2>/dev/null | wc -l) files"

echo ""
echo "🔒 Files NOT touched (preserved as-is):"
echo "---------------------------------------"
echo "  • mcp_server.py (main server)"
echo "  • agent/ directory (LangGraph agents)"
echo "  • mcp/ directory (MCP tools)"
echo "  • app/ directory (frontend)"
echo "  • tests/ directory (official test suites)"
echo "  • All .sh scripts (setup, start, run_tests)"
echo "  • All configuration files (.env, package.json, etc.)"

echo ""
echo -e "${GREEN}✅ Safe cleanup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review archived files in archive/ directory"
echo "2. Delete archive/ if everything is working correctly"
echo "3. Commit with: git add . && git commit -m 'chore: archive debug scripts and completed documentation'"
