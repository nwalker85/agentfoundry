## Agent Foundry – AWS Deployment (ECS / Fargate)

**Purpose:** This is the **current, supported** deployment path for Agent Foundry to AWS using **ECR + ECS Fargate + ALB + Route53**, driven by Terraform in `infra/` and Docker build scripts.

For the older single‑EC2 + docker‑compose approach, see `deploy/DEPLOYMENT_EC2_LEGACY.md` and the legacy root `DEPLOYMENT.md`.

---

## 1. Architecture Overview

### 1.1 Core AWS Components

- **VPC & Networking**
  - VPC, public subnets, security groups declared in `infra/vpc.tf` and `infra/security.tf`
- **ECS / Fargate**
  - Cluster: `agentfoundry-cluster`
  - Services:
    - `agentfoundry-ui-svc` → UI container (port 3000)
    - `agentfoundry-api-svc` → backend container (port 8000)
- **ECR**
  - Repositories (from `infra/ecr.tf`):
    - `agentfoundry-ui`
    - `agentfoundry-backend`
    - `agentfoundry-compiler`
    - `agentfoundry-forge`
- **ALB + Routing**
  - ALB name: `${var.project_name}-alb` (typically `agentfoundry-alb`)
  - HTTPS listener (443) with ACM certificate (`var.foundry_cert_arn`)
  - Target groups:
    - `agentfoundry-ui-tg` (port 3000, `/` health check)
    - `agentfoundry-api-tg` (port 8000, `/health` health check)
  - Routing:
    - `/api/*` → API target group
    - `/` (and everything else) → UI target group
- **DNS / SSL**
  - Route53 hosted zone: `ravenhelm.ai`
  - `foundry.ravenhelm.ai` A‑record alias → ALB
  - ACM certificate for `foundry.ravenhelm.ai` in `us-east-1`

### 1.2 Application Topology (Deployed)

From a user perspective:

- `https://foundry.ravenhelm.ai/` → UI (Next.js)
- `https://foundry.ravenhelm.ai/api/*` → backend FastAPI service

The UI connects to the backend via:

- `NEXT_PUBLIC_API_URL=https://foundry.ravenhelm.ai/api`

This is wired in `infra/ecs.tf` via task definition environment variables.

---

## 2. One-Time AWS Setup

### 2.1 Prerequisites

- AWS account (dev) and **AWS CLI** configured (`aws sts get-caller-identity` must work)
- **Terraform** ≥ 1.6
- **Docker** and **Docker Buildx**
- Permissions to create:
  - VPC, ALB, ECS, ECR, Route53, IAM roles, ACM certificates

### 2.2 Configure Terraform in `infra/`

From the repo root:

```bash
cd infra

cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and set (at minimum):

- `project_name       = "agentfoundry"`
- `foundry_domain     = "foundry.ravenhelm.ai"`
- `foundry_cert_arn   = "arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/..."`  # ACM cert for foundry.ravenhelm.ai
- Any other variables required by `variables.tf`

Then apply:

```bash
terraform init
terraform plan
terraform apply
```

Terraform will:

- Create VPC + networking
- Create ALB and target groups
- Create ECS cluster + task definitions for UI and API
- Create ECR repos
- Create Route53 zone/record for `foundry.ravenhelm.ai`

Once applied, Terraform will output the ALB DNS name and other useful values.

---

## 3. Build & Push Images (Dev)

### 3.1 Configure Local Build Environment (One-Time Per Machine)

From the repo root:

```bash
./configure_build_env.sh
```

This will:

- Create (or reuse) a Docker buildx builder `af-builder`
- Bootstrap buildx
- Log into your AWS ECR registry for the configured account/region

You can verify:

```bash
docker buildx ls
aws ecr describe-repositories
```

### 3.2 Build & Deploy to ECS (Dev)

For the dev environment, use:

```bash
./deploy_dev.sh
```

What `deploy_dev.sh` does:

1. Uses the `af-builder` buildx builder
2. Logs into ECR
3. Builds **linux/amd64** images for:
   - UI:       `${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/agentfoundry-ui:latest`
   - Backend:  `${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/agentfoundry-backend:latest`
   - Compiler: `${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/agentfoundry-compiler:latest`
   - Forge:    `${ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/agentfoundry-forge:latest`
4. Pushes all images to ECR
5. Triggers new deployments for:
   - `agentfoundry-ui-svc`
   - `agentfoundry-api-svc`

You can control:

- `AWS_ACCOUNT_ID`, `AWS_REGION`, `ECS_CLUSTER`
- Image tags: `UI_TAG`, `BACKEND_TAG`, `COMPILER_TAG`, `FORGE_TAG`

by editing `deploy_dev.sh` as needed (or overriding via env vars if you extend the script).

---

## 4. DNS, SSL, and Endpoints

### 4.1 Domains & Certificates

- Hosted zone: `ravenhelm.ai` (created by Terraform)
- Application domain: `foundry.ravenhelm.ai`
  - A‑record alias → `agentfoundry-alb`
  - ACM certificate ARN referenced in `infra/alb.tf` via `var.foundry_cert_arn`

### 4.2 Runtime URLs

- UI: `https://foundry.ravenhelm.ai/`
- API:
  - `https://foundry.ravenhelm.ai/api/health`
  - `https://foundry.ravenhelm.ai/api/...` (backend routes)

Make sure your **UI image** is built with:

- `NEXT_PUBLIC_API_URL=https://foundry.ravenhelm.ai/api`

This is wired in `infra/ecs.tf` via task definition environment variables.

---

## 5. Monitoring & Diagnostics (AWS)

### 5.1 ECS / Service Health

Use the helper script:

```bash
./scripts/monitor_aws_health.sh
```

This script (by default):

- Checks ECS cluster `agentfoundry-cluster`
- Shows desired vs running tasks for:
  - `agentfoundry-ui-svc`
  - `agentfoundry-api-svc`
- Verifies that ALB DNS is reachable
- Optionally curls `/api/health` through the ALB if configured

You can override key environment variables:

- `AWS_REGION` (default: `us-east-1`)
- `ECS_CLUSTER` (default: `agentfoundry-cluster`)
- `UI_SERVICE`, `API_SERVICE`

### 5.2 ALB Target Health

Use:

```bash
./scripts/check_alb_targets.sh
```

This script:

- Resolves target groups by name:
  - `${PROJECT_NAME}-ui-tg` (default `agentfoundry-ui-tg`)
  - `${PROJECT_NAME}-api-tg` (default `agentfoundry-api-tg`)
- Shows target health for UI and API target groups

You can override:

- `PROJECT_NAME` (default: `agentfoundry`)
- `AWS_REGION`

### 5.3 Manual Checks

From your laptop:

```bash
curl -I https://foundry.ravenhelm.ai/
curl -I https://foundry.ravenhelm.ai/api/health
```

From AWS console:

- **ECS → Services**
  - Confirm desired vs running count = 1/1 for both services
- **ALB → Target Groups**
  - Confirm healthy targets for UI/API

---

## 6. Updating Secrets & Config

Agent Foundry relies on environment variables for:

- API keys (OpenAI, Notion, GitHub, LiveKit, etc.)
- Service configuration
- Environment/tenant names

In the ECS model you normally store these in:

- ECS task definitions (environment variables)
- AWS Systems Manager Parameter Store / Secrets Manager (referenced from task definitions)

The `scripts/env_to_ssm.py` helper can still be used to push `.env` values to SSM paths (e.g. `/foundry/dev/...`), but the **canonical configuration** for ECS now lives in Terraform + task definitions rather than a single `.env` file on an EC2 host.

If you are still using the original EC2 deployment flow, see `deploy/DEPLOYMENT_EC2_LEGACY.md` and `deploy/deploy.sh`.

---

## 7. Teardown

To remove the ECS infrastructure:

```bash
cd infra
terraform destroy
```

Optional clean‑up:

- Delete ECR images / repositories if you no longer need them
- Delete SSM parameters under `/foundry/dev` if you used that path

---

## 8. Legacy vs Current Paths

- **Current (recommended):**
  - Terraform in `infra/` (VPC, ALB, ECS, ECR, Route53)
  - Docker buildx via `configure_build_env.sh`
  - Image build + ECS deploy via `deploy_dev.sh`
  - Health monitoring via `scripts/monitor_aws_health.sh` and `scripts/check_alb_targets.sh`
- **Legacy (kept for reference):**
  - Single EC2 instance + docker‑compose
  - Terraform in `terraform/`
  - Rsync code + docker‑compose via `deploy/deploy.sh`
  - Documented in `deploy/DEPLOYMENT_EC2_LEGACY.md` and `deploy/AWS_DEPLOYMENT_GUIDE.md`

Unless you have a specific reason to target the single‑EC2 pattern, **use the ECS/ECR path described in this document.**


