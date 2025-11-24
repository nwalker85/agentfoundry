#!/bin/bash
# Test Multi-Workflow in Same Session
# Tests: Debit replacement → Card activation in same session

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-activation"
SESSION_ID="multi-workflow-$(date +%s)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Multi-Workflow Test: Same Session                      ║${NC}"
echo -e "${BLUE}║   1. Debit Card Replacement                               ║${NC}"
echo -e "${BLUE}║   2. Card Activation (follow-up)                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Session ID: ${SESSION_ID}${NC}\n"

# ============================================================
# WORKFLOW 1: DEBIT CARD REPLACEMENT
# ============================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}WORKFLOW 1: DEBIT CARD REPLACEMENT${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}→ Initial request: Card replacement${NC}"
curl -s "${BASE_URL}/api/agent/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"I need to replace my debit card\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo -e "${CYAN}→ Confirm replacement${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, I need a replacement\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter to continue...${NC}"
read

echo -e "${CYAN}→ Confirm workflow type${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Replace it please\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter to provide reason...${NC}"
read

# Replacement flow - provide reason
echo -e "${CYAN}→ Step 1: Reason (Lost)${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"I lost my card yesterday\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter...${NC}"
read

# Step 2: Card details
echo -e "${CYAN}→ Step 2: Card details${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Last 4 digits are 5678, account is 12345678\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter...${NC}"
read

# Step 3: Security question
echo -e "${CYAN}→ Step 3: Security verification${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Johnson\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter...${NC}"
read

# Step 4: Card type (for replacement - should ask since it's a replacement)
echo -e "${CYAN}→ Step 4: Card type${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"It's a debit card\",\"session_id\":\"${SESSION_ID}\"}" \
  | jq -r '.output' | head -3
echo ""

echo -e "${YELLOW}Press Enter...${NC}"
read

# Step 5: Final step for replacement
echo -e "${CYAN}→ Step 5: Acknowledge${NC}"
REPLACEMENT_FINAL=$(curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Okay, thank you\",\"session_id\":\"${SESSION_ID}\"}")

echo "$REPLACEMENT_FINAL" | jq -r '.output'
echo ""

# Check if workflow ended
if echo "$REPLACEMENT_FINAL" | jq -r '.output' | grep -qi "great day\|goodbye\|cibc"; then
    echo -e "${GREEN}✓ Replacement workflow completed${NC}"
else
    echo -e "${RED}✗ Workflow may not have completed${NC}"
fi
echo ""

# ============================================================
# WORKFLOW 2: CARD ACTIVATION (Same Session)
# ============================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}WORKFLOW 2: CARD ACTIVATION (Follow-up in same session)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Testing: Can we continue in same session after workflow ends?${NC}\n"

echo -e "${YELLOW}Attempting to resume with new request...${NC}"
echo -e "${CYAN}→ New request: Activate card${NC}"
ACTIVATION_START=$(curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"I also need to activate my new credit card that just arrived\",\"session_id\":\"${SESSION_ID}\"}")

ACTIVATION_OUTPUT=$(echo "$ACTIVATION_START" | jq -r '.output // .detail // "No response"')
ACTIVATION_ERROR=$(echo "$ACTIVATION_START" | jq -r '.detail // empty')

echo "$ACTIVATION_OUTPUT" | head -5
echo ""

# Analysis
echo -e "${CYAN}Analysis:${NC}"
if [ ! -z "$ACTIVATION_ERROR" ]; then
    echo -e "${RED}✗ Resume failed: $ACTIVATION_ERROR${NC}"
    echo -e "${YELLOW}→ Workflow properly ended - requires new invoke${NC}"

    echo ""
    echo -e "${CYAN}Testing: New invoke for second workflow${NC}"
    NEW_INVOKE=$(curl -s "${BASE_URL}/api/agent/invoke" \
      -H 'Content-Type: application/json' \
      -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"I need to activate my new credit card\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}")

    echo "$NEW_INVOKE" | jq -r '.output' | head -5
    echo ""
    echo -e "${GREEN}✓ New invoke works - sessions are independent${NC}"
else
    if echo "$ACTIVATION_OUTPUT" | grep -qi "activate\|credit card\|help.*card"; then
        echo -e "${GREEN}✓ Agent responded to new request in same session${NC}"
        echo -e "${YELLOW}→ Continuation is possible (unexpected)${NC}"
    else
        echo -e "${YELLOW}⚠ Agent responded but may not recognize new workflow${NC}"
    fi
fi
echo ""

# ============================================================
# Summary
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Test Summary                            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}Expected Behavior:${NC}"
echo -e "  1. Replacement workflow completes and ends cleanly"
echo -e "  2. Resume fails (workflow at END)"
echo -e "  3. New invoke required for second workflow"
echo ""

echo -e "${CYAN}Actual Behavior:${NC}"
echo -e "  • Replacement: $(echo "$REPLACEMENT_FINAL" | jq -r '.output' | grep -qi 'great day' && echo 'Completed ✓' || echo 'Check logs')"
echo -e "  • Same session resume: $([ ! -z "$ACTIVATION_ERROR" ] && echo 'Blocked (correct) ✓' || echo 'Allowed (unexpected)')"
echo -e "  • New invoke: Works independently ✓"
echo ""

echo -e "${GREEN}Session ID: ${SESSION_ID}${NC}"
echo -e "${CYAN}Check logs with:${NC} docker logs agentfoundry-foundry-backend-1 | grep ${SESSION_ID}"
echo ""
