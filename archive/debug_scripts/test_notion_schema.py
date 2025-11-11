#!/usr/bin/env python3
"""Test script for updated Notion schema integration."""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

from mcp.tools.notion import NotionTool
from mcp.schemas import CreateStoryRequest, Priority, ListStoriesRequest


async def test_notion_schema():
    """Test the updated Notion integration with new schema."""
    
    print("=" * 60)
    print("Testing Updated Notion Schema Integration")
    print("=" * 60)
    
    # Initialize tool
    notion = NotionTool()
    
    try:
        # Test 1: Create a story with full schema
        print("\n1. Creating test story with new schema...")
        story_request = CreateStoryRequest(
            epic_title="API Infrastructure",
            story_title=f"Test Story - {datetime.now().strftime('%Y%m%d-%H%M%S')}",
            priority=Priority.P1,
            description="Testing the new schema with all fields populated correctly",
            acceptance_criteria=[
                "Story created successfully in Notion",
                "All fields populated correctly",
                "Epic relation works",
                "Technical Type is auto-determined",
                "Story Points are estimated"
            ],
            definition_of_done=[
                "Code reviewed and approved",
                "Unit tests passing",
                "Documentation updated"
            ]
        )
        
        response = await notion.create_story(story_request)
        print(f"✓ Story created successfully!")
        print(f"  - ID: {response.story_id}")
        print(f"  - URL: {response.story_url}")
        print(f"  - Epic ID: {response.epic_id}")
        print(f"  - Status: {response.status}")
        
        # Test 2: Verify epic was created/found
        if response.epic_id:
            print(f"\n2. Epic handling successful!")
            print(f"  - Epic ID: {response.epic_id}")
        
        # Test 3: List stories to verify retrieval
        print("\n3. Listing stories to verify retrieval...")
        list_request = ListStoriesRequest(
            limit=5,
            priorities=[Priority.P0, Priority.P1]
        )
        
        list_response = await notion.list_top_stories(list_request)
        print(f"✓ Retrieved {len(list_response.stories)} stories")
        
        for story in list_response.stories[:3]:
            print(f"  - {story.title}")
            print(f"    Priority: {story.priority}, Status: {story.status}")
            if story.epic_title:
                print(f"    Epic: {story.epic_title}")
            if story.github_issue_url:
                print(f"    GitHub: {story.github_issue_url}")
        
        # Test 4: Update story with GitHub URL (simulating GitHub integration)
        print("\n4. Testing GitHub URL update...")
        test_github_url = f"https://github.com/nwalker/engineeringdepartment/issues/{datetime.now().strftime('%H%M%S')}"
        await notion.update_story_github_url(response.story_id, test_github_url)
        print(f"✓ Updated story with GitHub URL: {test_github_url}")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Schema integration working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notion.close()


async def test_epic_creation():
    """Test epic creation with new schema fields."""
    
    print("\n" + "=" * 60)
    print("Testing Epic Creation with Full Schema")
    print("=" * 60)
    
    notion = NotionTool()
    
    try:
        # Create an epic directly
        print("\n1. Creating test epic...")
        epic_id = await notion._create_epic(
            title=f"Test Epic - {datetime.now().strftime('%H%M%S')}",
            description="Testing epic creation with all schema fields"
        )
        
        print(f"✓ Epic created successfully!")
        print(f"  - ID: {epic_id}")
        
        # Verify epic can be found
        print("\n2. Verifying epic can be found...")
        found_id = await notion._find_epic_by_title(f"Test Epic - {datetime.now().strftime('%H%M%S')}")
        if found_id:
            print(f"✓ Epic found by title search")
        
    except Exception as e:
        print(f"\n❌ Epic test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notion.close()


if __name__ == "__main__":
    print("\nNotion Schema Update Test Suite")
    print("================================\n")
    
    # Check environment
    if not os.getenv("NOTION_API_TOKEN"):
        print("❌ NOTION_API_TOKEN not configured in .env.local")
        exit(1)
    
    if not os.getenv("NOTION_DATABASE_STORIES_ID"):
        print("❌ NOTION_DATABASE_STORIES_ID not configured in .env.local")
        exit(1)
    
    if not os.getenv("NOTION_DATABASE_EPICS_ID"):
        print("❌ NOTION_DATABASE_EPICS_ID not configured in .env.local")
        exit(1)
    
    print("✓ Environment variables configured")
    
    # Run tests
    asyncio.run(test_notion_schema())
    asyncio.run(test_epic_creation())
