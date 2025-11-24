# Migration to New Repository

## Repository Move

**Old Location**: Local development  
**New Location**: https://github.com/quant-eng/agent-foundry  
**Organization**: Quant Engineering

---

## What to Include in New Repo

### Essential Files

#### Core Application
- ✅ `backend/` - All backend code
- ✅ `app/` - All frontend code
- ✅ `agents/` - LangGraph agent implementations
- ✅ `openfga/` - Authorization model & tests
- ✅ `mcp/` - MCP integration gateway
- ✅ `scripts/` - Utility scripts

#### Configuration
- ✅ `docker-compose.yml` - All services
- ✅ `requirements.txt` - Python dependencies
- ✅ `package.json` - Node dependencies
- ✅ `.env.example` - Environment template
- ✅ `.gitignore` - Exclude secrets

#### Documentation
- ✅ `README.md` - Main readme (use README_NEW_REPO.md)
- ✅ `openfga/README.md` - Authorization docs
- ✅ Key architecture docs (if desired)

### Optional (Archive First)
- ⚠️ `archive/` - Old code (maybe don't include)
- ⚠️ `docs/` - Most docs deleted, keep only essentials
- ⚠️ `mcp_server.py` - Legacy, being replaced

---

## Pre-Migration Checklist

### Clean Up

```bash
# Remove sensitive data
rm -f .env .env.local
rm -rf data/*.db  # Remove local databases
rm -rf node_modules/
rm -rf venv/
rm -rf __pycache__/
rm -rf **/__pycache__/

# Create .env.example
cat > .env.example << 'EOF'
# Agent Foundry Environment Configuration
ENVIRONMENT=development
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Service Discovery (DNS names)
SVC_BACKEND_HOST=foundry-backend
SVC_OPENFGA_HOST=openfga
SVC_LOCALSTACK_HOST=localstack

# Note: API keys stored in LocalStack, not here!
EOF
```

### Update README

```bash
# Use the new README
cp README_NEW_REPO.md README.md
```

### Verify Tests Pass

```bash
# OpenFGA tests
python openfga/test_authorization_checks.py

# Should show: 12/12 passed ✅
```

---

## Post-Migration Setup

### For New Contributors

```bash
# 1. Clone
git clone https://github.com/quant-eng/agent-foundry.git
cd agent-foundry

# 2. Copy environment template
cp .env.example .env

# 3. Start services
docker-compose up -d

# 4. Initialize OpenFGA
python scripts/openfga_load_model_v2.py
python scripts/openfga_setup_initial_data.py

# 5. Verify
curl http://localhost:8000/health
python openfga/test_authorization_checks.py
```

---

## What Makes This Repo Special

### 1. Zero Secrets in Git

All secrets in LocalStack:
- ✅ API keys (OpenAI, Anthropic, etc.)
- ✅ OpenFGA configuration (store_id, model_id)
- ✅ Integration credentials

**Nothing sensitive in .env or git!**

### 2. Service Discovery

All services use DNS names:
- ✅ No hardcoded URLs
- ✅ No port configuration
- ✅ Works in Docker + K8s

### 3. Production-Ready Authorization

OpenFGA with Google Zanzibar:
- ✅ 5-level hierarchy
- ✅ Team collaboration
- ✅ System protection
- ✅ 12/12 tests passing

---

## Files to NOT Include

❌ `.env` - Local secrets  
❌ `data/*.db` - Local databases  
❌ `node_modules/` - Dependencies  
❌ `venv/` - Python virtual env  
❌ `__pycache__/` - Compiled Python  
❌ `.DS_Store` - Mac files  

**Make sure `.gitignore` is comprehensive!**

---

## Recommended .gitignore

```gitignore
# Environment
.env
.env.local
.env.*.local

# Dependencies
node_modules/
venv/
__pycache__/
*.pyc

# Databases
data/*.db
data/*.db-shm
data/*.db-wal
*.sqlite

# Build
dist/
build/
.next/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Secrets (extra safety)
*.key
*.pem
*.secret
```

---

## CI/CD Recommendations

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Run OpenFGA tests
        run: |
          pip install -r requirements.txt
          python openfga/test_authorization_checks.py
      
      - name: Run backend tests
        run: pytest tests/
```

---

## Migration Commands

```bash
# In old repo
git remote add new-origin https://github.com/quant-eng/agent-foundry.git

# Clean up
rm -rf venv node_modules data/*.db

# Push to new repo
git push new-origin main

# Set as default
git remote set-url origin https://github.com/quant-eng/agent-foundry.git
```

---

## Summary

### What's in New Repo

✅ **Complete application** (backend + frontend)  
✅ **OpenFGA authorization** (enhanced model)  
✅ **LocalStack secrets** (blind-write pattern)  
✅ **Service discovery** (DNS-based)  
✅ **Docker Compose** (all services)  
✅ **Tests** (12/12 passing)  
✅ **Zero secrets** in git  

### What's Excluded

❌ Local databases  
❌ Node modules  
❌ Virtual environments  
❌ Archived/legacy code  
❌ Secrets/API keys  

---

**Ready for:** Open source, collaboration, production deployment  
**Architecture:** Enterprise-grade, zero-configuration-debt  
**Status:** ✅ Production-ready

