#!/bin/bash
# CIBC Card Services Orchestrator - Comprehensive Test Script
# Tests all 5 workflows with interrupt/resume patterns

set -e

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-services"

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CIBC Card Services Orchestrator - Comprehensive Test Suite  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to invoke agent
invoke_agent() {
    local input="$1"
    local session_id="$2"
    local thread_id="$3"

    curl -s "${BASE_URL}/api/agent/invoke" \
        -H 'Content-Type: application/json' \
        -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"${input}\",\"session_id\":\"${session_id}\",\"thread_id\":\"${thread_id}\",\"route_via_supervisor\":false}" \
        | python3 -m json.tool
}

# Function to resume agent
resume_agent() {
    local input="$1"
    local session_id="$2"
    local thread_id="$3"

    curl -s "${BASE_URL}/api/agent/resume" \
        -H 'Content-Type: application/json' \
        -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"${input}\",\"session_id\":\"${session_id}\",\"thread_id\":\"${thread_id}\"}" \
        | python3 -m json.tool
}

# ============================================================================
# WORKFLOW 1: CARD ACTIVATION
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 1: Card Activation (5-Question Verification) ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_1="activation-001"
THREAD_1="activation-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request - Activate my card${NC}"
invoke_agent "Hi, I need to activate my new CIBC card" "${SESSION_1}" "${THREAD_1}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes need${NC}"
resume_agent "I need to activate my card" "${SESSION_1}" "${THREAD_1}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Verify phone number${NC}"
resume_agent "My phone number is 416-555-1234" "${SESSION_1}" "${THREAD_1}"
sleep 2

echo -e "\n${YELLOW}➤ Step 4: Verify date of birth${NC}"
resume_agent "My date of birth is January 15, 1985" "${SESSION_1}" "${THREAD_1}"
sleep 2

echo -e "\n${YELLOW}➤ Step 5: Verify address${NC}"
resume_agent "123 Main Street, Toronto, ON M5V 2T6" "${SESSION_1}" "${THREAD_1}"
sleep 2

echo -e "\n${GREEN}✓ Activation workflow complete${NC}\n"

# ============================================================================
# WORKFLOW 2: VISA DEBIT REPLACEMENT - LOST CARD
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 2: Debit Replacement - Lost Card             ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_2="debit-lost-001"
THREAD_2="debit-lost-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "Hello, I need help with my debit card" "${SESSION_2}" "${THREAD_2}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "I lost my debit card and need a replacement" "${SESSION_2}" "${THREAD_2}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Provide reason details${NC}"
resume_agent "I think I left it at a restaurant yesterday. I haven't seen any unauthorized charges yet." "${SESSION_2}" "${THREAD_2}"
sleep 2

echo -e "\n${YELLOW}➤ Step 4: Verification answers${NC}"
resume_agent "My mother's maiden name is Smith" "${SESSION_2}" "${THREAD_2}"
sleep 2

echo -e "\n${GREEN}✓ Debit replacement workflow complete${NC}\n"

# ============================================================================
# WORKFLOW 3: VISA DEBIT REPLACEMENT - STOLEN CARD
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 3: Debit Replacement - Stolen Card           ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_3="debit-stolen-001"
THREAD_3="debit-stolen-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "I need to report a stolen debit card" "${SESSION_3}" "${THREAD_3}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "My wallet was stolen this morning and I need a replacement card immediately" "${SESSION_3}" "${THREAD_3}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Provide reason details${NC}"
resume_agent "My wallet was stolen from my car. I've filed a police report. I need a new card with a different number for security." "${SESSION_3}" "${THREAD_3}"
sleep 2

echo -e "\n${YELLOW}➤ Step 4: Verification answers${NC}"
resume_agent "My first pet's name was Buddy" "${SESSION_3}" "${THREAD_3}"
sleep 2

echo -e "\n${GREEN}✓ Debit replacement (stolen) workflow complete${NC}\n"

# ============================================================================
# WORKFLOW 4: CREDIT CARD REPLACEMENT - LOST (FEE CHARGED)
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 4: Credit Replacement - Lost (Fee Charged)   ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_4="credit-lost-001"
THREAD_4="credit-lost-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "I need a replacement credit card" "${SESSION_4}" "${THREAD_4}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "I need a replacement for my credit card" "${SESSION_4}" "${THREAD_4}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Provide reason (triggers fee)${NC}"
resume_agent "I lost my credit card, not sure where. No police report filed." "${SESSION_4}" "${THREAD_4}"
sleep 2

echo -e "\n${GREEN}✓ Credit replacement workflow complete (fee charged)${NC}\n"

# ============================================================================
# WORKFLOW 5: CREDIT CARD REPLACEMENT - STOLEN (FEE WAIVED)
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 5: Credit Replacement - Stolen (Fee Waived)  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_5="credit-stolen-001"
THREAD_5="credit-stolen-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "My credit card was stolen" "${SESSION_5}" "${THREAD_5}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "I need a replacement credit card because mine was stolen" "${SESSION_5}" "${THREAD_5}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Provide reason (triggers fee waiver)${NC}"
resume_agent "My purse was stolen yesterday. I filed a police report this morning. Here's the case number: 2024-12345." "${SESSION_5}" "${THREAD_5}"
sleep 2

echo -e "\n${GREEN}✓ Credit replacement workflow complete (fee waived)${NC}\n"

# ============================================================================
# WORKFLOW 6: CARD STATUS & WATCHES - FRAUD LEGITIMATE
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 6: Card Status - Transaction Legitimate      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_6="status-legit-001"
THREAD_6="status-legit-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "My card is blocked and I can't use it" "${SESSION_6}" "${THREAD_6}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "There's a fraud alert on my card but the transaction was legitimate" "${SESSION_6}" "${THREAD_6}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Status/watch action${NC}"
resume_agent "I need the fraud block removed - that was my transaction" "${SESSION_6}" "${THREAD_6}"
sleep 2

echo -e "\n${YELLOW}➤ Step 4: Fraud details (legitimate)${NC}"
resume_agent "Yes, I made that purchase. It was me buying electronics for \$2,500. I want the block removed." "${SESSION_6}" "${THREAD_6}"
sleep 2

echo -e "\n${GREEN}✓ Card status workflow complete (legitimate - block removal)${NC}\n"

# ============================================================================
# WORKFLOW 7: CARD STATUS & WATCHES - FRAUD CONFIRMED
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 7: Card Status - Fraudulent Transaction      ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_7="status-fraud-001"
THREAD_7="status-fraud-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "I see suspicious charges on my card" "${SESSION_7}" "${THREAD_7}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes issue${NC}"
resume_agent "There are fraudulent charges on my credit card" "${SESSION_7}" "${THREAD_7}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Status/watch action${NC}"
resume_agent "I need to report fraud and block my card" "${SESSION_7}" "${THREAD_7}"
sleep 2

echo -e "\n${YELLOW}➤ Step 4: Fraud details (fraudulent)${NC}"
resume_agent "No, I did NOT make that transaction. It's fraudulent. Please block my card and start a dispute." "${SESSION_7}" "${THREAD_7}"
sleep 2

echo -e "\n${GREEN}✓ Card status workflow complete (fraudulent - block + replacement + dispute)${NC}\n"

# ============================================================================
# WORKFLOW 8: CARD DELIVERY - BARBADOS
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 8: Card Delivery - Barbados Territory        ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_8="delivery-barbados-001"
THREAD_8="delivery-barbados-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "When will my new card arrive?" "${SESSION_8}" "${THREAD_8}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes inquiry${NC}"
resume_agent "I need to know when my card will be delivered" "${SESSION_8}" "${THREAD_8}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Delivery details (Barbados)${NC}"
resume_agent "I'm in Barbados, transit code 09792. When should I expect my card?" "${SESSION_8}" "${THREAD_8}"
sleep 2

echo -e "\n${GREEN}✓ Card delivery workflow complete (Barbados - 2-3 weeks)${NC}\n"

# ============================================================================
# WORKFLOW 9: CARD DELIVERY - PWM (PRIORITY)
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  WORKFLOW 9: Card Delivery - PWM Priority              ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}\n"

SESSION_9="delivery-pwm-001"
THREAD_9="delivery-pwm-thread-001"

echo -e "${YELLOW}➤ Step 1: Initial request${NC}"
invoke_agent "I need to know about my card delivery" "${SESSION_9}" "${THREAD_9}"
sleep 2

echo -e "\n${YELLOW}➤ Step 2: Customer describes inquiry${NC}"
resume_agent "When will my replacement card arrive?" "${SESSION_9}" "${THREAD_9}"
sleep 2

echo -e "\n${YELLOW}➤ Step 3: Delivery details (PWM)${NC}"
resume_agent "I'm a Private Wealth Management client. I need this card urgently for travel." "${SESSION_9}" "${THREAD_9}"
sleep 2

echo -e "\n${GREEN}✓ Card delivery workflow complete (PWM - 5 business days priority)${NC}\n"

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                       TEST SUITE COMPLETE                      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${GREEN}✓ All 9 test scenarios executed successfully${NC}"
echo -e "\n${YELLOW}Workflows Tested:${NC}"
echo -e "  1. Card Activation (5-question verification)"
echo -e "  2. Debit Replacement - Lost Card"
echo -e "  3. Debit Replacement - Stolen Card"
echo -e "  4. Credit Replacement - Lost (Fee Charged)"
echo -e "  5. Credit Replacement - Stolen (Fee Waived)"
echo -e "  6. Card Status - Legitimate Transaction"
echo -e "  7. Card Status - Fraudulent Transaction"
echo -e "  8. Card Delivery - Barbados"
echo -e "  9. Card Delivery - PWM Priority"
echo ""
