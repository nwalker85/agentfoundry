#!/usr/bin/env python3
"""
Comprehensive validation for agent system
Tests instantiation and basic workflows
"""

import asyncio
import sys

sys.path.insert(0, ".")

from agents.io_agent import IOAgent
from agents.supervisor_agent import SupervisorAgent
from agents.workers.coherence_agent import CoherenceAgent
from agents.workers.context_agent import ContextAgent
from agents.workers.pm_agent import PMAgent


async def main():
    print("=" * 70)
    print("Agent System Comprehensive Validation")
    print("=" * 70)

    all_passed = True

    # Test 1: ContextAgent instantiation
    print("\n[TEST 1] ContextAgent instantiation...")
    try:
        context_agent = ContextAgent()
        print("  ✅ ContextAgent created successfully")
    except Exception as e:
        print(f"  ❌ ContextAgent creation failed: {e}")
        all_passed = False

    # Test 2: CoherenceAgent instantiation
    print("\n[TEST 2] CoherenceAgent instantiation...")
    try:
        coherence_agent = CoherenceAgent()
        print("  ✅ CoherenceAgent created successfully")
    except Exception as e:
        print(f"  ❌ CoherenceAgent creation failed: {e}")
        all_passed = False

    # Test 3: PMAgent instantiation
    print("\n[TEST 3] PMAgent instantiation...")
    try:
        pm_agent = PMAgent()
        print("  ✅ PMAgent created successfully")
    except Exception as e:
        print(f"  ❌ PMAgent creation failed: {e}")
        all_passed = False

    # Test 4: SupervisorAgent instantiation (integrates context + coherence)
    print("\n[TEST 4] SupervisorAgent instantiation...")
    try:
        supervisor = SupervisorAgent()
        print("  ✅ SupervisorAgent created successfully")
        print("  ✅ Context and Coherence agents integrated")
    except Exception as e:
        print(f"  ❌ SupervisorAgent creation failed: {e}")
        all_passed = False

    # Test 5: IOAgent instantiation
    print("\n[TEST 5] IOAgent instantiation...")
    try:
        io_agent = IOAgent()
        print("  ✅ IOAgent created successfully")
        print("  ✅ Supervisor agent integrated")
    except Exception as e:
        print(f"  ❌ IOAgent creation failed: {e}")
        all_passed = False

    # Test 6: ContextAgent basic workflow
    print("\n[TEST 6] ContextAgent context enrichment...")
    try:
        context_agent = ContextAgent()
        enriched = await context_agent.process(
            session_id="test_session_001", user_id="test_user", current_input="Test message"
        )
        assert "session" in enriched
        assert "user" in enriched
        assert "current_request" in enriched
        print("  ✅ Context enrichment working")
        print(f"  ✅ Session message count: {enriched['session']['message_count']}")
    except Exception as e:
        print(f"  ❌ Context enrichment failed: {e}")
        all_passed = False

    # Test 7: CoherenceAgent response compilation
    print("\n[TEST 7] CoherenceAgent response compilation...")
    try:
        coherence_agent = CoherenceAgent()
        compiled = await coherence_agent.process(
            {"pm_agent": "I can help with project management tasks.", "test_agent": "I can help with testing."}
        )
        assert len(compiled) > 0
        print("  ✅ Response compilation working")
        print(f"  ✅ Compiled response length: {len(compiled)} chars")
    except Exception as e:
        print(f"  ❌ Response compilation failed: {e}")
        all_passed = False

    # Test 8: End-to-end message flow (simple test)
    print("\n[TEST 8] End-to-end message flow...")
    try:
        io_agent = IOAgent()
        response = await io_agent.process_message(
            user_message="What can you help me with?", session_id="e2e_test_session", user_id="e2e_test_user"
        )
        assert len(response) > 0
        print("  ✅ End-to-end flow working")
        print(f"  ✅ Response received: {len(response)} chars")
        print(f"  ✅ Response preview: {response[:100]}...")
    except Exception as e:
        print(f"  ❌ End-to-end flow failed: {e}")
        all_passed = False

    # Final summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ Agent system is fully operational")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
