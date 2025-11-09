#!/usr/bin/env python3
"""
Initialize Notion Databases for PM Agent
Creates the required databases with proper schemas
"""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_databases():
    """Create all required Notion databases with proper schemas"""
    
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    
    # Find the parent page (you may need to adjust this)
    # For now, we'll create at workspace level
    
    print("Creating Notion databases for PM Agent...")
    
    # 1. Create Tasks Database
    try:
        tasks_db = notion.databases.create(
            parent={"type": "page_id", "page_id": os.getenv("NOTION_PARENT_PAGE_ID", "YOUR_PAGE_ID_HERE")},
            title=[{"type": "text", "text": {"content": "Tasks"}}],
            properties={
                "Name": {"title": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Backlog", "color": "gray"},
                            {"name": "To Do", "color": "yellow"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Blocked", "color": "red"},
                            {"name": "In Review", "color": "purple"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "P0", "color": "red"},
                            {"name": "P1", "color": "orange"},
                            {"name": "P2", "color": "yellow"},
                            {"name": "P3", "color": "gray"}
                        ]
                    }
                },
                "Assigned To": {"rich_text": {}},
                "Story ID": {"rich_text": {}},
                "Estimate (hrs)": {"number": {"format": "number"}},
                "Blocked Reason": {"rich_text": {}},
                "Dependencies": {"rich_text": {}},
                "Created": {"created_time": {}},
                "Updated": {"last_edited_time": {}}
            }
        )
        print(f"✅ Created Tasks database: {tasks_db['id']}")
    except Exception as e:
        print(f"❌ Failed to create Tasks database: {e}")
    
    # 2. Create Stories Database
    try:
        stories_db = notion.databases.create(
            parent={"type": "page_id", "page_id": os.getenv("NOTION_PARENT_PAGE_ID", "YOUR_PAGE_ID_HERE")},
            title=[{"type": "text", "text": {"content": "Stories"}}],
            properties={
                "Name": {"title": {}},
                "User Story": {"rich_text": {}},
                "Description": {"rich_text": {}},
                "Acceptance Criteria": {"rich_text": {}},
                "Epic ID": {"rich_text": {}},
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "P0", "color": "red"},
                            {"name": "P1", "color": "orange"},
                            {"name": "P2", "color": "yellow"},
                            {"name": "P3", "color": "gray"}
                        ]
                    }
                },
                "Story Points": {"number": {"format": "number"}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Backlog", "color": "gray"},
                            {"name": "Ready", "color": "yellow"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"}
                        ]
                    }
                },
                "Created": {"created_time": {}},
                "Updated": {"last_edited_time": {}}
            }
        )
        print(f"✅ Created Stories database: {stories_db['id']}")
    except Exception as e:
        print(f"❌ Failed to create Stories database: {e}")
    
    # 3. Create Epics Database
    try:
        epics_db = notion.databases.create(
            parent={"type": "page_id", "page_id": os.getenv("NOTION_PARENT_PAGE_ID", "YOUR_PAGE_ID_HERE")},
            title=[{"type": "text", "text": {"content": "Epics"}}],
            properties={
                "Name": {"title": {}},
                "Description": {"rich_text": {}},
                "Business Value": {"rich_text": {}},
                "Success Metrics": {"rich_text": {}},
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "P0", "color": "red"},
                            {"name": "P1", "color": "orange"},
                            {"name": "P2", "color": "yellow"},
                            {"name": "P3", "color": "gray"}
                        ]
                    }
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "Planning", "color": "gray"},
                            {"name": "Active", "color": "blue"},
                            {"name": "On Hold", "color": "orange"},
                            {"name": "Completed", "color": "green"},
                            {"name": "Cancelled", "color": "red"}
                        ]
                    }
                },
                "Target Date": {"date": {}},
                "Created": {"created_time": {}},
                "Updated": {"last_edited_time": {}}
            }
        )
        print(f"✅ Created Epics database: {epics_db['id']}")
    except Exception as e:
        print(f"❌ Failed to create Epics database: {e}")
    
    print("\nDatabase creation complete!")
    print("\nNext steps:")
    print("1. Update your .env file with the database IDs")
    print("2. Test the PM Agent with a simple breakdown task")

if __name__ == "__main__":
    if not os.getenv("NOTION_API_KEY"):
        print("Error: NOTION_API_KEY not found in environment variables")
        print("Please add it to your .env file")
        sys.exit(1)
    
    if not os.getenv("NOTION_PARENT_PAGE_ID"):
        print("Warning: NOTION_PARENT_PAGE_ID not set")
        print("Please add the parent page ID to your .env file")
        print("You can find this in the URL of any Notion page where you want the databases")
        print("Example: https://www.notion.so/YOUR_WORKSPACE/PAGE_NAME/PAGE_ID_HERE")
        sys.exit(1)
    
    create_databases()
