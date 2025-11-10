#!/bin/bash
# Git Status and Validation Script for Engineering Department
# This script checks the complete git status and identifies uncommitted files

echo "========================================="
echo "Git Repository Status Check"
echo "========================================="
echo ""

# Navigate to project directory
cd "/Users/nate/Development/1. Projects/Engineering Department" || exit 1

echo "📍 Current Directory: $(pwd)"
echo "🌿 Current Branch: $(git branch --show-current)"
echo ""

echo "========================================="
echo "1. Git Status Overview"
echo "========================================="
git status --short

echo ""
echo "========================================="
echo "2. Uncommitted Changes (Detailed)"
echo "========================================="

# Check for untracked files
if [[ -n $(git ls-files --others --exclude-standard) ]]; then
    echo "❌ UNTRACKED FILES (not in git):"
    git ls-files --others --exclude-standard | while read file; do
        echo "   - $file"
    done
else
    echo "✅ No untracked files"
fi

echo ""

# Check for modified files
if [[ -n $(git diff --name-only) ]]; then
    echo "⚠️ MODIFIED FILES (not staged):"
    git diff --name-only | while read file; do
        echo "   - $file"
    done
else
    echo "✅ No modified files"
fi

echo ""

# Check for staged but uncommitted files
if [[ -n $(git diff --staged --name-only) ]]; then
    echo "🔄 STAGED FILES (ready to commit):"
    git diff --staged --name-only | while read file; do
        echo "   - $file"
    done
else
    echo "✅ No staged files"
fi

echo ""
echo "========================================="
echo "3. Remote Repository Status"
echo "========================================="

# Check remote status
git remote -v

echo ""
echo "📊 Branch Comparison with Remote:"
if git rev-parse @{u} &>/dev/null; then
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    BASE=$(git merge-base @ @{u})

    if [ $LOCAL = $REMOTE ]; then
        echo "✅ Branch is up to date with remote"
    elif [ $LOCAL = $BASE ]; then
        echo "⬇️ Branch is behind remote (need to pull)"
        echo "   Commits behind: $(git rev-list --count HEAD..@{u})"
    elif [ $REMOTE = $BASE ]; then
        echo "⬆️ Branch is ahead of remote (need to push)"
        echo "   Commits to push: $(git rev-list --count @{u}..HEAD)"
    else
        echo "🔀 Branch has diverged from remote"
    fi
else
    echo "❌ No upstream branch configured"
fi

echo ""
echo "========================================="
echo "4. Recent Commits"
echo "========================================="
echo "Last 5 commits:"
git log --oneline -5

echo ""
echo "========================================="
echo "5. Important Files Status Check"
echo "========================================="

# Define critical files to check
critical_files=(
    "mcp_server.py"
    "mcp/schemas.py"
    "mcp/tools/__init__.py"
    "mcp/tools/notion.py"
    "mcp/tools/github.py"
    "mcp/tools/audit.py"
    "agent/simple_pm.py"
    "agent/pm_graph.py"
    "test_e2e.py"
    "uat_runner.py"
    "requirements.txt"
    "README.md"
    "PROJECT_INVENTORY.md"
    "Current State.md"
    "PROJECT_PLAN.md"
    "UAT_GUIDE.md"
    "docs/POC_PERSONAS_USE_CASES.md"
    "docs/PROD_PERSONAS_USE_CASES.md"
    "docs/POC_TO_PROD_DELTA.md"
    "docs/TESTING_FRAMEWORK.md"
)

echo "Checking critical project files..."
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        if git ls-files --error-unmatch "$file" &>/dev/null; then
            if git diff --quiet "$file"; then
                echo "✅ $file (committed)"
            else
                echo "⚠️ $file (modified)"
            fi
        else
            echo "❌ $file (not tracked)"
        fi
    else
        echo "❓ $file (file missing)"
    fi
done

echo ""
echo "========================================="
echo "6. Summary and Recommendations"
echo "========================================="

# Count issues
untracked_count=$(git ls-files --others --exclude-standard | wc -l)
modified_count=$(git diff --name-only | wc -l)
staged_count=$(git diff --staged --name-only | wc -l)

total_issues=$((untracked_count + modified_count + staged_count))

if [ $total_issues -eq 0 ]; then
    echo "✅ All files are committed!"
    echo ""
    echo "Next step: Push to remote if needed"
    echo "Command: git push origin $(git branch --show-current)"
else
    echo "⚠️ Found $total_issues uncommitted changes:"
    echo "   - $untracked_count untracked files"
    echo "   - $modified_count modified files"
    echo "   - $staged_count staged files"
    echo ""
    echo "Suggested commands:"
    
    if [ $untracked_count -gt 0 ]; then
        echo ""
        echo "# To add all untracked files:"
        echo "git add ."
    fi
    
    if [ $modified_count -gt 0 ]; then
        echo ""
        echo "# To stage modified files:"
        echo "git add -u"
    fi
    
    if [ $staged_count -gt 0 ] || [ $modified_count -gt 0 ] || [ $untracked_count -gt 0 ]; then
        echo ""
        echo "# Then commit:"
        echo "git commit -m \"feat: Complete Phase 3 implementation\""
        echo ""
        echo "# Finally push:"
        echo "git push origin $(git branch --show-current)"
    fi
fi

echo ""
echo "========================================="
echo "Script Complete"
echo "========================================="
