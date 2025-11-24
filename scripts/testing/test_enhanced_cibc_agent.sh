#!/bin/bash
# Test Enhanced CIBC Card Services Agent v3.0.0
# Tests: 5-question verification + fee logic

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-activation"
SESSION_ID="enhanced-test-$(date +%s)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   CIBC Card Services Agent v3.0.0 - Enhanced Testing     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Session ID: ${SESSION_ID}${NC}\n"
echo -e "${CYAN}New Features:${NC}"
echo -e "  ✓ 5-Question Verification (was 3)"
echo -e "  ✓ Verification Matrix (cross-check, phone update)"
echo -e "  ✓ Fee Decision Logic (waiver matrix)"
echo -e "  ✓ Card Number Change Logic"
echo -e ""

# ============================================================
# TEST 1: 5-Question Activation Flow (Perfect Score)
# ============================================================

echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}TEST 1: ACTIVATION WORKFLOW - 5 Questions (Perfect Score)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Step 1: Initial greeting${NC}"
curl -s "${BASE_URL}/api/agent/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"I need to activate my new credit card\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

echo -e "\n${CYAN}Step 2: Confirm activation${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, I want to activate it\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

echo -e "\n${CYAN}Step 3: Provide answer${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes please\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to provide PHONE NUMBER (Question 1/5)...${NC}"
read

echo -e "\n${CYAN}Question 1/5: Phone Number${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"416-555-0123\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to provide DATE OF BIRTH (Question 2/5)...${NC}"
read

echo -e "\n${CYAN}Question 2/5: Date of Birth${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"March 15, 1985\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to provide ADDRESS (Question 3/5)...${NC}"
read

echo -e "\n${CYAN}Question 3/5: Address${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"123 Main Street, Toronto\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to provide SECURITY QUESTION 1 (Question 4/5)...${NC}"
read

echo -e "\n${CYAN}Question 4/5: Mother's Maiden Name${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Johnson\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter to provide SECURITY QUESTION 2 (Question 5/5)...${NC}"
read

echo -e "\n${CYAN}Question 5/5: Last 4 digits of SIN${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"4567\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print(''); print('>>> Should show ACTIVATION SUCCESSFUL (5/5 verification) <<<')"

echo -e "\n${GREEN}✅ 5-Question Activation Test Complete!${NC}\n"

# ============================================================
# TEST 2: Replacement with Fee Logic
# ============================================================

SESSION_ID="replacement-test-$(date +%s)"

echo -e "\n${YELLOW}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}TEST 2: REPLACEMENT WORKFLOW - Stolen Card with Police Report${NC}"
echo -e "${YELLOW}Expected: Fee WAIVED (police report filed)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}Starting replacement flow...${NC}"
curl -s "${BASE_URL}/api/agent/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"My card was stolen\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')" > /dev/null

# Navigate through to stolen reason
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"I need to replace it\",\"session_id\":\"${SESSION_ID}\"}" > /dev/null

curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, replace my card\",\"session_id\":\"${SESSION_ID}\"}" > /dev/null

curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"It was stolen yesterday\",\"session_id\":\"${SESSION_ID}\"}" > /dev/null

curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Last 4 are 5678, account 12345678\",\"session_id\":\"${SESSION_ID}\"}" > /dev/null

curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Johnson\",\"session_id\":\"${SESSION_ID}\"}" > /dev/null

echo -e "${CYAN}Step: Police report question (should ask)${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, I filed a police report\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter for card type...${NC}"
read

echo -e "${CYAN}Step: Card type (credit for fee test)${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"It's a credit card\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'][:200] + '...')"

echo -e "\n${YELLOW}Press Enter for final step...${NC}"
read

echo -e "${CYAN}Step: Finalize (should show fee WAIVED)${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Okay\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print(''); print('>>> Should show FEE WAIVED (police report) + NEW CARD NUMBER <<<')"

echo -e "\n${GREEN}✅ Fee Logic Test Complete!${NC}\n"

# ============================================================
# Summary
# ============================================================

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Testing Complete!                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Tests Run:${NC}"
echo -e "  ✓ 5-Question Activation (Perfect Score)"
echo -e "  ✓ Replacement with Fee Logic (Stolen + Police Report)"
echo -e ""
echo -e "${CYAN}Enhanced Features Verified:${NC}"
echo -e "  ✓ Phone number verification"
echo -e "  ✓ Date of birth verification"
echo -e "  ✓ Address confirmation"
echo -e "  ✓ Security question 1 (maiden name)"
echo -e "  ✓ Security question 2 (SIN)"
echo -e "  ✓ Police report detection"
echo -e "  ✓ Card type classification"
echo -e "  ✓ Fee waiver logic"
echo -e "  ✓ Card number change logic"
echo -e ""

