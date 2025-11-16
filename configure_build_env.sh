#!/usr/bin/env bash
set -euo pipefail

# ==============================
# CONFIG - EDIT IF NEEDED
# ==============================
AWS_ACCOUNT_ID="122441748701"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
BUILDER_NAME="af-builder"

echo "=== Configure build environment ==="
echo "AWS account: ${AWS_ACCOUNT_ID}"
echo "Region     : ${AWS_REGION}"
echo "ECR base   : ${ECR_BASE}"
echo

# ==============================
# Ensure buildx builder exists
# ==============================
if ! docker buildx inspect "${BUILDER_NAME}" > /dev/null 2>&1; then
  echo "Creating docker buildx builder '${BUILDER_NAME}'..."
  docker buildx create --name "${BUILDER_NAME}" --use
else
  echo "Using existing docker buildx builder '${BUILDER_NAME}'..."
  docker buildx use "${BUILDER_NAME}"
fi

echo "Bootstrapping buildx..."
docker buildx inspect "${BUILDER_NAME}" --bootstrap > /dev/null
echo "buildx builder '${BUILDER_NAME}' is ready."
echo

# ==============================
# ECR login
# ==============================
echo "Logging into ECR at ${ECR_BASE}..."
aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${ECR_BASE}"

echo
echo "✅ Build environment configured successfully."