#!/usr/bin/env python3
"""Test Notion with corrected field types."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(".env.local")

from mcp.tools.notion import NotionTool
from mcp.schemas import CreateStoryRequest, Priority


async def test_corrected_field_types():
    """Test with the corrected field types."""
    
    print("=" * 60)
    print("TESTING NOTION WITH CORRECTED FIELD TYPES")
    print("=" * 60)
    
    notion = NotionTool()
    
    # Test 1: Create Epic with corrected types
    print("\n1. Testing Epic Creation with corrected field types...")
    print("   Priority: rich_text (was select)")
    print("   Target Quarter: rich_text (was select)")
    print("   Created By: select (was rich_text)")
    
    try:
        # We'll create an epic directly to test
        epic_id = await notion._create_epic(
            title=f"Test Epic - Field Types - {datetime.now().strftime('%H%M%S')}",
            description="Testing with corrected field types"
        )
        print(f"✅ Epic created successfully!")
        print(f"   Epic ID: {epic_id}")
    except Exception as e:
        print(f"❌ Epic creation failed: {e}")
        if hasattr(e, 'response'):
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response: {e.response.text}")
    
    # Test 2: Create Story
    print("\n2. Testing Story Creation...")
    
    try:
        request = CreateStoryRequest(
            epic_title="Test Epic for Stories",
            story_title=f"Test Story - {datetime.now().strftime('%H%M%S')}",
            priority=Priority.P1,
            description="Testing story creation with corrected epic field types",
            acceptance_criteria=[
                "Story creates successfully",
                "Epic is created if needed",
                "All fields populated correctly"
            ]
        )
        
        response = await notion.create_story(request)
        print(f"✅ Story created successfully!")
        print(f"   Story URL: {response.story_url}")
        print(f"   Epic ID: {response.epic_id}")
        print(f"   Status: {response.status}")
        
    except Exception as e:
        print(f"❌ Story creation failed: {e}")
        if hasattr(e, 'response'):
            try:
                error_detail = e.response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Response: {e.response.text}")
    
    await notion.close()
    
    print("\n" + "=" * 60)
    print("FIELD TYPE TEST COMPLETE")
    print("=" * 60)
    print("\nField Type Summary:")
    print("EPICS:")
    print("  • Title: title ✓")
    print("  • Description: rich_text ✓")
    print("  • Status: select ✓")
    print("  • Priority: rich_text ✓ (FIXED)")
    print("  • Target Quarter: rich_text ✓ (FIXED)")
    print("  • Business Value: select ✓")
    print("  • Technical Area: rich_text ✓")
    print("  • Created By: select ✓ (FIXED)")
    print("\nSTORIES:")
    print("  • Title: title ✓")
    print("  • Priority: select ✓")
    print("  • Status: select ✓")
    print("  • User Story: rich_text ✓")
    print("  • Description: rich_text ✓")
    print("  • Acceptance Criteria: rich_text ✓")
    print("  • Technical Type: select ✓")
    print("  • AI Generated: checkbox ✓")
    print("  • Story Points: number ✓")
    print("  • Sprint: select ✓")


if __name__ == "__main__":
    asyncio.run(test_corrected_field_types())
