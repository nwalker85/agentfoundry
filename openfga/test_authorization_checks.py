"""
OpenFGA Authorization Test Suite
---------------------------------
Tests the complete authorization model with real-world scenarios.

Based on the working example with:
- Platform admin (nate)
- Tenant (ravenhelm)
- Organization (cibc)
- Team (card-support, member: bob)
- Project (card-services)
- Domain hierarchy (banking → banking-fraud)
- Agents (fraud-detector, marshal)

Run after setup_initial_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.openfga_client import fga_client


async def run_tests():
    """Run comprehensive authorization tests"""
    
    print("🧪 OpenFGA Authorization Test Suite")
    print("="*60)
    print()
    
    tests = [
        {
            "category": "Team-Based Access",
            "tests": [
                {
                    "name": "Bob (team member) can read fraud-detector agent",
                    "user": "user:bob",
                    "relation": "can_read",
                    "object": "agent:fraud-detector",
                    "expected": True,
                    "path": "Bob → team:card-support → project:card-services → domain:banking → domain:banking-fraud → agent"
                },
                {
                    "name": "Bob can execute fraud-detector (via can_read)",
                    "user": "user:bob",
                    "relation": "can_execute",
                    "object": "agent:fraud-detector",
                    "expected": True,
                    "path": "can_execute = can_read (from model)"
                }
            ]
        },
        {
            "category": "System Agent Protection",
            "tests": [
                {
                    "name": "Bob CANNOT write to system agent (marshal)",
                    "user": "user:bob",
                    "relation": "can_write",
                    "object": "agent:marshal",
                    "expected": False,
                    "path": "is_system exclusion prevents writes"
                },
                {
                    "name": "Bob CANNOT delete system agent (marshal)",
                    "user": "user:bob",
                    "relation": "can_delete",
                    "object": "agent:marshal",
                    "expected": False,
                    "path": "is_system exclusion prevents deletes"
                },
                {
                    "name": "Even Alice (org admin) CANNOT delete marshal",
                    "user": "user:alice",
                    "relation": "can_delete",
                    "object": "agent:marshal",
                    "expected": False,
                    "path": "is_system protects critical infrastructure"
                }
            ]
        },
        {
            "category": "Hierarchical Permissions",
            "tests": [
                {
                    "name": "Alice (org admin) can delete domain:banking",
                    "user": "user:alice",
                    "relation": "can_delete",
                    "object": "domain:banking",
                    "expected": True,
                    "path": "Alice is org admin → can_delete cascades to domains"
                },
                {
                    "name": "Nate (tenant admin) can delete domain:banking",
                    "user": "user:nate",
                    "relation": "can_delete",
                    "object": "domain:banking",
                    "expected": True,
                    "path": "Nate → tenant admin → org admin → domain delete"
                },
                {
                    "name": "Bob CANNOT delete domain (not admin)",
                    "user": "user:bob",
                    "relation": "can_delete",
                    "object": "domain:banking",
                    "expected": False,
                    "path": "Bob is team member, not admin"
                }
            ]
        },
        {
            "category": "Subdomain Inheritance",
            "tests": [
                {
                    "name": "Access to parent domain grants subdomain access",
                    "user": "user:bob",
                    "relation": "can_read",
                    "object": "domain:banking-fraud",
                    "expected": True,
                    "path": "Bob can read banking → inherits banking-fraud"
                }
            ]
        },
        {
            "category": "Owner Permissions",
            "tests": [
                {
                    "name": "Alice (owner) can write fraud-detector",
                    "user": "user:alice",
                    "relation": "can_write",
                    "object": "agent:fraud-detector",
                    "expected": True,
                    "path": "Alice is owner"
                },
                {
                    "name": "Alice can deploy fraud-detector",
                    "user": "user:alice",
                    "relation": "can_deploy",
                    "object": "agent:fraud-detector",
                    "expected": True,
                    "path": "can_deploy = can_write"
                }
            ]
        },
        {
            "category": "Platform Admin",
            "tests": [
                {
                    "name": "Nate (platform admin) has global access",
                    "user": "user:nate",
                    "relation": "global_admin",
                    "object": "platform:foundry",
                    "expected": True,
                    "path": "Direct global_admin relationship"
                }
            ]
        }
    ]
    
    total_tests = sum(len(cat["tests"]) for cat in tests)
    passed = 0
    failed = 0
    
    for category_data in tests:
        print(f"📁 {category_data['category']}")
        print("-" * 60)
        
        for test in category_data["tests"]:
            try:
                result = await fga_client.check(
                    user=test["user"],
                    relation=test["relation"],
                    object=test["object"]
                )
                
                if result == test["expected"]:
                    print(f"  ✓ {test['name']}")
                    print(f"    → {test['path']}")
                    passed += 1
                else:
                    print(f"  ✗ {test['name']}")
                    print(f"    Expected: {test['expected']}, Got: {result}")
                    print(f"    → {test['path']}")
                    failed += 1
            except Exception as e:
                print(f"  ✗ {test['name']}")
                print(f"    Error: {e}")
                failed += 1
            
            print()
        
        print()
    
    # Summary
    print("="*60)
    print(f"Test Results: {passed}/{total_tests} passed")
    print("="*60)
    
    if failed == 0:
        print("\n✅ All tests passed!")
        print("\nYour authorization model is working correctly:")
        print("  ✓ Hierarchical permissions")
        print("  ✓ Team-based access")
        print("  ✓ System agent protection")
        print("  ✓ Subdomain inheritance")
        print("  ✓ Owner permissions")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)

