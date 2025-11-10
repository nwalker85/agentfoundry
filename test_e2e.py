#!/usr/bin/env python
"""Test script for E2E story creation flow."""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import httpx

# Load environment
load_dotenv('.env.local')


async def test_mcp_endpoints():
    """Test MCP server endpoints directly."""
    
    base_url = "http://localhost:8001"
    client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
    
    print("=" * 60)
    print("MCP Server E2E Test")
    print("=" * 60)
    
    try:
        # 1. Check server status
        print("\n1. Checking server status...")
        response = await client.get("/")
        response.raise_for_status()
        status = response.json()
        print(f"   Server version: {status['version']}")
        print(f"   Environment: {status['environment']}")
        print(f"   Tools available: {status.get('tools', 'not reported')}")
        
        # 2. Check API status
        print("\n2. Checking API status...")
        response = await client.get("/api/status")
        response.raise_for_status()
        api_status = response.json()
        print(f"   API version: {api_status['api_version']}")
        print(f"   Tools available: {api_status.get('tools_available', {})}")
        
        # Only proceed if tools are available
        if not api_status.get('tools_available', {}).get('notion'):
            print("\n   WARNING: Notion tool not available. Check NOTION_API_TOKEN")
            print("   Skipping Notion tests...")
            return
        
        # 3. Create a test story
        print("\n3. Creating test story in Notion...")
        story_request = {
            "epic_title": "Platform Hardening",
            "story_title": f"Add healthcheck endpoint - Test {datetime.now().strftime('%H:%M:%S')}",
            "priority": "P1",
            "description": "Add /health endpoint for service monitoring",
            "acceptance_criteria": [
                "Endpoint returns 200 OK when service is healthy",
                "Response includes service version and status",
                "Response time under 100ms"
            ],
            "definition_of_done": [
                "Code reviewed and approved",
                "Unit tests written with >80% coverage",
                "Integration tests passing",
                "Documentation updated",
                "No security vulnerabilities"
            ]
        }
        
        story_data = None
        try:
            response = await client.post(
                "/api/tools/notion/create-story",
                json=story_request
            )
            
            if response.status_code == 200:
                story_data = response.json()
                print(f"   SUCCESS: Story created")
                print(f"   Story ID: {story_data['story_id']}")
                print(f"   Story URL: {story_data['story_url']}")
                print(f"   Idempotency Key: {story_data['idempotency_key']}")
            else:
                print(f"   ERROR: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ERROR creating story: {str(e)}")
        
        # 4. Create GitHub issue (if story was created)
        if story_data and api_status.get('tools_available', {}).get('github'):
            print("\n4. Creating GitHub issue...")
            issue_request = {
                "title": f"[P1] {story_request['story_title']}",
                "body": f"""## Description
{story_request['description']}

## Acceptance Criteria
{chr(10).join(f'- [ ] {ac}' for ac in story_request['acceptance_criteria'])}

## Definition of Done  
{chr(10).join(f'- [ ] {dod}' for dod in story_request['definition_of_done'])}

## Links
- [Notion Story]({story_data['story_url']})
""",
                "labels": ["priority/P1", "source/agent-pm"],
                "story_url": story_data['story_url']
            }
            
            try:
                response = await client.post(
                    "/api/tools/github/create-issue",
                    json=issue_request
                )
                
                if response.status_code == 200:
                    issue_data = response.json()
                    print(f"   SUCCESS: Issue created")
                    print(f"   Issue Number: #{issue_data['issue_number']}")
                    print(f"   Issue URL: {issue_data['issue_url']}")
                    print(f"   Idempotency Key: {issue_data['idempotency_key']}")
                else:
                    print(f"   ERROR: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
            except Exception as e:
                print(f"   ERROR creating issue: {str(e)}")
        
        # 5. Test idempotency
        if story_data:
            print("\n5. Testing idempotency (should return same story)...")
            try:
                response = await client.post(
                    "/api/tools/notion/create-story",
                    json=story_request
                )
                if response.status_code == 200:
                    story_data2 = response.json()
                    if story_data2['story_id'] == story_data['story_id']:
                        print(f"   SUCCESS: Idempotency working - same story returned")
                    else:
                        print(f"   ERROR: Different story created!")
            except Exception as e:
                print(f"   ERROR testing idempotency: {str(e)}")
        
        # 6. List stories
        print("\n6. Listing top stories...")
        try:
            response = await client.post(
                "/api/tools/notion/list-stories",
                json={
                    "limit": 5,
                    "priorities": ["P0", "P1"]
                }
            )
            
            if response.status_code == 200:
                list_data = response.json()
                print(f"   Found {len(list_data['stories'])} stories:")
                for story in list_data['stories'][:3]:
                    print(f"   - [{story['priority']}] {story['title']}")
            else:
                print(f"   ERROR: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   ERROR listing stories: {str(e)}")
        
        # 7. Query audit log
        print("\n7. Checking audit log...")
        try:
            response = await client.get(
                "/api/tools/audit/query",
                params={"limit": 5, "tool": "notion"}
            )
            
            if response.status_code == 200:
                audit_data = response.json()
                print(f"   Found {audit_data['count']} audit entries")
                if audit_data['entries']:
                    entry = audit_data['entries'][0]
                    print(f"   Latest: {entry.get('action')} by {entry.get('actor')} - {entry.get('result')}")
            else:
                print(f"   ERROR: {response.status_code}")
        except Exception as e:
            print(f"   ERROR querying audit: {str(e)}")
        
        print("\n" + "=" * 60)
        print("MCP Server Test Complete!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("\nERROR: Cannot connect to MCP server at http://localhost:8001")
        print("Make sure the server is running: python mcp_server.py")
        print("Run this test in a separate terminal while the server is running.")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
    finally:
        await client.aclose()


async def test_simple_pm_agent():
    """Test the simplified PM agent."""
    
    print("\n" + "=" * 60)
    print("Simple PM Agent Test")
    print("=" * 60)
    
    from agent.simple_pm import SimplePMAgent
    
    try:
        agent = SimplePMAgent()
        
        # Test message
        message = """Create a story for adding a healthcheck endpoint to our service. 
        This should be part of the Platform Hardening epic with P1 priority.
        The endpoint should return service status and version."""
        
        print(f"\nProcessing: {message[:100]}...\n")
        
        result = await agent.process_message(message)
        
        print("Agent Response:")
        for msg in result["messages"]:
            print(f"  {msg}")
        
        print(f"\nStatus: {result['status']}")
        print(f"Parsed task: {result['task']}")
        
        if result.get("story_url"):
            print(f"Story URL: {result['story_url']}")
        if result.get("issue_url"):
            print(f"Issue URL: {result['issue_url']}")
        
        await agent.close()
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    
    print("\nMCP Server E2E Test Suite")
    print("=" * 60)
    print("Note: Make sure MCP server is running in another terminal!")
    print("Start it with: python mcp_server.py")
    print("=" * 60)
    
    # Test MCP endpoints
    await test_mcp_endpoints()
    
    # Test simple PM agent
    await test_simple_pm_agent()


if __name__ == "__main__":
    asyncio.run(main())
