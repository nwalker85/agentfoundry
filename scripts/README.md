# Engineering Department - Helper Scripts

**Last Updated:** November 10, 2025  
**Purpose:** Utility scripts for development, git operations, documentation, and setup

---

## Directory Structure

```
scripts/
├── README.md                    # This file
├── git/                         # Git operation helpers
│   ├── check_git_status.py     # Python git status validator
│   ├── check_git_status.sh     # Shell git status checker
│   └── commit_helper.sh        # Interactive commit helper
├── docs/                        # Documentation utilities
│   ├── consolidate_docs.py     # Documentation consolidation (v1)
│   └── consolidate_docs_v2.py  # Documentation consolidation (v2)
└── setup/                       # Setup and initialization
    └── create_frontend.py      # Frontend setup script
```

---

## Git Scripts (`scripts/git/`)

### check_git_status.py

**Purpose:** Python-based comprehensive git status validator  
**Author:** Engineering Department Team  
**Lines:** ~260

**What it does:**
- Checks current branch
- Lists untracked files
- Lists modified files (unstaged)
- Lists staged files
- Shows unpushed commits
- Checks if behind remote
- Provides actionable git commands

**Usage:**
```bash
cd scripts/git
python check_git_status.py

# Or from project root
python scripts/git/check_git_status.py
```

**Example output:**
```
=========================================
Git Repository Status Check
=========================================
📍 Current Branch: main
🏠 Repository: /Users/nwalker/Development/Projects/Engineering Department

Status Summary:
✅ Clean working directory
✅ No untracked files
✅ No modified files
✅ No staged files
✅ Up to date with remote

🎉 Everything looks good! Ready to continue working.
```

---

### check_git_status.sh

**Purpose:** Shell-based git status checker  
**Lines:** ~195

**What it does:**
- Quick git status overview
- Lists uncommitted changes
- Shows unpushed commits
- Provides next actions

**Usage:**
```bash
cd scripts/git
./check_git_status.sh

# Or from project root
./scripts/git/check_git_status.sh
```

**Features:**
- Color-coded output
- Categorized file listings
- Quick status summary
- Actionable recommendations

---

### commit_helper.sh

**Purpose:** Interactive git commit helper  
**Lines:** ~191

**What it does:**
- Shows current file status counts
- Interactive staging
- Guided commit message creation
- Optional push to remote

**Usage:**
```bash
cd scripts/git
./commit_helper.sh

# Or from project root
./scripts/git/commit_helper.sh
```

**Workflow:**
1. Shows current status (untracked, modified, staged)
2. Offers to stage all changes or select specific files
3. Prompts for commit message
4. Creates commit
5. Offers to push to remote

**Example interaction:**
```
🚀 Engineering Department - Git Commit Helper
=============================================

📊 Current Status:
  - Untracked files: 2
  - Modified files: 5
  - Staged files: 0

Would you like to:
  1) Stage all changes
  2) Stage specific files
  3) Exit

> 1

Enter commit message: Add user authentication feature

✅ Changes committed successfully!

📤 Push to remote? (y/n) y
✅ Pushed successfully!
```

---

## Documentation Scripts (`scripts/docs/`)

### consolidate_docs.py

**Purpose:** Original documentation consolidation script  
**Status:** Deprecated (use v2)  
**Lines:** TBD

**What it does:**
- Initial attempt at documentation consolidation
- Basic file merging

**Note:** This script was superseded by `consolidate_docs_v2.py` which provides better organization and comprehensive merging.

---

### consolidate_docs_v2.py

**Purpose:** Enhanced documentation consolidation script  
**Status:** Active  
**Lines:** TBD

**What it does:**
- Consolidates multiple documentation files into organized structure
- Merges related documentation (status, testing, architecture)
- Creates unified testing guide
- Organizes artifacts

**Usage:**
```bash
cd scripts/docs
python consolidate_docs_v2.py

# Or from project root
python scripts/docs/consolidate_docs_v2.py
```

**Results:**
- Creates `docs/PROJECT_STATUS.md` (from Current State + Plan + Inventory)
- Creates `docs/TESTING_GUIDE.md` (from UAT + Tests + Framework)
- Creates `docs/ARCHITECTURE.md` (from Lessons + Telemetry)
- Moves artifacts to `docs/artifacts/`
- Removes redundant files

---

## Setup Scripts (`scripts/setup/`)

### create_frontend.py

**Purpose:** Frontend initialization and setup  
**Status:** Active  
**Lines:** TBD

**What it does:**
- Sets up Next.js frontend structure
- Creates necessary configuration files
- Initializes TypeScript config
- Sets up Tailwind CSS

**Usage:**
```bash
cd scripts/setup
python create_frontend.py

# Or from project root
python scripts/setup/create_frontend.py
```

**Creates:**
- Next.js App Router structure
- TypeScript configuration
- Tailwind CSS setup
- ESLint configuration
- Base layouts and pages

---

## Usage Guidelines

### When to Use Git Scripts

**check_git_status.py / .sh:**
- Before committing changes
- Before pushing to remote
- To verify clean working directory
- When debugging git issues

**commit_helper.sh:**
- When you have multiple files to commit
- When you want guided commit workflow
- For consistent commit messages
- Quick staging and committing

### When to Use Documentation Scripts

**consolidate_docs_v2.py:**
- After major documentation updates
- When reorganizing documentation structure
- To eliminate duplicate information
- Before major releases

### When to Use Setup Scripts

**create_frontend.py:**
- Initial project setup
- Recreating frontend structure
- Setting up new development environment
- Resetting frontend to baseline

---

## Best Practices

### Script Execution

1. **Always run from correct directory:**
   ```bash
   # From script directory
   cd scripts/git && ./check_git_status.sh
   
   # Or with full path from project root
   ./scripts/git/check_git_status.sh
   ```

2. **Make scripts executable:**
   ```bash
   chmod +x scripts/git/*.sh
   ```

3. **Check permissions before running:**
   ```bash
   ls -la scripts/git/
   ```

### Script Maintenance

1. **Update hardcoded paths** when moving projects
2. **Test scripts after modifications**
3. **Keep scripts version controlled**
4. **Document any changes**
5. **Add comments for complex logic**

### Safety

1. **Review before running** scripts that modify files
2. **Backup important data** before running setup scripts
3. **Test in development** before using in production
4. **Check git status** before running git helper scripts

---

## Script Dependencies

### Python Scripts
- Python 3.9+
- Standard library only (no external dependencies)
- Cross-platform compatible

### Shell Scripts
- Bash (macOS/Linux)
- Git CLI
- Standard Unix utilities (grep, wc, etc.)

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Permission denied" | Run `chmod +x script.sh` |
| "Command not found" | Ensure you're in correct directory or use full path |
| Hardcoded paths fail | Update paths in script to match your setup |
| Git commands fail | Ensure you're in a git repository |
| Python script errors | Check Python version (requires 3.9+) |

### Debug Mode

**For shell scripts:**
```bash
bash -x scripts/git/check_git_status.sh
```

**For Python scripts:**
```bash
python -v scripts/git/check_git_status.py
```

---

## Contributing Scripts

### Adding New Scripts

1. **Choose appropriate directory:**
   - `git/` - Git operations
   - `docs/` - Documentation utilities
   - `setup/` - Setup and initialization
   - Create new category if needed

2. **Script template (Python):**
```python
#!/usr/bin/env python3
"""
Script Name - Brief Description
Author: Engineering Department Team
"""

import sys
from pathlib import Path

def main():
    """Main function."""
    # Your code here
    pass

if __name__ == "__main__":
    main()
```

3. **Script template (Shell):**
```bash
#!/bin/bash
# Script Name - Brief Description
# Author: Engineering Department Team

set -e  # Exit on error

echo "Starting script..."

# Your code here

echo "Script completed successfully!"
```

4. **Update this README** with script documentation

---

## Script Roadmap

### Planned Scripts

**Git Category:**
- [ ] `branch_cleaner.sh` - Clean up merged branches
- [ ] `sync_fork.sh` - Sync with upstream fork
- [ ] `pr_helper.sh` - Create pull requests

**Docs Category:**
- [ ] `generate_api_docs.py` - Generate API documentation
- [ ] `validate_links.py` - Check for broken documentation links
- [ ] `update_toc.py` - Update table of contents

**Setup Category:**
- [ ] `setup_dev_env.sh` - Complete development environment setup
- [ ] `install_deps.sh` - Install all dependencies
- [ ] `init_databases.py` - Initialize Notion databases

**Testing Category:**
- [ ] `run_benchmarks.sh` - Run performance benchmarks
- [ ] `generate_test_report.py` - Generate test coverage report
- [ ] `cleanup_test_data.py` - Clean up test data

---

## References

- [Project Status](../docs/PROJECT_STATUS.md) - Current project status
- [Testing Guide](../docs/TESTING_GUIDE.md) - Testing documentation
- [Architecture](../docs/ARCHITECTURE.md) - System architecture

---

*Helper Scripts Documentation - Engineering Department*  
*Last Updated: November 10, 2025*

