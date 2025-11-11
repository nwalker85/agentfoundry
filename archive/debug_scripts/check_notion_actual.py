#!/usr/bin/env python3
"""Quick diagnostic to see actual Notion database properties."""

import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")


async def check_actual_schema():
    """Check what properties actually exist in the databases."""
    
    api_token = os.getenv("NOTION_API_TOKEN")
    stories_db_id = os.getenv("NOTION_DATABASE_STORIES_ID")
    epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
    
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
        }
    )
    
    print("=" * 60)
    print("ACTUAL NOTION DATABASE SCHEMAS")
    print("=" * 60)
    
    # Check Epics Database
    print(f"\n🎯 EPICS DATABASE ({epics_db_id})")
    print("-" * 40)
    
    response = await client.get(f"https://api.notion.com/v1/databases/{epics_db_id}")
    if response.status_code == 200:
        data = response.json()
        properties = data.get("properties", {})
        
        print("Properties found:")
        for name, config in properties.items():
            prop_type = config.get("type")
            print(f"  • '{name}': {prop_type}")
            
            # Show options for select fields
            if prop_type == "select":
                options = config.get("select", {}).get("options", [])
                if options:
                    print(f"    Options: {[opt['name'] for opt in options]}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    # Check Stories Database
    print(f"\n📚 STORIES DATABASE ({stories_db_id})")
    print("-" * 40)
    
    response = await client.get(f"https://api.notion.com/v1/databases/{stories_db_id}")
    if response.status_code == 200:
        data = response.json()
        properties = data.get("properties", {})
        
        print("Properties found:")
        for name, config in properties.items():
            prop_type = config.get("type")
            print(f"  • '{name}': {prop_type}")
            
            # Show options for select fields
            if prop_type == "select":
                options = config.get("select", {}).get("options", [])
                if options:
                    print(f"    Options: {[opt['name'] for opt in options]}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    # Now test creating a minimal epic with the actual field names
    print("\n" + "=" * 60)
    print("TESTING EPIC CREATION")
    print("-" * 40)
    
    # Get the title field name (might be "Title" or "Name")
    response = await client.get(f"https://api.notion.com/v1/databases/{epics_db_id}")
    data = response.json()
    properties = data.get("properties", {})
    
    # Find the title property
    title_field = None
    for name, config in properties.items():
        if config.get("type") == "title":
            title_field = name
            break
    
    print(f"Title field identified: '{title_field}'")
    
    if title_field:
        # Create minimal epic
        epic_data = {
            "parent": {"database_id": epics_db_id},
            "properties": {
                title_field: {
                    "title": [{"text": {"content": "Test Epic - Diagnostic"}}]
                }
            }
        }
        
        print(f"\nCreating epic with minimal properties:")
        print(json.dumps(epic_data, indent=2))
        
        response = await client.post("https://api.notion.com/v1/pages", json=epic_data)
        
        if response.status_code == 200:
            print("✅ SUCCESS! Epic created with minimal fields")
            epic_id = response.json()["id"]
            print(f"Epic ID: {epic_id}")
            
            # Now try with additional fields
            print("\n" + "-" * 40)
            print("Testing with additional fields...")
            
            # Build properties based on what exists
            enhanced_props = {
                title_field: {
                    "title": [{"text": {"content": "Test Epic - Full Schema"}}]
                }
            }
            
            # Try adding other fields one by one
            test_fields = [
                ("Status", "select", "Active"),
                ("Priority", "select", "P1"),
                ("Description", "rich_text", "Test description"),
                ("Target Quarter", "select", "Q1 2025"),
                ("Business Value", "select", "High"),
                ("Technical Area", "rich_text", "Backend,API"),
                ("Created By", "rich_text", "PM Agent")
            ]
            
            for field_name, field_type, field_value in test_fields:
                if field_name in properties:
                    actual_type = properties[field_name].get("type")
                    print(f"  Adding {field_name} ({actual_type})...")
                    
                    if actual_type == "select":
                        enhanced_props[field_name] = {"select": {"name": field_value}}
                    elif actual_type == "rich_text":
                        enhanced_props[field_name] = {"rich_text": [{"text": {"content": field_value}}]}
                    elif actual_type == "multi_select":
                        values = field_value.split(",")
                        enhanced_props[field_name] = {"multi_select": [{"name": v.strip()} for v in values]}
            
            epic_data = {
                "parent": {"database_id": epics_db_id},
                "properties": enhanced_props
            }
            
            print(f"\nCreating epic with enhanced properties:")
            print(json.dumps(epic_data, indent=2))
            
            response = await client.post("https://api.notion.com/v1/pages", json=epic_data)
            
            if response.status_code == 200:
                print("✅ SUCCESS! Epic created with full schema")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"Response: {response.text}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    await client.aclose()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(check_actual_schema())
