# OpenFGA + LocalStack Integration

## Architecture: Separation of Concerns

### Clear Responsibilities

```
┌─────────────────────────────────────────────────┐
│              User Request                        │
│  "Update OpenAI API key for acme-corp"          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              OpenFGA (Authorization)             │
│  Question: "Can user:alice update this secret?" │
│  Answer: Check relationship graph                │
│    - alice is admin of organization:acme-corp?  │
│    - secret parent_org is acme-corp?            │
│  Result: ALLOWED ✅                             │
└──────────────────┬──────────────────────────────┘
                   │ Authorization passed
┌──────────────────▼──────────────────────────────┐
│         LocalStack (Secret Storage)              │
│  Action: Store secret value                      │
│  Location: agentfoundry/dev/acme-corp/shared/   │
│            openai_api_key                        │
│  Value: sk-... (encrypted)                       │
│  Result: Stored ✅                              │
└──────────────────────────────────────────────────┘
```

### Who Does What

| System         | Responsibility    | Example                       |
| -------------- | ----------------- | ----------------------------- |
| **OpenFGA**    | **Authorization** | "Can alice update secret X?"  |
| **LocalStack** | **Storage**       | "Store/retrieve secret value" |
| **Backend**    | **Orchestration** | "Check auth, then store"      |

## Current Implementation

### Secrets Route with Both Systems

```python
# backend/routes/secrets.py

@router.put("/{org_id}/{secret_name}")
async def upsert_secret(
    org_id: str,
    secret_name: str,
    payload: SecretUpsertRequest,
    context: AuthContext = Depends(get_current_user)
):
    # Step 1: OpenFGA checks authorization
    secret_id = secrets_manager.get_secret_id(org_id, None, secret_name)

    can_update = await context.can("can_update", f"secret:{secret_id}")
    can_manage_org = await context.can("can_manage_secrets", f"organization:{org_id}")

    if not (can_update or can_manage_org):
        raise HTTPException(403, "Cannot update secret")

    # Step 2: LocalStack stores the secret
    success = await secrets_manager.upsert_secret(
        organization_id=org_id,
        secret_name=secret_name,
        secret_value=payload.secret_value,  # Never logged
        domain_id=payload.domain_id
    )

    # Step 3: Audit log (WHO, not WHAT)
    await log_auth_event(
        request=request,
        action="secret.update",
        resource_type="secret",
        resource_id=secret_id,
        result="success"
    )
```

## Authorization Model for Secrets

### OpenFGA Relationships

```typescript
// openfga/authorization_model.fga

type secret
  relations
    define parent_org: [organization]
    define parent_domain: [domain]
    define owner: [user]
    define viewer: [user]

    // Computed permissions
    define can_read_status: viewer or owner or parent_org->member
    define can_update: owner or parent_org->admin or parent_domain->owner
    define can_delete: owner or parent_org->admin
```

### Example Relationships

```
# Secret belongs to organization
{
  user: "organization:acme-corp",
  relation: "parent_org",
  object: "secret:agentfoundry/dev/acme-corp/shared/openai_api_key"
}

# Alice is owner of this secret
{
  user: "user:alice",
  relation: "owner",
  object: "secret:agentfoundry/dev/acme-corp/shared/openai_api_key"
}

# Bob is admin of acme-corp (can manage all org secrets)
{
  user: "user:bob",
  relation: "admin",
  object: "organization:acme-corp"
}

# Result:
# - Alice can update (owner)
# - Bob can update (admin of parent_org)
# - Charlie cannot update (no relationship)
```

## Secret Lifecycle with Both Systems

### 1. Create Secret

```
User → Frontend
  ↓ PUT /api/secrets/acme-corp/openai_api_key
Backend
  ↓
┌─────────────────────────────────────┐
│ Step 1: OpenFGA Authorization       │
├─────────────────────────────────────┤
│ Check: can_update on secret         │
│ OR can_manage_secrets on org        │
│ Result: ALLOWED ✅                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Step 2: LocalStack Storage          │
├─────────────────────────────────────┤
│ CreateSecret or PutSecretValue      │
│ Path: agentfoundry/dev/acme-corp/   │
│       shared/openai_api_key         │
│ Value: sk-... (encrypted at rest)   │
│ Result: Stored ✅                   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Step 3: OpenFGA Relationship        │
├─────────────────────────────────────┤
│ Write tuple:                         │
│ - user:alice → owner → secret:X     │
│ - org:acme → parent_org → secret:X  │
│ Result: Relationships created ✅    │
└─────────────────────────────────────┘
```

### 2. Read Secret (Backend Only)

```
Agent Execution
  ↓
Backend needs OpenAI key for org
  ↓
┌─────────────────────────────────────┐
│ Step 1: OpenFGA Check (Optional)    │
├─────────────────────────────────────┤
│ Backend has service account         │
│ Service account can read secrets    │
│ Result: ALLOWED ✅                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Step 2: LocalStack Retrieval        │
├─────────────────────────────────────┤
│ GetSecretValue from LocalStack      │
│ Path: agentfoundry/dev/acme-corp/   │
│       shared/openai_api_key         │
│ Result: sk-... (decrypted)          │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Step 3: Use Secret                  │
├─────────────────────────────────────┤
│ Execute agent with API key          │
│ Never log or expose the value       │
│ Result: Agent executed ✅           │
└─────────────────────────────────────┘
```

### 3. Check Secret Status (Frontend Safe)

```
User → Frontend
  ↓ GET /api/secrets/acme-corp/openai_api_key
Backend
  ↓
┌─────────────────────────────────────┐
│ Step 1: OpenFGA Authorization       │
├─────────────────────────────────────┤
│ Check: can_read_status on secret    │
│ Result: ALLOWED ✅                  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│ Step 2: LocalStack Metadata Only    │
├─────────────────────────────────────┤
│ DescribeSecret (NOT GetSecretValue) │
│ Returns: exists=true, last_updated  │
│ Does NOT return the actual value    │
│ Result: {configured: true} ✅       │
└─────────────────────────────────────┘
```

## Why Both Systems?

### OpenFGA Answers: "CAN user do action?"

```python
# Authorization questions
- Can alice update secret:openai_key?
- Can bob read secret:github_token?
- Can charlie delete secret:anthropic_key?

# Hierarchical inheritance
- Bob is admin of organization:acme-corp
- organization:acme-corp is parent_org of secret:openai_key
- Therefore: Bob can manage all secrets in acme-corp
```

### LocalStack Answers: "WHAT is the secret value?"

```python
# Storage operations
- Store secret value (encrypted)
- Retrieve secret value (for backend use only)
- Check if secret exists (metadata only)
- Delete secret

# Never answers authorization questions!
```

## Integration Points

### 1. Secret Creation Flow

```python
# backend/routes/secrets.py

@router.put("/{org_id}/{secret_name}")
async def upsert_secret(...):
    # OpenFGA: Check permission
    if not await context.can("can_update", f"secret:{secret_id}"):
        raise HTTPException(403)

    # LocalStack: Store value
    await secrets_manager.upsert_secret(org_id, secret_name, value)

    # OpenFGA: Create relationships (if new secret)
    await fga_client.write([
        {
            "user": f"organization:{org_id}",
            "relation": "parent_org",
            "object": f"secret:{secret_id}"
        },
        {
            "user": context.get_fga_user(),
            "relation": "owner",
            "object": f"secret:{secret_id}"
        }
    ])
```

### 2. Secret Retrieval (Backend)

```python
# backend/agents/execute_agent.py

async def execute_agent(agent_id: str, org_id: str):
    # Get secret from LocalStack
    # (Backend service account authorized via OpenFGA)
    api_key = await get_llm_api_key(org_id, "openai")

    # Use secret
    llm = ChatOpenAI(api_key=api_key)
    response = await llm.ainvoke("Hello")
```

### 3. Secret Status Check (Frontend)

```typescript
// Frontend component
const response = await fetch(`${apiUrl}/api/secrets/${orgId}/${secretName}`);

// Backend checks OpenFGA: can_read_status
// Backend checks LocalStack: DescribeSecret (metadata only)
// Returns: { configured: true }
// NEVER returns actual secret value
```

## Security Model

### Defense in Depth

| Layer             | System     | Protection         |
| ----------------- | ---------- | ------------------ |
| **Authorization** | OpenFGA    | WHO can access     |
| **Storage**       | LocalStack | WHAT is encrypted  |
| **Transport**     | HTTPS      | Data in transit    |
| **Audit**         | Backend    | WHO did WHAT, WHEN |
| **Blind Write**   | Frontend   | Can't read secrets |

### Attack Scenarios

#### Scenario 1: XSS Attack on Frontend

```
Attacker compromises frontend JavaScript
  ↓
Tries to read API keys via API
  ↓
Backend returns: { configured: true }
  ↓
BLOCKED: Actual values never sent to frontend ✅
```

#### Scenario 2: Unauthorized Backend Access

```
Attacker gets backend access
  ↓
Tries to read secret for org they don't own
  ↓
OpenFGA check: DENIED ❌
  ↓
LocalStack call never made
  ↓
BLOCKED: Authorization prevents access ✅
```

#### Scenario 3: LocalStack Compromise

```
Attacker gains LocalStack access
  ↓
Can read encrypted secrets
  ↓
But: Secrets are encrypted at rest
  ↓
MITIGATED: Encryption provides additional layer ✅
```

## Configuration

### Environment Variables

```yaml
# docker-compose.yml

foundry-backend:
  environment:
    # OpenFGA configuration
    - SVC_OPENFGA_HOST=openfga
    - OPENFGA_HTTP_PORT=8081
    - OPENFGA_STORE_ID=${OPENFGA_STORE_ID}
    - OPENFGA_AUTH_MODEL_ID=${OPENFGA_AUTH_MODEL_ID}

    # LocalStack configuration
    - SVC_LOCALSTACK_HOST=localstack
    - LOCALSTACK_PORT=4566
    - AWS_REGION=us-east-1
```

### No Secrets in Environment!

```yaml
# ❌ OLD WAY - Secrets as env vars
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
# ✅ NEW WAY - Secrets in LocalStack
# Backend retrieves from LocalStack based on organization context
# OpenFGA controls who can access
```

## Permission Examples

### 1. Org Admin Can Manage All Secrets

```python
# OpenFGA tuple
{
  "user": "user:alice",
  "relation": "admin",
  "object": "organization:acme-corp"
}

# Result: Alice can manage ANY secret in acme-corp
# via: parent_org->admin in secret definition
```

### 2. Domain Owner Can Manage Domain Secrets

```python
# OpenFGA tuples
{
  "user": "user:bob",
  "relation": "owner",
  "object": "domain:card-services"
}
{
  "user": "domain:card-services",
  "relation": "parent_domain",
  "object": "secret:agentfoundry/dev/acme/card-services/openai_key"
}

# Result: Bob can manage secrets scoped to his domain
```

### 3. User Can Only View Status

```python
# OpenFGA tuple
{
  "user": "user:charlie",
  "relation": "viewer",
  "object": "secret:agentfoundry/dev/acme/shared/openai_key"
}

# Result: Charlie can see "configured: true" but not the value
```

## Implementation Pattern

### When Creating Resource (Agent, Domain, etc.)

```python
async def create_agent(agent_data, context: AuthContext):
    # 1. Create in database
    agent_id = db.create_agent(agent_data)

    # 2. Get org-specific secrets from LocalStack
    api_key = await get_llm_api_key(
        organization_id=context.organization_id,
        provider="openai",
        domain_id=agent_data.domain_id
    )

    # 3. Set up OpenFGA relationships
    await fga_client.write([
        {
            "user": f"domain:{agent_data.domain_id}",
            "relation": "parent_domain",
            "object": f"agent:{agent_id}"
        },
        {
            "user": context.get_fga_user(),
            "relation": "owner",
            "object": f"agent:{agent_id}"
        }
    ])

    return agent_id
```

### When Executing Agent

```python
async def execute_agent(agent_id: str, input: str, context: AuthContext):
    # 1. OpenFGA checks authorization
    if not await context.can("can_execute", f"agent:{agent_id}"):
        raise HTTPException(403, "Cannot execute agent")

    # 2. Get agent metadata (includes org_id)
    agent = await get_agent(agent_id)

    # 3. LocalStack retrieves org-specific API key
    api_key = await get_llm_api_key(
        organization_id=agent.organization_id,
        provider="openai",
        domain_id=agent.domain_id
    )

    # 4. Execute with org-specific credentials
    llm = ChatOpenAI(api_key=api_key)
    response = await agent.graph.ainvoke(input)

    return response
```

## Multi-Tenant Isolation

### Each Organization Has Own Secrets

```
LocalStack Secrets:
├── agentfoundry/dev/acme-corp/
│   ├── shared/
│   │   ├── openai_api_key
│   │   └── anthropic_api_key
│   └── card-services/
│       └── livekit_token
│
└── agentfoundry/dev/globaltech/
    ├── shared/
    │   ├── openai_api_key (different key!)
    │   └── anthropic_api_key (different key!)
    └── finance/
        └── quickbooks_token
```

### OpenFGA Enforces Boundaries

```python
# User from acme-corp tries to access globaltech secret
await context.can("can_read", "secret:agentfoundry/dev/globaltech/shared/openai_key")

# OpenFGA checks:
# - Is user member of organization:globaltech? → NO
# - Is user owner of this secret? → NO
# Result: DENIED ❌
```

## Practical Examples

### Example 1: New Organization Setup

```python
# 1. Create organization (OpenFGA)
await fga_client.setup_organization(
    org_id="acme-corp",
    owner_id="alice"
)

# 2. Add initial secrets (LocalStack via backend)
await secrets_manager.upsert_secret(
    organization_id="acme-corp",
    secret_name="openai_api_key",
    secret_value="sk-..."
)

# 3. Create secret relationship (OpenFGA)
await fga_client.write([{
    "user": "organization:acme-corp",
    "relation": "parent_org",
    "object": "secret:agentfoundry/dev/acme-corp/shared/openai_api_key"
}])

# Result:
# - Org admins can manage this secret
# - Secret value stored encrypted in LocalStack
# - Audit trail in both systems
```

### Example 2: Share Secret with User

```python
# Grant read-only access to specific secret
await fga_client.write([{
    "user": "user:bob",
    "relation": "viewer",
    "object": "secret:agentfoundry/dev/acme-corp/shared/openai_api_key"
}])

# Bob can now:
# - See that secret is configured (can_read_status)
# - But CANNOT get the actual value (not in backend, only backend service can)
```

### Example 3: Rotate Secret

```python
# User rotates API key
# 1. OpenFGA checks: can_update
# 2. LocalStack: PutSecretValue (overwrites old value)
# 3. Old value is immediately inaccessible
# 4. Audit log records WHO rotated (not new value)
```

## Migration from Environment Variables

### Before (Insecure)

```yaml
# docker-compose.yml - SECRETS VISIBLE
environment:
  - OPENAI_API_KEY=sk-proj-abc123...
  - ANTHROPIC_API_KEY=sk-ant-xyz789...
  - GITHUB_TOKEN=ghp_def456...
```

### After (Secure)

```yaml
# docker-compose.yml - NO SECRETS
environment:
  - SVC_LOCALSTACK_HOST=localstack
  - SVC_OPENFGA_HOST=openfga
  # Secrets retrieved at runtime from LocalStack
  # Authorization checked via OpenFGA
```

### Migration Script

```python
# scripts/migrate_env_to_localstack.py
import asyncio
import os
from backend.config.secrets import secrets_manager
from backend.openfga_client import fga_client

async def migrate_org_secrets(org_id: str, owner_id: str):
    """Migrate secrets from .env to LocalStack with OpenFGA relationships"""

    secrets_to_migrate = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
        "deepgram_api_key": os.getenv("DEEPGRAM_API_KEY"),
        "elevenlabs_api_key": os.getenv("ELEVENLABS_API_KEY"),
    }

    for secret_name, secret_value in secrets_to_migrate.items():
        if not secret_value:
            continue

        print(f"Migrating {secret_name}...")

        # 1. Store in LocalStack
        await secrets_manager.upsert_secret(
            organization_id=org_id,
            secret_name=secret_name,
            secret_value=secret_value
        )

        # 2. Create OpenFGA relationships
        secret_id = secrets_manager.get_secret_id(org_id, None, secret_name)
        await fga_client.write([
            # Link to org
            {
                "user": f"organization:{org_id}",
                "relation": "parent_org",
                "object": f"secret:{secret_id}"
            },
            # Set owner
            {
                "user": f"user:{owner_id}",
                "relation": "owner",
                "object": f"secret:{secret_id}"
            }
        ])

        print(f"  ✓ {secret_name} migrated")

    print("\n✅ Migration complete!")
    print("You can now remove secrets from .env")

# Run
asyncio.run(migrate_org_secrets("your-org-id", "your-user-id"))
```

## Summary

### Clear Separation of Concerns

| Question                         | System     | Method                         |
| -------------------------------- | ---------- | ------------------------------ |
| "Can user X update secret Y?"    | OpenFGA    | `fga_client.check()`           |
| "What is the value of secret Y?" | LocalStack | `secrets_manager.get_secret()` |
| "Who can access secret Y?"       | OpenFGA    | `fga_client.read()`            |
| "Is secret Y configured?"        | LocalStack | `secrets_manager.has_secret()` |

### Benefits of Integration

✅ **Authorization** separate from **Storage**  
✅ **Fine-grained** permissions (per-secret)  
✅ **Hierarchical** (org admins → all secrets)  
✅ **Auditable** (both systems log)  
✅ **Secure** (blind write + encryption)  
✅ **Scalable** (proven architectures)

---

**OpenFGA:** WHO can do WHAT  
**LocalStack:** WHERE secrets are stored  
**Backend:** Orchestrates both systems

This is **enterprise-grade security architecture!** 🔒
