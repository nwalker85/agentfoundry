#!/usr/bin/env python3
"""Quick script to check the actual field types in Notion databases."""

import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv(".env.local")


async def check_field_types():
    """Get the exact field types from Notion."""
    
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
    print("NOTION DATABASE FIELD TYPES")
    print("=" * 60)
    
    # Check Epics Database
    print(f"\n🎯 EPICS DATABASE")
    print("-" * 40)
    
    response = await client.get(f"https://api.notion.com/v1/databases/{epics_db_id}")
    if response.status_code == 200:
        data = response.json()
        properties = data.get("properties", {})
        
        print("\nField Types:")
        for name, config in sorted(properties.items()):
            prop_type = config.get("type")
            print(f"  • {name}: {prop_type}")
            
            # Show select options
            if prop_type == "select":
                options = config.get("select", {}).get("options", [])
                if options:
                    print(f"    Options: {', '.join([opt['name'] for opt in options])}")
    
    # Check Stories Database  
    print(f"\n📚 STORIES DATABASE")
    print("-" * 40)
    
    response = await client.get(f"https://api.notion.com/v1/databases/{stories_db_id}")
    if response.status_code == 200:
        data = response.json()
        properties = data.get("properties", {})
        
        print("\nField Types:")
        for name, config in sorted(properties.items()):
            prop_type = config.get("type")
            print(f"  • {name}: {prop_type}")
            
            # Show select options
            if prop_type == "select":
                options = config.get("select", {}).get("options", [])
                if options:
                    print(f"    Options: {', '.join([opt['name'] for opt in options])}")
    
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(check_field_types())
