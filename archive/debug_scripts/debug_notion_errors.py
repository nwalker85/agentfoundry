#!/usr/bin/env python3
"""Debug script to capture exact Notion API errors."""

import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(".env.local")

from mcp.tools.notion import NotionTool
from mcp.schemas import CreateStoryRequest, Priority


async def test_with_detailed_error():
    """Test story creation with detailed error capture."""
    
    print("=" * 60)
    print("TESTING NOTION STORY CREATION - DETAILED ERROR CAPTURE")
    print("=" * 60)
    
    notion = NotionTool()
    
    # Test data that was failing in the logs
    test_cases = [
        {
            "epic_title": "ERD Designer Development",
            "story_title": "Build ERD Designer using ReactFlow",
            "priority": Priority.P2,
            "description": "Create an Entity Relationship Diagram designer using ReactFlow library",
            "acceptance_criteria": [
                "Users can drag and drop entities",
                "Users can create relationships between entities", 
                "Users can export the diagram"
            ],
            "definition_of_done": [
                "Code reviewed",
                "Tests written",
                "Documentation updated",
                "Deployed to staging"
            ]
        },
        {
            "epic_title": "UI Development",
            "story_title": "Build an ERD Designer using ReactFlow",
            "priority": Priority.P2,
            "description": "Create a visual ERD designer component",
            "acceptance_criteria": [
                "Drag and drop entities",
                "Connect entities with relationships",
                "Save and load diagrams"
            ],
            "definition_of_done": [
                "Unit tests pass",
                "Integration tests pass", 
                "Code reviewed",
                "Documentation complete"
            ]
        }
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n{'='*40}")
        print(f"Test Case {i}: {test_data['story_title']}")
        print(f"Epic: {test_data['epic_title']}")
        print(f"{'='*40}")
        
        try:
            request = CreateStoryRequest(**test_data)
            
            print("\nAttempting to create story...")
            response = await notion.create_story(request)
            
            print(f"✅ SUCCESS!")
            print(f"   Story ID: {response.story_id}")
            print(f"   Story URL: {response.story_url}")
            print(f"   Epic ID: {response.epic_id}")
            print(f"   Status: {response.status}")
            
        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}")
            print(f"   Error: {str(e)}")
            
            # Try to get more details from the error
            if hasattr(e, 'response'):
                print(f"\n   Response Status: {e.response.status_code}")
                print(f"   Response Headers: {dict(e.response.headers)}")
                try:
                    error_detail = e.response.json()
                    print(f"   Response Body: {error_detail}")
                except:
                    print(f"   Response Text: {e.response.text}")
    
    await notion.close()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


async def test_minimal_story():
    """Test with absolute minimum fields."""
    
    print("\n" + "=" * 60)
    print("TESTING MINIMAL STORY CREATION")
    print("=" * 60)
    
    notion = NotionTool()
    
    # Test without epic first
    print("\nTest 1: Story without epic...")
    try:
        request = CreateStoryRequest(
            epic_title="",  # Empty epic
            story_title=f"Minimal Test Story - {datetime.now().strftime('%H%M%S')}",
            priority=Priority.P2
        )
        
        response = await notion.create_story(request)
        print(f"✅ SUCCESS without epic!")
        print(f"   Story URL: {response.story_url}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    # Test with epic
    print("\nTest 2: Story with epic...")
    try:
        request = CreateStoryRequest(
            epic_title="Test Epic",
            story_title=f"Test Story with Epic - {datetime.now().strftime('%H%M%S')}",
            priority=Priority.P1
        )
        
        response = await notion.create_story(request)
        print(f"✅ SUCCESS with epic!")
        print(f"   Story URL: {response.story_url}")
        print(f"   Epic ID: {response.epic_id}")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
    
    await notion.close()


if __name__ == "__main__":
    asyncio.run(test_with_detailed_error())
    asyncio.run(test_minimal_story())
