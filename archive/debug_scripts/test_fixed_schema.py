#!/usr/bin/env python3
"""Quick test to verify the fixed Notion schema."""

import asyncio
import os
import httpx
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv(".env.local")


async def test_fixed_schema():
    """Test creating entries with the fixed schema."""
    
    api_token = os.getenv("NOTION_API_TOKEN")
    stories_db_id = os.getenv("NOTION_DATABASE_STORIES_ID")
    epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    
    print("=" * 60)
    print("TESTING FIXED NOTION SCHEMA")
    print("=" * 60)
    
    # Test Epic Creation
    print("\n📚 Testing Epic Creation with Title field...")
    print("-" * 40)
    
    epic_data = {
        "parent": {"database_id": epics_db_id},
        "properties": {
            "Title": {
                "title": [{"text": {"content": f"Test Epic - {datetime.now().strftime('%H%M%S')}"}}]
            },
            "Status": {
                "select": {"name": "Active"}
            },
            "Priority": {
                "select": {"name": "P1"}
            },
            "Description": {
                "rich_text": [{"text": {"content": "Testing epic with fixed Title field"}}]
            }
        }
    }
    
    print("Creating epic with:")
    print(json.dumps(epic_data["properties"], indent=2))
    
    response = await client.post("https://api.notion.com/v1/pages", json=epic_data)
    
    if response.status_code == 200:
        print("✅ Epic created successfully!")
        epic_id = response.json()["id"]
        print(f"Epic ID: {epic_id}")
        
        # Test Story Creation
        print("\n📚 Testing Story Creation with Title field...")
        print("-" * 40)
        
        story_data = {
            "parent": {"database_id": stories_db_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": f"Test Story - {datetime.now().strftime('%H%M%S')}"}}]
                },
                "Epic": {
                    "relation": [{"id": epic_id}]
                },
                "Status": {
                    "select": {"name": "Ready"}
                },
                "Priority": {
                    "select": {"name": "P1"}
                },
                "User Story": {
                    "rich_text": [{"text": {"content": "As a user, I want to test the fixed schema"}}]
                },
                "Description": {
                    "rich_text": [{"text": {"content": "Testing story with fixed Title field and epic relation"}}]
                },
                "Acceptance Criteria": {
                    "rich_text": [{"text": {"content": "• Story created successfully\n• Epic relation works\n• All fields populated"}}]
                },
                "Technical Type": {
                    "select": {"name": "Feature"}
                },
                "AI Generated": {
                    "checkbox": True
                },
                "Story Points": {
                    "number": 3
                },
                "Sprint": {
                    "select": {"name": "Backlog"}
                }
            }
        }
        
        print("Creating story with:")
        print(json.dumps(story_data["properties"], indent=2))
        
        response = await client.post("https://api.notion.com/v1/pages", json=story_data)
        
        if response.status_code == 200:
            print("✅ Story created successfully!")
            story_id = response.json()["id"]
            story_url = response.json()["url"]
            print(f"Story ID: {story_id}")
            print(f"Story URL: {story_url}")
        else:
            print(f"❌ Story creation failed: {response.status_code}")
            print(f"Error: {response.text}")
    else:
        print(f"❌ Epic creation failed: {response.status_code}")
        print(f"Error: {response.text}")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_fixed_schema())
