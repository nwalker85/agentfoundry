"""
OpenFGA Initial Data Setup
---------------------------
Sets up the initial relationship tuples for Agent Foundry.

This creates the hierarchy shown in the authorization model:
- Platform admin
- Tenant → Organization
- Team membership
- Project with team visibility
- Domain hierarchy (with subdomain)
- Agents (user and system)

Usage:
    python scripts/openfga_setup_initial_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.openfga_client import fga_client


async def setup_initial_data():
    """Set up initial relationship tuples"""

    print("🚀 Setting up initial OpenFGA relationships...\n")

    # Initialize OpenFGA client (loads config from LocalStack)
    print("Step 1: Loading OpenFGA configuration from LocalStack...")
    await fga_client.initialize()
    print(f"✓ Store ID: {fga_client.store_id}")
    print(f"✓ Model ID: {fga_client.auth_model_id}\n")

    # Initial relationships from your example
    tuples = [
        # ========================================================================
        # Platform global admin
        # ========================================================================
        {"user": "user:nate", "relation": "global_admin", "object": "platform:foundry"},
        # ========================================================================
        # Tenant → Org
        # ========================================================================
        {"user": "user:nate", "relation": "admin", "object": "tenant:ravenhelm"},
        {"user": "tenant:ravenhelm", "relation": "tenant", "object": "organization:cibc"},
        {"user": "user:alice", "relation": "admin", "object": "organization:cibc"},
        # ========================================================================
        # Team
        # ========================================================================
        {"user": "organization:cibc", "relation": "organization", "object": "team:card-support"},
        {"user": "user:bob", "relation": "member", "object": "team:card-support"},
        # ========================================================================
        # Project with team visibility
        # ========================================================================
        {"user": "organization:cibc", "relation": "organization", "object": "project:card-services"},
        {"user": "user:alice", "relation": "admin", "object": "project:card-services"},
        {"user": "team:card-support", "relation": "team_visibility", "object": "project:card-services"},
        # ========================================================================
        # Domain under project
        # ========================================================================
        {"user": "project:card-services", "relation": "project", "object": "domain:banking"},
        # ========================================================================
        # Subdomain
        # ========================================================================
        {"user": "domain:banking", "relation": "parent", "object": "domain:banking-fraud"},
        # ========================================================================
        # Agent in domain
        # ========================================================================
        {"user": "domain:banking-fraud", "relation": "domain", "object": "agent:fraud-detector"},
        {"user": "user:alice", "relation": "owner", "object": "agent:fraud-detector"},
        # ========================================================================
        # System agent (protected)
        # ========================================================================
        {"user": "platform:foundry", "relation": "is_system", "object": "agent:marshal"},
    ]

    # Write all tuples
    print(f"📝 Writing {len(tuples)} relationship tuples...\n")

    success = await fga_client.write(tuples)

    if not success:
        print("❌ Failed to write relationships")
        sys.exit(1)

    print("✅ Initial relationships created!\n")

    # ========================================================================
    # Verification Tests (from your examples)
    # ========================================================================

    print("🔍 Running verification checks...\n")

    test_cases = [
        {
            "name": "Can Bob read fraud-detector agent?",
            "user": "user:bob",
            "relation": "can_read",
            "object": "agent:fraud-detector",
            "expected": True,
            "reason": "Bob → team → project → domain → subdomain → agent",
        },
        {
            "name": "Can Bob write to system agent Marshal?",
            "user": "user:bob",
            "relation": "can_write",
            "object": "agent:marshal",
            "expected": False,
            "reason": "is_system exclusion prevents writes",
        },
        {
            "name": "Can Alice delete domain:banking?",
            "user": "user:alice",
            "relation": "can_delete",
            "object": "domain:banking",
            "expected": True,
            "reason": "Alice is org admin → domain admin",
        },
        {
            "name": "Can Bob execute fraud-detector?",
            "user": "user:bob",
            "relation": "can_execute",
            "object": "agent:fraud-detector",
            "expected": True,
            "reason": "can_execute = can_read (cascaded)",
        },
        {
            "name": "Can Nate (platform admin) do anything?",
            "user": "user:nate",
            "relation": "can_read",
            "object": "agent:fraud-detector",
            "expected": True,
            "reason": "Tenant admin → org → project → domain → agent",
        },
    ]

    all_passed = True
    for test in test_cases:
        try:
            result = await fga_client.check(user=test["user"], relation=test["relation"], object=test["object"])

            passed = result == test["expected"]
            icon = "✓" if passed else "✗"

            print(f"{icon} {test['name']}")
            print(f"  Result: {result} (expected: {test['expected']})")
            print(f"  Reason: {test['reason']}")
            print()

            if not passed:
                all_passed = False
        except Exception as e:
            print(f"✗ {test['name']}")
            print(f"  Error: {e}")
            print()
            all_passed = False

    if all_passed:
        print("=" * 60)
        print("✅ All verification checks passed!")
        print("=" * 60)
        print("\nYour OpenFGA authorization model is working perfectly!")
        print("\nHierarchy verified:")
        print("  Platform → Tenant → Org → Project → Domain → Assets")
        print("\nFeatures verified:")
        print("  ✓ Team-based access")
        print("  ✓ System agent protection")
        print("  ✓ Permission cascading")
        print("  ✓ Subdomain inheritance")
    else:
        print("=" * 60)
        print("❌ Some checks failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_initial_data())
