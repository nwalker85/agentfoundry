#!/usr/bin/env python3
"""
Test the fixed LangGraph PM Agent
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.pm_graph import PMAgent


async def test_pm_agent():
    """Test the PM agent with a simple message."""
    
    print("=" * 60)
    print("Testing LangGraph PM Agent")
    print("=" * 60)
    
    # Initialize agent
    print("\n1. Initializing PM Agent...")
    agent = PMAgent()
    
    # Test message
    test_message = "Create a story for adding a healthcheck endpoint to our API"
    print(f"\n2. Test Message: '{test_message}'")
    print("-" * 60)
    
    try:
        print("\n3. Processing message through LangGraph...")
        result = await agent.process_message(test_message)
        
        print("\n4. Result received!")
        print("-" * 60)
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"State: {result.get('state', 'unknown')}")
        
        if result.get('story_created'):
            print(f"\nStory Created:")
            print(f"  - Title: {result['story_created'].get('title')}")
            print(f"  - Epic: {result['story_created'].get('epic')}")
            print(f"  - Priority: {result['story_created'].get('priority')}")
            print(f"  - URL: {result['story_created'].get('url')}")
        
        if result.get('issue_created'):
            print(f"\nIssue Created:")
            print(f"  - Title: {result['issue_created'].get('title')}")
            print(f"  - URL: {result['issue_created'].get('url')}")
        
        if result.get('error'):
            print(f"\n⚠️ Error: {result['error']}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await agent.close()
    
    print("=" * 60)


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_pm_agent())
