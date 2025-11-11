#!/usr/bin/env python3
"""
Direct test of Notion tool with real API
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from mcp.tools.notion import NotionTool
from mcp.schemas import CreateStoryRequest, Priority

# Load environment
load_dotenv('.env.local')


async def test_notion_tool():
    """Test the Notion tool directly."""
    
    print("=" * 60)
    print("Testing Notion Tool with Real API")
    print("=" * 60)
    
    # Check environment
    token = os.getenv("NOTION_API_TOKEN")
    stories_db = os.getenv("NOTION_DATABASE_STORIES_ID")
    
    print(f"\nEnvironment:")
    print(f"  Token: {'✅ Set' if token else '❌ Not set'}")
    print(f"  Stories DB: {stories_db if stories_db else '❌ Not set'}")
    
    if not token or not stories_db:
        print("\n❌ Missing required environment variables!")
        return
    
    # Initialize tool
    print("\n1. Initializing NotionTool...")
    try:
        tool = NotionTool()
        print("   ✅ Tool initialized")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    
    # Create test story
    print("\n2. Creating test story...")
    
    test_request = CreateStoryRequest(
        epic_title="Test Epic",
        story_title="Test Story from Direct API Test",
        priority=Priority.P2,
        acceptance_criteria=[
            "System should work",
            "No errors should occur",
            "Story should appear in Notion"
        ],
        definition_of_done=[
            "Code reviewed",
            "Tests pass",
            "Documentation updated"
        ],
        description="This is a test story created directly via the Notion API to verify the integration works correctly."
    )
    
    try:
        print(f"   Request: {test_request.story_title}")
        print(f"   Priority: {test_request.priority.value}")
        
        response = await tool.create_story(test_request)
        
        print(f"\n   ✅ Story created successfully!")
        print(f"   Story ID: {response.story_id}")
        print(f"   Story URL: {response.story_url}")
        print(f"   Status: {response.status.value}")
        
    except Exception as e:
        print(f"\n   ❌ Failed to create story: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await tool.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_notion_tool())
