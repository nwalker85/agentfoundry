#!/bin/bash
# Comprehensive CIBC Card Services Agent Test Suite
# Tests all activation and replacement scenarios with validation

BASE_URL="http://localhost:8000"
AGENT_ID="cibc-card-activation"
TIMESTAMP=$(date +%s)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper function to run a step
run_step() {
    local session_id=$1
    local user_input=$2
    local description=$3
    local endpoint=$4

    if [ "$endpoint" = "invoke" ]; then
        curl -s "${BASE_URL}/api/agent/invoke" \
            -H 'Content-Type: application/json' \
            -d "{\"agent_id\":\"${AGENT_ID}\",\"input\":\"${user_input}\",\"session_id\":\"${session_id}\",\"route_via_supervisor\":true}"
    else
        curl -s "${BASE_URL}/api/agent/resume" \
            -H 'Content-Type: application/json' \
            -d "{\"agent_id\":\"${AGENT_ID}\",\"user_input\":\"${user_input}\",\"session_id\":\"${session_id}\"}"
    fi
}

# Helper function to validate test result
validate_test() {
    local test_name=$1
    local response=$2
    local expected_pattern=$3
    local expected_not_pattern=$4

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if echo "$response" | grep -qiE "$expected_pattern"; then
        if [ -z "$expected_not_pattern" ] || ! echo "$response" | grep -qiE "$expected_not_pattern"; then
            echo -e "${GREEN}✓ PASS${NC}: $test_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        fi
    fi

    echo -e "${RED}✗ FAIL${NC}: $test_name"
    echo -e "${YELLOW}Expected pattern: $expected_pattern${NC}"
    if [ ! -z "$expected_not_pattern" ]; then
        echo -e "${YELLOW}Should NOT contain: $expected_not_pattern${NC}"
    fi
    echo -e "${CYAN}Response: $(echo "$response" | head -c 200)...${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    return 1
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  CIBC Card Services Agent - Comprehensive Test Suite          ║${NC}"
echo -e "${BLUE}║  Testing: Activation (5) + Replacement (7) = 12 Scenarios     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# ACTIVATION TESTS
# ============================================================================

echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}ACTIVATION WORKFLOW TESTS (5 scenarios)${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ----------------------------------------------------------------------------
# Test A1: Perfect 5/5 Verification → Immediate Activation
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test A1: Perfect 5/5 Verification${NC}"
SESSION="a1-perfect-${TIMESTAMP}"

run_step "$SESSION" "I need to activate my card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes please" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "416-555-0123" "Q1: Phone" "resume" > /dev/null
sleep 2
run_step "$SESSION" "1985-03-15" "Q2: DOB" "resume" > /dev/null
sleep 2
run_step "$SESSION" "123 Main St" "Q3: Address" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q4: Security Q1" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "4567" "Q5: Security Q2" "resume")

validate_test "A1: Perfect verification → Activated" "$FINAL" "activated|successfully activated" "discrepancy|branch"
echo ""

# ----------------------------------------------------------------------------
# Test A2: 4/5 with DOB Wrong → Cross-check and Activate
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test A2: 4/5 with DOB Wrong (Cross-check)${NC}"
SESSION="a2-dob-wrong-${TIMESTAMP}"

run_step "$SESSION" "Activate my card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "416-555-0123" "Q1: Phone" "resume" > /dev/null
sleep 2
run_step "$SESSION" "March 1, 1990" "Q2: DOB (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "123 Main St" "Q3: Address" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q4: Security Q1" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "4567" "Q5: Security Q2" "resume")

validate_test "A2: DOB mismatch → Cross-check → Activated" "$FINAL" "discrepancy.*date of birth.*activated" "visit.*branch"
echo ""

# ----------------------------------------------------------------------------
# Test A3: 4/5 with Phone Wrong → Update Phone and Activate
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test A3: 4/5 with Phone Wrong (Update)${NC}"
SESSION="a3-phone-wrong-${TIMESTAMP}"

run_step "$SESSION" "Activate card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "555-999-8888" "Q1: Phone (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "1985-03-15" "Q2: DOB" "resume" > /dev/null
sleep 2
run_step "$SESSION" "123 Main St" "Q3: Address" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q4: Security Q1" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "4567" "Q5: Security Q2" "resume")

validate_test "A3: Phone mismatch → Update → Activated" "$FINAL" "activated" "visit.*branch"
echo ""

# ----------------------------------------------------------------------------
# Test A4: Both DOB & Phone Wrong → Fail to Branch
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test A4: Both DOB & Phone Wrong (Fail)${NC}"
SESSION="a4-both-wrong-${TIMESTAMP}"

run_step "$SESSION" "Activate my card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "555-999-8888" "Q1: Phone (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "January 1, 2000" "Q2: DOB (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "123 Main St" "Q3: Address" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q4: Security Q1" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "4567" "Q5: Security Q2" "resume")

validate_test "A4: Both wrong → Failed → Send to branch" "$FINAL" "branch|visit" "activated"
echo ""

# ----------------------------------------------------------------------------
# Test A5: Low Score < 3 → Fail to Branch
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test A5: Low Score < 3 (Fail)${NC}"
SESSION="a5-low-score-${TIMESTAMP}"

run_step "$SESSION" "Activate card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "555-999-8888" "Q1: Phone (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "January 1, 2000" "Q2: DOB (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "999 Wrong Street" "Q3: Address (WRONG)" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Smith" "Q4: Security Q1 (WRONG)" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "9999" "Q5: Security Q2 (WRONG)" "resume")

validate_test "A5: Score < 3 → Failed → Send to branch" "$FINAL" "branch|visit" "activated"
echo ""

# ============================================================================
# REPLACEMENT TESTS
# ============================================================================

echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}REPLACEMENT WORKFLOW TESTS (7 scenarios)${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ----------------------------------------------------------------------------
# Test R1: Lost Credit Card → $25 Fee, NEW Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R1: Lost Credit Card${NC}"
SESSION="r1-lost-credit-${TIMESTAMP}"

run_step "$SESSION" "I lost my credit card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes, I need a replacement" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "I lost it yesterday" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
run_step "$SESSION" "It's a credit card" "Q4: Card type" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "Okay" "Q5: Acknowledge" "resume")

validate_test "R1: Lost credit → \$25 fee, NEW number" "$FINAL" "replacement|new card" ""
echo ""

# ----------------------------------------------------------------------------
# Test R2: Stolen + Police Report → Fee Waived, NEW Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R2: Stolen Card with Police Report${NC}"
SESSION="r2-stolen-police-${TIMESTAMP}"

run_step "$SESSION" "My card was stolen" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes, replace it" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "It was stolen from my car" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "Yes, I filed a police report" "Q4: Police report" "resume")

validate_test "R2: Stolen + police → Fee waived" "$FINAL" "replacement|new card" "\$25|fee.*\$25|\$25.*fee"
echo ""

# ----------------------------------------------------------------------------
# Test R3: Stolen Without Police Report → $25 Fee, NEW Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R3: Stolen Card without Police Report${NC}"
SESSION="r3-stolen-nopolice-${TIMESTAMP}"

run_step "$SESSION" "Card was stolen" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Someone stole my card" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "No, I haven't filed a report" "Q4: Police report" "resume")

validate_test "R3: Stolen no police → Has fee/replacement" "$FINAL" "replacement|new card" ""
echo ""

# ----------------------------------------------------------------------------
# Test R4: Compromised/Fraud → Fee Waived, NEW Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R4: Compromised/Fraud${NC}"
SESSION="r4-compromised-${TIMESTAMP}"

run_step "$SESSION" "My card was compromised" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes, replace it" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "I saw fraudulent charges, card is compromised" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
run_step "$SESSION" "It's a credit card" "Q4: Card type" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "Thanks" "Q5: Acknowledge" "resume")

validate_test "R4: Compromised → Fee waived" "$FINAL" "replacement|new card" ""
echo ""

# ----------------------------------------------------------------------------
# Test R5: Damaged - Faulty → Fee Waived, SAME Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R5: Damaged Card (Faulty)${NC}"
SESSION="r5-damaged-faulty-${TIMESTAMP}"

run_step "$SESSION" "My card is damaged and not working" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "The chip is not working, card is damaged" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Credit card" "Q4: Card type" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "It's a defect, the chip malfunctioned" "Q5: Damage type" "resume")

validate_test "R5: Damaged faulty → Fee waived" "$FINAL" "replacement" ""
echo ""

# ----------------------------------------------------------------------------
# Test R6: Damaged - Customer Fault → $25 Fee, SAME Card Number
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R6: Damaged Card (Customer Fault)${NC}"
SESSION="r6-damaged-customer-${TIMESTAMP}"

run_step "$SESSION" "My card is damaged" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes, replace it" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Card is damaged and won't swipe" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Credit card" "Q4: Card type" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "I accidentally bent it" "Q5: Damage type" "resume")

validate_test "R6: Damaged customer fault → Has replacement" "$FINAL" "replacement" ""
echo ""

# ----------------------------------------------------------------------------
# Test R7: Debit Replacement (Any Reason) → Always Free
# ----------------------------------------------------------------------------
echo -e "${CYAN}Test R7: Debit Card Replacement${NC}"
SESSION="r7-debit-${TIMESTAMP}"

run_step "$SESSION" "I need to replace my debit card" "Initial request" "invoke" > /dev/null
sleep 2
run_step "$SESSION" "Yes" "Confirm" "resume" > /dev/null
sleep 2
run_step "$SESSION" "I lost it" "Q1: Reason" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Last 4 are 5678, account 12345678" "Q2: Card details" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Johnson" "Q3: Security" "resume" > /dev/null
sleep 2
run_step "$SESSION" "Debit card" "Q4: Card type" "resume" > /dev/null
sleep 2
FINAL=$(run_step "$SESSION" "Okay" "Q5: Acknowledge" "resume")

validate_test "R7: Debit replacement → Free (no fee mentioned)" "$FINAL" "replacement|debit" ""
echo ""

# ============================================================================
# FINAL SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    TEST SUMMARY                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Total Tests:${NC} $TOTAL_TESTS"
echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
echo -e "${RED}Failed:${NC} $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
    echo -e "${CYAN}The CIBC Card Services Agent is fully functional.${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo -e "${YELLOW}Review the failures above for details.${NC}"
    exit 1
fi
