# Agent Foundry vs Runtime Instances – Architecture & Deployment

## 1. Control Plane vs Data Plane

### Agent Foundry (Control Plane)

**What it is**:  
The Foundry is a _suite of tools_ that enables a complete AgentOps workflow:

- Forge (graph / workflow builder)
- Agent configuration (system + custom)
- Datasets, monitoring, deployments, governance
- UI + MCP clients (VS Code, CLI, etc.)

**Responsibilities**:

- Stores **agent templates** (LangGraph graphs + YAML specs)
- Stores **manifests** that describe which agents belong to which
  `organization / domain / environment / instance`
- Builds and ships **runtime bundles** for each instance
- Observes instances via MCP (optional)

**What it does _not_ do**:

- It does **not** host production traffic directly
- It does **not** talk to external APIs/DBs except through the **backend MCP
  server**

### Runtime Instance (Data Plane)

**What it is**:  
Each **Instance** is a **standalone runtime deployment** identified by:

- `organization_id`
- `domain_id`
- `environment` (`dev`, `staging`, `prod`)
- `instance_id` (e.g. `dev`, `us-east-1`, `tenant-123`)

**Responsibilities**:

- Runs its own **LangGraph + MCP runtime**
- Hosts its own **system agents**
  (io/supervisor/context/coherence/exception/observability/governance)
- Hosts its own **custom worker agents** (pm, ticket, qa, customer-defined)
- Owns its own **data plane** (Redis, Postgres, S3, etc.)

**Key property**:  
An Instance can run independently of the Foundry once deployed. The Foundry is
the _control plane_; Instances are the _data plane_.

---

## 2. Manifests – Binding Agents to Orgs / Domains / Instances

We use **manifests** to describe _where_ agents live.

### 2.1 Environment Manifests (Foundry Side)

Path:

- `agents/manifests/manifest.dev.yaml`
- `agents/manifests/manifest.staging.yaml`
- `agents/manifests/manifest.prod.yaml`

These files live in the Foundry repo and describe **all agents bound into a
given environment**.

Example (`agents/manifests/manifest.dev.yaml`):

```yaml
apiVersion: agent-foundry/v1
kind: AgentManifest
metadata:
  description: Dev environment manifest for all system agents
  generated_at: '2025-11-16T00:00:00Z'
  version: '0.1.0'

spec:
  entries:
    - agent_id: io-agent
      yaml_path: dev_io_agent.yaml
      organization_id: default-org
      organization_name: Default Organization
      domain_id: default-domain
      domain_name: Default Domain
      environment: dev
      instance_id: dev
      is_system_agent: true
      system_tier: 0
      version: '0.8.0'
      author: system
      last_editor: system
      tags: [platform, io, adapter]
    # ... other system agents ...
```

This manifest is used by the **Foundry backend MCP** to:

- Know which agents exist in a given environment
- Build per-instance runtime bundles
- Filter agents by `org/domain/instance` when the UI queries via MCP

### 2.2 Instance Template Manifest

Path:

- `agents/manifests/manifest.instance-template.yaml`

Describes **what a runtime Instance should look like**. It is parameterised
(placeholders) and filled in at build/deploy time.

Example:

```yaml
apiVersion: agent-foundry/v1
kind: AgentInstanceTemplate
metadata:
  description: Template for runtime instances
  version: '0.1.0'

spec:
  # Required system agents for every instance
  system_agents:
    - agent_id: io-agent
    - agent_id: supervisor-agent
    - agent_id: context-agent
    - agent_id: coherence-agent
    - agent_id: exception-agent
    - agent_id: observability-agent
    - agent_id: governance-agent

  # Custom workers will be filled in per instance
  custom_agents: []
```

At deploy time the Foundry:

1. Selects a subset of agents from the **environment manifest** for a given
   `org/domain`.
2. Merges them with the **instance template** to produce a concrete **Instance
   manifest** (e.g. `manifest.org-123.domain-retail.instance-us-east-1.yaml`).
3. Packs that manifest + YAML specs + LangGraph graphs into a **runtime bundle**
   for deployment.

---

## 3. Execution Architecture – LangGraph + MCP Only

**Rule**:  
Only the **backend MCP server** talks to external APIs/datastores.  
All intra-platform communication is via **MCP tools**, and all orchestration is
via **LangGraph**.

### 3.1 Control Plane Flow (Foundry)

1. UI (Next.js) → MCP client (WebSocket) → `mcp_server.py`
2. `mcp_server` loads environment manifest(s) and templates
3. LangGraph graphs are compiled (or cached) for:
   - System agents (platform graphs)
   - Customer agents (worker graphs)
4. MCP tools expose operations like:
   - `foundry.list_agents`, `foundry.get_agent_config`
   - `foundry.deploy_instance`, `foundry.get_instance_status`

The Foundry **never** talks directly to LLMs/Redis/Postgres; it always calls MCP
tools.

### 3.2 Data Plane Flow (Instance Runtime)

1. External client (UI, voice app, API) → **Instance hostname** (see below)
2. Instance MCP server receives request and runs the **Instance LangGraph**:

   ```text
   io → governance → context → supervisor → workers → coherence → observability → io
   ```

3. Each node calls MCP tools for:
   - LLMs, tools, Redis, Postgres, LiveKit, etc.

Each Instance has its **own MCP server + LangGraph graphs + config** and can be
deployed and scaled independently.

---

## 4. Deployment Architecture – One Container per Instance

### 4.1 Goal

- Each `(org, domain, instance)` gets its **own containerized runtime**:
  - Its own MCP+LangGraph process
  - Its own configuration + secrets
  - A dedicated **hostname** for external communication

Example hostnames:

- `dev-retail-1.instances.agentfoundry.internal`
- `prod-retail-1.instances.agentfoundry.com`

### 4.2 How to Do This in AWS

You _can_ scale this pattern with Docker in AWS, but you generally don’t run raw
Docker; you use an orchestrator. The two most straightforward choices:

- **AWS ECS (Elastic Container Service)** – simpler, integrates well with
  ALB/Route53
- **AWS ECS on Fargate** – same as ECS but serverless (no EC2 management)

#### Recommended: ECS + Fargate

1. **Build a single runtime image**:

   - Contains:
     - MCP server
     - LangGraph runtime
     - Code for system/custom agents
   - Configured via environment variables / mounted manifests.

2. **Define an ECS Task Definition** for the runtime image.

3. For each `(org, domain, instance)`:

   - Create an **ECS Service** (or a task) using that task definition.
   - Inject environment-specific configuration:
     - `ORG_ID`, `DOMAIN_ID`, `INSTANCE_ID`
     - Paths or S3 locations for the Instance manifest and agent specs
     - Secrets in AWS Secrets Manager or SSM Parameter Store.

4. Attach the service to:

   - An **Application Load Balancer (ALB)** with path/host-based routing, or
   - **AWS Cloud Map** for internal service discovery.

5. Use **Route53** to create DNS records for each instance hostname, pointing at
   the ALB or Cloud Map name.

This gives you:

- One container (or a small scalable replica set) per Instance
- Clear network boundary per Instance
- Ability to scale instances up/down independently
- Isolation of secrets and environment variables per Instance

### 4.3 Can Docker Scale Like That in AWS?

Yes, with the right orchestrator:

- **ECS/Fargate**:

  - Scales to hundreds/thousands of tasks
  - Each Instance = one ECS Service (or at least one task)
  - Auto-scaling per Instance or per environment

- **EKS (Kubernetes)** (alternative):
  - More complex, more flexible
  - You would model each Instance as a Deployment/Service

For Agent Foundry’s use case, **ECS + Fargate** is typically the sweet spot:

- No cluster management
- First-class integration with ALB, Route53, Secrets Manager, CloudWatch
- Easy to stamp out “one service per Instance” from the Foundry.

---

## 5. Putting It All Together – Build & Deploy Workflow

1. **Design in Foundry** (Control Plane)

   - Create/modify agents in Forge
   - Update YAML specs in `agents/`
   - Update `agents/manifests/manifest.<env>.yaml` for environment bindings
   - Use instance template manifest to define required system agents

2. **Build Instance Bundle**

   - Foundry backend MCP reads:
     - Environment manifest
     - Instance template
   - Generates an **Instance manifest** for a specific `(org, domain, instance)`
   - Packages:
     - Instance manifest
     - All referenced agent YAMLs
     - LangGraph graph definitions
     - Config for MCP tools (without secrets)

3. **Deploy to AWS**

   - CI/CD pipeline builds runtime Docker image (if needed)
   - Creates/updates ECS Service (Fargate) for the Instance
   - Injects:
     - Instance manifest (S3 path or mounted file)
     - Org/domain/instance IDs
     - Secrets (in Secrets Manager / SSM)
   - Configures ALB + Route53 to give the Instance a hostname

4. **Operate**

   - Foundry uses MCP to:
     - Query Instance health & metrics (via observability_agent)
     - Trigger rolling updates / redeploys
   - Instances run traffic independently and can be auto-scaled or shut down
     without impacting the Foundry.

---

## 6. Next Steps

1. **Finalize manifest shapes**:
   - Lock in `AgentManifest` and `AgentInstanceTemplate` schemas.
2. **Implement build pipeline**:
   - Code that turns environment + template manifests into per-instance
     manifests.
3. **Add MCP tools** for:
   - `foundry.deploy_instance`
   - `foundry.list_instances`
   - `foundry.get_instance_status`
4. **Define ECS/Fargate templates**:
   - Task definitions
   - Services
   - ALB + Route53 wiring

Once those pieces are in place, Agent Foundry will cleanly separate **AgentOps
(control plane)** from **runtime Instances (data plane)**, with LangGraph + MCP
at the core and ECS/Fargate providing scalable containerized deployments in AWS.
