# Agent Foundry - Roadmap Wishlist & Gap Analysis

**Status:** Planning
**Last Updated:** November 2024

This document captures strategic platform improvements, architectural gaps, and wishlist items for Agent Foundry. Unlike the sprint-based [ROADMAP.md](../../ROADMAP.md), this focuses on longer-term architectural decisions and enterprise requirements.

---

## 1. Core Platform & Architecture

### [ ] Official MCP Server Embedding (Priority 1)

**Goal:** Migrate from the custom Python "Shadow MCP" to the official `@modelcontextprotocol/sdk` (Node.js).

**Why:** Enables native integration with Cursor, Claude Desktop, and future AI agents. Ensures type safety via Zod.

**Action:** Implement the "Adapter Pattern" where Node.js handles the protocol and proxies execution to the Python/n8n layer.

**Related Docs:** [MCP SDK Migration Plan](../mcp/MCP_SDK_MIGRATION_PLAN.md)

---

### [ ] Postgres RLS & Tenant Isolation (Priority 1)

**Goal:** Enforce tenant isolation at the database level.

**Why:** "Defense-in-depth." Prevents AI agents from hallucinating data leaks.

**Action:** Complete the migration from SQLite to Postgres 16. Implement `tenant_id` columns on all core tables and apply Row-Level Security (RLS) policies.

**Related Docs:** [RBAC Implementation](../rbac/RBAC_IMPLEMENTATION.md)

---

### [ ] Hybrid Auth with Zitadel (Priority 2)

**Goal:** Support B2B Enterprise SSO (Okta/Azure AD) per tenant.

**Why:** Enterprise customers require their own IdP.

**Action:** Deploy Zitadel as the Identity Provider. Configure Fastify middleware to validate JWTs using JWKS and extract tenant context for RLS.

**Related Docs:** [OpenFGA Architecture](../openfga/OPENFGA_ARCHITECTURE.md)

---

### [ ] Google AIP-160 Filtering

**Goal:** Standardize API filtering (e.g., `filter="status=active AND created_at > '2024-01-01'"`).

**Why:** Required by Master Document (Section 4.2). Fastify currently lacks this.

**Action:** Implement a CEL (Common Expression Language) parser middleware for Fastify to translate AIP-160 strings into SQLAlchemy/SQL filters.

---

## 2. Reliability & Observability (The "Audit Proof")

### [ ] Local Observability Stack (LGTM)

**Goal:** Run Grafana, Loki, Tempo, and Prometheus locally via Docker Compose.

**Why:** "Compliance as Code" requires audit trails. You cannot debug distributed traces or verify RLS effectiveness without seeing the traces locally.

**Action:** Add the LGTM stack to `docker-compose.yml` and instrument Fastify/FastAPI with OpenTelemetry SDKs.

**Related Docs:** [Docker Dev Workflow](../DOCKER_DEV_WORKFLOW.md)

---

### [ ] Disaster Recovery (DR) & Data Lifecycle

**Goal:** Automated backups and data retention policies.

**Why:** Enterprise compliance (GDPR/CCPA) and reliability.

**Action:** Define automated workflows for tenant-specific data expiry and deletion. Implement cross-region replication strategy for production.

**Related Docs:** [Database Import/Export Guide](../DATABASE_IMPORT_EXPORT_GUIDE.md)

---

### [ ] Rate Limiting & Quotas

**Goal:** Prevent "noisy neighbor" issues.

**Why:** Multi-tenant fairness and cost control.

**Action:** Implement a distributed rate limiter (Redis-backed) keyed by `tenant_id`.

---

## 3. Developer Experience (DX)

### [ ] "Forge" CLI or UI

**Goal:** A robust tool for building, validating, and deploying Agent Manifests.

**Why:** "Manifest-Driven" architecture needs good tooling.

**Action:** Build a CLI that validates YAML manifests against the Domain Intelligence Schema (DIS) and allows local sandbox testing.

**Related Docs:** [Forge User Guide](../forge/FORGE_AI_USER_GUIDE.md)

---

### [ ] LangGraph Persistence (Postgres Checkpointer)

**Goal:** Durable agent state.

**Why:** In-memory state is lost on restart. Long-running agent workflows need persistence.

**Action:** Replace the default LangGraph checkpointer with a Postgres-backed implementation using the `foundry_app` database.

**Related Docs:** [LangGraph Agents Overview](../LANGGRAPH_AGENTS_OVERVIEW.md)

---

## 4. AI & Domain Intelligence

### [ ] DIS Version Control

**Goal:** Versioning and rollback for the Domain Intelligence Schema.

**Why:** Business rules change. Agents need to run against specific versions of the domain logic.

**Action:** Treat DIS definitions as code (Git-backed) with a migration strategy for live agents.

**Related Docs:** [Foundry Instance Architecture](../FOUNDARY_INSTANCE_ARCHITECTURE.md)

---

### [ ] Cost Attribution & Billing

**Goal:** Track LLM token usage per tenant/project.

**Why:** AI costs are high. You need accurate internal chargeback or external billing.

**Action:** Tag all LLM calls with `tenant_id` and aggregate usage metrics in Prometheus/Mimir or a dedicated billing table.

---

## 5. Security & Compliance

### [ ] Audit Log Immutability

**Goal:** Tamper-proof audit logs.

**Why:** High-trust enterprise requirement.

**Action:** Ensure audit logs are written to a WORM (Write Once, Read Many) compliant store or strictly permissioned Postgres table, with export capabilities for tenants (SIEM integration).

---

### [ ] Service-to-Service Auth (mTLS or JWT)

**Goal:** Secure internal traffic (e.g., Fastify -> Python Gateway).

**Why:** "Zero Trust" internal network.

**Action:** Enforce authentication between internal microservices, potentially using Zitadel Service Users or mTLS.

**Related Docs:** [Service Discovery](SERVICE_DISCOVERY.md)

---

## Priority Matrix

| Item | Priority | Complexity | Dependencies |
|------|----------|------------|--------------|
| Official MCP Server Embedding | P1 | High | Node.js adapter |
| Postgres RLS & Tenant Isolation | P1 | High | Postgres migration |
| Local Observability Stack (LGTM) | P1 | Medium | Docker Compose |
| Hybrid Auth with Zitadel | P2 | High | OpenFGA |
| LangGraph Persistence | P2 | Medium | Postgres |
| Rate Limiting & Quotas | P2 | Medium | Redis |
| Forge CLI/UI | P2 | Medium | DIS schema |
| Google AIP-160 Filtering | P3 | Medium | None |
| DIS Version Control | P3 | Medium | Git integration |
| Cost Attribution & Billing | P3 | Medium | Observability |
| Audit Log Immutability | P3 | Low | Postgres |
| Service-to-Service Auth | P3 | High | Zitadel |
| Disaster Recovery | P3 | High | Cloud infra |

---

## See Also

- [ROADMAP.md](../../ROADMAP.md) - Sprint-based release schedule
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Current system architecture
- [POC_TO_PROD_DELTA.md](../POC_TO_PROD_DELTA.md) - POC vs production gaps
