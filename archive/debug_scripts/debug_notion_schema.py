#!/usr/bin/env python3
"""Debug script to understand Notion database schema."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")


async def inspect_database_schema():
    """Inspect the actual schema of Notion databases."""
    
    api_token = os.getenv("NOTION_API_TOKEN")
    stories_db_id = os.getenv("NOTION_DATABASE_STORIES_ID")
    epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
    
    if not api_token:
        print("❌ NOTION_API_TOKEN not configured")
        return
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    
    print("=" * 60)
    print("Notion Database Schema Inspector")
    print("=" * 60)
    
    # Inspect Stories Database
    if stories_db_id:
        print(f"\n📚 Stories Database: {stories_db_id}")
        print("-" * 40)
        
        try:
            response = await client.get(f"https://api.notion.com/v1/databases/{stories_db_id}")
            if response.status_code == 200:
                data = response.json()
                print("Properties:")
                for prop_name, prop_data in data.get("properties", {}).items():
                    prop_type = prop_data.get("type", "unknown")
                    print(f"  • {prop_name}: {prop_type}")
                    
                    # Show select options if applicable
                    if prop_type == "select" and "select" in prop_data:
                        options = prop_data["select"].get("options", [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
                    elif prop_type == "multi_select" and "multi_select" in prop_data:
                        options = prop_data["multi_select"].get("options", [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
            else:
                print(f"❌ Failed to fetch database: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Inspect Epics Database
    if epics_db_id:
        print(f"\n🎯 Epics Database: {epics_db_id}")
        print("-" * 40)
        
        try:
            response = await client.get(f"https://api.notion.com/v1/databases/{epics_db_id}")
            if response.status_code == 200:
                data = response.json()
                print("Properties:")
                for prop_name, prop_data in data.get("properties", {}).items():
                    prop_type = prop_data.get("type", "unknown")
                    print(f"  • {prop_name}: {prop_type}")
                    
                    # Show select options if applicable
                    if prop_type == "select" and "select" in prop_data:
                        options = prop_data["select"].get("options", [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
                    elif prop_type == "multi_select" and "multi_select" in prop_data:
                        options = prop_data["multi_select"].get("options", [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
            else:
                print(f"❌ Failed to fetch database: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    await client.aclose()
    
    print("\n" + "=" * 60)
    print("✅ Schema inspection complete")
    print("=" * 60)


async def test_minimal_epic():
    """Test creating an epic with minimal fields."""
    
    api_token = os.getenv("NOTION_API_TOKEN")
    epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
    
    if not api_token or not epics_db_id:
        print("❌ Environment not configured")
        return
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    
    print("\n" + "=" * 60)
    print("Testing Minimal Epic Creation")
    print("=" * 60)
    
    # Try with just a title
    minimal_epic = {
        "parent": {"database_id": epics_db_id},
        "properties": {
            "Name": {  # Try "Name" instead of "Title"
                "title": [{"text": {"content": "Test Epic - Minimal"}}]
            }
        }
    }
    
    print("\nTrying minimal epic with 'Name' field...")
    try:
        response = await client.post("https://api.notion.com/v1/pages", json=minimal_epic)
        if response.status_code == 200:
            print("✅ Success with 'Name' field!")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Try with "Title" field
    minimal_epic["properties"] = {
        "Title": {
            "title": [{"text": {"content": "Test Epic - Minimal"}}]
        }
    }
    
    print("\nTrying minimal epic with 'Title' field...")
    try:
        response = await client.post("https://api.notion.com/v1/pages", json=minimal_epic)
        if response.status_code == 200:
            print("✅ Success with 'Title' field!")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await client.aclose()


if __name__ == "__main__":
    print("\nNotion Database Schema Inspector")
    print("================================\n")
    
    # Run inspection
    asyncio.run(inspect_database_schema())
    asyncio.run(test_minimal_epic())
