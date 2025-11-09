"""
Notion Integration Tools for PM Agent
Handles database setup and CRUD operations
"""

import os
from typing import Dict, List, Optional
from notion_client import Client
from datetime import datetime
from pm_agent.state import Task, Story, Epic, TaskStatus, TaskPriority, PMToolResult


class NotionPMTools:
    """Notion API wrapper for PM operations"""
    
    def __init__(self):
        self.client = Client(auth=os.getenv("NOTION_API_KEY"))
        self.teamspace_name = os.getenv("NOTION_TEAMSPACE", "Engineering Department")
        self._task_db_id: Optional[str] = None
        self._story_db_id: Optional[str] = None
        self._epic_db_id: Optional[str] = None
    
    async def initialize_databases(self) -> PMToolResult:
        """Create Notion databases if they don't exist"""
        try:
            search_results = self.client.search(
                query="Tasks",
                filter={"property": "object", "value": "database"}
            )
            
            if not search_results["results"]:
                print("No existing databases found. Please create them manually in Notion:")
                print("1. Create database: Tasks")
                print("2. Create database: Stories")
                print("3. Create database: Epics")
                return {
                    "success": False,
                    "data": None,
                    "error": "Databases not found - create manually in Notion",
                    "notion_id": None
                }
            else:
                for result in search_results["results"]:
                    title = result.get("title", [{}])[0].get("plain_text", "")
                    if "Tasks" in title:
                        self._task_db_id = result["id"]
                    elif "Stories" in title:
                        self._story_db_id = result["id"]
                    elif "Epics" in title:
                        self._epic_db_id = result["id"]
            
            return {
                "success": True,
                "data": {
                    "task_db": self._task_db_id,
                    "story_db": self._story_db_id,
                    "epic_db": self._epic_db_id
                },
                "error": None,
                "notion_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "notion_id": None
            }
    
    async def create_task(self, task: Task) -> PMToolResult:
        """Create a new task in Notion"""
        try:
            if not self._task_db_id:
                await self.initialize_databases()
            
            properties = {
                "Name": {"title": [{"text": {"content": task.title}}]},
                "Status": {"select": {"name": task.status.value}},
                "Priority": {"select": {"name": task.priority.value}},
                "Estimate (hrs)": {"number": task.estimate_hours}
            }
            
            if task.assigned_to:
                properties["Assigned To"] = {"rich_text": [{"text": {"content": task.assigned_to}}]}
            
            page = self.client.pages.create(
                parent={"database_id": self._task_db_id},
                properties=properties
            )
            
            return {
                "success": True,
                "data": {"task": task.title, "url": page["url"]},
                "error": None,
                "notion_id": page["id"]
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "notion_id": None
            }
    
    async def create_story(self, story: Story) -> PMToolResult:
        """Create a new story in Notion"""
        try:
            if not self._story_db_id:
                await self.initialize_databases()
            
            properties = {
                "Name": {"title": [{"text": {"content": story.title}}]},
                "User Story": {"rich_text": [{"text": {"content": story.user_story}}]},
                "Priority": {"select": {"name": story.priority.value}}
            }
            
            page = self.client.pages.create(
                parent={"database_id": self._story_db_id},
                properties=properties
            )
            
            return {
                "success": True,
                "data": {"story": story.title},
                "error": None,
                "notion_id": page["id"]
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "notion_id": None
            }
    
    async def create_epic(self, epic: Epic) -> PMToolResult:
        """Create a new epic in Notion"""
        try:
            if not self._epic_db_id:
                await self.initialize_databases()
            
            properties = {
                "Name": {"title": [{"text": {"content": epic.title}}]},
                "Description": {"rich_text": [{"text": {"content": epic.description}}]},
                "Business Value": {"rich_text": [{"text": {"content": epic.business_value}}]},
                "Priority": {"select": {"name": epic.priority.value}}
            }
            
            page = self.client.pages.create(
                parent={"database_id": self._epic_db_id},
                properties=properties
            )
            
            return {
                "success": True,
                "data": {"epic": epic.title},
                "error": None,
                "notion_id": page["id"]
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "notion_id": None
            }
    
    async def query_tasks(self, filters: Optional[Dict] = None) -> PMToolResult:
        """Query tasks"""
        try:
            if not self._task_db_id:
                await self.initialize_databases()
            
            query_params = {"database_id": self._task_db_id}
            if filters:
                query_params["filter"] = filters
            
            results = self.client.databases.query(**query_params)
            
            tasks = []
            for page in results["results"]:
                props = page["properties"]
                tasks.append({
                    "id": page["id"],
                    "title": props["Name"]["title"][0]["plain_text"] if props["Name"]["title"] else "",
                    "status": props["Status"]["select"]["name"] if props["Status"]["select"] else "",
                    "priority": props["Priority"]["select"]["name"] if props["Priority"]["select"] else ""
                })
            
            return {
                "success": True,
                "data": tasks,
                "error": None,
                "notion_id": None
            }
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "notion_id": None
            }


_notion_tools = None

def get_notion_tools() -> NotionPMTools:
    """Get singleton instance of Notion tools"""
    global _notion_tools
    if _notion_tools is None:
        _notion_tools = NotionPMTools()
    return _notion_tools
