#!/usr/bin/env python3
"""
Test the PM Agent without the frontend
Useful for testing while Node.js is being installed
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_mcp_server():
    """Test if MCP server is running and responsive."""
    base_url = "http://localhost:8001"
    
    print("🔍 Testing MCP Server Connection...")
    print("-" * 40)
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ MCP Server is healthy: {data}")
                else:
                    print(f"❌ MCP Server returned status: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Cannot connect to MCP Server: {e}")
            print("\nPlease start the MCP server:")
            print("  source venv/bin/activate")
            print("  python mcp_server.py")
            return False
        
        # Test agent endpoint
        print("\n📝 Testing PM Agent...")
        print("-" * 40)
        
        test_message = "Create a story for adding a healthcheck endpoint to our API"
        
        try:
            payload = {
                "message": test_message,
                "session_id": f"test-{datetime.now().isoformat()}"
            }
            
            async with session.post(
                f"{base_url}/api/agent/process",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Agent Response:")
                    print(f"   Message: {data.get('response', 'No response')[:100]}...")
                    if data.get('artifacts'):
                        print(f"   Artifacts: {len(data['artifacts'])} created")
                    print(f"   Success: {data.get('success', False)}")
                else:
                    print(f"❌ Agent returned status: {response.status}")
                    text = await response.text()
                    print(f"   Error: {text}")
                    
        except Exception as e:
            print(f"❌ Agent test failed: {e}")
    
    return True

async def interactive_test():
    """Interactive testing with the PM Agent."""
    print("\n🤖 Interactive PM Agent Test")
    print("=" * 40)
    print("Type 'exit' to quit")
    print()
    
    base_url = "http://localhost:8001/api/agent/process"
    session_id = f"interactive-{datetime.now().isoformat()}"
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                message = input("\n📝 You: ").strip()
                if message.lower() == 'exit':
                    break
                
                if not message:
                    continue
                
                print("\n⏳ Processing...")
                
                payload = {
                    "message": message,
                    "session_id": session_id
                }
                
                async with session.post(
                    base_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"\n🤖 Agent: {data.get('response', 'No response')}")
                        
                        if data.get('artifacts'):
                            print(f"\n📎 Artifacts created:")
                            for artifact in data['artifacts']:
                                print(f"   - {artifact['type']}: {artifact.get('data', {}).get('title', 'Untitled')}")
                    else:
                        print(f"\n❌ Error: {response.status}")
                        
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

async def main():
    """Main test function."""
    if await test_mcp_server():
        await interactive_test()

if __name__ == "__main__":
    print("🚀 Engineering Department - Backend Test")
    print("=" * 40)
    asyncio.run(main())
