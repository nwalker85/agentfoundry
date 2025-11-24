# Dossier Management System - Design Specification

## Executive Summary

The Dossier Management System is a **fundamental, critical component** of Agent
Foundry that enables storage, versioning, and agent-driven operations on Domain
Intelligence Schema (DIS) 1.6.0 compliant dossiers. These dossiers represent
complete domain intelligence packages containing entities, functions, workflows,
governance rules, and operational knowledge for specific business domains.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Agent Foundry Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐   ┌──────────────┐ │
│  │   Dossier    │      │   Dossier    │   │   Dossier    │ │
│  │   Agent      │◄────►│     API      │◄─►│   Frontend   │ │
│  │  (System)    │      │  (FastAPI)   │   │   (React)    │ │
│  └──────────────┘      └──────────────┘   └──────────────┘ │
│         │                      │                             │
│         │                      │                             │
│         ▼                      ▼                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Dossier Service Layer                     │   │
│  │  - Validation  - Versioning  - Query  - Transform  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
├───────────────────────────┼──────────────────────────────────┤
│        Data Layer         │                                  │
│                           │                                  │
│   ┌───────────────────────▼──────────┐   ┌───────────────┐ │
│   │      MongoDB (NoSQL)             │   │  PostgreSQL   │ │
│   │  - dossiers (encrypted)          │   │  - metadata   │ │
│   │  - versions                      │   │  - audit logs │ │
│   │  - change_history                │   │  - RBAC       │ │
│   │  Isolated security boundary      │   └───────────────┘ │
│   └──────────────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## 1. Data Model Design

### 1.1 MongoDB Collections

#### Collection: `dossiers`

```javascript
{
  _id: ObjectId,
  dossierId: String,              // Unique dossier identifier (indexed, unique)
  version: String,                // Semantic version (e.g., "2.2.0")
  organizationId: String,         // Organization owner (indexed)

  // DIS 1.6.0 Header
  header: {
    dossierId: String,
    domainName: String,
    description: String,
    version: String,
    versionDate: ISODate,
    disSpecificationRef: String,  // "1.6.0"
    dossierType: String,          // DESIGN | OPERATIONAL | REFERENCE
    dossierStatus: String,        // DRAFT | REVIEW | APPROVED | ARCHIVED
    authors: [String],
    geographicScope: [String],
    industryVertical: String,
    knowledgeDocumentIds: [String],
    tags: [String]
  },

  // DIS Specification Content
  dossierSpecificDefinitions: {
    commonEnums: [{
      enumId: String,
      enumName: String,
      enumValues: [String],
      description: String
    }],
    entities: [{
      entityId: String,
      entityName: String,
      entityType: String,         // DATA | AGENT | SYSTEM | ROLE
      description: String,
      keys: [{
        keyName: String,
        keyType: String,          // PRIMARY | FOREIGN | COMPOSITE
        dataType: String
      }],
      attributes: [{
        attributeName: String,
        dataType: String,
        required: Boolean,
        sensitive: Boolean,
        validation: Object
      }],
      relationships: [Object],
      tags: [String]
    }],
    capabilities: [{
      capabilityId: String,
      capabilityName: String,
      description: String,
      category: String,
      prerequisites: [String],
      tags: [String]
    }]
  },

  // Triplet Function Matrix
  tripletFunctionMatrix: [{
    tripletId: String,
    subject: String,              // Entity performing action
    verb: String,                 // Action/function
    object: String,               // Entity being acted upon
    modeOfInteraction: String,    // CREATE | READ | UPDATE | DELETE | etc.
    functionBinding: {
      functionId: String,
      functionName: String,
      implementation: String,
      parameters: [Object]
    },
    governanceRules: [Object],
    accessGates: [Object]
  }],

  // Workflows
  workflows: [{
    workflowId: String,
    workflowName: String,
    description: String,
    steps: [{
      stepId: String,
      stepName: String,
      tripletRefs: [String],
      conditions: [Object],
      transitions: [Object]
    }],
    triggerEvents: [String]
  }],

  // Governance
  accessGateMatrix: [{
    gateId: String,
    entityId: String,
    requiredRoles: [String],
    requiredPermissions: [String],
    conditions: [Object]
  }],

  validationRules: [{
    ruleId: String,
    entityId: String,
    expression: String,
    errorMessage: String
  }],

  privacyManifest: {
    sensitiveEntities: [String],
    retentionPolicies: [Object],
    encryptionRequirements: [Object],
    gdprCompliance: Object
  },

  // Metadata
  metadata: {
    createdAt: ISODate,
    createdBy: String,
    updatedAt: ISODate,
    updatedBy: String,
    locked: Boolean,
    lockedBy: String,
    lockedAt: ISODate
  },

  // Security
  encryption: {
    encrypted: Boolean,
    encryptedFields: [String],
    keyId: String
  },

  // Indexing & Search
  searchableText: String,         // Full-text search index

  // Version lineage
  parentVersionId: ObjectId,      // Previous version reference
  versionHistory: [{
    version: String,
    versionDate: ISODate,
    changes: String,
    changedBy: String
  }]
}
```

#### Collection: `dossier_versions`

```javascript
{
  _id: ObjectId,
  dossierId: String,              // Reference to parent dossier
  version: String,
  snapshotDate: ISODate,
  dossierSnapshot: Object,        // Complete dossier at this version
  changeManagement: {
    changeType: String,           // MAJOR | MINOR | PATCH
    changeDescription: String,
    changedBy: String,
    approvedBy: String,
    approvalDate: ISODate
  },
  tags: [String]
}
```

#### Collection: `dossier_operations`

```javascript
{
  _id: ObjectId,
  operationId: String,
  dossierId: String,
  agentId: String,
  operationType: String,          // READ | CREATE | UPDATE | VALIDATE | TRANSFORM
  timestamp: ISODate,
  userId: String,
  input: Object,
  output: Object,
  status: String,                 // SUCCESS | FAILURE | PARTIAL
  errors: [Object],
  duration: Number,
  metadata: Object
}
```

### 1.2 MongoDB Indexes

```javascript
// dossiers collection
db.dossiers.createIndex({ dossierId: 1 }, { unique: true });
db.dossiers.createIndex({ organizationId: 1, dossierId: 1 });
db.dossiers.createIndex({ 'header.dossierStatus': 1 });
db.dossiers.createIndex({ 'header.tags': 1 });
db.dossiers.createIndex({ 'header.industryVertical': 1 });
db.dossiers.createIndex({ searchableText: 'text' });
db.dossiers.createIndex({ 'metadata.createdAt': -1 });
db.dossiers.createIndex({ 'metadata.updatedAt': -1 });

// dossier_versions collection
db.dossier_versions.createIndex({ dossierId: 1, version: 1 }, { unique: true });
db.dossier_versions.createIndex({ snapshotDate: -1 });

// dossier_operations collection
db.dossier_operations.createIndex({ dossierId: 1, timestamp: -1 });
db.dossier_operations.createIndex({ agentId: 1, timestamp: -1 });
db.dossier_operations.createIndex({ operationType: 1 });
```

## 2. Security Architecture

### 2.1 Isolation Strategy

**MongoDB runs in isolated security boundary:**

- Separate connection pool from PostgreSQL
- Dedicated authentication credentials
- Network isolation (different port, optionally different host)
- Field-level encryption for sensitive data
- TLS/SSL encryption in transit

### 2.2 Access Control

```python
# RBAC Permissions for Dossier Operations
DOSSIER_PERMISSIONS = {
    "dossier:read": "View dossier content",
    "dossier:create": "Create new dossiers",
    "dossier:update": "Modify existing dossiers",
    "dossier:delete": "Delete dossiers",
    "dossier:version": "Create new versions",
    "dossier:approve": "Approve dossier changes",
    "dossier:lock": "Lock/unlock dossiers",
    "dossier:export": "Export dossiers",
    "dossier:import": "Import dossiers"
}

# Role Assignments
ROLES = {
    "domain_architect": [
        "dossier:read", "dossier:create", "dossier:update",
        "dossier:version", "dossier:export"
    ],
    "domain_admin": [
        "dossier:read", "dossier:update", "dossier:approve",
        "dossier:lock", "dossier:export", "dossier:import"
    ],
    "developer": [
        "dossier:read", "dossier:export"
    ],
    "system_agent": [
        "dossier:read"  # Agents can only read, not modify
    ]
}
```

### 2.3 Encryption

```python
# Field-level encryption for sensitive data
ENCRYPTED_FIELDS = [
    "dossierSpecificDefinitions.entities.*.attributes[sensitive=true]",
    "privacyManifest",
    "accessGateMatrix"
]

# Encryption at rest (MongoDB native)
# - WiredTiger encryption
# - KMIP key management integration
```

## 3. API Design

### 3.1 REST API Endpoints

```python
# Dossier CRUD
POST   /api/dossiers                      # Create dossier
GET    /api/dossiers                      # List dossiers (paginated, filtered)
GET    /api/dossiers/{dossierId}          # Get dossier by ID
PUT    /api/dossiers/{dossierId}          # Update dossier
DELETE /api/dossiers/{dossierId}          # Delete dossier
PATCH  /api/dossiers/{dossierId}          # Partial update

# Versioning
POST   /api/dossiers/{dossierId}/versions      # Create new version
GET    /api/dossiers/{dossierId}/versions      # List versions
GET    /api/dossiers/{dossierId}/versions/{v}  # Get specific version
POST   /api/dossiers/{dossierId}/rollback/{v}  # Rollback to version

# Validation
POST   /api/dossiers/validate              # Validate dossier against DIS schema
POST   /api/dossiers/{dossierId}/validate  # Validate existing dossier

# Query & Search
GET    /api/dossiers/search?q={query}     # Full-text search
POST   /api/dossiers/query                # Complex query (entity, triplet, etc.)

# Operations
GET    /api/dossiers/{dossierId}/entities              # List entities
GET    /api/dossiers/{dossierId}/entities/{entityId}   # Get entity
GET    /api/dossiers/{dossierId}/triplets              # List triplet functions
GET    /api/dossiers/{dossierId}/workflows             # List workflows

# Governance
GET    /api/dossiers/{dossierId}/access-gates          # Get access control
GET    /api/dossiers/{dossierId}/validation-rules      # Get validation rules

# Locking (concurrent editing)
POST   /api/dossiers/{dossierId}/lock      # Acquire lock
DELETE /api/dossiers/{dossierId}/lock      # Release lock

# Import/Export
POST   /api/dossiers/import                # Import dossier from JSON
GET    /api/dossiers/{dossierId}/export    # Export to JSON

# Agent Operations (used by Dossier Agent)
POST   /api/dossiers/{dossierId}/agent/query     # Agent query interface
POST   /api/dossiers/{dossierId}/agent/transform # Transform dossier
POST   /api/dossiers/{dossierId}/agent/generate  # Generate artifacts
```

### 3.2 Request/Response Examples

**Create Dossier:**

```json
POST /api/dossiers
{
  "header": {
    "dossierId": "my-domain-v1",
    "domainName": "My Business Domain",
    "description": "Domain intelligence for...",
    "version": "1.0.0",
    "dossierType": "DESIGN",
    "dossierStatus": "DRAFT",
    "industryVertical": "FINANCIAL_SERVICES"
  },
  "dossierSpecificDefinitions": {
    "entities": [...],
    "capabilities": [...]
  }
}

Response: 201 Created
{
  "dossierId": "my-domain-v1",
  "version": "1.0.0",
  "_id": "507f1f77bcf86cd799439011",
  "createdAt": "2025-11-16T10:00:00Z"
}
```

**Query Dossier:**

```json
POST /api/dossiers/query
{
  "filters": {
    "industryVertical": "FINANCIAL_SERVICES",
    "dossierStatus": "APPROVED",
    "tags": ["card-operations"]
  },
  "projection": {
    "include": ["header", "entities"],
    "exclude": ["privacyManifest"]
  },
  "limit": 20,
  "offset": 0
}
```

## 4. Dossier Agent Design

### 4.1 Agent Capabilities

The Dossier Agent is a **system agent** with specialized capabilities:

```python
DOSSIER_AGENT_CAPABILITIES = [
    "dossier_retrieval",           # Find and retrieve dossiers
    "entity_lookup",               # Query entities within dossiers
    "triplet_search",              # Search triplet function matrix
    "workflow_analysis",           # Analyze workflow definitions
    "compliance_check",            # Validate against governance rules
    "artifact_generation",         # Generate code/docs from dossier
    "domain_question_answering",   # Answer questions about domain
    "relationship_mapping",        # Map entity relationships
    "change_impact_analysis"       # Analyze change impacts
]
```

### 4.2 Agent Tools

```python
@tool
def get_dossier(dossierId: str, version: Optional[str] = None) -> Dict:
    """Retrieve a dossier by ID and optional version."""
    pass

@tool
def search_dossiers(
    query: str,
    filters: Optional[Dict] = None,
    limit: int = 10
) -> List[Dict]:
    """Search dossiers using full-text search and filters."""
    pass

@tool
def query_entities(
    dossierId: str,
    entity_type: Optional[str] = None,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """Query entities within a dossier."""
    pass

@tool
def get_entity_relationships(
    dossierId: str,
    entityId: str
) -> Dict:
    """Get all relationships for an entity."""
    pass

@tool
def find_triplets(
    dossierId: str,
    subject: Optional[str] = None,
    verb: Optional[str] = None,
    object: Optional[str] = None
) -> List[Dict]:
    """Find triplet functions matching criteria."""
    pass

@tool
def validate_dossier(
    dossier: Dict,
    schema_version: str = "1.6.0"
) -> Dict:
    """Validate dossier against DIS schema."""
    pass

@tool
def generate_entity_code(
    dossierId: str,
    entityId: str,
    language: str = "python"
) -> str:
    """Generate code for an entity definition."""
    pass

@tool
def analyze_workflow(
    dossierId: str,
    workflowId: str
) -> Dict:
    """Analyze a workflow and return insights."""
    pass

@tool
def check_access_permissions(
    dossierId: str,
    entityId: str,
    userId: str,
    action: str
) -> bool:
    """Check if user has permission for action on entity."""
    pass
```

### 4.3 Agent Persona

```yaml
name: 'Dossier Intelligence Agent'
role: 'Domain Intelligence Specialist'
personality: |
  I am an expert in Domain Intelligence Schema (DIS) 1.6.0 and help users
  navigate, query, and work with domain intelligence dossiers. I understand
  entities, triplet functions, workflows, and governance structures.

  I can:
  - Find and retrieve dossiers based on your needs
  - Explain entity definitions and relationships
  - Analyze workflows and suggest improvements
  - Generate code from entity definitions
  - Validate dossiers against DIS specifications
  - Answer questions about domain knowledge

knowledge_bases:
  - dis_specification_1_6_0
  - dossier_patterns
  - domain_modeling_best_practices

constraints:
  - I can only read dossiers, not create or modify them
  - I respect RBAC permissions for dossier access
  - I protect sensitive data in privacy manifests
```

## 5. Frontend UI Components

### 5.1 Dossier Registry Page

```
┌─────────────────────────────────────────────────────────┐
│ Dossiers                                          [+New] │
├─────────────────────────────────────────────────────────┤
│ [Search...] │ [Status ▼] [Industry ▼] [Tags ▼]         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📋 CIBC Consumer Banking Cards v2.2.0                  │
│     Financial Services • APPROVED • Caribbean           │
│     47 entities • 128 triplets • 15 workflows           │
│     Updated 2 days ago by Jane Doe                      │
│                                         [View] [Export]  │
│  ─────────────────────────────────────────────────────  │
│  📋 Payment Processing Domain v1.5.0                    │
│     Financial Services • DRAFT • Global                 │
│     23 entities • 56 triplets • 8 workflows             │
│     Updated 1 week ago by John Smith                    │
│                                         [View] [Export]  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.2 Dossier Viewer

```
┌─────────────────────────────────────────────────────────┐
│ ← Back  CIBC Consumer Banking Cards v2.2.0              │
│         [Edit] [Version ▼] [Lock] [Export] [Validate]   │
├─────────────────────────────────────────────────────────┤
│ [Overview] [Entities] [Triplets] [Workflows] [Settings] │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📊 Overview                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│  Domain: Consumer Banking – Card & Contact Centre       │
│  Version: 2.2.0 (2025-11-14)                            │
│  Status: DRAFT                                           │
│  Industry: FINANCIAL_SERVICES                            │
│  Scope: Barbados, Bahamas, Jamaica, Cayman Islands...  │
│                                                          │
│  📈 Statistics                                          │
│  • 47 Entities (23 DATA, 12 AGENT, 8 SYSTEM, 4 ROLE)   │
│  • 128 Triplet Functions                                │
│  • 15 Workflows                                         │
│  • 34 Validation Rules                                  │
│  • 18 Access Gates                                      │
│                                                          │
│  🏷️ Tags                                                │
│  [consumer-banking] [card-operations] [contact-centre]  │
│  [caribbean] [multi-channel] [future-state]             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Entity Explorer

```
┌─────────────────────────────────────────────────────────┐
│ Entities                               [Filter by type ▼]│
├───────────────┬─────────────────────────────────────────┤
│               │                                          │
│ ◉ ClientAccount   Entity: ClientAccount                 │
│   Card             Type: DATA                            │
│   CardWatch        Keys:                                 │
│   CardStatus       • accountId (PRIMARY, uuid)           │
│   ReplacementReq   Attributes:                           │
│   Verification     • accountNumber (string) 🔒           │
│   Territory        • accountType (enum)                  │
│   Channel          • customerId (uuid)                   │
│ ...                • territoryCode (string)              │
│                    Relationships:                        │
│                    • hasMany: Card                       │
│                    • belongsTo: Customer                 │
│                    Triplets using this entity: 12        │
│                                      [View Code] [Graph] │
└───────────────┴─────────────────────────────────────────┘
```

## 6. Implementation Plan

### Phase 1: Foundation (Week 1-2)

- [ ] Set up MongoDB connection and security
- [ ] Create MongoDB collections with indexes
- [ ] Implement basic CRUD operations
- [ ] Create validation against DIS 1.6.0 schema
- [ ] Build encryption layer for sensitive fields

### Phase 2: API Layer (Week 3-4)

- [ ] Implement all REST endpoints
- [ ] Add RBAC middleware
- [ ] Create versioning system
- [ ] Build query engine
- [ ] Implement locking mechanism

### Phase 3: Dossier Agent (Week 5-6)

- [ ] Create Dossier Agent system agent
- [ ] Implement all agent tools
- [ ] Build agent orchestration logic
- [ ] Add LLM integration for Q&A
- [ ] Test agent capabilities

### Phase 4: Frontend (Week 7-8)

- [ ] Build Dossier Registry page
- [ ] Create Dossier Viewer
- [ ] Implement Entity Explorer
- [ ] Add Triplet Matrix viewer
- [ ] Build Workflow visualizer

### Phase 5: Integration & Testing (Week 9-10)

- [ ] End-to-end integration testing
- [ ] Security penetration testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] User acceptance testing

## 7. Technology Stack

**Backend:**

- FastAPI (Python 3.11+)
- MongoDB 7.0+ (NoSQL storage)
- Motor (async MongoDB driver)
- PyMongo encryption
- Pydantic (validation)
- JSON Schema validators

**Frontend:**

- Next.js 14+ (React)
- TanStack Query (data fetching)
- Monaco Editor (JSON editing)
- React Flow (workflow visualization)
- Recharts (statistics)

**Security:**

- MongoDB field-level encryption
- TLS/SSL connections
- JWT authentication
- RBAC authorization
- Audit logging

## 8. Success Metrics

- **Storage:** Support 10,000+ dossiers per organization
- **Performance:** < 100ms read latency, < 500ms write latency
- **Security:** 100% field-level encryption for sensitive data
- **Availability:** 99.9% uptime
- **Agent Accuracy:** > 95% correct responses for domain queries
- **Validation:** 100% DIS 1.6.0 schema compliance

## 9. Future Enhancements

- **Dossier Marketplace:** Public/private dossier sharing
- **Collaborative Editing:** Real-time multi-user editing
- **Diff & Merge:** Visual dossier comparison and merging
- **AI-Assisted Design:** LLM-powered dossier generation
- **Graph Visualization:** Interactive entity relationship graphs
- **Integration Plugins:** Import from Enterprise Architect, draw.io
- **Workflow Engine:** Execute workflows defined in dossiers
- **Code Generation:** Auto-generate microservices from dossiers
