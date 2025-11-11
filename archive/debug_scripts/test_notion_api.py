#!/usr/bin/env python3
"""
Test Notion API connection and inspect database schema
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv('.env.local')


async def test_notion_connection():
    """Test Notion API and get database schemas."""
    
    api_token = os.getenv("NOTION_API_TOKEN")
    stories_db_id = os.getenv("NOTION_DATABASE_STORIES_ID")
    epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
    
    print("=" * 60)
    print("Notion API Connection Test")
    print("=" * 60)
    print(f"\nAPI Token: {api_token[:20]}..." if api_token else "NOT SET")
    print(f"Stories DB ID: {stories_db_id}")
    print(f"Epics DB ID: {epics_db_id}")
    print()
    
    if not api_token:
        print("❌ NOTION_API_TOKEN not set!")
        return
    
    # Create client
    client = httpx.AsyncClient(
        base_url="https://api.notion.com/v1",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    )
    
    try:
        # Test Stories Database
        if stories_db_id:
            print(f"\n📚 Testing Stories Database ({stories_db_id})...")
            print("-" * 40)
            
            response = await client.get(f"/databases/{stories_db_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database Title: {data.get('title', [{}])[0].get('plain_text', 'Untitled')}")
                print(f"\nProperties:")
                
                properties = data.get('properties', {})
                for prop_name, prop_config in properties.items():
                    prop_type = prop_config.get('type', 'unknown')
                    print(f"  - {prop_name}: {prop_type}")
                    
                    # Show select options if available
                    if prop_type == 'select' and 'select' in prop_config:
                        options = prop_config['select'].get('options', [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
                    elif prop_type == 'multi_select' and 'multi_select' in prop_config:
                        options = prop_config['multi_select'].get('options', [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
        
        # Test Epics Database
        if epics_db_id:
            print(f"\n🎯 Testing Epics Database ({epics_db_id})...")
            print("-" * 40)
            
            response = await client.get(f"/databases/{epics_db_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Database Title: {data.get('title', [{}])[0].get('plain_text', 'Untitled')}")
                print(f"\nProperties:")
                
                properties = data.get('properties', {})
                for prop_name, prop_config in properties.items():
                    prop_type = prop_config.get('type', 'unknown')
                    print(f"  - {prop_name}: {prop_type}")
                    
                    # Show select options if available
                    if prop_type == 'select' and 'select' in prop_config:
                        options = prop_config['select'].get('options', [])
                        if options:
                            print(f"    Options: {', '.join(opt['name'] for opt in options)}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
        
        # Test creating a simple page (test write permissions)
        print("\n🔧 Testing Write Permissions...")
        print("-" * 40)
        
        if stories_db_id:
            test_page = {
                "parent": {"database_id": stories_db_id},
                "properties": {
                    "Name": {
                        "title": [{"text": {"content": "Test Story - Delete Me"}}]
                    }
                }
            }
            
            response = await client.post("/pages", json=test_page)
            if response.status_code == 200:
                page_data = response.json()
                page_id = page_data['id']
                print(f"✅ Successfully created test page (ID: {page_id})")
                
                # Archive the test page
                archive_response = await client.patch(
                    f"/pages/{page_id}",
                    json={"archived": True}
                )
                if archive_response.status_code == 200:
                    print("✅ Test page archived successfully")
            else:
                print(f"❌ Error creating test page: {response.status_code}")
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
                
    except Exception as e:
        print(f"\n❌ Exception: {e}")
    
    finally:
        await client.aclose()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_notion_connection())
