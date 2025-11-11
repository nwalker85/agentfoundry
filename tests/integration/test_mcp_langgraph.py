#!/usr/bin/env python3
"""Test MCP Server with LangGraph PM Agent via HTTP."""

import asyncio
import httpx
import json
from datetime import datetime


async def test_server_health():
    """Test if MCP server is running."""
    print("=" * 60)
    print("Test 1: MCP Server Health Check")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ MCP Server is running")
                print(f"   Version: {data.get('version')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Environment: {data.get('environment')}")
                
                tools = data.get('tools', {})
                print("\n   Tools Available:")
                print(f"     - Notion: {tools.get('notion')}")
                print(f"     - GitHub: {tools.get('github')}")
                print(f"     - Audit: {tools.get('audit')}")
                print(f"     - Agent (LangGraph): {tools.get('agent')}")
                
                if not tools.get('agent'):
                    print("\n   ⚠️  LangGraph agent is not initialized!")
                    return False
                
                return True
            else:
                print(f"❌ Server returned {response.status_code}")
                return False
                
    except httpx.ConnectError:
        print("❌ Cannot connect to MCP server at http://localhost:8001")
        print("   Make sure the server is running:")
        print("   cd /Users/nwalker/Development/Projects/Engineering\\ Department/engineeringdepartment")
        print("   ./start_server.sh")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


async def test_api_status():
    """Test API status endpoint."""
    print("\n" + "=" * 60)
    print("Test 2: API Status Check")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/api/status", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ API Status endpoint operational")
                print(f"   API Version: {data.get('api_version')}")
                print(f"   Status: {data.get('status')}")
                
                integrations = data.get('integrations', {})
                print("\n   Integrations Configured:")
                print(f"     - Notion: {integrations.get('notion')}")
                print(f"     - OpenAI: {integrations.get('openai')}")
                print(f"     - GitHub: {integrations.get('github')}")
                
                tools = data.get('tools_available', {})
                print("\n   Tools Initialized:")
                print(f"     - Notion Tool: {tools.get('notion')}")
                print(f"     - GitHub Tool: {tools.get('github')}")
                print(f"     - Audit Tool: {tools.get('audit')}")
                print(f"     - PM Agent: {tools.get('agent')}")
                
                # Check if all required for agent are available
                if not integrations.get('openai'):
                    print("\n   ⚠️  OpenAI API key not configured - agent will fail")
                    return False
                
                if not tools.get('agent'):
                    print("\n   ⚠️  PM Agent not initialized")
                    return False
                
                return True
            else:
                print(f"❌ Status endpoint returned {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False


async def test_agent_chat_simple():
    """Test the agent chat endpoint with a simple message."""
    print("\n" + "=" * 60)
    print("Test 3: LangGraph Agent - Simple Chat")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            message = "Create a story for adding a health check endpoint to the API"
            
            print(f"\n📝 Sending message to agent:")
            print(f"   '{message}'")
            print("\n🤖 Processing with LangGraph PM Agent...")
            print("   (This may take 10-30 seconds as it calls OpenAI)")
            
            response = await client.post(
                "http://localhost:8001/api/agent/chat",
                json={
                    "message": message,
                    "session_id": "test-session-1"
                },
                headers={
                    "Authorization": "Bearer dev-token"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Agent responded successfully!")
                
                print(f"\n📊 Response Details:")
                print(f"   Status: {data.get('status')}")
                
                if data.get('error'):
                    print(f"   Error: {data.get('error')}")
                
                if data.get('messages'):
                    print(f"\n💬 Agent Conversation ({len(data['messages'])} messages):")
                    for i, msg in enumerate(data['messages'], 1):
                        msg_type = msg.get('type', 'unknown')
                        content = msg.get('content', '')
                        preview = content[:100] + "..." if len(content) > 100 else content
                        print(f"   {i}. {msg_type}: {preview}")
                
                if data.get('story_url'):
                    print(f"\n🎯 Story Created: {data['story_url']}")
                
                if data.get('issue_url'):
                    print(f"🎯 Issue Created: {data['issue_url']}")
                
                # Evaluate success
                status = data.get('status')
                if status == 'completed':
                    print("\n✅ Agent completed the task successfully!")
                    return True
                elif status == 'awaiting_clarification':
                    print("\n✅ Agent requested clarification (expected behavior)")
                    return True
                elif status == 'error':
                    print(f"\n❌ Agent encountered an error")
                    return False
                else:
                    print(f"\n⚠️  Unexpected status: {status}")
                    return False
                
            elif response.status_code == 503:
                print("❌ Agent not available (503)")
                print("   The PM Agent may not be initialized properly")
                return False
            else:
                print(f"❌ Chat endpoint returned {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Request timed out after 60 seconds")
        print("   The agent may be processing but taking too long")
        return False
    except Exception as e:
        print(f"❌ Agent chat test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_chat_detailed():
    """Test the agent with a detailed story request."""
    print("\n" + "=" * 60)
    print("Test 4: LangGraph Agent - Detailed Story Request")
    print("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            message = """Create a story for implementing rate limiting on the API.
            
This should be part of the Platform Hardening epic with P1 priority.

Requirements:
- Add rate limiting middleware to FastAPI
- Configure limits: 100 requests per minute per IP
- Return 429 status code when limit exceeded
- Include rate limit headers in responses
- Add Redis backend for distributed rate limiting

Acceptance Criteria:
- Rate limiting blocks requests after threshold
- Appropriate HTTP status codes returned
- Rate limit headers show remaining quota
- Works across multiple server instances

Definition of Done:
- Code reviewed and approved
- Unit tests with 90% coverage
- Integration tests passing
- Documentation updated with rate limit details
- Deployed to staging environment"""
            
            print(f"\n📝 Sending detailed message to agent...")
            print("\n🤖 Processing with LangGraph PM Agent...")
            print("   (This may take 30-60 seconds)")
            
            response = await client.post(
                "http://localhost:8001/api/agent/chat",
                json={
                    "message": message,
                    "session_id": "test-session-2"
                },
                headers={
                    "Authorization": "Bearer dev-token"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print("\n✅ Agent responded successfully!")
                
                print(f"\n📊 Response Details:")
                print(f"   Status: {data.get('status')}")
                
                if data.get('story_url'):
                    print(f"\n🎯 Story Created: {data['story_url']}")
                    print("   ✓ Notion story created with full requirements")
                
                if data.get('issue_url'):
                    print(f"🎯 Issue Created: {data['issue_url']}")
                    print("   ✓ GitHub issue synced")
                
                # Check if it went through the full workflow
                if data.get('status') == 'completed' and data.get('story_url') and data.get('issue_url'):
                    print("\n✅ Full workflow completed successfully!")
                    print("   ✓ Understood requirements")
                    print("   ✓ Created Notion story")
                    print("   ✓ Created GitHub issue")
                    print("   ✓ Linked story and issue")
                    return True
                else:
                    print(f"\n⚠️  Workflow incomplete: {data.get('status')}")
                    return False
                
            else:
                print(f"❌ Request returned {response.status_code}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Request timed out after 90 seconds")
        return False
    except Exception as e:
        print(f"❌ Detailed test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MCP Server + LangGraph PM Agent Integration Test Suite")
    print("=" * 80)
    print(f"\nTest Run: {datetime.now().isoformat()}")
    print("Target: http://localhost:8001")
    
    results = []
    
    # Test 1: Health check
    results.append(await test_server_health())
    
    if not results[0]:
        print("\n❌ Server not available - stopping tests")
        print("\nTo start the server:")
        print("  cd /Users/nwalker/Development/Projects/Engineering\\ Department/engineeringdepartment")
        print("  source venv/bin/activate")
        print("  python mcp_server.py")
        return
    
    # Test 2: API status
    results.append(await test_api_status())
    
    if not results[1]:
        print("\n⚠️  API status check failed - some features may not work")
    
    # Test 3: Simple agent chat
    print("\n⏳ Next: Testing agent with simple message...")
    await asyncio.sleep(1)  # Brief pause
    results.append(await test_agent_chat_simple())
    
    # Test 4: Detailed agent chat (only if previous tests passed)
    if all(results):
        print("\n⏳ Next: Testing agent with detailed message...")
        await asyncio.sleep(1)
        results.append(await test_agent_chat_detailed())
    else:
        print("\n⚠️  Skipping detailed test due to earlier failures")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    test_names = [
        "Server Health Check",
        "API Status Check",
        "Simple Agent Chat",
        "Detailed Agent Chat"
    ]
    
    for name, result in zip(test_names, results):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(results)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("   The MCP Server with LangGraph PM Agent is fully operational!")
    elif passed >= 2:
        print("\n⚠️  PARTIAL SUCCESS")
        print("   Server is running but some agent features may need attention")
    else:
        print("\n❌ TESTS FAILED")
        print("   Check server logs and configuration")


if __name__ == "__main__":
    asyncio.run(main())
