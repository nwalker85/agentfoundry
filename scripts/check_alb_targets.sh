#!/usr/bin/env bash
# Agent Foundry - ALB Target Group Health Check
#
# Shows target health for the UI and API target groups created by Terraform.
#
# Environment variables (override as needed):
#   AWS_REGION    (default: us-east-1)
#   PROJECT_NAME  (default: agentfoundry)
#   UI_TG_NAME    (default: ${PROJECT_NAME}-ui-tg)
#   API_TG_NAME   (default: ${PROJECT_NAME}-api-tg)

set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-agentfoundry}"
UI_TG_NAME="${UI_TG_NAME:-${PROJECT_NAME}-ui-tg}"
API_TG_NAME="${API_TG_NAME:-${PROJECT_NAME}-api-tg}"

echo "🎯 Agent Foundry - ALB Target Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Region      : ${AWS_REGION}"
echo "Project     : ${PROJECT_NAME}"
echo "UI TG Name  : ${UI_TG_NAME}"
echo "API TG Name : ${API_TG_NAME}"
echo ""

if ! command -v aws >/dev/null 2>&1; then
  echo "❌ aws CLI not found. Install and configure AWS credentials first."
  exit 1
fi

get_tg_arn() {
  local name="$1"
  aws elbv2 describe-target-groups \
    --region "${AWS_REGION}" \
    --names "${name}" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || true
}

describe_tg_health() {
  local name="$1"
  local label="$2"

  local arn
  arn=$(get_tg_arn "${name}")

  if [ -z "${arn}" ] || [ "${arn}" = "None" ]; then
    echo "   ❌ ${label}: target group '${name}' not found"
    return
  fi

  echo "   ${label} (${name})"
  aws elbv2 describe-target-health \
    --region "${AWS_REGION}" \
    --target-group-arn "${arn}" \
    --query 'TargetHealthDescriptions[].{Id:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' \
    --output table || echo "   (no targets registered)"
  echo ""
}

echo "1️⃣  UI Target Group"
echo "--------------------"
describe_tg_health "${UI_TG_NAME}" "UI"

echo "2️⃣  API Target Group"
echo "---------------------"
describe_tg_health "${API_TG_NAME}" "API"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✔️  ALB target health check complete."
echo ""


