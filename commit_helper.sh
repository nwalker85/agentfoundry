#!/bin/bash
# Quick Git Commit Helper for Engineering Department

echo "🚀 Engineering Department - Git Commit Helper"
echo "============================================="

cd "/Users/nate/Development/1. Projects/Engineering Department" || exit 1

# Function to count files
count_files() {
    echo "$1" | grep -v "^$" | wc -l | tr -d ' '
}

# Check current status
UNTRACKED=$(git ls-files --others --exclude-standard)
MODIFIED=$(git diff --name-only)
STAGED=$(git diff --staged --name-only)

UNTRACKED_COUNT=$(count_files "$UNTRACKED")
MODIFIED_COUNT=$(count_files "$MODIFIED")
STAGED_COUNT=$(count_files "$STAGED")

echo ""
echo "📊 Current Status:"
echo "  - Untracked files: $UNTRACKED_COUNT"
echo "  - Modified files: $MODIFIED_COUNT"
echo "  - Staged files: $STAGED_COUNT"
echo ""

# If everything is clean
if [ "$UNTRACKED_COUNT" -eq 0 ] && [ "$MODIFIED_COUNT" -eq 0 ] && [ "$STAGED_COUNT" -eq 0 ]; then
    echo "✅ Working directory is clean!"
    
    # Check if we need to push
    if git rev-parse @{u} &>/dev/null; then
        UNPUSHED=$(git rev-list --count @{u}..HEAD)
        if [ "$UNPUSHED" -gt 0 ]; then
            echo ""
            echo "📤 You have $UNPUSHED commits to push"
            echo ""
            read -p "Push to remote? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git push origin $(git branch --show-current)
                echo "✅ Pushed successfully!"
            fi
        else
            echo "✅ Everything is up to date with remote!"
        fi
    fi
    exit 0
fi

# Show what needs to be committed
echo "📝 Files to commit:"
echo ""

if [ "$UNTRACKED_COUNT" -gt 0 ]; then
    echo "New files:"
    echo "$UNTRACKED" | head -10 | sed 's/^/  + /'
    if [ "$UNTRACKED_COUNT" -gt 10 ]; then
        echo "  ... and $((UNTRACKED_COUNT - 10)) more"
    fi
    echo ""
fi

if [ "$MODIFIED_COUNT" -gt 0 ]; then
    echo "Modified files:"
    echo "$MODIFIED" | head -10 | sed 's/^/  M /'
    if [ "$MODIFIED_COUNT" -gt 10 ]; then
        echo "  ... and $((MODIFIED_COUNT - 10)) more"
    fi
    echo ""
fi

echo "============================================="
echo "Choose an action:"
echo "  1) Commit ALL changes (Phase 3 complete)"
echo "  2) Commit core implementation only"
echo "  3) Commit documentation only"
echo "  4) Custom commit (manual staging)"
echo "  5) Show detailed status"
echo "  0) Cancel"
echo ""
read -p "Your choice (0-5): " choice

case $choice in
    1)
        echo "📦 Staging all changes..."
        git add .
        git status --short
        echo ""
        echo "Commit message:"
        echo "feat: Complete Phase 3 - MCP tools and agent implementation"
        echo ""
        read -p "Use this message? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git commit -m "feat: Complete Phase 3 - MCP tools and agent implementation

- Implemented MCP server v0.2.0 with full tool suite
- Added NotionTool, GitHubTool, and AuditTool with idempotency
- Created SimplePMAgent avoiding LangGraph compatibility issues
- Added comprehensive testing framework (E2E and UAT)
- Documented user personas and use cases for POC and Production
- Added testing strategy with BDD approach
- Updated project plan and current state
- Created project inventory and README

Testing: E2E tests operational, UAT runner created
Docs: Complete personas, use cases, and testing framework"
            
            echo ""
            read -p "Push to remote? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git push origin $(git branch --show-current)
                echo "✅ All changes committed and pushed!"
            else
                echo "✅ Changes committed locally"
            fi
        fi
        ;;
        
    2)
        echo "📦 Staging core implementation..."
        git add mcp_server.py
        git add mcp/
        git add agent/
        git add test_e2e.py uat_runner.py
        git add requirements.txt
        git add *.sh
        
        git status --short
        echo ""
        read -p "Commit these files? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git commit -m "feat: Core implementation - MCP tools and agents"
            echo "✅ Core implementation committed"
        fi
        ;;
        
    3)
        echo "📦 Staging documentation..."
        git add *.md
        git add docs/
        git add UAT_GUIDE.md TEST_README.md
        
        git status --short
        echo ""
        read -p "Commit these files? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git commit -m "docs: Add comprehensive documentation suite"
            echo "✅ Documentation committed"
        fi
        ;;
        
    4)
        echo "📝 Manual staging mode"
        echo "Use these commands:"
        echo ""
        echo "  git add <files>"
        echo "  git commit -m \"your message\""
        echo "  git push origin $(git branch --show-current)"
        echo ""
        echo "Starting interactive git status..."
        git status
        ;;
        
    5)
        echo "📊 Detailed status:"
        git status -v
        ;;
        
    0)
        echo "❌ Cancelled"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "============================================="
echo "Done! Use './check_git_status.py' to verify"
