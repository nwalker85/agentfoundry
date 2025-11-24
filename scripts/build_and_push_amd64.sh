#!/usr/bin/env bash
set -euo pipefail

# ==========================================
# CONFIG
# ==========================================
AWS_ACCOUNT_ID="122441748701"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Tags (change if you want versioned tags instead of latest)
UI_TAG="latest"
BACKEND_TAG="latest"
COMPILER_TAG="latest"
FORGE_TAG="latest"

# ==========================================
# Buildx setup (one-time, safe to re-run)
# ==========================================
if ! docker buildx inspect af-builder > /dev/null 2>&1; then
  echo "Creating buildx builder 'af-builder'..."
  docker buildx create --name af-builder --use
fi
docker buildx inspect af-builder --bootstrap > /dev/null

# ==========================================
# ECR login
# ==========================================
echo "Logging into ECR ${ECR_BASE}..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_BASE}"

# ==========================================
# UI
# ==========================================
build_push_ui() {
  local image="${ECR_BASE}/agentfoundry-ui:${UI_TAG}"
  echo "Building UI (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f Dockerfile.frontend \
    . \
    --push
}

# ==========================================
# Backend (API + voice worker)
# ==========================================
build_push_backend() {
  local image="${ECR_BASE}/agentfoundry-backend:${BACKEND_TAG}"
  echo "Building Backend (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f backend/Dockerfile \
    . \
    --push
}

# ==========================================
# Compiler
# ==========================================
build_push_compiler() {
  local image="${ECR_BASE}/agentfoundry-compiler:${COMPILER_TAG}"
  echo "Building Compiler (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f compiler/Dockerfile \
    . \
    --push
}

# ==========================================
# Forge Service
# ==========================================
build_push_forge() {
  local image="${ECR_BASE}/agentfoundry-forge:${FORGE_TAG}"
  echo "Building Forge Service (linux/amd64) -> ${image}"

  docker buildx build \
    --platform linux/amd64 \
    -t "${image}" \
    -f forge_service/Dockerfile \
    . \
    --push
}

# ==========================================
# Main
# ==========================================
case "${1:-all}" in
  ui)
    build_push_ui
    ;;
  backend)
    build_push_backend
    ;;
  compiler)
    build_push_compiler
    ;;
  forge)
    build_push_forge
    ;;
  all)
    build_push_ui
    build_push_backend
    build_push_compiler
    build_push_forge
    ;;
  *)
    echo "Usage: $0 [ui|backend|compiler|forge|all]" >&2
    exit 1
    ;;
esac

echo "Done."