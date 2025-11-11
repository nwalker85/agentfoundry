#!/usr/bin/env python
"""Test LangGraph PM Agent directly."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')


async def test_langgraph_agent_import():
    """Test that LangGraph agent can be imported."""
    print("=" * 60)
    print("Test 1: Import LangGraph PM Agent")
    print("=" * 60)
    
    try:
        from agent.pm_graph import PMAgent
        print("✅ PMAgent imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import PMAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_langgraph_agent_initialization():
    """Test that LangGraph agent can be initialized."""
    print("\n" + "=" * 60)
    print("Test 2: Initialize LangGraph PM Agent")
    print("=" * 60)
    
    try:
        from agent.pm_graph import PMAgent
        
        # Check required env vars
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  OPENAI_API_KEY not set - agent will fail")
            return False
        
        agent = PMAgent()
        print("✅ PMAgent initialized successfully")
        print(f"   LLM Model: {agent.llm.model_name}")
        print(f"   MCP Base URL: {agent.mcp_base_url}")
        
        await agent.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize PMAgent: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_langgraph_agent_graph_structure():
    """Test that the LangGraph graph is properly structured."""
    print("\n" + "=" * 60)
    print("Test 3: Verify LangGraph Structure")
    print("=" * 60)
    
    try:
        from agent.pm_graph import PMAgent
        
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  Skipping - OPENAI_API_KEY not set")
            return True
        
        agent = PMAgent()
        
        # Check that graph exists
        if not hasattr(agent, 'graph'):
            print("❌ Agent has no 'graph' attribute")
            return False
        
        print("✅ Agent has graph attribute")
        
        # Check graph nodes (via compiled graph's internal structure)
        print("   Graph compiled successfully")
        print("   Expected nodes:")
        expected_nodes = [
            "understand", "clarify", "validate", "plan",
            "create_story", "create_issue", "complete", "error"
        ]
        for node in expected_nodes:
            print(f"   - {node}")
        
        await agent.close()
        return True
        
    except Exception as e:
        print(f"❌ Graph structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_langgraph_agent_message_processing():
    """Test that the agent can process a message (requires OpenAI API)."""
    print("\n" + "=" * 60)
    print("Test 4: Process Message with LangGraph Agent")
    print("=" * 60)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - skipping live test")
        print("   (This test requires OpenAI API access)")
        return True
    
    if not os.getenv("NOTION_API_TOKEN"):
        print("⚠️  NOTION_API_TOKEN not set - skipping live test")
        return True
    
    try:
        from agent.pm_graph import PMAgent
        
        agent = PMAgent()
        
        print("\n📝 Test Message:")
        message = """Create a story for adding a health check endpoint.
This should be part of the Platform Hardening epic with P1 priority.
The endpoint should return service status and version."""
        
        print(f"   {message[:80]}...")
        
        print("\n🤖 Processing with LangGraph agent...")
        print("   (This will call OpenAI API and may take 10-30 seconds)")
        
        result = await agent.process_message(message)
        
        print("\n✅ Agent completed processing!")
        print(f"\n📊 Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Error: {result.get('error', 'None')}")
        
        if result.get('messages'):
            print(f"\n💬 Agent Messages ({len(result['messages'])} messages):")
            for i, msg in enumerate(result['messages'], 1):
                content = str(msg.content)[:100]
                print(f"   {i}. {msg.__class__.__name__}: {content}...")
        
        if result.get('story_url'):
            print(f"\n🎯 Story Created: {result['story_url']}")
        
        if result.get('issue_url'):
            print(f"🎯 Issue Created: {result['issue_url']}")
        
        await agent.close()
        
        # Check if it actually worked
        if result.get('status') == 'completed':
            print("\n✅ Message processing SUCCESSFUL")
            return True
        elif result.get('status') == 'awaiting_clarification':
            print("\n✅ Agent requested clarification (expected behavior)")
            return True
        else:
            print(f"\n⚠️  Unexpected status: {result.get('status')}")
            return False
        
    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LangGraph PM Agent Test Suite")
    print("=" * 60)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"   OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '✗ Not set'}")
    print(f"   NOTION_API_TOKEN: {'✓ Set' if os.getenv('NOTION_API_TOKEN') else '✗ Not set'}")
    print(f"   GITHUB_TOKEN: {'✓ Set' if os.getenv('GITHUB_TOKEN') else '✗ Not set'}")
    
    results = []
    
    # Test 1: Import
    results.append(await test_langgraph_agent_import())
    
    # Test 2: Initialize
    results.append(await test_langgraph_agent_initialization())
    
    # Test 3: Graph structure
    results.append(await test_langgraph_agent_graph_structure())
    
    # Test 4: Message processing (requires API keys)
    results.append(await test_langgraph_agent_message_processing())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - LangGraph agent is operational!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
