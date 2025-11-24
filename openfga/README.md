# OpenFGA Authorization Model

## Overview

Agent Foundry uses **OpenFGA** (Google Zanzibar) for fine-grained,
relationship-based authorization.

This directory contains:

- `authorization_model_v2.fga` - Complete authorization model
- `authorization_model.json` - JSON format (for API loading)
- `test_authorization_checks.py` - Test suite

---

## Model Highlights

### Hierarchy (5 Levels)

```
platform:foundry (global admins)
  ↓
tenant:ravenhelm (billing, top-level isolation)
  ↓
organization:cibc (business entity)
  ↓
project:card-services (initiative)
  ↓
domain:banking (knowledge vertical)
  ↓ (can nest: domain:banking-fraud)
  ↓
Assets: agent, report, config, dataset, tool, secret, session, graph
```

### Key Features

1. **Team Collaboration**

   ```fga
   type team
     define member: [user, user:*] or lead
   ```

2. **System Agent Protection**

   ```fga
   define can_write: ... but not is_system
   ```

3. **Permission Cascading**

   - Tenant admin → Org admin → Project admin → Domain admin → Asset access

4. **Subdomains**

   ```fga
   define parent: [domain]
   define can_read: ... or can_read from parent
   ```

5. **Shared Resources**

   ```fga
   define is_shared: [organization]
   define can_read: ... or member from is_shared
   ```

6. **Compliance Roles**
   ```fga
   define compliance_officer: [user]
   ```

---

## Setup

### 1. Load Model

```bash
# Install FGA CLI
brew install fga

# Load authorization model
fga model write \
  --store-id 01KATFSA1G5FRN6682HGAJX6XR \
  --file authorization_model_v2.fga \
  --api-url http://localhost:9080

# Get MODEL_ID from output
```

### 2. Store Config in LocalStack

```bash
python ../scripts/openfga_setup_localstack.py \
  01KATFSA1G5FRN6682HGAJX6XR \
  <MODEL_ID>
```

### 3. Set Up Initial Data

```bash
python ../scripts/openfga_setup_initial_data.py
```

### 4. Run Tests

```bash
python test_authorization_checks.py
```

---

## Example Relationships

```
Platform Admin:
  user:nate → global_admin → platform:foundry

Tenant:
  user:nate → admin → tenant:ravenhelm
  tenant:ravenhelm → tenant → organization:cibc

Team:
  user:bob → member → team:card-support
  team:card-support → organization → organization:cibc

Project:
  organization:cibc → organization → project:card-services
  team:card-support → team_visibility → project:card-services

Domain:
  project:card-services → project → domain:banking
  domain:banking → parent → domain:banking-fraud

Agent:
  domain:banking-fraud → domain → agent:fraud-detector
  user:alice → owner → agent:fraud-detector

System Agent:
  platform:foundry → is_system → agent:marshal
```

---

## Authorization Queries

### Can Bob read fraud-detector?

```
user:bob → member of → team:card-support
  ↓
team:card-support → team_visibility → project:card-services
  ↓
project:card-services → organization → domain:banking
  ↓
domain:banking → parent → domain:banking-fraud
  ↓
domain:banking-fraud → domain → agent:fraud-detector
  ↓
Result: ✓ TRUE (cascading permissions)
```

### Can Bob delete marshal?

```
Check: can_delete on agent:marshal
  ↓
can_delete: owner or can_delete from domain but not is_system
  ↓
agent:marshal has is_system: platform:foundry
  ↓
"but not is_system" exclusion applies
  ↓
Result: ✗ FALSE (protected by is_system)
```

---

## Asset Types

| Type        | Permissions                                              | Special Features                 |
| ----------- | -------------------------------------------------------- | -------------------------------- |
| **agent**   | can_read, can_write, can_delete, can_deploy, can_execute | `but not is_system` protection   |
| **report**  | can_read, can_write, can_delete                          | Team viewer support              |
| **config**  | can_read, can_write, can_delete                          | Domain-level delete only         |
| **dataset** | can_read, can_write, can_delete, can_ingest              | Org-wide sharing via `is_shared` |
| **tool**    | can_read, can_write, can_delete, can_invoke              | Runtime execution permission     |
| **secret**  | can_read_status, can_update, can_delete, can_rotate      | **Never** `can_read_value`       |
| **session** | can_read, can_terminate, can_replay                      | Agent-linked                     |
| **graph**   | can_read, can_update, can_deploy, can_delete, can_share  | Forge visual designer            |

---

## Integration with LocalStack

**OpenFGA handles WHO can access secrets** **LocalStack handles WHAT the secrets
are**

```python
# Check authorization
if not await context.can("can_update", "secret:openai_key"):
    raise HTTPException(403)

# Store in LocalStack
await secrets_manager.upsert_secret(org_id, "openai_api_key", value)
```

See: `../docs/OPENFGA_LOCALSTACK_INTEGRATION.md`

---

**This is enterprise-grade, production-ready authorization!** 🏆
