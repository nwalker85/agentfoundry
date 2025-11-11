# Scripts Quick Reference

**Quick command reference for helper scripts**

---

## Git Operations

### Check Status
```bash
# Python version (comprehensive)
python scripts/git/check_git_status.py

# Shell version (quick)
./scripts/git/check_git_status.sh
```

### Commit Changes
```bash
# Interactive commit helper
./scripts/git/commit_helper.sh
```

---

## Documentation

### Consolidate Docs
```bash
# Run documentation consolidation
python scripts/docs/consolidate_docs_v2.py
```

---

## Setup

### Create Frontend
```bash
# Initialize frontend structure
python scripts/setup/create_frontend.py
```

---

## Common Workflows

### Before Committing
```bash
# 1. Check status
./scripts/git/check_git_status.sh

# 2. Use commit helper
./scripts/git/commit_helper.sh
```

### After Documentation Changes
```bash
# Consolidate and organize
python scripts/docs/consolidate_docs_v2.py
```

### New Development Environment
```bash
# Setup frontend
python scripts/setup/create_frontend.py

# Verify git status
python scripts/git/check_git_status.py
```

---

See [scripts/README.md](./README.md) for complete documentation.

