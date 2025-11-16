#!/usr/bin/env bash
# Agent Foundry - AWS ECS / ALB Health Monitor (Dev)
#
# Summarizes ECS service status and basic ALB / API health for the dev environment.
#
# Environment variables (override as needed):
#   AWS_REGION        (default: us-east-1)
#   ECS_CLUSTER       (default: agentfoundry-cluster)
#   UI_SERVICE        (default: agentfoundry-ui-svc)
#   API_SERVICE       (default: agentfoundry-api-svc)
#   PROJECT_NAME      (default: agentfoundry)

set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
ECS_CLUSTER="${ECS_CLUSTER:-agentfoundry-cluster}"
UI_SERVICE="${UI_SERVICE:-agentfoundry-ui-svc}"
API_SERVICE="${API_SERVICE:-agentfoundry-api-svc}"
PROJECT_NAME="${PROJECT_NAME:-agentfoundry}"

echo "🌐 Agent Foundry - AWS Dev Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Region : ${AWS_REGION}"
echo "Cluster: ${ECS_CLUSTER}"
echo ""

if ! command -v aws >/dev/null 2>&1; then
  echo "❌ aws CLI not found. Install and configure AWS credentials first."
  exit 1
fi

echo "1️⃣  ECS Service Status"
echo "----------------------"

describe_service() {
  local service="$1"
  local label="$2"

  if ! aws ecs describe-services \
    --region "${AWS_REGION}" \
    --cluster "${ECS_CLUSTER}" \
    --services "${service}" >/tmp/af_${service}.json 2>/dev/null; then
    echo "   ❌ ${label}: service not found (${service})"
    return
  fi

  local desired
  local running
  desired=$(jq -r '.services[0].desiredCount' </tmp/af_${service}.json)
  running=$(jq -r '.services[0].runningCount' </tmp/af_${service}.json)

  if [ "${desired}" = "${running}" ]; then
    echo "   ✅ ${label}: desired=${desired}, running=${running}"
  else
    echo "   ❌ ${label}: desired=${desired}, running=${running}"
  fi
}

describe_service "${UI_SERVICE}"  "UI Service"
describe_service "${API_SERVICE}" "API Service"
echo ""

echo "2️⃣  ALB & DNS"
echo "-------------"

ALB_NAME="${PROJECT_NAME}-alb"

ALB_INFO=$(aws elbv2 describe-load-balancers \
  --region "${AWS_REGION}" \
  --names "${ALB_NAME}" 2>/dev/null || true)

if [ -z "${ALB_INFO}" ]; then
  echo "   ❌ ALB '${ALB_NAME}' not found"
else
  ALB_DNS=$(echo "${ALB_INFO}" | jq -r '.LoadBalancers[0].DNSName')
  echo "   ✅ ALB '${ALB_NAME}' exists"
  echo "      DNS: ${ALB_DNS}"

  echo ""
  echo "3️⃣  API /health via ALB"
  echo "------------------------"

  if command -v curl >/dev/null 2>&1; then
    if curl -sf -m 5 "https://${ALB_DNS}/api/health" >/dev/null 2>&1; then
      echo "   ✅ https://${ALB_DNS}/api/health OK"
    else
      echo "   ❌ https://${ALB_DNS}/api/health failed"
    fi
  else
    echo "   (curl not installed; skipping API check)"
  fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✔️  AWS health check complete."
echo ""
echo "Tips:"
echo "  • See target details: ./scripts/check_alb_targets.sh"
echo "  • Inspect ECS events: aws ecs describe-services --cluster ${ECS_CLUSTER} --services ${API_SERVICE}"
echo ""


