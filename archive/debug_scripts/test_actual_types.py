#!/usr/bin/env python3
"""Test Notion with actual field types from screenshots."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env.local")

from mcp.tools.notion import NotionTool
from mcp.schemas import CreateStoryRequest, Priority


async def test_actual_field_types():
    """Test with the actual field types from Notion screenshots."""
    
    print("=" * 60)
    print("TESTING WITH ACTUAL NOTION FIELD TYPES")
    print("=" * 60)
    print("\nField types from screenshots:")
    print("\nEPICS Database:")
    print("  • Title: title (Aa)")
    print("  • Business Value: select (⭕)")
    print("  • Created By: select (⭕)")
    print("  • Description: rich_text (≡)")
    print("  • Priority: rich_text (≡)")
    print("  • Status: select (⭕)")
    print("  • Target Quarter: rich_text (≡)")
    print("  • Technical Area: rich_text (≡)")
    
    print("\nSTORIES Database:")
    print("  • Title: title (Aa)")
    print("  • AI Generated: select (⭕)")
    print("  • Acceptance Criteria: rich_text (≡)")
    print("  • Assignee: rich_text (≡)")
    print("  • Description: rich_text (≡)")
    print("  • Epic: rich_text (≡) - NOT relation!")
    print("  • GitHub Issue: url (🔗)")
    print("  • GitHub PR: url (🔗)")
    print("  • Priority: select (⭕)")
    print("  • Sprint: select (⭕)")
    print("  • Status: rich_text (≡) - NOT select!")
    print("  • Story Points: number (#)")
    print("  • Technical Type: rich_text (≡) - NOT select!")
    print("  • User Story: rich_text (≡)")
    
    print("\n" + "=" * 60)
    
    notion = NotionTool()
    
    # Test Story Creation with correct field types
    print("\nTesting Story Creation with corrected field types...")
    
    try:
        request = CreateStoryRequest(
            epic_title="ERD Designer Development",
            story_title=f"Build ERD Designer - Test {datetime.now().strftime('%H%M%S')}",
            priority=Priority.P2,
            description="Create an ERD designer using ReactFlow library",
            acceptance_criteria=[
                "Users can drag and drop entities",
                "Users can create relationships",
                "Users can export diagrams"
            ],
            definition_of_done=[
                "Code reviewed",
                "Tests written",
                "Documentation updated"
            ]
        )
        
        response = await notion.create_story(request)
        print(f"✅ Story created successfully!")
        print(f"   Story URL: {response.story_url}")
        print(f"   Epic ID: {response.epic_id}")
        print(f"   Status: {response.status}")
        
        # Test listing stories
        print("\n\nTesting Story Listing...")
        from mcp.schemas import ListStoriesRequest
        
        list_request = ListStoriesRequest(limit=5)
        list_response = await notion.list_top_stories(list_request)
        
        print(f"✅ Listed {len(list_response.stories)} stories")
        for story in list_response.stories[:2]:
            print(f"   - {story.title}")
            print(f"     Epic: {story.epic_title}")
            print(f"     Status: {story.status}")
            print(f"     Priority: {story.priority}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        if hasattr(e, 'response'):
            try:
                error_detail = e.response.json()
                print(f"\nError details: {error_detail}")
            except:
                print(f"\nResponse: {e.response.text}")
    
    await notion.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_actual_field_types())
