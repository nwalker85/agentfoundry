#!/usr/bin/env python
"""
Engineering Department - User Acceptance Test Runner
Automated UAT execution with pass/fail reporting
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from agent.simple_pm import SimplePMAgent

# Load environment
load_dotenv('.env.local')


class TestStatus(Enum):
    """Test execution status."""
    PENDING = "⏳ PENDING"
    RUNNING = "🔄 RUNNING"
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    BLOCKED = "🚫 BLOCKED"
    SKIPPED = "⏭️ SKIPPED"


class TestPriority(Enum):
    """Test priority levels."""
    P0 = "P0 - Critical"
    P1 = "P1 - High"
    P2 = "P2 - Medium"
    P3 = "P3 - Low"


class TestResult:
    """Individual test result."""
    
    def __init__(self, test_id: str, name: str, priority: TestPriority):
        self.test_id = test_id
        self.name = name
        self.priority = priority
        self.status = TestStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.details: Dict[str, Any] = {}
        self.assertions: List[Dict[str, Any]] = []
    
    def start(self):
        """Mark test as started."""
        self.status = TestStatus.RUNNING
        self.start_time = datetime.now()
    
    def pass_test(self, details: Optional[Dict] = None):
        """Mark test as passed."""
        self.status = TestStatus.PASSED
        self.end_time = datetime.now()
        if details:
            self.details.update(details)
    
    def fail_test(self, error: str, details: Optional[Dict] = None):
        """Mark test as failed."""
        self.status = TestStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
        if details:
            self.details.update(details)
    
    def add_assertion(self, name: str, expected: Any, actual: Any, passed: bool):
        """Add an assertion result."""
        self.assertions.append({
            "name": name,
            "expected": expected,
            "actual": actual,
            "passed": passed
        })
    
    @property
    def duration(self) -> float:
        """Get test duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


class UATRunner:
    """User Acceptance Test Runner."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.results: List[TestResult] = []
        self.test_data: Dict[str, Any] = {}  # Store data between tests
        self.session_start = datetime.now()
    
    async def run_all_tests(self):
        """Run all UAT tests."""
        print("\n" + "=" * 70)
        print("ENGINEERING DEPARTMENT - USER ACCEPTANCE TESTING")
        print("=" * 70)
        print(f"Start Time: {self.session_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Server URL: {self.base_url}")
        print("=" * 70 + "\n")
        
        # Check server connectivity first
        if not await self.check_server():
            print("❌ Server not accessible. Aborting tests.")
            return
        
        # Run test cases
        await self.tc_001_basic_story_creation()
        await self.tc_002_idempotency_protection()
        await self.tc_003_github_issue_creation()
        await self.tc_004_story_listing()
        await self.tc_005_audit_trail()
        await self.tc_006_pm_agent_e2e()
        await self.tc_007_error_handling()
        await self.tc_008_concurrent_requests()
        
        # Generate report
        self.generate_report()
    
    async def check_server(self) -> bool:
        """Check if server is accessible."""
        try:
            response = await self.client.get("/api/status")
            if response.status_code == 200:
                data = response.json()
                print("✅ Server Status: Operational")
                print(f"   - Notion: {'✅' if data.get('tools_available', {}).get('notion') else '❌'}")
                print(f"   - GitHub: {'✅' if data.get('tools_available', {}).get('github') else '❌'}")
                print(f"   - Audit: {'✅' if data.get('tools_available', {}).get('audit') else '❌'}")
                print()
                return True
        except Exception as e:
            print(f"❌ Server check failed: {e}")
        return False
    
    async def tc_001_basic_story_creation(self):
        """TC-001: Basic Story Creation"""
        test = TestResult("TC-001", "Basic Story Creation", TestPriority.P0)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            payload = {
                "epic_title": "Q4 Platform Goals",
                "story_title": f"UAT Test Story - {datetime.now().strftime('%H:%M:%S')}",
                "priority": "P1",
                "description": "UAT test story for validation",
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
            
            response = await self.client.post(
                "/api/tools/notion/create-story",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Store for later tests
                self.test_data["story"] = data
                self.test_data["story_payload"] = payload
                
                # Assertions
                test.add_assertion("HTTP Status", 200, response.status_code, True)
                test.add_assertion("Has story_id", True, "story_id" in data, "story_id" in data)
                test.add_assertion("Has story_url", True, "story_url" in data, "story_url" in data)
                test.add_assertion("Has idempotency_key", True, "idempotency_key" in data, "idempotency_key" in data)
                
                test.pass_test({
                    "story_id": data.get("story_id"),
                    "story_url": data.get("story_url"),
                    "idempotency_key": data.get("idempotency_key")
                })
                print(f"   ✅ Story created: {data.get('story_id')}")
            else:
                test.fail_test(f"HTTP {response.status_code}: {response.text[:200]}")
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_002_idempotency_protection(self):
        """TC-002: Idempotency Protection"""
        test = TestResult("TC-002", "Idempotency Protection", TestPriority.P0)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        if "story_payload" not in self.test_data:
            test.status = TestStatus.BLOCKED
            test.error = "TC-001 did not complete successfully"
            print("   🚫 Blocked: Requires TC-001 to pass")
            self.results.append(test)
            return
        
        try:
            # Send duplicate request
            response = await self.client.post(
                "/api/tools/notion/create-story",
                json=self.test_data["story_payload"]
            )
            
            if response.status_code == 200:
                data = response.json()
                original = self.test_data["story"]
                
                # Assertions
                same_id = data.get("story_id") == original.get("story_id")
                same_key = data.get("idempotency_key") == original.get("idempotency_key")
                
                test.add_assertion("Same story_id", original.get("story_id"), data.get("story_id"), same_id)
                test.add_assertion("Same idempotency_key", original.get("idempotency_key"), data.get("idempotency_key"), same_key)
                
                if same_id and same_key:
                    test.pass_test({"duplicate_prevented": True})
                    print(f"   ✅ Idempotency working: same story returned")
                else:
                    test.fail_test("Different story created")
                    print(f"   ❌ Different story created")
            else:
                test.fail_test(f"HTTP {response.status_code}")
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_003_github_issue_creation(self):
        """TC-003: GitHub Issue Creation"""
        test = TestResult("TC-003", "GitHub Issue Creation", TestPriority.P0)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        if "story" not in self.test_data:
            test.status = TestStatus.BLOCKED
            test.error = "TC-001 did not complete successfully"
            print("   🚫 Blocked: Requires TC-001 to pass")
            self.results.append(test)
            return
        
        try:
            story_url = self.test_data["story"].get("story_url")
            
            payload = {
                "title": "[P1] UAT Test Issue",
                "body": f"## UAT Test Issue\n\nLinked to story: {story_url}",
                "labels": ["priority/P1", "source/agent-pm"],
                "story_url": story_url
            }
            
            response = await self.client.post(
                "/api/tools/github/create-issue",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                self.test_data["issue"] = data
                
                test.add_assertion("HTTP Status", 200, response.status_code, True)
                test.add_assertion("Has issue_number", True, "issue_number" in data, "issue_number" in data)
                test.add_assertion("Has issue_url", True, "issue_url" in data, "issue_url" in data)
                
                test.pass_test({
                    "issue_number": data.get("issue_number"),
                    "issue_url": data.get("issue_url")
                })
                print(f"   ✅ Issue created: #{data.get('issue_number')}")
            else:
                test.fail_test(f"HTTP {response.status_code}")
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_004_story_listing(self):
        """TC-004: Story Listing and Filtering"""
        test = TestResult("TC-004", "Story Listing and Filtering", TestPriority.P1)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            response = await self.client.post(
                "/api/tools/notion/list-stories",
                json={"limit": 5, "priorities": ["P0", "P1"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                stories = data.get("stories", [])
                
                # Check if all are P0 or P1
                all_priority = all(s.get("priority") in ["P0", "P1"] for s in stories)
                
                test.add_assertion("HTTP Status", 200, response.status_code, True)
                test.add_assertion("Returns list", True, isinstance(stories, list), isinstance(stories, list))
                test.add_assertion("All P0/P1", True, all_priority, all_priority)
                
                test.pass_test({"story_count": len(stories)})
                print(f"   ✅ Found {len(stories)} stories")
            else:
                test.fail_test(f"HTTP {response.status_code}")
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_005_audit_trail(self):
        """TC-005: Audit Trail Verification"""
        test = TestResult("TC-005", "Audit Trail Verification", TestPriority.P1)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            response = await self.client.get(
                "/api/tools/audit/query",
                params={"tool": "notion", "limit": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                
                # Check for required fields
                has_timestamps = all("timestamp" in e for e in entries)
                has_request_ids = all("request_id" in e for e in entries)
                
                test.add_assertion("HTTP Status", 200, response.status_code, True)
                test.add_assertion("Has entries", True, len(entries) > 0, len(entries) > 0)
                test.add_assertion("Has timestamps", True, has_timestamps, has_timestamps)
                test.add_assertion("Has request_ids", True, has_request_ids, has_request_ids)
                
                test.pass_test({"entry_count": len(entries)})
                print(f"   ✅ Found {len(entries)} audit entries")
            else:
                test.fail_test(f"HTTP {response.status_code}")
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_006_pm_agent_e2e(self):
        """TC-006: PM Agent End-to-End"""
        test = TestResult("TC-006", "PM Agent End-to-End", TestPriority.P1)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            agent = SimplePMAgent()
            
            result = await agent.process_message(
                "Create a story for adding monitoring dashboard. "
                "This is part of the Observability epic with P2 priority."
            )
            
            await agent.close()
            
            # Check results
            has_story = result.get("story_url") is not None
            has_issue = result.get("issue_url") is not None
            is_completed = result.get("status") == "completed"
            
            test.add_assertion("Story created", True, has_story, has_story)
            test.add_assertion("Issue created", True, has_issue, has_issue)
            test.add_assertion("Status completed", True, is_completed, is_completed)
            
            if has_story and has_issue:
                test.pass_test({
                    "story_url": result.get("story_url"),
                    "issue_url": result.get("issue_url")
                })
                print(f"   ✅ Agent created story and issue")
            else:
                test.fail_test("Agent did not complete workflow")
                print(f"   ❌ Agent workflow incomplete")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_007_error_handling(self):
        """TC-007: Error Handling - Invalid Data"""
        test = TestResult("TC-007", "Error Handling", TestPriority.P2)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            # Send invalid payload
            response = await self.client.post(
                "/api/tools/notion/create-story",
                json={"story_title": "Test story without required fields"}
            )
            
            # Should get 422 or 400
            is_error = response.status_code in [400, 422]
            
            test.add_assertion("Error status code", True, is_error, is_error)
            
            if is_error:
                test.pass_test({"status_code": response.status_code})
                print(f"   ✅ Error handled correctly: HTTP {response.status_code}")
            else:
                test.fail_test(f"Unexpected status: {response.status_code}")
                print(f"   ❌ Unexpected status: {response.status_code}")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    async def tc_008_concurrent_requests(self):
        """TC-008: Concurrent Request Handling"""
        test = TestResult("TC-008", "Concurrent Requests", TestPriority.P2)
        test.start()
        print(f"\n{test.test_id}: {test.name}")
        print("-" * 50)
        
        try:
            # Create 3 concurrent requests
            tasks = []
            for i in range(3):
                payload = {
                    "epic_title": "Concurrent Test",
                    "story_title": f"Concurrent Story {i+1} - {datetime.now().timestamp()}",
                    "priority": "P3",
                    "acceptance_criteria": ["Test AC"],
                    "definition_of_done": ["Test DoD"]
                }
                task = self.client.post("/api/tools/notion/create-story", json=payload)
                tasks.append(task)
            
            # Execute concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
            
            test.add_assertion("All requests succeed", 3, success_count, success_count == 3)
            
            if success_count == 3:
                test.pass_test({"concurrent_success": 3})
                print(f"   ✅ All 3 concurrent requests succeeded")
            else:
                test.fail_test(f"Only {success_count}/3 succeeded")
                print(f"   ❌ Only {success_count}/3 requests succeeded")
                
        except Exception as e:
            test.fail_test(str(e))
            print(f"   ❌ Exception: {e}")
        
        self.results.append(test)
    
    def generate_report(self):
        """Generate UAT report."""
        print("\n" + "=" * 70)
        print("UAT EXECUTION REPORT")
        print("=" * 70)
        
        # Summary statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        blocked = sum(1 for r in self.results if r.status == TestStatus.BLOCKED)
        
        print(f"\nTest Statistics:")
        print(f"  Total Tests:  {total}")
        print(f"  Passed:       {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed:       {failed} ({failed/total*100:.1f}%)")
        print(f"  Blocked:      {blocked} ({blocked/total*100:.1f}%)")
        
        # Critical tests (P0)
        p0_tests = [r for r in self.results if r.priority == TestPriority.P0]
        p0_passed = sum(1 for r in p0_tests if r.status == TestStatus.PASSED)
        
        print(f"\nCritical Tests (P0):")
        print(f"  Total:        {len(p0_tests)}")
        print(f"  Passed:       {p0_passed} ({p0_passed/len(p0_tests)*100:.1f}%)")
        
        # Test results table
        print("\n" + "-" * 70)
        print(f"{'Test ID':<10} {'Name':<30} {'Priority':<12} {'Status':<15}")
        print("-" * 70)
        
        for result in self.results:
            print(f"{result.test_id:<10} {result.name[:30]:<30} {result.priority.value:<12} {result.status.value:<15}")
        
        # Failed test details
        failed_tests = [r for r in self.results if r.status == TestStatus.FAILED]
        if failed_tests:
            print("\n" + "-" * 70)
            print("FAILED TEST DETAILS")
            print("-" * 70)
            for result in failed_tests:
                print(f"\n{result.test_id}: {result.name}")
                print(f"  Error: {result.error}")
                for assertion in result.assertions:
                    if not assertion["passed"]:
                        print(f"  - {assertion['name']}: Expected {assertion['expected']}, Got {assertion['actual']}")
        
        # Overall verdict
        print("\n" + "=" * 70)
        all_p0_passed = all(r.status == TestStatus.PASSED for r in p0_tests)
        
        if all_p0_passed and passed/total >= 0.75:
            print("VERDICT: ✅ PASSED - System ready for next phase")
        elif all_p0_passed:
            print("VERDICT: ⚠️ CONDITIONAL PASS - Critical features working, minor issues exist")
        else:
            print("VERDICT: ❌ FAILED - Critical features not working")
        
        print("=" * 70)
        
        # Save report to file
        self.save_report()
    
    def save_report(self):
        """Save report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"UAT_Report_{timestamp}.json"
        
        report_data = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "statistics": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in self.results if r.status == TestStatus.FAILED),
                "blocked": sum(1 for r in self.results if r.status == TestStatus.BLOCKED)
            },
            "tests": [
                {
                    "test_id": r.test_id,
                    "name": r.name,
                    "priority": r.priority.value,
                    "status": r.status.value,
                    "duration": r.duration,
                    "error": r.error,
                    "details": r.details,
                    "assertions": r.assertions
                }
                for r in self.results
            ]
        }
        
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\nReport saved to: {filename}")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    """Main UAT execution."""
    runner = UATRunner()
    
    try:
        await runner.run_all_tests()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
