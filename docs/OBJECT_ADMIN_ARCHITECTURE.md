# Object Admin Architecture - Dynamic Admin Panel

**Status:** Design Proposal **Last Updated:** 2025-11-16 **Owner:**
ObjectAdminAgent + DataAgent

## 🎯 Overview

The Object Admin system provides a **dynamic, single-panel admin interface** for
managing core platform objects:

- Organizations
- Domains
- Instances
- Users
- Deployments
- Agents

**Key Principles:**

1. **Separation of Concerns:** ObjectAdminAgent handles presentation logic,
   DataAgent handles data access
2. **Dynamic Schema:** All entity types rendered from schema definitions
3. **Single Panel:** One component that adapts to context (list ↔ detail)
4. **Declarative:** Field definitions drive UI rendering

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin UI (/admin)                        │
│                   Single Dynamic Panel Component                 │
│                                                                   │
│  ┌──────────────┐        ┌──────────────┐                      │
│  │  List View   │  ←→    │ Detail View  │                      │
│  │  (Table)     │        │ (Form/Card)  │                      │
│  └──────────────┘        └──────────────┘                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API: /api/admin
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ObjectAdminAgent                           │
│                   (Presentation Logic)                          │
│                                                                  │
│  1. authenticate()         → Verify permissions                │
│  2. load_schema()          → Get entity schema                 │
│  3. fetch_data()           → Call DataAgent                    │
│  4. validate_fields()      → Ensure all required fields        │
│  5. format_response()      → Structure for UI                  │
│  6. audit_log()            → Record access                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Internal call
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DataAgent                               │
│                      (Data Access Layer)                        │
│                                                                  │
│  • NL → SQL translation                                         │
│  • Safe query execution                                         │
│  • Relationship traversal                                       │
│  • Caching & optimization                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      PostgreSQL Database
```

---

## 📊 Current State vs. Desired State

### **Current State** ❌

```python
# ObjectAdminAgent directly queries database
def _list_objects(self, state):
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM organizations...")
```

**Problems:**

- No separation of concerns
- Duplicates data access logic
- Can't leverage DataAgent's NL→SQL capabilities
- No caching
- Hard to audit

### **Desired State** ✅

```python
# ObjectAdminAgent delegates to DataAgent
async def _fetch_data(self, state: ObjectAdminState):
    schema = self.schema_registry.get(state["object_type"])

    # Use DataAgent for data fetching
    data_result = await self.data_agent.query(
        self._build_query(state, schema)
    )

    # ObjectAdminAgent adds presentation logic
    state["result"] = self._format_for_ui(
        data_result,
        schema,
        state["view_mode"]  # "list" or "detail"
    )
```

**Benefits:**

- Clean separation: DataAgent = data, ObjectAdminAgent = presentation
- Reusable data access
- Centralized caching in DataAgent
- Audit trail
- Can use NL queries if needed

---

## 🗂️ Schema Registry

### **Schema Definition Format**

Each entity type has a declarative schema:

```typescript
interface EntitySchema {
  name: string; // "organization"
  displayName: string; // "Organization"
  pluralName: string; // "Organizations"

  // List view configuration
  listView: {
    columns: ColumnDefinition[];
    defaultSort: { field: string; direction: 'asc' | 'desc' };
    searchFields: string[];
    filters: FilterDefinition[];
  };

  // Detail view configuration
  detailView: {
    sections: SectionDefinition[];
    relatedEntities: RelationshipDefinition[];
  };

  // Permissions
  permissions: {
    view: string[]; // Roles that can view
    create: string[]; // Roles that can create
    edit: string[]; // Roles that can edit
    delete: string[]; // Roles that can delete
  };

  // API configuration
  api: {
    listEndpoint: string;
    getEndpoint: string;
    createEndpoint?: string;
    updateEndpoint?: string;
    deleteEndpoint?: string;
  };
}
```

### **Example: Organization Schema**

```typescript
const OrganizationSchema: EntitySchema = {
  name: 'organization',
  displayName: 'Organization',
  pluralName: 'Organizations',

  listView: {
    columns: [
      {
        field: 'name',
        label: 'Name',
        type: 'text',
        sortable: true,
        searchable: true,
        width: '30%',
      },
      {
        field: 'tier',
        label: 'Tier',
        type: 'badge',
        sortable: true,
        options: {
          free: { label: 'Free', color: 'gray' },
          pro: { label: 'Pro', color: 'blue' },
          enterprise: { label: 'Enterprise', color: 'purple' },
        },
        width: '15%',
      },
      {
        field: 'domain_count',
        label: 'Domains',
        type: 'number',
        sortable: true,
        width: '10%',
      },
      {
        field: 'user_count',
        label: 'Users',
        type: 'number',
        sortable: true,
        width: '10%',
      },
      {
        field: 'created_at',
        label: 'Created',
        type: 'date',
        sortable: true,
        width: '15%',
      },
      {
        field: 'updated_at',
        label: 'Updated',
        type: 'date',
        sortable: true,
        width: '15%',
      },
    ],
    defaultSort: { field: 'created_at', direction: 'desc' },
    searchFields: ['name', 'tier'],
    filters: [
      {
        field: 'tier',
        label: 'Tier',
        type: 'select',
        options: ['free', 'pro', 'enterprise'],
      },
    ],
  },

  detailView: {
    sections: [
      {
        title: 'Basic Information',
        fields: [
          { field: 'id', label: 'ID', type: 'text', readonly: true },
          { field: 'name', label: 'Name', type: 'text', required: true },
          {
            field: 'tier',
            label: 'Tier',
            type: 'select',
            required: true,
            options: ['free', 'pro', 'enterprise'],
          },
        ],
      },
      {
        title: 'Metadata',
        fields: [
          {
            field: 'created_at',
            label: 'Created',
            type: 'datetime',
            readonly: true,
          },
          {
            field: 'updated_at',
            label: 'Updated',
            type: 'datetime',
            readonly: true,
          },
        ],
      },
    ],
    relatedEntities: [
      {
        entity: 'domain',
        label: 'Domains',
        type: 'one-to-many',
        foreignKey: 'organization_id',
        displayFields: ['name', 'version', 'created_at'],
      },
      {
        entity: 'user',
        label: 'Users',
        type: 'one-to-many',
        foreignKey: 'organization_id',
        displayFields: ['email', 'name', 'role'],
      },
    ],
  },

  permissions: {
    view: ['admin', 'user'],
    create: ['admin'],
    edit: ['admin'],
    delete: ['admin'],
  },

  api: {
    listEndpoint: '/api/admin/organizations',
    getEndpoint: '/api/admin/organizations/:id',
  },
};
```

---

## 🎨 UI Component Architecture

### **Single Dynamic Panel Component**

```tsx
// app/admin/page.tsx
'use client';

import { useState } from 'react';
import { AdminPanel } from './components/AdminPanel';
import { AdminSidebar } from './components/AdminSidebar';

export default function AdminPage() {
  const [context, setContext] = useState({
    entityType: 'organization',
    viewMode: 'list',
    selectedId: null,
  });

  return (
    <div className="flex h-full">
      {/* Sidebar with entity type selector */}
      <AdminSidebar
        onSelectEntity={(type) =>
          setContext({
            entityType: type,
            viewMode: 'list',
            selectedId: null,
          })
        }
      />

      {/* Dynamic panel - single component that adapts */}
      <AdminPanel context={context} onContextChange={setContext} />
    </div>
  );
}
```

### **Dynamic Panel Component**

```tsx
// app/admin/components/AdminPanel.tsx
'use client';

import { useEffect, useState } from 'react';
import { AdminListView } from './AdminListView';
import { AdminDetailView } from './AdminDetailView';
import { useAdminData } from '../hooks/useAdminData';
import { EntitySchema } from '../types/schema';
import { schemas } from '../schemas';

interface AdminContext {
  entityType: string;
  viewMode: 'list' | 'detail';
  selectedId: string | null;
}

export function AdminPanel({ context, onContextChange }: Props) {
  const schema = schemas[context.entityType];
  const { data, loading, error } = useAdminData(context);

  if (!schema) {
    return <div>Entity type not found</div>;
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Breadcrumb navigation */}
      <AdminBreadcrumb context={context} schema={schema} />

      {/* Dynamic content based on view mode */}
      {context.viewMode === 'list' ? (
        <AdminListView
          schema={schema}
          data={data}
          loading={loading}
          error={error}
          onRowClick={(id) =>
            onContextChange({
              ...context,
              viewMode: 'detail',
              selectedId: id,
            })
          }
        />
      ) : (
        <AdminDetailView
          schema={schema}
          data={data}
          loading={loading}
          error={error}
          onBack={() =>
            onContextChange({
              ...context,
              viewMode: 'list',
              selectedId: null,
            })
          }
        />
      )}
    </div>
  );
}
```

### **Data Hook (Calls ObjectAdminAgent)**

```tsx
// app/admin/hooks/useAdminData.ts
import { useEffect, useState } from 'react';

export function useAdminData(context: AdminContext) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const endpoint =
          context.viewMode === 'list'
            ? `/api/admin/${context.entityType}`
            : `/api/admin/${context.entityType}/${context.selectedId}`;

        const response = await fetch(endpoint);
        const result = await response.json();

        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [context]);

  return { data, loading, error };
}
```

---

## 🔐 Security & Permissions

### **Permission Checking in ObjectAdminAgent**

```python
# Updated ObjectAdminAgent with security layer
class ObjectAdminAgent:
    def __init__(self):
        self.schema_registry = SchemaRegistry()
        self.data_agent = DataAgent()
        self.audit_logger = AuditLogger()

        builder = StateGraph(ObjectAdminState)
        builder.add_node("authenticate", self._authenticate)
        builder.add_node("check_permissions", self._check_permissions)
        builder.add_node("load_schema", self._load_schema)
        builder.add_node("fetch_data", self._fetch_data)
        builder.add_node("validate_fields", self._validate_fields)
        builder.add_node("format_response", self._format_response)
        builder.add_node("audit_log", self._audit_log)

        builder.set_entry_point("authenticate")
        builder.add_edge("authenticate", "check_permissions")
        builder.add_edge("check_permissions", "load_schema")
        builder.add_edge("load_schema", "fetch_data")
        builder.add_edge("fetch_data", "validate_fields")
        builder.add_edge("validate_fields", "format_response")
        builder.add_edge("format_response", "audit_log")
        builder.add_edge("audit_log", END)

        self.graph = builder.compile()

    async def _authenticate(self, state: ObjectAdminState):
        """Verify user authentication."""
        user = await self.auth_service.verify_token(state["auth_token"])
        if not user:
            state["error"] = "Unauthorized"
            return state

        state["user"] = user
        return state

    async def _check_permissions(self, state: ObjectAdminState):
        """Check if user has permission for this operation."""
        schema = self.schema_registry.get(state["object_type"])
        user_role = state["user"]["role"]

        operation_permissions = {
            "list": schema["permissions"]["view"],
            "get": schema["permissions"]["view"],
            "create": schema["permissions"]["create"],
            "update": schema["permissions"]["edit"],
            "delete": schema["permissions"]["delete"]
        }

        required_roles = operation_permissions[state["operation"]]
        if user_role not in required_roles:
            state["error"] = f"Permission denied: {user_role} cannot {state['operation']} {state['object_type']}"
            return state

        return state

    async def _fetch_data(self, state: ObjectAdminState):
        """Fetch data using DataAgent."""
        schema = state["schema"]

        # Build natural language query for DataAgent
        if state["operation"] == "list":
            query = self._build_list_query(state, schema)
        elif state["operation"] == "get":
            query = f"Get {state['object_type']} with id {state['id']}"

        # Call DataAgent
        result = await self.data_agent.query(query)

        if result.get("error"):
            state["error"] = result["error"]
        else:
            state["raw_data"] = result["rows"]

        return state

    async def _validate_fields(self, state: ObjectAdminState):
        """Ensure all required fields are populated."""
        schema = state["schema"]
        raw_data = state.get("raw_data", [])

        if state["operation"] == "get":
            # Single record - validate all fields
            record = raw_data[0] if raw_data else None
            if not record:
                state["error"] = f"{state['object_type']} not found"
                return state

            # Check required fields
            required_fields = self._get_required_fields(schema, "detail")
            missing_fields = [f for f in required_fields if f not in record or record[f] is None]

            if missing_fields:
                # Log warning but don't fail
                logger.warning(f"Missing fields in {state['object_type']}: {missing_fields}")

        return state

    async def _format_response(self, state: ObjectAdminState):
        """Format data for UI consumption."""
        schema = state["schema"]
        raw_data = state.get("raw_data", [])

        if state["operation"] == "list":
            # Format list view
            state["result"] = {
                "items": [self._format_list_item(item, schema) for item in raw_data],
                "total": len(raw_data),
                "schema": schema["listView"]
            }
        elif state["operation"] == "get":
            # Format detail view
            record = raw_data[0] if raw_data else None
            state["result"] = {
                "data": self._format_detail_item(record, schema),
                "schema": schema["detailView"],
                "related": await self._fetch_related_entities(record, schema)
            }

        return state

    async def _audit_log(self, state: ObjectAdminState):
        """Log admin access for audit trail."""
        await self.audit_logger.log({
            "user_id": state["user"]["id"],
            "user_email": state["user"]["email"],
            "action": state["operation"],
            "entity_type": state["object_type"],
            "entity_id": state.get("id"),
            "timestamp": datetime.utcnow(),
            "ip_address": state.get("ip_address"),
            "success": not state.get("error")
        })

        return state
```

---

## 🔄 Data Flow Example

### **Scenario: User views Organization details**

```
1. User clicks "Ravenhelm AI" in Organizations list
   └─> UI sets context: { entityType: "organization", viewMode: "detail", selectedId: "org-123" }

2. AdminPanel component fetches data
   └─> GET /api/admin/organizations/org-123

3. API route calls ObjectAdminAgent
   └─> ObjectAdminAgent.run({
         operation: "get",
         object_type: "organization",
         id: "org-123",
         auth_token: "...",
         user: { id: "user-1", role: "admin" }
       })

4. ObjectAdminAgent LangGraph Flow:
   ├─> authenticate:       ✓ User verified
   ├─> check_permissions:  ✓ Admin can view orgs
   ├─> load_schema:        ✓ Loaded OrganizationSchema
   ├─> fetch_data:
   │   └─> DataAgent.query("Get organization with id org-123")
   │       └─> Generates SQL: SELECT * FROM organizations WHERE id = 'org-123'
   │       └─> Returns: { id: "org-123", name: "Ravenhelm AI", tier: "pro", ... }
   ├─> validate_fields:    ✓ All required fields present
   ├─> format_response:
   │   ├─> Format organization data
   │   └─> Fetch related: Domains (5), Users (12), Instances (8)
   └─> audit_log:          ✓ Logged access

5. ObjectAdminAgent returns:
   {
     "data": {
       "id": "org-123",
       "name": "Ravenhelm AI",
       "tier": "pro",
       "created_at": "2024-01-15T10:00:00Z",
       "updated_at": "2024-11-16T08:30:00Z"
     },
     "schema": { /* detail view schema */ },
     "related": {
       "domains": [
         { id: "dom-1", name: "retail-banking", ... },
         { id: "dom-2", name: "investment", ... }
       ],
       "users": [
         { id: "user-1", email: "admin@ravenhelm.ai", ... }
       ],
       "instances": [ /* ... */ ]
     }
   }

6. UI renders detail view with:
   ├─> Breadcrumb: Organizations > Ravenhelm AI
   ├─> Detail card with all fields
   └─> Related entities tabs (Domains, Users, Instances)
```

---

## 📈 Broader Platform Implications

### **1. Consistency Across All Admin Views**

- All entity types use the same UI pattern
- Predictable UX for administrators
- Easy to add new entity types (just add schema)

### **2. Reusability**

- DataAgent is reused across the platform
- ObjectAdminAgent pattern can extend to other admin needs
- Schema definitions are single source of truth

### **3. Security**

- Centralized permission checking
- Complete audit trail
- Role-based access control at field level

### **4. Extensibility**

- Add new entity types: just define schema
- Add custom actions: extend ObjectAdminAgent
- Add new field types: extend renderer components

### **5. Governance**

- All admin actions go through ObjectAdminAgent
- GovernanceAgent can hook into the flow
- Policy enforcement point

### **6. Observability**

- All admin operations traced
- Performance metrics per entity type
- User activity analytics

### **7. Data Quality**

- Field validation ensures completeness
- Relationship integrity checks
- Required field enforcement

### **8. Performance**

- DataAgent can implement caching
- Pagination for large lists
- Lazy loading of related entities

### **9. Multi-tenancy**

- Organization-scoped data access
- User permissions per org
- Data isolation

### **10. Future Features**

- Bulk operations (multi-select + action)
- Export/import (CSV, JSON)
- Advanced search/filter
- Real-time updates (WebSocket)
- Change history/versioning

---

## 🚀 Implementation Roadmap

### **Phase 1: Foundation** (Week 1)

- [ ] Create schema registry
- [ ] Define schemas for all entity types
- [ ] Refactor ObjectAdminAgent to use DataAgent
- [ ] Add authentication/permissions layer

### **Phase 2: UI Components** (Week 2)

- [ ] Build AdminPanel dynamic component
- [ ] Build AdminListView (table with dynamic columns)
- [ ] Build AdminDetailView (form with dynamic sections)
- [ ] Build AdminBreadcrumb
- [ ] Build AdminSidebar

### **Phase 3: Integration** (Week 3)

- [ ] Create API routes for each entity
- [ ] Hook up UI to ObjectAdminAgent
- [ ] Add loading states, error handling
- [ ] Add relationship rendering

### **Phase 4: Advanced Features** (Week 4)

- [ ] Add search/filter
- [ ] Add sorting
- [ ] Add pagination
- [ ] Add audit logging UI
- [ ] Add export functionality

---

## 📚 Code Examples

See the following files for implementation:

- **Schemas:** `app/admin/schemas/` (to be created)
- **Components:** `app/admin/components/` (to be created)
- **API:** `app/api/admin/route.ts` (to be created)
- **Agents:** `agent/object_admin_agent.py` (update), `agent/data_agent.py`
  (extend)

---

**Generated by:** Claude Code **Architecture Review:** Pending **Status:**
Design Proposal
