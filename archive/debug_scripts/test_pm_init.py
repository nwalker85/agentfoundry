#!/usr/bin/env python3
"""Test PM Agent initialization after updates."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv(".env.local", override=True)

# Ensure we have OpenAI key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not set")
    exit(1)


async def test_pm_agent_init():
    """Test PM Agent initialization."""
    
    print("=" * 60)
    print("TESTING PM AGENT INITIALIZATION")
    print("=" * 60)
    
    try:
        print("\n1️⃣ Importing PM Agent...")
        from agent.pm_graph import PMAgent
        print("✅ Import successful")
        
        print("\n2️⃣ Creating PM Agent instance...")
        agent = PMAgent()
        print("✅ Agent created")
        
        print("\n3️⃣ Checking agent configuration...")
        print(f"   MCP URL: {agent.mcp_base_url}")
        print(f"   LLM Model: {agent.llm.model_name}")
        print(f"   Graph nodes: {list(agent.graph.nodes.keys())}")
        
        print("\n4️⃣ Testing simple message...")
        result = await agent.process_message("Create a test story")
        print(f"✅ Message processed")
        print(f"   Status: {result.get('status')}")
        print(f"   Response: {result.get('response', '')[:100]}...")
        
        await agent.close()
        print("\n✅ PM Agent initialized and working!")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ Initialization Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_pm_agent_init())
