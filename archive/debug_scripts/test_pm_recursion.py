#!/usr/bin/env python3
"""Test to identify the recursion issue in PM Agent."""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Set OpenAI key if not set
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not configured")
    exit(1)

from agent.pm_graph import PMAgent


async def test_pm_agent():
    """Test the PM agent with simple requests."""
    
    print("=" * 60)
    print("TESTING PM AGENT - RECURSION DEBUG")
    print("=" * 60)
    
    # Start MCP server URL (assuming it's running)
    mcp_url = "http://localhost:8001"
    
    # Create agent
    print("\nInitializing PM Agent...")
    agent = PMAgent(mcp_base_url=mcp_url)
    
    # Test cases
    test_messages = [
        "Create a story for building an ERD designer using ReactFlow",
        "Add a healthcheck endpoint to our API",
        "We need user authentication"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{'='*40}")
        print(f"Test {i}: {message}")
        print(f"{'='*40}")
        
        try:
            print("Processing message...")
            result = await agent.process_message(message)
            
            print(f"\n✅ Success!")
            print(f"Status: {result.get('status')}")
            print(f"Response: {result.get('response')[:200]}...")
            
            if result.get('story_created'):
                print(f"Story URL: {result['story_created'].get('url')}")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
                
        except Exception as e:
            print(f"\n❌ Failed: {e}")
            import traceback
            traceback.print_exc()
    
    await agent.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_pm_agent())
