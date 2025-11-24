# Secrets Management Quick Start

## 5-Minute Setup

### 1. Add Dependencies

```bash
# Add boto3 for AWS SDK
echo "boto3>=1.34.0" >> requirements.txt
pip install boto3
```

### 2. Start LocalStack

```bash
# Start all services (includes LocalStack)
docker-compose up -d

# Verify LocalStack is running
curl http://localhost:4566/_localstack/health
```

### 3. Test Secret Operations

```bash
# From your workspace root
python3 << EOF
import asyncio
from backend.config.secrets import secrets_manager

async def test():
    # Create a secret
    await secrets_manager.upsert_secret(
        organization_id="test-org",
        secret_name="openai_api_key",
        secret_value="sk-test-123"
    )
    print("✓ Secret created")

    # Check it exists
    exists = await secrets_manager.has_secret(
        organization_id="test-org",
        secret_name="openai_api_key"
    )
    print(f"✓ Secret exists: {exists}")

    # Retrieve it
    value = await secrets_manager.get_secret(
        organization_id="test-org",
        secret_name="openai_api_key"
    )
    print(f"✓ Retrieved: {value}")

asyncio.run(test())
EOF
```

### 4. Access UI

Navigate to: `http://localhost:3000/settings/secrets`

Or integrate the component:

```tsx
// app/settings/secrets/page.tsx
import { SecretsManagementPanel } from '@/components/secrets/SecretsManagementPanel';

export default function SecretsPage() {
  return (
    <div className="container mx-auto py-8">
      <SecretsManagementPanel
        organizationId="your-org-id"
        domainId="optional-domain-id"
      />
    </div>
  );
}
```

## API Usage Examples

### Backend (Agent Execution)

```python
from backend.config.secrets import get_llm_api_key

async def run_agent(org_id: str, domain_id: str):
    # Get API key for this organization
    api_key = await get_llm_api_key(org_id, "openai", domain_id)

    if not api_key:
        raise ValueError("OpenAI API key not configured")

    # Use it
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(api_key=api_key, model="gpt-4")
    response = await llm.ainvoke("Hello!")
    return response
```

### Frontend (Status Check)

```tsx
'use client';
import { useState, useEffect } from 'react';
import { getServiceUrl } from '@/lib/config/services';

export function SecretStatus({ orgId, secretName }) {
  const [configured, setConfigured] = useState(false);

  useEffect(() => {
    fetch(`${getServiceUrl('backend')}/api/secrets/${orgId}/${secretName}`)
      .then((res) => res.json())
      .then((data) => setConfigured(data.configured));
  }, [orgId, secretName]);

  return (
    <span className={configured ? 'text-green-600' : 'text-gray-400'}>
      {configured ? '● Configured' : '○ Not Configured'}
    </span>
  );
}
```

## Environment Variables

### Development (.env)

```bash
# LocalStack (development)
ENVIRONMENT=development
LOCALSTACK_ENDPOINT=http://localstack:4566
AWS_REGION=us-east-1

# Legacy keys (optional - for backward compatibility)
# These will be checked if secrets aren't in LocalStack
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Production (.env.production)

```bash
# AWS Secrets Manager (production)
ENVIRONMENT=production
AWS_REGION=us-east-1
# IAM role provides credentials automatically - no keys needed!
```

## Common Operations

### Create/Update Secret

```bash
curl -X PUT http://localhost:8000/api/secrets/acme-corp/openai_api_key \
  -H "Content-Type: application/json" \
  -d '{
    "secret_value": "sk-...",
    "domain_id": "card-services",
    "description": "Production OpenAI key"
  }'
```

### Check Secret Status

```bash
curl http://localhost:8000/api/secrets/acme-corp/openai_api_key
```

### List All Secrets for Org

```bash
curl http://localhost:8000/api/secrets/acme-corp/status
```

### Delete Secret

```bash
curl -X DELETE "http://localhost:8000/api/secrets/acme-corp/openai_api_key?force=true"
```

## Migration Script

Migrate all secrets from `.env` to LocalStack:

```python
# scripts/migrate_secrets_to_localstack.py
import asyncio
import os
from dotenv import load_dotenv
from backend.config.secrets import secrets_manager

# Load from .env
load_dotenv()

async def migrate():
    org_id = input("Enter organization ID: ")

    secrets = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "deepgram_api_key": os.getenv("DEEPGRAM_API_KEY"),
        "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
        "notion_api_token": os.getenv("NOTION_API_TOKEN"),
        "n8n_api_key": os.getenv("N8N_API_KEY"),
    }

    print(f"\nMigrating secrets for organization: {org_id}\n")

    for name, value in secrets.items():
        if value:
            print(f"  Migrating {name}... ", end="")
            success = await secrets_manager.upsert_secret(
                organization_id=org_id,
                secret_name=name,
                secret_value=value,
                description=f"Migrated from .env"
            )
            print("✓" if success else "✗")

    print("\nMigration complete!")
    print("You can now remove these from your .env file.")

if __name__ == "__main__":
    asyncio.run(migrate())
```

Run it:

```bash
python scripts/migrate_secrets_to_localstack.py
```

## Troubleshooting

### LocalStack Not Running

```bash
docker-compose ps localstack
docker-compose logs localstack
docker-compose restart localstack
```

### Cannot Connect to LocalStack

```bash
# Check endpoint
curl http://localhost:4566/_localstack/health

# Inside container
docker-compose exec foundry-backend curl http://localstack:4566/_localstack/health
```

### Secrets Not Persisting

LocalStack persistence is enabled by default in docker-compose.yml:

```yaml
localstack:
  environment:
    - PERSISTENCE=1
    - DATA_DIR=/var/lib/localstack/data
  volumes:
    - localstack-data:/var/lib/localstack
```

### List All Secrets (Debug)

```bash
# Using AWS CLI with LocalStack
docker-compose exec localstack awslocal secretsmanager list-secrets

# Or from host (if awslocal installed)
AWS_ENDPOINT_URL=http://localhost:4566 \
AWS_ACCESS_KEY_ID=test \
AWS_SECRET_ACCESS_KEY=test \
aws secretsmanager list-secrets
```

## Next Steps

1. **Read full docs:** [SECRETS_MANAGEMENT.md](./SECRETS_MANAGEMENT.md)
2. **Integrate RBAC:** Add permission checks to routes
3. **Add validation:** Validate API keys before saving
4. **Enable audit:** Configure audit logging
5. **Plan migration:** Move existing secrets to LocalStack

## Support

- **Documentation:** `/docs/SECRETS_MANAGEMENT.md`
- **API Reference:** http://localhost:8000/docs (FastAPI auto-docs)
- **LocalStack:** https://docs.localstack.cloud/
- **AWS Secrets Manager:** https://docs.aws.amazon.com/secretsmanager/

---

**Status:** ✅ Ready for Development  
**Production:** ✅ AWS Compatible  
**Security:** ✅ Blind Write Pattern
