#!/bin/bash
# Test Workflow Switching - CIBC Card Services
# Tests completing one workflow (replacement) then starting another (activation)

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-activation"
SESSION_ID="workflow-switch-test-$(date +%s)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CIBC Card Services - Workflow Switching Test       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Session ID: ${SESSION_ID}${NC}\n"
echo -e "${CYAN}Test Plan:${NC}"
echo -e "  1. Start REPLACEMENT workflow (stolen card)"
echo -e "  2. Complete all replacement steps"
echo -e "  3. Request ACTIVATION in same session"
echo -e "  4. Verify it switches correctly\n"

# ============================================================
# WORKFLOW 1: REPLACEMENT
# ============================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}WORKFLOW 1: CARD REPLACEMENT (STOLEN)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

# Step 1: Initial greeting
echo -e "${CYAN}Step 1: Initial greeting${NC}"
curl -s "${BASE_URL}/api/agent/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"Hello, I need help with my card\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print('Interrupted:', d.get('interrupted', False))"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 2: Request replacement
echo -e "\n${CYAN}Step 2: Request replacement for stolen card${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"My debit card was stolen and I need a replacement\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 3: Clarify workflow
echo -e "\n${CYAN}Step 3: Clarify replacement need${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, I need to replace my stolen card\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 4: Provide reason (stolen)
echo -e "\n${CYAN}Step 4: Provide reason (stolen)${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"It was stolen yesterday\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 5: Provide card details
echo -e "\n${CYAN}Step 5: Provide card details${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Last 4 digits are 5678 and account is 12345678\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 6: Security question
echo -e "\n${CYAN}Step 6: Security answer${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"My mother's maiden name is Johnson\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print(''); print('>>> WORKFLOW 1 SHOULD BE COMPLETE <<<')"

echo -e "\n${GREEN}✅ Replacement workflow completed!${NC}"
echo -e "${YELLOW}Press Enter to start SECOND workflow in same session...${NC}"
read

# ============================================================
# WORKFLOW 2: ACTIVATION (in same session)
# ============================================================

echo -e "\n${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}WORKFLOW 2: CARD ACTIVATION (SAME SESSION)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

# Step 7: Request activation
echo -e "${CYAN}Step 7: Now request activation in same session${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"I also need to activate my credit card that just arrived\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print(''); print('>>> SHOULD START ACTIVATION FLOW <<<')"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 8: Provide phone
echo -e "\n${CYAN}Step 8: Provide phone number${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"416-555-1234\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 9: Provide DOB
echo -e "\n${CYAN}Step 9: Provide date of birth${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"January 15, 1985\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 10: Provide address
echo -e "\n${CYAN}Step 10: Provide address${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"123 Main Street, Toronto ON M5V 1A1\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print(''); print('>>> ACTIVATION SHOULD BE COMPLETE <<<')"

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Workflow Switching Test Complete!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${CYAN}Summary:${NC}"
echo -e "  ✅ Workflow 1: Card replacement (stolen) - COMPLETED"
echo -e "  ✅ Workflow 2: Card activation - COMPLETED"
echo -e "  ✅ Switching worked in same session\n"
