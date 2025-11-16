# Scripts Quick Reference

**Quick command reference for helper scripts**

---

## Local & AWS Diagnostics

### Local Docker Stack
```bash
# Start services (wrapper around ./start_foundry.sh)
./scripts/start-services.sh

# Check local health (Docker, ports, /health, logs)
./scripts/monitor_local_health.sh
```

### AWS Dev (ECS / ALB)
```bash
# High-level ECS + ALB + /api/health check
AWS_REGION=us-east-1 ./scripts/monitor_aws_health.sh

# Inspect ALB target group health
AWS_REGION=us-east-1 ./scripts/check_alb_targets.sh
```

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

