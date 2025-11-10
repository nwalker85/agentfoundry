# Engineering Department — Lessons Learned

## Context
Document captures insights and adjustments discovered during the initial implementation of the Engineering Department agentic stack.

## Key Learnings

### 1. Architectural Continuity
- **Decision:** Abandon Streamlit for Next.js to avoid rework.
- **Rationale:** Streamlit is not sustainable for production. Next.js (App Router + TypeScript) provides continuity, accessibility, and governance hooks.

### 2. MCP Tool Definition
- MCP needs explicit input/output schemas to ensure predictable agent behavior.
- Adopted **OpenAPI-first** pattern for all MCP endpoints; prevents silent tool drift.

### 3. Token Handling & Security
- Early test logs exposed full tokens; added redaction middleware.
- **Lesson:** Implement `*_TOKEN`, `*_KEY` masking at logger level before expansion.

### 4. Notion Schema Volatility
- Discovered inconsistency in Notion API responses for relation fields.
- Mitigation: dynamic schema discovery at startup + local cache.

### 5. Idempotency
- Re-runs produced duplicate issues in GitHub.
- Introduced hash-based idempotency key (title + epic) written into issue body comment block.

### 6. Audit & Observability
- Simple console logs insufficient; moved to JSONL append log + traceparent propagation.
- OpenTelemetry integration scheduled for Phase 4.

### 7. Prompt Governance
- LangGraph prompts require version pinning; added `policy.py` to isolate template versions for eval tracking.

### 8. Next.js App Router Discipline

- Root-level `app/` directory must contain `page.tsx` and `layout.tsx`; nesting an extra `app/` produced 404s until we flattened the structure.
- Tailwind configuration needs the `app/**/*` glob to pick up App Router components, otherwise styles silently fail.

### 9. Environment Reprovisioning

- Rebuilding the Python 3.12 virtualenv and reinstalling dependencies resolved `pydantic-core` wheel issues and removed drift from old packages.
- npm dependency upgrades (Next.js 14.2.33, eslint-config-next parity) avoided security advisories flagged by `npm audit`.

### 10. CLI Output Hygiene

- Replaced emoji indicators in CLI smoke tests with ASCII to keep logs automation-friendly and avoid encoding issues in CI.
- Added standalone Notion smoke test (`test_notion.py`) so environment validation is scriptable before running the full stack.

## Outstanding Questions

- Will FastAPI remain embedded, or should MCP become a standalone service container?
- Should audit logs replicate to SQLite for persistence beyond JSONL?

## Next Review

Update this document after MCP + Agent integration test (end of Phase 2).

---
