#!/usr/bin/env python3
"""Simple test to query existing data in Notion databases."""

import asyncio
import os
import httpx
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")


async def query_databases():
    """Query both databases to see what's there."""
    
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
    print("QUERYING NOTION DATABASES")
    print("=" * 60)
    
    # Query Epics
    print(f"\n📚 EPICS DATABASE")
    print("-" * 40)
    
    response = await client.post(
        f"https://api.notion.com/v1/databases/{epics_db_id}/query",
        json={"page_size": 2}
    )
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"Found {len(results)} epics")
        
        if results:
            print("\nFirst epic properties:")
            props = results[0].get("properties", {})
            for name, value in props.items():
                prop_type = value.get("type")
                print(f"  • {name} ({prop_type})")
                
                # Show actual values
                if prop_type == "title":
                    title_text = "".join([t["text"]["content"] for t in value.get("title", [])])
                    print(f"    Value: '{title_text}'")
                elif prop_type == "select":
                    select_val = value.get("select", {})
                    if select_val:
                        print(f"    Value: '{select_val.get('name')}'")
                elif prop_type == "rich_text":
                    text = "".join([t["text"]["content"] for t in value.get("rich_text", [])])
                    if text:
                        print(f"    Value: '{text[:50]}...'")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    # Query Stories
    print(f"\n📚 STORIES DATABASE")
    print("-" * 40)
    
    response = await client.post(
        f"https://api.notion.com/v1/databases/{stories_db_id}/query",
        json={"page_size": 2}
    )
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"Found {len(results)} stories")
        
        if results:
            print("\nFirst story properties:")
            props = results[0].get("properties", {})
            for name, value in props.items():
                prop_type = value.get("type")
                print(f"  • {name} ({prop_type})")
                
                # Show actual values
                if prop_type == "title":
                    title_text = "".join([t["text"]["content"] for t in value.get("title", [])])
                    print(f"    Value: '{title_text}'")
                elif prop_type == "select":
                    select_val = value.get("select", {})
                    if select_val:
                        print(f"    Value: '{select_val.get('name')}'")
                elif prop_type == "rich_text":
                    text = "".join([t["text"]["content"] for t in value.get("rich_text", [])])
                    if text:
                        print(f"    Value: '{text[:50]}...'")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
    
    await client.aclose()


if __name__ == "__main__":
    asyncio.run(query_databases())
