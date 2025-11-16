#!/usr/bin/env bash
set -euo pipefail

# ==============================
# CONFIG - EDIT IF NEEDED
# ==============================
AWS_ACCOUNT_ID="122441748701"
AWS_REGION="us-east-1"
ECS_CLUSTER="agentfoundry-cluster"

ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Image tags (use semantic versions later if you like)
UI_TAG="latest"
BACKEND_TAG="latest"
COMPILER_TAG="latest"
FORGE_TAG="latest"

# ECS Service names (from Terraform)
UI_SERVICE="agentfoundry-ui-svc"
API_SERVICE="agentfoundry-api-svc"
# Later: COMPILER_SERVICE, FORGE_SERVICE, etc.

echo "=== Deploying Agent Foundry to AWS Dev ==="
echo "Account : ${AWS_ACCOUNT_ID}"
echo "Region  : ${AWS_REGION}"
echo "Cluster : ${ECS_CLUSTER}"
echo "ECR base: ${ECR_BASE}"
echo

# ==============================
# Ensure buildx builder is selected
# ==============================
BUILDER_NAME="af-builder"

if ! docker buildx inspect "${BUILDER_NAME}" > /dev/null 2>&1; then
  echo "ERROR: buildx builder '${BUILDER_NAME}' not found."
  echo "Run ./configure_build_env.sh first."
  exit 1
fi

docker buildx use "${BUILDER_NAME}"

# ==============================
# ECR login (again, safe to repeat)
# ==============================
echo "Logging into ECR at ${ECR_BASE}..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_BASE}"
echo

# ==============================
# Build & push functions
# ==============================
build_push_ui() {
  local image="${ECR_BASE}/agentfoundry-ui:${UI_TAG}"
  echo "Building UI (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f Dockerfile.frontend \
    . \
    --push
  echo
}

build_push_backend() {
  local image="${ECR_BASE}/agentfoundry-backend:${BACKEND_TAG}"
  echo "Building Backend (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f backend/Dockerfile \
    . \
    --push
  echo
}

build_push_compiler() {
  local image="${ECR_BASE}/agentfoundry-compiler:${COMPILER_TAG}"
  echo "Building Compiler (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f compiler/Dockerfile \
    . \
    --push
  echo
}

build_push_forge() {
  local image="${ECR_BASE}/agentfoundry-forge:${FORGE_TAG}"
  echo "Building Forge Service (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f forge_service/Dockerfile \
    . \
    --push
  echo
}

# ==============================
# Build & push all images
# ==============================
echo "=== Building & pushing images (linux/amd64) ==="
build_push_ui
build_push_backend
build_push_compiler
build_push_forge

# ==============================
# Force ECS to roll to new images
# ==============================
echo "=== Forcing new ECS deployments ==="

echo "Updating UI service: ${UI_SERVICE}"
aws ecs update-service \
  --cluster "${ECS_CLUSTER}" \
  --service "${UI_SERVICE}" \
  --force-new-deployment \
  --region "${AWS_REGION}"
echo

echo "Updating API service: ${API_SERVICE}"
aws ecs update-service \
  --cluster "${ECS_CLUSTER}" \
  --service "${API_SERVICE}" \
  --force-new-deployment \
  --region "${AWS_REGION}"
echo

# Uncomment when you have ECS services for these:
# echo "Updating Compiler service: ${COMPILER_SERVICE}"
# aws ecs update-service \
#   --cluster "${ECS_CLUSTER}" \
#   --service "${COMPILER_SERVICE}" \
#   --force-new-deployment \
#   --region "${AWS_REGION}"
# echo
#
# echo "Updating Forge service: ${FORGE_SERVICE}"
# aws ecs update-service \
#   --cluster "${ECS_CLUSTER}" \
#   --service "${FORGE_SERVICE}" \
#   --force-new-deployment \
#   --region "${AWS_REGION}"
# echo

echo "✅ Deploy triggered. Watch ECS console / target group health for status."