# Secrets Management with LocalStack

## Overview

Agent Foundry uses LocalStack Secrets Manager for secure, organization-scoped
secret storage following the **"Blind Write"** pattern. This provides
AWS-compatible secret management for development that seamlessly transitions to
production.

## Architecture

### Blind Write Pattern

**Key Principle:** The frontend can write secrets but never read them.

```
User (Browser)
  ↓ PUT /api/secrets/{org_id}/{secret_name}
Backend (FastAPI)
  ↓ PutSecretValue
LocalStack/AWS Secrets Manager
  ↓ Encrypted Storage
```

**Security Benefits:**

- ✅ Secret values never exposed to browser
- ✅ Cannot be extracted via XSS or client-side attacks
- ✅ All operations audit logged (WHO, but not WHAT)
- ✅ Immediate overwrite prevents recovery of old values

### Secret Naming Convention

Secrets use deterministic, hierarchical naming:

```
agentfoundry/[env]/[org_id]/[domain_id]/[secret_name]
```

**Examples:**

- `agentfoundry/dev/acme-corp/card-services/openai_api_key`
- `agentfoundry/prod/acme-corp/shared/anthropic_api_key`
- `agentfoundry/dev/globaltech/shared/github_token`

**Benefits:**

- Organization isolation (cannot access other orgs' secrets)
- Domain-level scoping (optional)
- Environment separation (dev/staging/prod)
- Clear audit trail

## Service Discovery Integration

LocalStack uses the new service discovery pattern:

```yaml
# docker-compose.yml
localstack:
  ports:
    - '4566:4566' # External access for testing
  networks:
    - foundry

foundry-backend:
  environment:
    - SVC_LOCALSTACK_HOST=localstack
    - LOCALSTACK_ENDPOINT=http://localstack:4566
```

**Backend automatically detects environment:**

```python
# Development: Uses LocalStack (localhost:4566)
# Production: Uses AWS Secrets Manager
```

## Usage

### Backend (Python)

#### Get Secret for Agent Execution

```python
from backend.config.secrets import get_llm_api_key

# Get OpenAI key for organization
api_key = await get_llm_api_key(
    organization_id="acme-corp",
    provider="openai",
    domain_id="card-services"  # Optional
)

if api_key:
    # Use for agent execution
    llm = ChatOpenAI(api_key=api_key)
```

#### Check if Secret Exists

```python
from backend.config.secrets import secrets_manager

# Check status (safe to expose to API)
exists = await secrets_manager.has_secret(
    organization_id="acme-corp",
    secret_name="openai_api_key",
    domain_id="card-services"
)
```

#### Create/Update Secret

```python
# ⚠️ BACKEND ONLY - Never expose this endpoint
from backend.config.secrets import secrets_manager

success = await secrets_manager.upsert_secret(
    organization_id="acme-corp",
    secret_name="openai_api_key",
    secret_value="sk-...",  # NEVER LOGGED
    domain_id="card-services"
)
```

### Frontend (React)

#### Display Secret Status

```tsx
import { SecretConfigCard } from '@/components/secrets/SecretConfigCard';

<SecretConfigCard
  organizationId="acme-corp"
  domainId="card-services"
  secretName="openai_api_key"
  displayName="OpenAI API Key"
  description="API key for GPT models"
  placeholder="sk-..."
/>;
```

#### Full Secrets Panel

```tsx
import { SecretsManagementPanel } from '@/components/secrets/SecretsManagementPanel';

<SecretsManagementPanel organizationId="acme-corp" domainId="card-services" />;
```

### API Endpoints

#### Check Secret Status (Safe)

```http
GET /api/secrets/{org_id}/{secret_name}?domain_id={domain_id}

Response:
{
  "configured": true,
  "secret_name": "openai_api_key",
  "organization_id": "acme-corp",
  "domain_id": "card-services"
}
```

#### Update Secret (Blind Write)

```http
PUT /api/secrets/{org_id}/{secret_name}

Body:
{
  "secret_value": "sk-...",
  "domain_id": "card-services",
  "description": "Production OpenAI key"
}

Response:
{
  "status": "success",
  "configured": true,
  "message": "Secret 'openai_api_key' has been updated successfully"
}
```

#### List Well-Known Secrets

```http
GET /api/secrets/well-known

Response:
{
  "categories": {
    "llm": [
      {
        "secret_name": "openai_api_key",
        "display_name": "OpenAI API Key",
        "description": "API key for GPT models",
        "category": "llm"
      },
      ...
    ]
  }
}
```

## Supported Secret Types

### LLM Providers

| Secret Name          | Display Name       | Provider           |
| -------------------- | ------------------ | ------------------ |
| `openai_api_key`     | OpenAI API Key     | OpenAI             |
| `anthropic_api_key`  | Anthropic API Key  | Anthropic (Claude) |
| `deepgram_api_key`   | Deepgram API Key   | Deepgram (STT)     |
| `elevenlabs_api_key` | ElevenLabs API Key | ElevenLabs (TTS)   |

### Integrations

| Secret Name        | Display Name     | Integration   |
| ------------------ | ---------------- | ------------- |
| `github_token`     | GitHub Token     | GitHub API    |
| `notion_api_token` | Notion API Token | Notion API    |
| `n8n_api_key`      | n8n API Key      | n8n Workflows |

### Infrastructure

| Secret Name          | Display Name       | Service |
| -------------------- | ------------------ | ------- |
| `livekit_api_key`    | LiveKit API Key    | LiveKit |
| `livekit_api_secret` | LiveKit API Secret | LiveKit |

## Migration from Environment Variables

### Step 1: Start LocalStack

```bash
docker-compose up -d localstack

# Verify it's running
curl http://localhost:4566/_localstack/health
```

### Step 2: Migrate Secrets via UI

1. Navigate to Organization Settings → Secrets
2. For each configured API key:
   - Click "Add Key" or "Rotate Key"
   - Paste the value from your `.env` file
   - Click "Save & Overwrite"

### Step 3: Migrate Secrets via API (Batch)

```python
# scripts/migrate_secrets.py
import asyncio
import os
from backend.config.secrets import secrets_manager

async def migrate_org_secrets(org_id: str):
    """Migrate secrets from env vars to LocalStack"""

    secrets_to_migrate = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "deepgram_api_key": os.getenv("DEEPGRAM_API_KEY"),
        "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
        "notion_api_token": os.getenv("NOTION_API_TOKEN"),
    }

    for secret_name, secret_value in secrets_to_migrate.items():
        if secret_value:
            print(f"Migrating {secret_name}...")
            await secrets_manager.upsert_secret(
                organization_id=org_id,
                secret_name=secret_name,
                secret_value=secret_value
            )
            print(f"✓ {secret_name} migrated")

# Run migration
asyncio.run(migrate_org_secrets("your-org-id"))
```

### Step 4: Update Agent Code

**Before:**

```python
import os
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

**After:**

```python
from backend.config.secrets import get_llm_api_key

api_key = await get_llm_api_key(org_id, "openai")
llm = ChatOpenAI(api_key=api_key)
```

### Step 5: Remove from .env (Optional)

Once migrated, you can remove from `.env`:

```bash
# ❌ Remove these (now in LocalStack)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# DEEPGRAM_API_KEY=...
```

## Security Best Practices

### ✅ DO

- **Use secrets_manager for all API keys**
- **Check has_secret() before showing UI**
- **Log all secret operations (audit trail)**
- **Rotate secrets regularly via UI**
- **Use domain-scoped secrets when possible**
- **Validate API keys before saving** (if validation endpoint available)

### ❌ DON'T

- **Never log secret values**
- **Never return secrets in API responses**
- **Never store secrets in frontend state**
- **Never commit secrets to git**
- **Never send secrets to frontend (even encrypted)**
- **Never expose get_secret() via API**

## Testing

### Local Development

```bash
# Start LocalStack
docker-compose up -d localstack

# Test secret operations
curl http://localhost:4566/_localstack/health

# View secrets in LocalStack
awslocal secretsmanager list-secrets

# Get a secret (CLI only, for testing)
awslocal secretsmanager get-secret-value \
  --secret-id agentfoundry/dev/test-org/shared/openai_api_key
```

### Integration Tests

```python
import pytest
from backend.config.secrets import secrets_manager

@pytest.mark.asyncio
async def test_secret_lifecycle():
    org_id = "test-org"
    secret_name = "test_api_key"
    secret_value = "test-value-123"

    # Create
    success = await secrets_manager.upsert_secret(
        org_id, secret_name, secret_value
    )
    assert success

    # Check exists
    exists = await secrets_manager.has_secret(org_id, secret_name)
    assert exists

    # Retrieve
    retrieved = await secrets_manager.get_secret(org_id, secret_name)
    assert retrieved == secret_value

    # Delete
    deleted = await secrets_manager.delete_secret(org_id, secret_name, force=True)
    assert deleted

    # Verify gone
    exists = await secrets_manager.has_secret(org_id, secret_name)
    assert not exists
```

## Production Deployment

### AWS Secrets Manager

In production, set `ENVIRONMENT=production` and the system automatically uses
AWS Secrets Manager:

```yaml
# production.env
ENVIRONMENT=production AWS_REGION=us-east-1
# IAM role provides credentials automatically
```

**No code changes needed** - same API works for both LocalStack and AWS.

### IAM Permissions

Required IAM permissions for backend service:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:CreateSecret",
        "secretsmanager:GetSecretValue",
        "secretsmanager:PutSecretValue",
        "secretsmanager:DescribeSecret",
        "secretsmanager:DeleteSecret",
        "secretsmanager:ListSecrets"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:agentfoundry/*"
    }
  ]
}
```

## Troubleshooting

### LocalStack Not Starting

```bash
# Check logs
docker-compose logs localstack

# Verify port not in use
lsof -ti:4566

# Restart
docker-compose restart localstack
```

### Secret Not Found

```python
# Check if secret exists
exists = await secrets_manager.has_secret(org_id, secret_name)

# Check secret ID format
secret_id = secrets_manager.get_secret_id(org_id, domain_id, secret_name)
print(f"Looking for: {secret_id}")

# List all secrets for org
secrets = await secrets_manager.list_secrets(org_id)
print(f"Found: {secrets}")
```

### Permission Denied

```bash
# LocalStack: Check endpoint
echo $LOCALSTACK_ENDPOINT  # Should be http://localstack:4566

# AWS: Check IAM role
aws sts get-caller-identity

# Check region
echo $AWS_REGION
```

## Summary

### Key Features

- ✅ **Blind Write Pattern** - Frontend cannot read secrets
- ✅ **Organization Scoped** - Multi-tenant isolation
- ✅ **LocalStack Dev** - Full AWS compatibility locally
- ✅ **Zero Code Changes** - Dev → Prod seamless transition
- ✅ **Audit Logged** - All operations tracked
- ✅ **Type Safe** - Well-known secret types defined

### Configuration Hierarchy

```
User Action (Browser)
  ↓
React UI (Blind Write)
  ↓
FastAPI Routes (RBAC Protected)
  ↓
Secrets Service (Python)
  ↓
LocalStack/AWS Secrets Manager
  ↓
Encrypted Storage
```

This architecture ensures secrets are:

- **Never exposed** to frontend
- **Organization isolated** (multi-tenant safe)
- **Production ready** (AWS compatible)
- **Developer friendly** (LocalStack for local dev)
- **Audit compliant** (all operations logged)

## References

- [Backend Secrets Config](../backend/config/secrets.py)
- [API Routes](../backend/routes/secrets.py)
- [React Components](../app/components/secrets/)
- [Docker Compose](../docker-compose.yml)
- [LocalStack Docs](https://docs.localstack.cloud/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
