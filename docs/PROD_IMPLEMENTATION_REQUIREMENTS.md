Implementation Requirements — Engineering Department (Agentic SDLC)

Scope aligned to the Enterprise Multi-Platform Architecture Scaffold and your Engineering Department plan. Structured for execution.

⸻

0) Scope & Assumptions
	•	Scope: Stand up a governed, multi-tenant, MCP-first software factory where AI agents operate the SDLC end-to-end with human oversight.
	•	SSOT: Notion for portfolio/backlog/queues; Git for code; CI/CD for build; Observability stack for run.
	•	Agent Stack: Product Owner, Project Manager, Engineer (BE/FE/ML/PE/DATA), QA, SRE/AIOps, Release, Judge/ARB.
	•	Guardrails: Strong identity, role/authority catalogs, policy-as-code, auditability, and evals for LLM/agent safety.
	•	Out-of-scope (M0-M1): Marketplace/extensibility store, billing/quotes, complex partner SSO federation.

⸻

1) Reference Architecture Mapping (Planes)
	•	Control Plane: Identity/SSO, RBAC/ABAC, MCP tool registry, policy/evidence, audit, billing hooks.
	•	Data Plane: Repo/registry, datasets/features/model store, object store, vector store, relational DB(s).
	•	Event Plane: CloudEvents-wrapped domain events; AsyncAPI catalog; optional broker (Kafka/NATS).
	•	Observability Plane: OTel collectors, traces/logs/metrics, SLO dashboards, alerts, runbooks.

⸻

2) Identity, Roles, Scopes (Multi-Tenant)

Requirements
	•	SSO (OIDC/SAML), MFA; SCIM for provisioning.
	•	Scopes: organization → team → project → resource with hierarchical inheritance.
	•	Authorities: immutable CRUDX actions; Roles: catalog + custom roles (admin/editor/read-only).
	•	ABAC (phase-in): region/classification/time attributes via policy engine (OPA/Cedar/OpenFGA).
	•	Audit: All authz decisions + MCP tool invocations (actor, inputs, output hashes) persisted and queryable.

Acceptance
	•	Login via OIDC, MFA enforced per org; role catalog seeded; audit query returns complete decision trail.

⸻

3) API & Integration Surfaces

Requirements
	•	REST APIs (OpenAPI 3.1, Google AIP style: pagination, filters, field masks, partial responses).
	•	Events: CloudEvents 1.0 envelope everywhere; AsyncAPI source-of-truth for channels.
	•	MCP Server embedded: typed tools for backlog, queues, tasks, repo ops, CI gates, observability queries.
	•	Idempotency keys, problem-details errors (RFC 7807), rate-limit headers.
	•	Webhooks with signed delivery; SDKs generated from OpenAPI/AsyncAPI.

Acceptance
	•	OpenAPI/AsyncAPI published; codegen stubs compile; MCP tool permission model verified by tests.

⸻

4) Data & ML Readiness

Data
	•	Data inventory, lineage, SLAs, consent/license capture; dataset versioning (DVC/Lake/LakeFS).
	•	PII handling: masking/redaction; per-tenant namespaces and KMS-wrapped keys; residency tags.

ML/Agents
	•	Model registry (tags: version, license, eval score, latency); feature store; inference service spec (FastAPI).
	•	Agent graph spec (LangGraph): roles, tools, policies; prompt/version pins; offline/online eval harness.
	•	Safety evals: hallucination/toxicity/bias gates; red-team corpus; cost tracking.

Acceptance
	•	Reproducible dataset → model → eval pipeline; eval thresholds enforced in CI; model card published.

⸻

5) Agentic SDLC (Backlog → Queues → Execution → QA → Release)

Work Ontology
	•	Release/Epic/Story/Task with Definition of Done, acceptance criteria, and test artifacts links.
	•	States: Backlog → To Do → In Progress → In Review → In QA → Done.
	•	Priority: P0–P3; PM resolves ties.

Queues & Autonomy
	•	Per-role AgentQueue with pull-based pickup of highest-priority ready tasks.
	•	PM Agent orchestrates priority, WIP limits, cross-lane dependencies; Judge/ARB resolves conflicts.
	•	Engineers (BE/FE/MLE/PE/DATA) update notes/status continuously; QA agents run contract/e2e/safety.

Acceptance
	•	E2E demo: PO interview → stories → PM assignment → Engineer PR → QA pass → canary → full rollout.

⸻

6) Platform & DevOps

IaC & Environments
	•	Terraform/Kubernetes/Secrets; environments: dev, pr-preview, staging, prod (tenancy aware).
	•	Git strategy: trunk-based with short-lived branches; PR checks mandatory.

CI/CD (Required Gates)
	•	Build SBOMs, SAST/DAST, license scan; unit/integration/e2e; AI evals for agent/model changes.
	•	Image signing (Sigstore/Cosign); provenance (SLSA); drift detection.

Release
	•	Release Manager tags versions; progressive delivery (canary/blue-green); feature flags; one-click rollback.
	•	Handover to SRE: runbooks, SLOs, alerts, dashboards.

Acceptance
	•	PR creates ephemeral environment with preview URLs; all gates green to merge; signed artifacts deployed.

⸻

7) Observability & AIOps

Telemetry
	•	OTel SDKs across services/agents; tenant and scope attributes; traceparent/baggage propagation.
	•	Logs (Loki), Metrics (Prometheus/Mimir), Traces (Tempo or vendor); alert rules tied to SLOs.

AIOps
	•	Anomaly detection, drift and capacity alerts; error-budget burn reports; RCA helpers.
	•	Cost/req telemetry for models and agents.

Acceptance
	•	Golden signals dashboards live; alert → incident → postmortem loop verified; cost dashboard visible.

⸻

8) Security, Privacy, Compliance

Baseline
	•	TLS 1.3 preferred; AES-256-GCM at rest; envelope encryption with per-tenant DEKs via KMS/HSM.
	•	Password hashing: Argon2id (default); secret manager (no plaintext secrets).
	•	SBOM generation, dependency risk gates; periodic pen-tests; breach workflow; DSR (GDPR/CCPA) flows.

AI Governance
	•	NIST AI RMF / ISO 42001 profile; HITL for sensitive actions; transparency notes.
	•	Trust Center: security overview, policies, architecture, audit reports (NDA-gated), updates feed.

Acceptance
	•	Control checklist evidence in repo; Trust Center serves public and gated content; pen-test findings tracked to closure SLAs.

⸻

9) UX, Accessibility, Docs

UX
	•	Wireframes and conversation flows; accessibility WCAG 2.1/2.2 AA; internationalization.
	•	Streamlit (initial) for agent dashboard/chat; Next.js for product surfaces (later).

Docs/DevRel
	•	API refs, runbooks, changelogs, deprecation notices; doc build in CI; versioned docs.

Acceptance
	•	Axe accessibility checks pass in CI; docs portal deploys per release with version switcher.

⸻

10) Environment & Tenancy Controls
	•	Tenant routing headers; scoped credentials for background jobs; per-tenant retention schedules.
	•	Optional dedicated single-tenant mode (sensitive customers) with private ingress/VPC peering.
	•	Federated analytics with tenant-scoped access; export controls.

Acceptance
	•	Tenant A cannot see B (data, telemetry, docs); dedicated deployment template passes smoke tests.

⸻

11) Non-Functional Requirements (SLOs)
	•	Availability: ≥ 99.9% (prod).
	•	Latency: p95 API ≤ 250 ms (read), ≤ 500 ms (write); p95 inference/agent step ≤ target per use case.
	•	Quality: Eval score ≥ threshold per task class; regression budget enforced.
	•	Security: 0 critical vulns in prod; key rotation ≥ annually; audit gap SLA ≤ 7 days.
	•	Cost: Cost/req tracked; budget alerts at 50/75/100%.

⸻

12) Change Management & Governance
	•	ADRs for material changes; ARB cadence; versioning policy (APIs/events/models/prompts).
	•	Deprecation windows with notices; postmortems with action items tracked to completion.

Acceptance
	•	ADR index live; deprecation notice pipeline tested; postmortem template used at least once.

⸻

13) Phased Execution Plan (DoD per Milestone)

M0 — Foundation
	•	Identity/SSO/MFA; roles/authorities; Notion schemas; core repos; OTel collectors; initial audit logs.
	•	DoD: Login through IdP; role-gated Notion views; traces visible; audit queries return results.

M1 — Events & MCP
	•	CloudEvents envelope; AsyncAPI catalog; embedded MCP server (read-only tools) + registry.
	•	DoD: MCP tool calls audited; AsyncAPI published; event ingestion verified.

M2 — SDLC Agent Loop
	•	Product Owner agent; PM agent; queues; Engineer/QA agents; CI/CD gates; ephemeral envs.
	•	DoD: E2E story from intake → deploy with canary; QA and safety gates enforced.

M3 — SRE, AIOps, Governance
	•	SLOs, alerts, runbooks; release automation; Trust Center; AI governance workflows; ABAC pilot.
	•	DoD: Alert → incident → postmortem; Trust Center live; ABAC policy exercised.

⸻

14) Artifacts to Produce (Immediate)
	•	Notion schema: Portfolio (Initiatives/Releases), Epics, Stories, Tasks, Queues, Risks, ADRs, DoD templates.
	•	OpenAPI/AsyncAPI skeletons; MCP tool contracts (backlog, queues, repo, CI, observability).
	•	OTel spec: resource attributes, sampling, log/metric/trace pipelines.
	•	CI policy: required checks matrix; SBOM/signing/provenance config.
	•	Security baseline: KMS layout, key policy, rotation calendar; secret classes and usage policy.
	•	SLO catalog and dashboards; runbook template; postmortem template.
	•	Eval harness: datasets, metrics, thresholds, red-team corpus, cost reporting.

⸻

15) Risks & Mitigations
	•	Role sprawl / permission drift: Managed catalogs, diffs, approvals; periodic audits.
	•	PII in telemetry: Redaction processors; secure telemetry project; access scoping.
	•	Agent safety regressions: Mandatory eval gates; canary shadow traffic; HITL escalation.
	•	Event plane complexity: Design-time optional broker; CloudEvents envelope mandated; outbox pattern.
	•	Vendor lock-in: OTLP everywhere; provider adapters; export tooling; open standards.

⸻

16) Definition of Done (Global)
	•	Every change has: ADR (if applicable), tests, SBOM, signed artifacts, eval report (if agent/model), docs updated, OTel traces, and audit entries.
	•	Tenancy isolation tests pass.
	•	SLOs met in staging prior to prod promotion.

⸻

Execution Note

This is ready to translate into Epics/Stories and MCP tool specs. When you’re ready to move, I’ll generate the initial Notion schema, OpenAPI/AsyncAPI/MCP stubs, CI policy file, and eval harness scaffold to fast-start M0→M1.