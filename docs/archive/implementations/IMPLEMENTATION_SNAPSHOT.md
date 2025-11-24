# Agent Foundry – Implementation Snapshot

_Updated: November 17, 2025_

This snapshot captures the current state of the platform after the latest
integration sprint so that anyone jumping in can understand what’s done, what’s
wired up, and what’s still outstanding.

> **How to use this document:** skim the summary to orient, then drill into the
> area you’re working on (backend/UI/integrations/docs) to see status + next
> steps. Update this doc whenever significant functionality lands or priorities
> change.

---

## 1. Platform Summary

| Area                    | Status                                                                                                         | Notes                                                                                                                               |
| ----------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Onboarding Docs         | ✅ README + START_HERE + Docker/AWS guides refreshed; LiveKit doc consolidated                                 | Need to weave new RBAC + integration gateway docs into main paths                                                                   |
| Control Plane Backend   | ✅ Org/domain/agent APIs live; LangGraph agents exposed; Admin assistant endpoint added                        | DB schema expanded with `integration_configs`; RBAC endpoints added but not wired to auth yet                                       |
| MCP Integration Gateway | ✅ FastAPI service + manifest loader + n8n sidecar running in Docker; `/tools` + `/invoke` endpoints available | Need operational docs + UI config screen                                                                                            |
| Frontend (Forge UI)     | 🚧 Layout shell stable; TopNav now drives org/domain from backend; Admin Assistant panel shipping              | `/tools` page still mock-based; needs real catalog + configuration workflow                                                         |
| Documentation Coverage  | ⚠️ Partial                                                                                                     | Architecture doc exists for MCP + n8n; no “Implementation Snapshot” until this file; RBAC and integration config procedures missing |

---

## 2. Backend State

### What’s Implemented

- Control-plane API endpoints (`/api/control/organizations`,
  `/api/control/agents`, `/api/control/query`, `/api/admin/assistant/chat`).
- MCP Integration proxy endpoints:
  - `/api/integrations/tools` (merges manifest + health metrics).
  - `/api/integrations/tools/{tool}` detail.
  - `/api/integrations/tools/{tool}/invoke` to proxy to gateway/n8n.
- Integration configuration persistence:
  - New `integration_configs` table in `backend/db_schema.sql`.
  - CRUD helpers in `backend/db.py` (`list_integration_configs`,
    `get_integration_config`, `upsert_integration_config`).
  - REST endpoints for listing/fetching/upserting configs (not yet consumed by
    UI).
- RBAC scaffolding: service + endpoints added (user-permissions lookup,
  placeholder `/api/auth/me`), plus schema + scripts for RBAC tables.

### Gaps / Next Actions

- Wire RBAC middleware/auth into FastAPI + NextAuth (`backend/rbac_*`,
  `middleware.ts` exist but not integrated).
- Add validation, masking, and secret storage for integration credentials
  (currently stored as JSONB without encryption).
- Document operational flow: how to seed `integration_configs`, how to rotate
  credentials, how to restart gateway.
- Telemetry/metrics for integration proxy (currently only success/failure
  counters stored in-memory).

---

## 3. Integration Gateway (MCP ↔ n8n)

### What’s Working

- `mcp/integration_server/` FastAPI app loads manifest, exposes `/tools`,
  `/tools/{tool}`, `/tools/{tool}/invoke`, `/health`.
- Sample manifest configured with ServiceNow, Slack, Jira workflows.
- Docker Compose service `mcp-integration` built + wired; backend references it
  via `MCP_INTEGRATION_URL`.
- Unit + integration tests (`tests/unit/mcp/...`,
  `tests/integration/test_mcp_integration_server.py`) green.

### What’s Missing

- Admin UX: no way for designers to configure per-org credentials inside Foundry
  (see UI section).
- Health metrics limited to success/failure counts; no latency or per-error
  detail.
- Need “runbook” doc (start/stop gateway, edit manifest, sync with n8n exports).

---

## 4. Frontend / Forge UI

### Current State

- Layout + navigation stabilized; TopNav pulls org/domain from backend API.
- Admin Assistant floating panel live across app.
- `/agents` page talks to backend; `/tools` still uses `mockTools`.
- No UI for integration credential entry; designers can’t configure instances
  from Foundry yet.

### Immediate TODOs

1. Rebuild `/tools` page to:
   - Fetch catalog from `/api/integrations/tools`.
   - Display health badges, categories, vendor logos (drop visible “n8n”
     branding per exec feedback).
   - Provide “Configure” drawer to save instance info + credentials via
     `/api/integrations/configs/...`.
2. Add visual cues linking tools to org/domain context (selected in header).
3. Document designer workflow in README or dedicated `docs/INTEGRATIONS.md`.

---

## 5. Documentation Checklist

| Doc                            | Status         | Action                                                   |
| ------------------------------ | -------------- | -------------------------------------------------------- |
| README / START_HERE            | ✅             | Mention RBAC + integration gateway next time they change |
| `docs/MCP_N8N_ARCHITECTURE.md` | ✅             | Add section on config persistence + UI                   |
| RBAC docs (`docs/RBAC_*`)      | 🆕 but siloed  | Fold key steps into onboarding                           |
| Implementation Snapshot        | ✅ (this file) | Update whenever a major subsystem changes                |

---

## 6. Action Items (Next Sprint)

1. **Finish Integration UI** – hook `/tools` to backend catalog + config APIs,
   update design (remove n8n term, show badges).
2. **RBAC Wiring** – enforce auth on new endpoints, integrate NextAuth session
   provider, update docs.
3. **Operational Docs** – create `docs/INTEGRATIONS_RUNBOOK.md` (manifest edits,
   gateway restarts, troubleshooting).
4. **Testing & Metrics** – add frontend tests for `/tools`, expand backend tests
   for config APIs, expose metrics dashboard.
5. **Forge LangGraph Enhancements** – start implementing high-priority items
   from `FORGE_LANGGRAPH_GAP_ANALYSIS.md` (state designer, routing).

---

_When you update major functionality, refresh this snapshot (including the date
above) so everyone knows the ground truth._
