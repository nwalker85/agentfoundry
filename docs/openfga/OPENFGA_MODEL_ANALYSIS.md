# OpenFGA Authorization Model Analysis

## Overview

This model provides a **mature, production-ready authorization hierarchy** for
Agent Foundry.

---

## 🎯 Key Improvements Over Initial Model

### 1. **Better Hierarchy** ✅

```
Platform (global admins)
  ↓
Tenant (billing, top-level isolation)
  ↓
Organization (business entity)
  ↓
Project (initiative/product)
  ↓
Domain (knowledge vertical)
  ↓ (can nest: parent domain)
  ↓
Assets (agents, reports, configs, datasets, tools)
```

**vs. My Initial (Simplified):**

```
Organization
  ↓
Domain
  ↓
Agent, Secret
```

### 2. **Team Support** ✅

```fga
type team
  relations
    define lead: [user]
    define member: [user, user:*] or lead
```

**Benefits:**

- Group-based access
- Team leads automatically members
- Can assign teams to projects (`team_visibility`)

### 3. **System Agent Protection** ✅

```fga
type agent
  relations
    define is_system: [platform]

    # Cannot modify system agents
    define can_write: ... but not is_system
    define can_delete: ... but not is_system
```

**Critical for:**

- Marshal Agent (can't be deleted)
- Supervisor Agent (protected)
- System observability agents

### 4. **Multiple Asset Types** ✅

Instead of just `agent`, you have:

- `agent` - LangGraph executables
- `report` - Analytics/dashboards
- `config` - Configuration assets
- `dataset` - RAG/vector stores
- `tool` - MCP integrations

### 5. **Compliance Role** ✅

```fga
type domain
  relations
    define compliance_officer: [user]
    define can_manage_compliance: compliance_officer or admin
```

**Use case:** Financial services, healthcare (HIPAA, SOC2)

### 6. **Subdomain Support** ✅

```fga
type domain
  relations
    define parent: [domain]

    # Permission cascades from parent
    define can_read: ... or can_read from parent
```

**Example:**

```
finance (domain)
  ↳ accounts-payable (subdomain)
  ↳ accounts-receivable (subdomain)
```

### 7. **Shared Datasets** ✅

```fga
type dataset
  relations
    define is_shared: [organization]
    define can_read: ... or member from is_shared
```

**Use case:** Org-wide knowledge bases, shared embeddings

---

## 🔍 Detailed Analysis

### Hierarchy Benefits

#### Permission Cascading

```
tenant:admin
  ↓ cascades to
organization:admin (via "admin from tenant")
  ↓ cascades to
project:can_write (via "can_write from organization")
  ↓ cascades to
domain:can_write (via "can_write from project")
  ↓ cascades to
agent:can_write (via "can_write from domain")
```

**Result:** Tenant admin can write ANY agent in ANY domain!

#### Team-Based Access

```
team:backend-engineers
  members: [alice, bob, charlie]
  ↓
project:customer-portal
  team_visibility: [team:backend-engineers]
  ↓
All team members can view the project
```

### Exclusion Patterns

```fga
define can_write: owner or can_write from domain but not is_system
```

**Meaning:** You can write IF (owner OR inherited) AND NOT (system agent)

**Use cases:**

- Protect system agents from modification
- Prevent deletion of critical infrastructure
- Preserve platform-level assets

### Role-Specific Permissions

```fga
# Compliance officer can manage compliance
define can_manage_compliance: compliance_officer or admin

# Only specific tool invocation
define can_invoke: can_read
```

---

## 🎨 Recommended Enhancements

### 1. Add Secrets Type (As We Discussed)

```fga
type secret
  relations
    define organization: [organization]
    define domain: [domain]
    define owner: [user]
    define viewer: [user]

    # IMPORTANT: can_read_value is NEVER granted (blind write pattern)
    define can_read_status: viewer or owner or can_read from organization
    define can_update: owner or admin from organization
    define can_delete: owner or admin from organization
    define can_rotate: can_update
```

### 2. Add Session Type

```fga
type session
  relations
    define agent: [agent]
    define owner: [user]
    define viewer: [user]

    define can_read: owner or viewer or can_read from agent
    define can_terminate: owner or admin from agent
    define can_replay: can_read
```

### 3. Add Graph Type (Forge)

```fga
type graph
  relations
    define domain: [domain]
    define owner: [user]
    define editor: [user, team#member]
    define viewer: [user, team#member]

    define can_read: viewer or editor or owner or can_read from domain
    define can_update: editor or owner or can_write from domain
    define can_deploy: owner or admin from domain
    define can_delete: owner or can_delete from domain
    define can_share: owner
```

---

## 🚀 Migration Strategy

### Phase 1: Update Authorization Model File

Replace `openfga/authorization_model.fga` with this enhanced model.

### Phase 2: Load New Model

```bash
# Load with FGA CLI
fga model write \
  --store-id 01KATFSA1G5FRN6682HGAJX6XR \
  --file openfga/authorization_model.fga \
  --api-url http://localhost:9080

# Get new MODEL_ID

# Store in LocalStack
python scripts/openfga_setup_localstack.py \
  01KATFSA1G5FRN6682HGAJX6XR \
  <NEW_MODEL_ID>
```

### Phase 3: Update Backend Routes

```python
# Example: Protect system agents
@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, context: AuthContext = ...):
    # OpenFGA will check: can_delete (which excludes is_system)
    if not await context.can("can_delete", f"agent:{agent_id}"):
        raise HTTPException(403, "Cannot delete this agent")

    # If agent is system agent, OpenFGA returns False automatically
```

### Phase 4: Set Up Initial Relationships

```python
# Mark system agents
await fga_client.write([
    {
        "user": "platform:agent-foundry",
        "relation": "is_system",
        "object": "agent:marshal-agent"
    },
    {
        "user": "platform:agent-foundry",
        "relation": "is_system",
        "object": "agent:supervisor-agent"
    }
])

# Create tenant → org → project → domain hierarchy
await fga_client.write([
    {
        "user": "tenant:acme-tenant",
        "relation": "tenant",
        "object": "organization:acme-corp"
    },
    {
        "user": "organization:acme-corp",
        "relation": "organization",
        "object": "project:customer-portal"
    },
    {
        "user": "project:customer-portal",
        "relation": "project",
        "object": "domain:card-services"
    }
])
```

---

## 💡 Key Features

### 1. Multi-Tenancy

```
tenant:enterprise-client
  ↓ has
organization:acme-corp
organization:globaltech-inc

Tenant admin can manage both orgs
Org admins stay within their org
```

### 2. Team-Based Access

```
team:backend-engineers
  members: [alice, bob]
  ↓ assigned to
project:api-platform
  ↓
All team members get project access
```

### 3. Compliance

```
domain:patient-records
  compliance_officer: [user:jane]
  ↓
Jane can manage_compliance but not write agents
```

### 4. Subdomain Hierarchy

```
domain:finance
  ↳ domain:accounts-payable (parent: finance)
  ↳ domain:accounts-receivable (parent: finance)

finance admin → AP and AR access automatically
```

### 5. Shared Resources

```
dataset:company-knowledge-base
  is_shared: [organization:acme-corp]
  ↓
All org members can read
Only owner can write
```

---

## 🎯 Recommended Implementation Order

### Week 1: Core Hierarchy

1. Load this model into OpenFGA
2. Set up tenant → org → project → domain relationships
3. Test permission cascading
4. Update agent creation to use domain relationship

### Week 2: Teams

1. Implement team management endpoints
2. Add team-based project visibility
3. Test team member access

### Week 3: Assets

1. Add report, config, dataset types
2. Implement asset creation with proper relationships
3. Test asset permissions

### Week 4: Advanced

1. Add subdomain support
2. Implement compliance roles
3. Add system agent protection
4. Performance testing

---

## 🔥 This Model vs. My Simple Model

| Feature               | My Model          | This Model                                         | Better? |
| --------------------- | ----------------- | -------------------------------------------------- | ------- |
| **Hierarchy Depth**   | 2 levels          | 5 levels                                           | ✅ YES  |
| **Team Support**      | ❌ None           | ✅ Built-in                                        | ✅ YES  |
| **System Protection** | ❌ None           | ✅ `but not is_system`                             | ✅ YES  |
| **Asset Types**       | 2 (agent, secret) | 6 (agent, report, config, dataset, tool, secret\*) | ✅ YES  |
| **Compliance**        | ❌ None           | ✅ compliance_officer                              | ✅ YES  |
| **Subdomains**        | ❌ None           | ✅ `parent` relation                               | ✅ YES  |
| **Shared Resources**  | ❌ None           | ✅ `is_shared`                                     | ✅ YES  |

**Recommendation:** ✅ **Use this model!**

---

## 🚀 Implementation Steps

### 1. Save This Model

```bash
# Save to file
cat > openfga/authorization_model_v2.fga << 'EOF'
# [paste the model you showed]
EOF
```

### 2. Load Into OpenFGA

```bash
fga model write \
  --store-id 01KATFSA1G5FRN6682HGAJX6XR \
  --file openfga/authorization_model_v2.fga \
  --api-url http://localhost:9080

# Get MODEL_ID from output
```

### 3. Store in LocalStack

```bash
python scripts/openfga_setup_localstack.py \
  01KATFSA1G5FRN6682HGAJX6XR \
  <NEW_MODEL_ID>
```

### 4. Update Backend

```python
# backend/routes/agents.py

@router.post("/agents")
async def create_agent(
    agent_data: AgentCreate,
    context: AuthContext = Depends(get_current_user)
):
    # Check: can_write on domain
    if not await context.can("can_write", f"domain:{agent_data.domain_id}"):
        raise HTTPException(403)

    # Create agent
    agent_id = create_agent_in_db(agent_data)

    # Set up relationships
    await fga_client.write([
        {
            "user": f"domain:{agent_data.domain_id}",
            "relation": "domain",
            "object": f"agent:{agent_id}"
        },
        {
            "user": context.get_fga_user(),
            "relation": "owner",
            "object": f"agent:{agent_id}"
        }
    ])
```

---

## 📊 Comparison Summary

| Aspect                | Simple Model | Enhanced Model | Recommendation |
| --------------------- | ------------ | -------------- | -------------- |
| **Complexity**        | Low          | Medium         | ⚠️ Worth it    |
| **Features**          | Basic        | Complete       | ✅ Use it      |
| **Multi-tenancy**     | Org-level    | Tenant-level   | ✅ Better      |
| **Teams**             | No           | Yes            | ✅ Essential   |
| **System Protection** | No           | Yes            | ✅ Critical    |
| **Asset Types**       | 2            | 6+             | ✅ Flexible    |

---

## ✅ My Recommendation

**Use this enhanced model!** It provides:

1. ✅ **True multi-tenancy** (tenant isolation)
2. ✅ **Team collaboration** (project visibility)
3. ✅ **System agent protection** (can't delete Marshal)
4. ✅ **Compliance support** (regulated industries)
5. ✅ **Flexible asset management** (reports, datasets, configs)
6. ✅ **Subdomain hierarchy** (nested domains)
7. ✅ **Shared resources** (org-wide datasets)

**This is enterprise-grade!** 🏆

---

## 🎯 Next Steps

1. **Save this model** to `openfga/authorization_model_v2.fga`
2. **Load with FGA CLI** (get model ID)
3. **Store in LocalStack** (not .env!)
4. **Update backend routes** to use new types
5. **Set up initial relationships** (tenant, org, project, domain)

**Shall I implement this enhanced model?**
