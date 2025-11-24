# Platform Implications - Object Admin Architecture

**Date:** 2025-11-16 **Impact Level:** 🔴 **High** - Affects multiple layers of
the platform

## 🎯 Key Architectural Decision

**ObjectAdminAgent → DataAgent pattern establishes a critical precedent for the
platform.**

This isn't just about admin UI—it's about establishing **clean separation of
concerns** across all agent interactions.

---

## 🏗️ The Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                   Presentation Layer                            │
│             (UI logic, formatting, validation)                  │
│                  ObjectAdminAgent                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ "Give me all orgs with tier=pro"
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│           (Queries, transformations, caching)                   │
│                     DataAgent                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ SQL
                             ▼
                        PostgreSQL
```

**This pattern should extend to ALL agent-to-data interactions.**

---

## 🌊 Ripple Effects Across Platform

### **1. Agent Design Pattern** 🎭

**Before:** Agents do their own data access

```python
class MyAgent:
    def do_work(self):
        # Agent directly queries DB
        with psycopg.connect(DB_URL) as conn:
            cur.execute("SELECT ...")
```

**After:** Agents delegate to specialized data agents

```python
class MyAgent:
    def __init__(self):
        self.data_agent = DataAgent()

    async def do_work(self):
        # Agent asks DataAgent for data
        result = await self.data_agent.query("Get all X where Y")
        # Agent focuses on business logic
        return self.process(result)
```

**Implication:** **Every agent should have a data layer counterpart**

- PMAgent → uses DataAgent for Notion queries
- ManifestAgent → uses DataAgent for manifest queries
- FormDataAgent → uses DataAgent for form data storage
- GovernanceAgent → uses DataAgent for policy rules

---

### **2. Caching Strategy** 💾

**Current:** No centralized caching **Future:** DataAgent becomes the caching
layer

```python
class DataAgent:
    def __init__(self):
        self.cache = RedisCache()

    async def query(self, question: str):
        # Check cache first
        cache_key = hash(question)
        if cached := await self.cache.get(cache_key):
            return cached

        # Execute query
        result = await self._execute_query(question)

        # Cache result
        await self.cache.set(cache_key, result, ttl=300)

        return result
```

**Implication:** **Single point of caching control**

- Reduced database load
- Faster response times
- Invalidation strategies centralized
- Cache hit rate metrics

---

### **3. Query Optimization** ⚡

**Current:** Each agent writes its own queries **Future:** DataAgent optimizes
all queries

```python
class DataAgent:
    async def query(self, question: str):
        # Generate SQL
        sql = await self.llm.generate_sql(question)

        # Optimize query
        optimized = self.query_optimizer.optimize(sql)

        # Add indexes if needed
        await self.index_advisor.suggest(optimized)

        # Execute
        return await self._execute(optimized)
```

**Implication:** **Platform-wide query performance improvement**

- Automatic query optimization
- Index recommendations
- Slow query identification
- Query plan analysis

---

### **4. Data Governance** 🛡️

**Current:** No centralized data access control **Future:** DataAgent enforces
all data policies

```python
class DataAgent:
    async def query(self, question: str):
        # Check data access policies
        if not await self.governance_agent.can_access(
            user=current_user,
            entity=extracted_entity,
            operation="read"
        ):
            raise PermissionDenied()

        # Check PII policies
        if self.contains_pii(question):
            await self.audit_logger.log_pii_access(...)

        # Apply row-level security
        sql = self._apply_rls(sql, current_user)

        return await self._execute(sql)
```

**Implication:** **Single enforcement point for data governance**

- GDPR compliance
- SOC2 audit trails
- PII detection
- Row-level security
- Column-level masking

---

### **5. Observability** 📊

**Current:** Scattered data access metrics **Future:** Centralized data access
telemetry

```python
class DataAgent:
    async def query(self, question: str):
        with tracer.start_span("data_agent.query") as span:
            span.set_attribute("question", question)
            span.set_attribute("user_id", current_user.id)

            start = time.time()
            result = await self._execute_query(question)
            duration = time.time() - start

            # Metrics
            metrics.histogram("data_agent.query_duration", duration)
            metrics.counter("data_agent.query_count", {
                "entity": extracted_entity,
                "user_role": current_user.role
            })

            return result
```

**Implication:** **Complete visibility into data access patterns**

- Query performance tracking
- User access patterns
- Entity popularity
- Bottleneck identification
- Cost attribution

---

### **6. Multi-Tenancy** 🏢

**Current:** Each agent handles org scoping independently **Future:** DataAgent
enforces tenant isolation

```python
class DataAgent:
    async def query(self, question: str):
        # Automatically inject tenant filter
        user_org = current_user.organization_id

        sql = await self.llm.generate_sql(question)

        # Add WHERE organization_id = ?
        sql = self.tenant_injector.add_filter(sql, user_org)

        return await self._execute(sql)
```

**Implication:** **Guaranteed tenant isolation**

- No cross-org data leaks
- Automatic org scoping
- Simplified agent logic
- Compliance requirement

---

### **7. Schema Evolution** 🔄

**Current:** Schema changes break multiple agents **Future:** DataAgent handles
schema compatibility

```python
class DataAgent:
    def __init__(self):
        self.schema_versioner = SchemaVersioner()

    async def query(self, question: str):
        # Get current schema version
        version = await self.schema_versioner.current()

        # Generate SQL for that version
        sql = await self.llm.generate_sql(
            question,
            schema=self.schema_versioner.get(version)
        )

        # Handle deprecated fields
        result = await self._execute(sql)

        # Transform to latest schema if needed
        return self.schema_versioner.transform(result, to=version)
```

**Implication:** **Backward compatibility for all agents**

- Gradual schema migrations
- No breaking changes
- Version-aware queries
- Deprecation warnings

---

### **8. Data Quality** ✅

**Current:** No centralized validation **Future:** DataAgent validates all data
operations

```python
class DataAgent:
    async def create(self, entity: str, data: dict):
        # Validate against schema
        schema = self.schema_registry.get(entity)
        errors = schema.validate(data)

        if errors:
            raise ValidationError(errors)

        # Check referential integrity
        if not await self._check_foreign_keys(entity, data):
            raise IntegrityError()

        # Execute insert
        return await self._insert(entity, data)
```

**Implication:** **Platform-wide data integrity**

- Required field enforcement
- Type validation
- Referential integrity
- Business rule validation

---

### **9. API Consistency** 🔌

**Current:** Each API endpoint implements own data access **Future:** All APIs
use DataAgent

```python
# Before: Inconsistent API implementations
@app.get("/api/orgs")
def get_orgs():
    conn = psycopg.connect(...)
    # Custom query

@app.get("/api/domains")
def get_domains():
    # Different pattern, different validation

# After: Consistent via DataAgent
@app.get("/api/orgs")
async def get_orgs():
    return await data_agent.query("List all organizations")

@app.get("/api/domains")
async def get_domains():
    return await data_agent.query("List all domains")
```

**Implication:** **Uniform API behavior**

- Consistent error handling
- Consistent pagination
- Consistent filtering
- Consistent caching

---

### **10. Testing Strategy** 🧪

**Current:** Mock database in every agent test **Future:** Mock DataAgent once,
test all agents

```python
# Before: Complex per-agent mocks
def test_my_agent():
    with mock.patch('psycopg.connect') as mock_db:
        mock_db.return_value.__enter__.return_value.cursor.return_value.fetchall.return_value = [...]
        # Complex setup

# After: Simple DataAgent mock
def test_my_agent():
    with mock.patch.object(DataAgent, 'query') as mock_query:
        mock_query.return_value = {"rows": [...]}
        # Simple setup
```

**Implication:** **Easier testing across platform**

- Reduced test complexity
- Faster test execution
- Better test coverage
- Consistent test patterns

---

## 🎯 Recommendations

### **Immediate Actions**

1. **Refactor ObjectAdminAgent** to use DataAgent (this week)
2. **Document the pattern** as standard practice (done ✅)
3. **Create DataAgent interface contract** (clear API)
4. **Add metrics** to DataAgent for observability

### **Short-term (1 month)**

5. **Audit all agents** for direct DB access
6. **Migrate agents** to use DataAgent pattern
7. **Implement caching** in DataAgent
8. **Add query optimization**

### **Long-term (3 months)**

9. **Add governance hooks** to DataAgent
10. **Implement schema versioning**
11. **Add data quality validation**
12. **Build DataAgent admin UI** (query logs, performance, etc.)

---

## ⚠️ Potential Risks

### **1. Single Point of Failure**

**Risk:** If DataAgent is down, all agents fail **Mitigation:**

- Circuit breaker pattern
- Fallback to direct queries (degraded mode)
- High availability deployment

### **2. Performance Bottleneck**

**Risk:** DataAgent becomes a bottleneck **Mitigation:**

- Aggressive caching
- Query optimization
- Horizontal scaling
- Connection pooling

### **3. Increased Complexity**

**Risk:** Extra layer adds latency **Mitigation:**

- Keep DataAgent simple and fast
- Async/await throughout
- Batch operations
- Parallel queries

### **4. Over-Abstraction**

**Risk:** DataAgent tries to do too much **Mitigation:**

- Keep focused on data access only
- Don't add business logic
- Clear interface boundaries
- Single responsibility

---

## 📊 Success Metrics

Track these metrics to validate the approach:

| Metric                         | Target       | Why             |
| ------------------------------ | ------------ | --------------- |
| Cache Hit Rate                 | >80%         | Efficiency      |
| Query Duration (p95)           | <100ms       | Performance     |
| Data Access Audit Coverage     | 100%         | Governance      |
| Agent Test Execution Time      | <50% current | Testing         |
| Code Duplication (data access) | <10%         | Maintainability |
| Data-related Bugs              | -50%         | Quality         |

---

## 🎓 Learning for the Team

**Key Insight:** **Agents should be "dumb" about data access**

```
Smart Agents = Business Logic + Presentation Logic
Dumb Agents = Just Business Logic

Smart DataAgent = Query Optimization + Caching + Governance
Dumb DataAgent = Just Execute SQL
```

We want:

- **Smart business agents** that delegate data to **smart data agents**
- Not: Smart agents that do everything themselves

**Mantra:** "If it touches the database, it goes through DataAgent"

---

## 🔮 Future Vision

In 6 months, every data interaction should look like:

```python
# Natural language interface to ALL data
result = await data_agent.query(
    "Show me all high-priority stories in the retail banking domain
     created in the last week that don't have acceptance criteria"
)

# DataAgent handles:
# ✅ NL → SQL translation
# ✅ Query optimization
# ✅ Permission checking
# ✅ Tenant filtering
# ✅ Caching
# ✅ Audit logging
# ✅ Result formatting
```

**This is the power of centralization done right.**

---

**Author:** Claude Code **Review Status:** Proposed **Impact:** Platform-wide
**Priority:** High
