"""Notion MCP Tool Implementation."""

import os
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

from mcp.schemas import (
    CreateStoryRequest, CreateStoryResponse,
    ListStoriesRequest, ListStoriesResponse, StoryItem,
    Priority, StoryStatus, AuditEntry
)


class NotionTool:
    """Notion integration tool for story management."""
    
    def __init__(self):
        self.api_token = os.getenv("NOTION_API_TOKEN")
        self.stories_db_id = os.getenv("NOTION_DATABASE_STORIES_ID")
        self.epics_db_id = os.getenv("NOTION_DATABASE_EPICS_ID")
        
        if not self.api_token:
            raise ValueError("NOTION_API_TOKEN not configured")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.notion.com/v1",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
        )
        
        # In-memory idempotency cache (production would use Redis)
        self.idempotency_cache: Dict[str, CreateStoryResponse] = {}
    
    async def create_story(self, request: CreateStoryRequest) -> CreateStoryResponse:
        """Create a story in Notion with idempotency protection."""
        
        # Check idempotency
        idempotency_key = request.idempotency_key()
        if idempotency_key in self.idempotency_cache:
            return self.idempotency_cache[idempotency_key]
        
        # First, find the epic by title
        epic_id = await self._find_epic_by_title(request.epic_title)
        if not epic_id:
            # Create epic if it doesn't exist
            epic_id = await self._create_epic(request.epic_title)
        
        # Build story properties
        properties = {
            "Name": {
                "title": [{"text": {"content": request.story_title}}]
            },
            "Priority": {
                "select": {"name": request.priority.value}
            },
            "Status": {
                "select": {"name": StoryStatus.BACKLOG.value}
            },
            "Epic": {
                "relation": [{"id": epic_id}] if epic_id else []
            }
        }
        
        # Add AC and DoD as rich text
        if request.acceptance_criteria:
            ac_content = "\n".join(f"• {ac}" for ac in request.acceptance_criteria)
            properties["Acceptance Criteria"] = {
                "rich_text": [{"text": {"content": ac_content[:2000]}}]
            }
        
        if request.definition_of_done:
            dod_content = "\n".join(f"• {dod}" for dod in request.definition_of_done)
            properties["Definition of Done"] = {
                "rich_text": [{"text": {"content": dod_content[:2000]}}]
            }
        
        # Add idempotency key as metadata
        properties["Idempotency Key"] = {
            "rich_text": [{"text": {"content": idempotency_key}}]
        }
        
        # Create the story
        response = await self.client.post(
            "/pages",
            json={
                "parent": {"database_id": self.stories_db_id},
                "properties": properties,
                "children": self._build_story_content(request)
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Build response
        story_response = CreateStoryResponse(
            story_id=data["id"],
            story_url=data["url"],
            epic_id=epic_id,
            idempotency_key=idempotency_key,
            created_at=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
            status=StoryStatus.BACKLOG
        )
        
        # Cache for idempotency
        self.idempotency_cache[idempotency_key] = story_response
        
        return story_response
    
    async def list_top_stories(self, request: ListStoriesRequest) -> ListStoriesResponse:
        """List top stories from Notion with filtering."""
        
        # Build filter
        filter_conditions = []
        
        if request.priorities:
            filter_conditions.append({
                "or": [
                    {"property": "Priority", "select": {"equals": p.value}}
                    for p in request.priorities
                ]
            })
        
        if request.status:
            filter_conditions.append({
                "or": [
                    {"property": "Status", "select": {"equals": s.value}}
                    for s in request.status
                ]
            })
        
        filter_obj = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                filter_obj = filter_conditions[0]
            else:
                filter_obj = {"and": filter_conditions}
        
        # Query database
        response = await self.client.post(
            f"/databases/{self.stories_db_id}/query",
            json={
                "filter": filter_obj,
                "page_size": request.limit,
                "sorts": [
                    {"property": "Priority", "direction": "ascending"},
                    {"timestamp": "created_time", "direction": "descending"}
                ]
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Parse results
        stories = []
        for page in data["results"]:
            props = page["properties"]
            
            # Extract story data
            story = StoryItem(
                id=page["id"],
                title=self._extract_text(props.get("Name", {})),
                epic_title=await self._get_epic_title(props.get("Epic", {})),
                priority=Priority(props.get("Priority", {}).get("select", {}).get("name", "P3")),
                status=StoryStatus(props.get("Status", {}).get("select", {}).get("name", "Backlog")),
                url=page["url"],
                github_issue_url=self._extract_text(props.get("GitHub URL", {})),
                created_at=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00"))
            )
            stories.append(story)
        
        return ListStoriesResponse(
            stories=stories,
            total_count=len(stories),
            has_more=data.get("has_more", False)
        )
    
    async def _find_epic_by_title(self, title: str) -> Optional[str]:
        """Find an epic by title."""
        if not self.epics_db_id:
            return None
            
        response = await self.client.post(
            f"/databases/{self.epics_db_id}/query",
            json={
                "filter": {
                    "property": "Title",
                    "title": {"equals": title}
                },
                "page_size": 1
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return data["results"][0]["id"]
        return None
    
    async def _create_epic(self, title: str) -> str:
        """Create a new epic."""
        if not self.epics_db_id:
            raise ValueError("NOTION_DATABASE_EPICS_ID not configured")
            
        response = await self.client.post(
            "/pages",
            json={
                "parent": {"database_id": self.epics_db_id},
                "properties": {
                    "Title": {
                        "title": [{"text": {"content": title}}]
                    },
                    "Status": {
                        "select": {"name": "Active"}
                    },
                    "Priority": {
                        "select": {"name": "P1"}
                    }
                }
            }
        )
        response.raise_for_status()
        return response.json()["id"]
    
    async def _get_epic_title(self, epic_relation: Dict) -> Optional[str]:
        """Get epic title from relation."""
        if not epic_relation or "relation" not in epic_relation:
            return None
        
        relations = epic_relation["relation"]
        if not relations:
            return None
        
        # Get the first related epic
        epic_id = relations[0]["id"]
        response = await self.client.get(f"/pages/{epic_id}")
        
        if response.status_code == 200:
            data = response.json()
            return self._extract_text(data["properties"].get("Title", {}))
        return None
    
    def _extract_text(self, prop: Dict) -> str:
        """Extract text from Notion property."""
        if "title" in prop:
            return "".join(t["text"]["content"] for t in prop["title"])
        elif "rich_text" in prop:
            return "".join(t["text"]["content"] for t in prop["rich_text"])
        elif "url" in prop:
            return prop["url"]
        return ""
    
    def _build_story_content(self, request: CreateStoryRequest) -> List[Dict]:
        """Build story page content blocks."""
        blocks = []
        
        # Description
        if request.description:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Description"}}]
                }
            })
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": request.description}}]
                }
            })
        
        # Acceptance Criteria
        if request.acceptance_criteria:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Acceptance Criteria"}}]
                }
            })
            for ac in request.acceptance_criteria:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": ac}}]
                    }
                })
        
        # Definition of Done
        if request.definition_of_done:
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"text": {"content": "Definition of Done"}}]
                }
            })
            for dod in request.definition_of_done:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": dod}}]
                    }
                })
        
        # Metadata
        blocks.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
        blocks.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"text": {"content": f"Idempotency Key: {request.idempotency_key()}"}}],
                "icon": {"emoji": "🔑"}
            }
        })
        
        return blocks
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
