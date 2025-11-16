## Fully Agentic Foundry Roadmap (MVP-Focused)

### 1. Objective

**Goal for MVP:**  
From Agent Foundry, a user can **design an agent**, **configure its system agents**, and **deploy it as an isolated runtime Instance** (identified by `organization / domain / environment / instance`) that exposes a hostname and serves traffic via LangGraph + MCP.

This roadmap focuses on what is strictly required to reach that build‑and‑deploy capability.

---

### 2. Guiding Principles

- **Control plane vs data plane**
  - Agent Foundry = *control plane* (design, configuration, manifests, deployments).
  - Instances = *data plane* (runtime containers per org/domain/instance).
- **LangGraph + MCP everywhere**
  - All execution = LangGraph graphs.
  - All side effects (LLMs, tools, DBs, infra) = MCP tools.
  - Foundry UI talks only to the backend MCP (or a thin HTTP→MCP bridge).
- **Manifest-driven**
  - Manifests are the source of truth for which agents exist in which org/domain/instance and environment.
- **Isolated instances**
  - Each instance runs in its own container (ECS/Fargate service), with its own config and secrets, and its own hostname.

---

### 3. MVP User Stories

1. **Design & Save**
   - As a platform builder, I can create or edit an agent in Forge and save it as a LangGraph/YAML definition in the Foundry.

2. **Configure System Agents**
   - I can view and edit the configuration of system agents (io/supervisor/context/coherence/exception/observability/governance) in the Foundry UI, scoped to an organization/domain/environment/instance.

3. **Bind Agent to Instance**
   - I can choose which agents (system + custom) belong to a specific `(org, domain, env, instance)` and see that reflected in manifests.

4. **Deploy Instance**
   - I can click “Deploy” and the Foundry will:
     - Build an Instance manifest.
     - Provision/update a containerized runtime in AWS (ECS/Fargate).
     - Return a hostname for that instance.

5. **Invoke Deployed Agent**
   - I can send a chat/voice request to the instance hostname and get a response from the deployed agent using the configured system agents.

---

### 4. Current Baseline (Already in Place)

- System agents defined as Python modules:
  - `io_agent`, `supervisor_agent`, `context_agent`, `coherence_agent`
  - `exception_agent`, `observability_agent`, `governance_agent`
- System agent YAML configs in `agents/`.
- System Agents configuration UI at `/system-agents`:
  - Tier 0 (foundation) + Tier 1 (production) grouping.
  - Reads/writes YAML via `/api/system-agents`.
- Environment manifests & instance template:
  - `agents/manifests/manifest.dev.yaml`
  - `agents/manifests/manifest.staging.yaml`
  - `agents/manifests/manifest.prod.yaml`
  - `agents/manifests/manifest.instance-template.yaml`
- TypeScript types for manifests: `AgentManifest`, `AgentManifestEntry`.
- `/api/system-agents` now backed by the **dev environment manifest**, with filters for `orgId/domainId/instanceId`.

This is a solid foundation for the MVP, but the actual runtime deployment and LangGraph/MCP wiring is still to be done.

---

### 5. MVP Phase 1 – LangGraph + MCP Runtime Skeleton

**Goal:** Have a single runtime process that can execute an agent graph via LangGraph and MCP tools, without yet worrying about multi‑instance deployment.

- **5.1 Define `PlatformState` and core LangGraph graph**
  - Implement a `PlatformState` type capturing:
    - `messages`, `session`, `user`, `worker_responses`, `final_response`, etc.
  - Build a **single LangGraph graph** representing the system agents chain:
    - Nodes: `io` → `governance` → `context` → `supervisor` → `workers` → `coherence` → `observability` → `io_out`.
  - Each node should internally call *functions that will be converted to MCP tools* (even if initially they are direct Python calls).

- **5.2 MCP backend for tooling**
  - In `mcp_server.py`, define tool namespaces for:
    - `llm` (Anthropic/OpenAI)
    - `redis` (stubbed or real)
    - `postgres` (stubbed or real)
    - `livekit` (stubbed or real)
  - Expose a `platform.run_agent` tool:
    - Input: `{ agent_id, org_id, domain_id, environment, instance_id, input }`
    - Behavior: load the right agent graph and run it with LangGraph.

- **5.3 Bridge UI to MCP**
  - Add a thin HTTP or WebSocket bridge from Next.js to MCP:
    - e.g. `/api/mcp` → forwards JSON RPC to MCP server.
  - Update any UI features that need runtime interaction (e.g. test‑run from Forge) to call MCP instead of direct Python/HTTP.

**Success criteria for Phase 1:**
- Able to call `platform.run_agent` from a dev script or the UI and get a response from the LangGraph runtime (on a single shared dev instance).

---

### 6. MVP Phase 2 – Instance Manifest → Runtime Bundle

**Goal:** Generate a concrete runtime configuration for a single instance using manifests.

- **6.1 Compose per‑instance manifest**
  - Implement a backend function / MCP tool:
    - `foundry.build_instance_manifest({ orgId, domainId, environment, instanceId })`
  - Logic:
    - Read `manifest.<environment>.yaml`.
    - Filter entries by `orgId/domainId/instanceId`.
    - Merge with `manifest.instance-template.yaml` (ensure all required system agents are present).
    - Attach custom worker agents selected from Forge.
  - Output: a **concrete Instance manifest** (YAML or JSON) describing:
    - All agents (system + custom) included in the instance.
    - Paths to their specs/graphs.
    - Org/domain/env/instance metadata.

- **6.2 Build runtime bundle (filesystem/S3)**
  - Implement `foundry.build_instance_bundle({ instanceManifest })`:
    - Packages:
      - Instance manifest
      - Referenced agent YAML files
      - LangGraph graph definitions
      - Any static configuration needed by MCP tools.
    - Stores bundle in a known location (e.g. S3 or local path in dev).

**Success criteria for Phase 2:**
- Given `org/domain/env/instance`, we can produce an **Instance manifest** and a corresponding **bundle** ready to be mounted into a runtime container.

---

### 7. MVP Phase 3 – Single-Instance Deployment on AWS (ECS + Fargate)

**Goal:** Deploy exactly one runtime Instance container from the Foundry and hit it over HTTP/WebSocket.

- **7.1 Runtime container image**
  - Build a Docker image that contains:
    - MCP server
    - LangGraph runtime
    - Code for system/custom agents
  - Parameterized via:
    - `ORG_ID`, `DOMAIN_ID`, `ENVIRONMENT`, `INSTANCE_ID`
    - `INSTANCE_MANIFEST_PATH` or S3 URL
    - Tool config env vars (e.g. Anthropic key via Secrets Manager).

- **7.2 ECS/Fargate service definition**
  - Manually or via Terraform:
    - Task definition using the runtime image.
    - Fargate service for one instance.
    - ALB + listener + target group.
    - Route53 record: e.g. `dev-retail-1.instances.agentfoundry.com`.

- **7.3 Foundry → Deploy button (single instance)**
  - Implement an MCP tool `foundry.deploy_instance` that:
    - Accepts `{ orgId, domainId, environment, instanceId }`.
    - Calls `build_instance_manifest` + `build_instance_bundle`.
    - Triggers ECS deployment (initially via a shell script or Terraform CLI).
  - Add a simple UI action (e.g. “Deploy Instance” button) that calls this MCP tool.

**Success criteria for Phase 3:**
- Click “Deploy Instance” in Foundry (for a chosen org/domain/env/instance) and:
  - A new ECS/Fargate service is created.
  - The instance is reachable at a hostname.
  - Sending a chat request to that hostname returns a response from the deployed agent via LangGraph.

---

### 8. MVP Phase 4 – Minimal AgentOps Around Deployment

**Goal:** Basic operational visibility for the deployed instance.

- **8.1 Health & status**
  - MCP tools:
    - `foundry.get_instance_status` (queries ECS service/task status).
    - `foundry.get_agent_health` (proxies to instance’s observability_agent / health checks).
  - UI:
    - Show simple status for the instance: `running / failed / deploying`.

- **8.2 Logs & traces (read-only)**
  - Wire `observability_agent` in the instance to:
    - Log traces to CloudWatch or a simple store accessed via MCP.
  - Foundry UI:
    - Basic “last N executions” view for an instance.

**Success criteria for Phase 4:**
- From Foundry, you can see whether your deployed instance is up and view basic recent execution traces.

---

### 9. Post-MVP (Later Phases, Not Required to Build & Deploy)

These are important but **not required** for the initial “build and deploy an agent” MVP:

- Multi-instance support and blue/green or canary deployments.
- Automated test orchestration across instances.
- Advanced cost & performance optimization agents.
- Full governance & compliance workflows.
- Rich Forge–runtime integration (step-through debugging, live graph introspection).

---

### 10. Summary – Minimal Path to “Build & Deploy”

To reach a usable MVP where you can **build and deploy an agent**:

- **Phase 1** – LangGraph + MCP runtime skeleton (single shared dev instance).
- **Phase 2** – Instance manifest + bundle generation.
- **Phase 3** – Single-instance ECS/Fargate deployment and hostname.
- **Phase 4** – Basic health & trace visibility.

Once these are in place, Agent Foundry will be able to:

1. Design an agent (Forge).  
2. Bind it to an org/domain/instance via manifests.  
3. Generate a runtime bundle.  
4. Deploy it as a standalone Instance container in AWS.  
5. Let you send real traffic to that instance and see responses.  

That’s the “fully agentic Foundry” MVP: **From graph to running instance** using LangGraph + MCP, with a clear separation between the Foundry control plane and Instance runtimes.


