#!/bin/bash
# Quick Demo Test - CIBC Card Activation
# This agent is PROVEN to work with interrupt/resume

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-activation"
SESSION_ID="vp-demo-$(date +%s)"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       CIBC Card Activation - VP Demo Test           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}\n"

echo -e "${GREEN}Session ID: ${SESSION_ID}${NC}\n"

# Step 1: Initial greeting
echo -e "${YELLOW}Step 1: Initial greeting${NC}"
curl -s "${BASE_URL}/api/agent/invoke" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"Hello, I need to activate my card\",\"session_id\":\"${SESSION_ID}\",\"route_via_supervisor\":true}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output']); print('Interrupted:', d.get('interrupted', False))"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 2: Confirm activation
echo -e "\n${YELLOW}Step 2: Confirm activation${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"Yes, I want to activate my credit card\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 3: Provide card details
echo -e "\n${YELLOW}Step 3: Provide card details${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"The last 4 digits are 1234 and expiry is 12/25\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${YELLOW}Press Enter to continue...${NC}"
read

# Step 4: Provide security answer
echo -e "\n${YELLOW}Step 4: Provide security answer${NC}"
curl -s "${BASE_URL}/api/agent/resume" \
  -H 'Content-Type: application/json' \
  -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"My mother's maiden name is Smith\",\"session_id\":\"${SESSION_ID}\"}" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print('Agent:', d['output'])"

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║            Card Activation Complete!                 ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}\n"
