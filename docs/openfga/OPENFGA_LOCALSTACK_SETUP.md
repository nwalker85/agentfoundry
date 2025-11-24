# OpenFGA + LocalStack Setup Guide

## Principle: Zero Secrets in .env

**OpenFGA configuration is stored in LocalStack, not environment variables.**

### Why?

- ✅ Consistent with secrets management pattern
- ✅ Configuration versioning and rotation
- ✅ Audit trail (WHO changed config)
- ✅ Multi-environment support
- ✅ No secrets in docker-compose.yml

---

## Setup Process

### Step 1: Start Services

```bash
docker-compose up -d localstack openfga postgres
```

### Step 2: Run OpenFGA Migrations

```bash
docker-compose run --rm openfga migrate
```

### Step 3: Initialize OpenFGA Store

Option A: Install FGA CLI (Recommended)

```bash
# Install
brew install fga

# Create store
STORE_ID=$(curl -X POST http://localhost:9080/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"agent-foundry"}' | jq -r '.id')

echo "Store created: $STORE_ID"

# Load authorization model
MODEL_ID=$(fga model write \
  --store-id $STORE_ID \
  --file openfga/authorization_model.fga \
  --api-url http://localhost:9080 | jq -r '.authorization_model_id')

echo "Model loaded: $MODEL_ID"
```

Option B: Manual (If no FGA CLI)

```bash
# Just use the store ID we created earlier
STORE_ID="01KATFSA1G5FRN6682HGAJX6XR"
MODEL_ID="01KATFSA1G5FRN6682HGAJX6XR"  # Temporary - load proper model later
```

### Step 4: Store Configuration in LocalStack (NOT .env!)

```bash
# Store OpenFGA config in LocalStack
python scripts/openfga_setup_localstack.py $STORE_ID $MODEL_ID

# Output:
# ✅ OpenFGA configuration stored in LocalStack
# Backend will automatically retrieve it at startup.
```

### Step 5: Restart Backend

```bash
docker-compose restart foundry-backend

# Backend will:
# 1. Start up
# 2. Initialize OpenFGA client
# 3. Retrieve store_id/model_id from LocalStack
# 4. Connect to OpenFGA
```

### Step 6: Verify

```bash
docker-compose logs foundry-backend | grep OpenFGA

# Should see:
# "OpenFGA config loaded from LocalStack: store=01KATFSA..."
```

---

## How It Works

### Startup Flow

```
Backend Startup
  ↓
OpenFGA Client.__init__()
  ↓
Lazy initialize on first use
  ↓
┌─────────────────────────────────────┐
│ 1. Fetch from LocalStack            │
│    Key: platform/shared/            │
│         openfga_config               │
│    Value: {                          │
│      "store_id": "01KATFSA...",      │
│      "model_id": "01KXXXXX..."       │
│    }                                 │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 2. Set client properties             │
│    self.store_id = config.store_id   │
│    self.auth_model_id = config.model │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ 3. Ready to authorize                │
│    await fga_client.check(...)       │
└─────────────────────────────────────┘
```

### LocalStack Secret Structure

```
LocalStack Secrets:
└── platform/
    └── shared/
        └── openfga_config
            {
              "store_id": "01KATFSA1G5FRN6682HGAJX6XR",
              "model_id": "01KBBBBB2H6GRO7793IICKYY7Y",
              "created_at": "2025-11-24",
              "description": "OpenFGA store and authorization model"
            }
```

### Fallback to .env (Development Only)

```python
# backend/openfga_client.py

async def initialize(self):
    # Try LocalStack first
    config = await secrets_manager.get_secret("platform", "openfga_config")

    if config:
        # Production: Use LocalStack
        self.store_id = json.loads(config)["store_id"]
    else:
        # Fallback: Use .env (initial setup only)
        self.store_id = os.getenv("OPENFGA_STORE_ID")
        logger.warning("Using env var fallback - store config in LocalStack!")
```

---

## Benefits

### 1. Consistent Secret Management

```
All configuration in LocalStack:
├── Organization secrets (API keys)
│   ├── acme-corp/openai_api_key
│   └── globaltech/anthropic_api_key
│
└── Platform secrets (infrastructure config)
    ├── openfga_config
    ├── livekit_config
    └── database_credentials
```

### 2. Configuration Rotation

```bash
# Rotate to new authorization model
NEW_MODEL_ID=$(fga model write --store-id $STORE_ID --file updated_model.fga)

# Update in LocalStack (NOT .env!)
python scripts/openfga_setup_localstack.py $STORE_ID $NEW_MODEL_ID

# Restart backend (picks up new model)
docker-compose restart foundry-backend
```

### 3. Environment Parity

```
Development: LocalStack (localhost:4566)
  ↓
Staging: AWS Secrets Manager (us-east-1)
  ↓
Production: AWS Secrets Manager (us-east-1)

Same code, same pattern, zero .env changes!
```

### 4. Audit Trail

```python
# Who changed OpenFGA config?
SELECT * FROM audit_logs
WHERE resource_type = 'secret'
  AND resource_id LIKE '%openfga_config%'
ORDER BY created_at DESC;

# Result:
# 2025-11-24 alice Updated openfga_config (model rotation)
# 2025-11-20 bob   Created openfga_config (initial setup)
```

---

## Migration from .env

### Old Way (❌ Don't Do This)

```yaml
# docker-compose.yml
environment:
  - OPENFGA_STORE_ID=01KATFSA1G5FRN6682HGAJX6XR
  - OPENFGA_AUTH_MODEL_ID=01KBBBBB2H6GRO7793IICKYY7Y

# .env
OPENFGA_STORE_ID=01KATFSA1G5FRN6682HGAJX6XR
OPENFGA_AUTH_MODEL_ID=01KBBBBB2H6GRO7793IICKYY7Y
```

### New Way (✅ Do This)

```bash
# Store in LocalStack
python scripts/openfga_setup_localstack.py \
  01KATFSA1G5FRN6682HGAJX6XR \
  01KBBBBB2H6GRO7793IICKYY7Y

# docker-compose.yml - NO CONFIG NEEDED
environment:
  - SVC_OPENFGA_HOST=openfga  # Just the service name
  - SVC_LOCALSTACK_HOST=localstack

# Backend retrieves from LocalStack at startup
```

---

## Complete Setup Example

```bash
# 1. Start infrastructure
docker-compose up -d localstack postgres

# 2. Run OpenFGA migrations
docker-compose run --rm openfga migrate

# 3. Start OpenFGA
docker-compose up -d openfga

# 4. Install FGA CLI
brew install fga

# 5. Create store
STORE_ID=$(curl -X POST http://localhost:9080/stores \
  -H "Content-Type: application/json" \
  -d '{"name":"agent-foundry"}' | jq -r '.id')

# 6. Load authorization model
MODEL_ID=$(fga model write \
  --store-id $STORE_ID \
  --file openfga/authorization_model.fga \
  --api-url http://localhost:9080)

# Extract model ID from output
# (fga command returns JSON or text depending on version)

# 7. Store in LocalStack
python scripts/openfga_setup_localstack.py $STORE_ID $MODEL_ID

# 8. Start backend
docker-compose up -d foundry-backend

# 9. Verify
docker-compose logs foundry-backend | grep "OpenFGA config loaded from LocalStack"
```

---

## Troubleshooting

### Backend Can't Load OpenFGA Config

```bash
# Check LocalStack has the secret
docker-compose exec localstack awslocal secretsmanager list-secrets

# Should show:
# - agentfoundry/development/platform/shared/openfga_config
```

### OpenFGA Checks Failing

```bash
# Check configuration loaded
docker-compose logs foundry-backend | grep OpenFGA

# Should see:
# "OpenFGA config loaded from LocalStack: store=01KATFSA..."

# If you see "Using env var fallback":
# Run: python scripts/openfga_setup_localstack.py <store_id> <model_id>
```

---

## Summary

### Before (❌)

```
.env file:
OPENFGA_STORE_ID=...
OPENFGA_AUTH_MODEL_ID=...
```

### After (✅)

```
LocalStack:
platform/shared/openfga_config = {
  "store_id": "...",
  "model_id": "..."
}

Backend automatically retrieves at startup
```

**Zero secrets/config in .env!** 🎉

---

**Pattern:** All configuration in LocalStack  
**Benefit:** Consistent, auditable, rotatable  
**Production:** Same code, AWS Secrets Manager
