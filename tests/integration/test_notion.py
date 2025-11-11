#!/usr/bin/env python3
"""Quick smoke test for Notion API integration."""

import os
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')


def test_notion_connection():
    """Test Notion API connection and database access."""
    print("Testing Notion API integration...")

    # Get credentials from environment
    notion_token = os.getenv('NOTION_API_TOKEN')
    stories_db_id = os.getenv('NOTION_DATABASE_STORIES_ID')
    epics_db_id = os.getenv('NOTION_DATABASE_EPICS_ID')

    if not notion_token:
        print("NOTION_API_TOKEN not found in environment")
        return False

    if not stories_db_id or not epics_db_id:
        print("Database IDs not found in environment")
        return False

    try:
        # Initialize Notion client
        notion = Client(auth=notion_token)
        print("Notion client initialized")

        # Test Stories database
        stories_response = notion.databases.query(
            database_id=stories_db_id,
            page_size=1,
        )
        print(
            "Stories database accessible "
            f"({len(stories_response['results'])} items)"
        )

        # Test Epics database
        epics_response = notion.databases.query(
            database_id=epics_db_id,
            page_size=1,
        )
        print(
            "Epics database accessible "
            f"({len(epics_response['results'])} items)"
        )

        print("All Notion API tests passed!")
        return True

    except Exception as e:
        print(f"Notion API test failed: {e}")
        return False


if __name__ == "__main__":
    test_notion_connection()
