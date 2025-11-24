#!/bin/bash
# CIBC Card Services - Simple Workflow Tests

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-services"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_workflow() {
    local name="$1"
    local session="$2"
    local thread="$3"
    local initial_msg="$4"
    local response_msg="$5"

    echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Testing: $name${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════${NC}\n"

    echo -e "${YELLOW}→ Initial request:${NC} $initial_msg"
    curl -s "${BASE_URL}/api/agent/invoke" \
        -H 'Content-Type: application/json' \
        -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"${initial_msg}\",\"session_id\":\"${session}\",\"thread_id\":\"${thread}\",\"route_via_supervisor\":true}" \
        | python3 -c "import sys, json; data=json.load(sys.stdin); print('Assistant:', data.get('output', '')[:200], '...')"

    echo ""
    sleep 2

    echo -e "${YELLOW}→ User response:${NC} $response_msg"
    curl -s "${BASE_URL}/api/agent/resume" \
        -H 'Content-Type: application/json' \
        -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"${response_msg}\",\"session_id\":\"${session}\",\"thread_id\":\"${thread}\"}" \
        | python3 -c "import sys, json; data=json.load(sys.stdin); print('Assistant:', data.get('output', '')[:300], '...')"

    echo -e "\n${GREEN}✓ Workflow test complete${NC}\n"
}

# Test 1: Card Activation
test_workflow \
    "Card Activation" \
    "test-activation-001" \
    "test-activation-thread-001" \
    "Hi, I received my new card and need to activate it" \
    "Yes, I want to activate my new credit card"

# Test 2: Debit Replacement - Lost
test_workflow \
    "Debit Replacement - Lost Card" \
    "test-debit-lost-001" \
    "test-debit-lost-thread-001" \
    "I need help, I lost my debit card" \
    "I lost my debit card yesterday, I need a replacement"

# Test 3: Credit Replacement - Stolen
test_workflow \
    "Credit Replacement - Stolen Card" \
    "test-credit-stolen-001" \
    "test-credit-stolen-thread-001" \
    "My credit card was stolen" \
    "My wallet was stolen with my credit card. I filed a police report."

# Test 4: Card Status - Fraud Block
test_workflow \
    "Card Status & Fraud" \
    "test-status-001" \
    "test-status-thread-001" \
    "My card is blocked due to suspected fraud" \
    "There's a fraud alert but that was my legitimate transaction"

# Test 5: Card Delivery Information
test_workflow \
    "Card Delivery Inquiry" \
    "test-delivery-001" \
    "test-delivery-thread-001" \
    "When will my replacement card arrive?" \
    "I'm in Barbados, when should I expect delivery?"

echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           All Workflow Tests Complete                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
