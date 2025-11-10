# Engineering Department — User Acceptance Testing (UAT) Guide

## Document Information
**Version:** 1.0  
**Date:** November 9, 2025  
**System:** Engineering Department MCP Server v0.2.0  
**Test Environment:** http://localhost:8001  
**Test Duration:** ~30 minutes

---

## 1. UAT Overview

### Purpose
Validate that the Engineering Department system meets business requirements for story creation, task management, and automated GitHub integration.

### Scope
- Story creation in Notion
- GitHub issue generation
- Idempotency protection
- Audit trail functionality
- PM Agent automation

### Prerequisites
- [ ] MCP Server running on port 8001
- [ ] Valid Notion workspace access
- [ ] GitHub repository configured
- [ ] Test environment credentials set

### Out of Scope
- WebSocket real-time features (Phase 4)
- Multi-agent orchestration (Phase 5)
- Production performance testing

---

## 2. Test Environment Setup

### Pre-Test Checklist
```bash
# Terminal 1: Start MCP Server
cd "/Users/nate/Development/1. Projects/Engineering Department"
source venv/bin/activate
python mcp_server.py

# Verify server is running
curl http://localhost:8001/api/status
```

### Expected Response
```json
{
  "api_version": "v1",
  "status": "operational",
  "tools_available": {
    "notion": true,
    "github": true,
    "audit": true
  }
}
```

---

## 3. Test Cases

### TC-001: Basic Story Creation
**Objective:** Create a new story in Notion  
**Priority:** P0 - Critical  
**Estimated Time:** 3 minutes

#### Steps:
1. Open your REST client (Postman, curl, or HTTPie)
2. Send POST request to `/api/tools/notion/create-story`
3. Use this payload:
```json
{
  "epic_title": "Q4 Platform Goals",
  "story_title": "Implement user authentication",
  "priority": "P1",
  "description": "Add OAuth2 authentication for users",
  "acceptance_criteria": [
    "Users can sign in with Google",
    "Sessions persist for 24 hours",
    "Logout invalidates tokens"
  ],
  "definition_of_done": [
    "Code reviewed",
    "Tests passing",
    "Documentation updated"
  ]
}
```

#### Expected Results:
- [ ] HTTP 200 response
- [ ] Response contains `story_id`
- [ ] Response contains `story_url`
- [ ] Response contains `idempotency_key`
- [ ] Story visible in Notion workspace

#### Actual Results:
```
Response Code: _______
Story ID: _______
Story URL: _______
Idempotency Key: _______
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-002: Idempotency Protection
**Objective:** Verify duplicate requests return same story  
**Priority:** P0 - Critical  
**Estimated Time:** 2 minutes

#### Steps:
1. Repeat the exact same request from TC-001
2. Send POST to `/api/tools/notion/create-story` with identical payload
3. Compare response with TC-001

#### Expected Results:
- [ ] Same `story_id` as TC-001
- [ ] Same `idempotency_key` as TC-001
- [ ] No new story created in Notion
- [ ] Response time < 500ms (cached)

#### Actual Results:
```
Story ID matches: ⬜ YES / ⬜ NO
New story created: ⬜ YES / ⬜ NO
Response time: _______ ms
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-003: GitHub Issue Creation
**Objective:** Create GitHub issue linked to story  
**Priority:** P0 - Critical  
**Estimated Time:** 3 minutes

#### Steps:
1. Copy the `story_url` from TC-001
2. Send POST to `/api/tools/github/create-issue`
3. Use this payload:
```json
{
  "title": "[P1] Implement user authentication",
  "body": "## Description\nAdd OAuth2 authentication for users\n\n## Acceptance Criteria\n- [ ] Users can sign in with Google\n- [ ] Sessions persist for 24 hours\n- [ ] Logout invalidates tokens\n\n## Definition of Done\n- [ ] Code reviewed\n- [ ] Tests passing\n- [ ] Documentation updated",
  "labels": ["priority/P1", "source/agent-pm"],
  "story_url": "<INSERT_STORY_URL_FROM_TC-001>"
}
```

#### Expected Results:
- [ ] HTTP 200 response
- [ ] Response contains `issue_number`
- [ ] Response contains `issue_url`
- [ ] Issue visible in GitHub repository
- [ ] Issue contains link to Notion story

#### Actual Results:
```
Response Code: _______
Issue Number: #_______
Issue URL: _______
Contains Story Link: ⬜ YES / ⬜ NO
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-004: Story Listing and Filtering
**Objective:** Query stories with priority filter  
**Priority:** P1 - High  
**Estimated Time:** 2 minutes

#### Steps:
1. Send POST to `/api/tools/notion/list-stories`
2. Use this payload:
```json
{
  "limit": 5,
  "priorities": ["P0", "P1"]
}
```

#### Expected Results:
- [ ] HTTP 200 response
- [ ] Returns array of stories
- [ ] All stories have P0 or P1 priority
- [ ] Story from TC-001 appears in list

#### Actual Results:
```
Stories returned: _______
All P0/P1: ⬜ YES / ⬜ NO
TC-001 story found: ⬜ YES / ⬜ NO
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-005: Audit Trail Verification
**Objective:** Confirm all actions are logged  
**Priority:** P1 - High  
**Estimated Time:** 2 minutes

#### Steps:
1. Send GET to `/api/tools/audit/query?tool=notion&limit=10`
2. Review audit entries

#### Expected Results:
- [ ] HTTP 200 response
- [ ] Contains entries for TC-001 story creation
- [ ] Each entry has timestamp
- [ ] Each entry has request_id
- [ ] Input/output hashes present

#### Actual Results:
```
Entries found: _______
TC-001 logged: ⬜ YES / ⬜ NO
Has timestamps: ⬜ YES / ⬜ NO
Has request IDs: ⬜ YES / ⬜ NO
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-006: PM Agent End-to-End
**Objective:** Test automated story creation via agent  
**Priority:** P1 - High  
**Estimated Time:** 5 minutes

#### Steps:
1. Run the test script:
```bash
cd "/Users/nate/Development/1. Projects/Engineering Department"
source venv/bin/activate
python -c "
from agent.simple_pm import SimplePMAgent
import asyncio

async def test():
    agent = SimplePMAgent()
    result = await agent.process_message(
        'Create a story for adding monitoring dashboard. '
        'This is part of the Observability epic with P2 priority.'
    )
    print('Status:', result['status'])
    print('Story URL:', result.get('story_url'))
    print('Issue URL:', result.get('issue_url'))
    await agent.close()

asyncio.run(test())
"
```

#### Expected Results:
- [ ] Agent extracts epic and story correctly
- [ ] Story created in Notion
- [ ] Issue created in GitHub
- [ ] Both URLs returned
- [ ] Status shows "completed"

#### Actual Results:
```
Epic extracted: _______
Story title: _______
Status: _______
Story URL: _______
Issue URL: _______
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-007: Error Handling - Invalid Data
**Objective:** Verify graceful error handling  
**Priority:** P2 - Medium  
**Estimated Time:** 3 minutes

#### Steps:
1. Send POST to `/api/tools/notion/create-story`
2. Use invalid payload (missing required fields):
```json
{
  "story_title": "Test story without epic"
}
```

#### Expected Results:
- [ ] HTTP 422 or 400 response
- [ ] Error message describes missing fields
- [ ] No story created
- [ ] Error logged in audit trail

#### Actual Results:
```
Response Code: _______
Error Message: _______
Audit logged: ⬜ YES / ⬜ NO
```

**Status:** ⬜ PASS / ⬜ FAIL

---

### TC-008: Concurrent Request Handling
**Objective:** Test multiple simultaneous requests  
**Priority:** P2 - Medium  
**Estimated Time:** 3 minutes

#### Steps:
1. Prepare 3 different story payloads
2. Send all 3 requests simultaneously
3. Verify all complete successfully

#### Expected Results:
- [ ] All 3 requests succeed
- [ ] 3 different stories created
- [ ] 3 different idempotency keys
- [ ] All appear in audit log

#### Actual Results:
```
Request 1: ⬜ SUCCESS / ⬜ FAILED
Request 2: ⬜ SUCCESS / ⬜ FAILED
Request 3: ⬜ SUCCESS / ⬜ FAILED
All in audit: ⬜ YES / ⬜ NO
```

**Status:** ⬜ PASS / ⬜ FAIL

---

## 4. Acceptance Criteria Summary

### Critical Features (Must Pass)
- [ ] TC-001: Basic Story Creation
- [ ] TC-002: Idempotency Protection
- [ ] TC-003: GitHub Issue Creation

### Important Features (Should Pass)
- [ ] TC-004: Story Listing
- [ ] TC-005: Audit Trail
- [ ] TC-006: PM Agent E2E

### Nice to Have (Can Fail)
- [ ] TC-007: Error Handling
- [ ] TC-008: Concurrent Requests

---

## 5. Test Execution Report

### Test Session Information
**Tester Name:** _______________________  
**Test Date:** _______________________  
**Start Time:** _______________________  
**End Time:** _______________________  
**Environment:** ⬜ Local / ⬜ Staging / ⬜ Other: _______

### Test Results Summary

| Test Case | Priority | Status | Notes |
|-----------|----------|--------|-------|
| TC-001 | P0 | ⬜ PASS / ⬜ FAIL | |
| TC-002 | P0 | ⬜ PASS / ⬜ FAIL | |
| TC-003 | P0 | ⬜ PASS / ⬜ FAIL | |
| TC-004 | P1 | ⬜ PASS / ⬜ FAIL | |
| TC-005 | P1 | ⬜ PASS / ⬜ FAIL | |
| TC-006 | P1 | ⬜ PASS / ⬜ FAIL | |
| TC-007 | P2 | ⬜ PASS / ⬜ FAIL | |
| TC-008 | P2 | ⬜ PASS / ⬜ FAIL | |

### Overall Statistics
- **Total Tests:** 8
- **Passed:** _____
- **Failed:** _____
- **Blocked:** _____
- **Pass Rate:** _____%

### Critical Issues Found

| Issue # | Test Case | Description | Severity |
|---------|-----------|-------------|----------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

---

## 6. Defect Reporting Template

### Defect #_____
**Test Case:** TC-_____  
**Title:** _______________________  
**Severity:** ⬜ Critical / ⬜ High / ⬜ Medium / ⬜ Low  
**Status:** ⬜ Open / ⬜ In Progress / ⬜ Resolved  

**Description:**
```
What happened:

What should have happened:

```

**Steps to Reproduce:**
1. 
2. 
3. 

**Evidence:**
```
Error message or screenshot:

```

**Environment:**
- Server Version: v0.2.0
- Browser/Client: 
- Timestamp: 

---

## 7. Sign-Off

### UAT Completion Criteria
- [ ] All P0 tests passed
- [ ] At least 75% of P1 tests passed
- [ ] No critical defects remain open
- [ ] Audit trail functioning
- [ ] Idempotency verified

### Approval

**Business Stakeholder**
- Name: _______________________
- Role: _______________________
- Signature: _______________________
- Date: _______________________
- ⬜ APPROVED / ⬜ REJECTED

**Technical Lead**
- Name: _______________________
- Role: _______________________
- Signature: _______________________
- Date: _______________________
- ⬜ APPROVED / ⬜ REJECTED

### Conditional Approval Notes
```
Conditions for approval:



Remediation required:



Target resolution date:

```

---

## 8. Post-UAT Actions

### If APPROVED:
- [ ] Document any workarounds needed
- [ ] Schedule Phase 4 kickoff
- [ ] Archive test results
- [ ] Update project status

### If REJECTED:
- [ ] Log all defects in tracking system
- [ ] Prioritize fixes with development
- [ ] Schedule retest date: _______
- [ ] Update stakeholders

---

## Appendix A: Quick Test Commands

### Create Story (curl)
```bash
curl -X POST http://localhost:8001/api/tools/notion/create-story \
  -H "Content-Type: application/json" \
  -d '{
    "epic_title": "Test Epic",
    "story_title": "Test Story",
    "priority": "P2",
    "acceptance_criteria": ["AC 1", "AC 2"],
    "definition_of_done": ["DoD 1", "DoD 2"]
  }'
```

### List Stories (curl)
```bash
curl -X POST http://localhost:8001/api/tools/notion/list-stories \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "priorities": ["P0", "P1"]}'
```

### Query Audit Log (curl)
```bash
curl "http://localhost:8001/api/tools/audit/query?tool=notion&limit=10"
```

---

## Appendix B: Troubleshooting

### Common Issues

| Symptom | Possible Cause | Solution |
|---------|---------------|----------|
| Connection refused | Server not running | Start MCP server |
| 401 Unauthorized | Missing auth header | Check .env.local |
| 500 Server Error | Tool initialization failed | Check API tokens |
| Notion story not visible | Wrong workspace | Verify database IDs |
| GitHub issue not created | Invalid repo | Check GITHUB_REPO env |

### Debug Commands
```bash
# Check server logs
tail -f audit/actions_*.jsonl

# Verify environment
python -c "import os; print(os.getenv('NOTION_API_TOKEN', 'NOT SET'))"

# Test connection
curl http://localhost:8001/health
```

---

*UAT Document Version 1.0 - Engineering Department*  
*Template Last Updated: November 9, 2025*
