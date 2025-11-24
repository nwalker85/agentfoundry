"""Notion MCP Tool Implementation with Enhanced Schema Support."""

import json
import os
from datetime import datetime

import httpx

from mcp.schemas import (
    CreateStoryRequest,
    CreateStoryResponse,
    ListStoriesRequest,
    ListStoriesResponse,
    Priority,
    StoryItem,
    StoryStatus,
)


class NotionTool:
    """Notion integration tool for story and epic management."""

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
                "Content-Type": "application/json",
            },
        )

        # In-memory idempotency cache (production would use Redis)
        self.idempotency_cache: dict[str, CreateStoryResponse] = {}

    async def create_story(self, request: CreateStoryRequest) -> CreateStoryResponse:
        """Create a story in Notion with idempotency protection."""

        # Check idempotency
        idempotency_key = request.idempotency_key()
        if idempotency_key in self.idempotency_cache:
            return self.idempotency_cache[idempotency_key]

        # Find or create the epic
        epic_id = await self._find_or_create_epic(request.epic_title)

        # Build story properties matching the ACTUAL schema from screenshots
        properties = {
            "Title": {"title": [{"text": {"content": request.story_title}}]},
            "Priority": {
                "select": {"name": request.priority.value}  # This is correct - select
            },
            "Status": {
                "rich_text": [{"text": {"content": "Ready"}}]  # Changed to rich_text
            },
            "Technical Type": {
                "rich_text": [
                    {"text": {"content": self._determine_technical_type(request.story_title, request.description)}}
                ]  # Changed to rich_text
            },
            "AI Generated": {
                "select": {"name": "TRUE"}  # Changed to select from checkbox
            },
            "Sprint": {
                "select": {"name": "Backlog"}  # This is correct - select
            },
            "Story Points": {"number": self._estimate_story_points(request)},
        }

        # Add the epic as text field (not relation)
        if epic_id:
            # Since Epic is a text field, we'll store the epic title
            epic_title = request.epic_title or "No Epic"
            properties["Epic"] = {
                "rich_text": [{"text": {"content": epic_title}}]  # Changed to rich_text
            }

        # Format User Story in standard format
        user_story = self._format_user_story(request)
        if user_story:
            properties["User Story"] = {"rich_text": [{"text": {"content": user_story[:2000]}}]}

        # Add description
        if request.description:
            properties["Description"] = {"rich_text": [{"text": {"content": request.description[:2000]}}]}

        # Format acceptance criteria
        if request.acceptance_criteria:
            ac_content = "\n".join(f"• {ac}" for ac in request.acceptance_criteria)
            properties["Acceptance Criteria"] = {"rich_text": [{"text": {"content": ac_content[:2000]}}]}

        # GitHub fields - Don't set initially, will be updated later
        # Note: Notion doesn't accept null URLs, so we omit these fields

        # Assignee - initially unassigned for AI-generated stories
        properties["Assignee"] = {"rich_text": [{"text": {"content": ""}}]}

        # Create the story
        try:
            response = await self.client.post(
                "/pages",
                json={
                    "parent": {"database_id": self.stories_db_id},
                    "properties": properties,
                    "children": self._build_story_content(request),
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[NotionTool] Error creating story: {e.response.status_code}")
            print(f"[NotionTool] Error response: {e.response.text}")
            print(f"[NotionTool] Request properties: {json.dumps(properties, indent=2)}")
            raise
        data = response.json()

        # Build response
        story_response = CreateStoryResponse(
            story_id=data["id"],
            story_url=data["url"],
            epic_id=epic_id,
            idempotency_key=idempotency_key,
            created_at=datetime.fromisoformat(data["created_time"].replace("Z", "+00:00")),
            status=StoryStatus.READY,  # Maps to Ready status
        )

        # Cache for idempotency
        self.idempotency_cache[idempotency_key] = story_response

        return story_response

    async def list_top_stories(self, request: ListStoriesRequest) -> ListStoriesResponse:
        """List top stories from Notion with filtering."""

        # Build filter
        filter_conditions = []

        if request.priorities and len(request.priorities) > 0:
            priority_filters = [{"property": "Priority", "select": {"equals": p.value}} for p in request.priorities]
            if len(priority_filters) == 1:
                filter_conditions.append(priority_filters[0])
            else:
                filter_conditions.append({"or": priority_filters})

        if request.status and len(request.status) > 0:
            # Map StoryStatus enum to actual Notion status values
            # Status is now rich_text, so we use rich_text filter
            status_mapping = {
                StoryStatus.BACKLOG: "Backlog",
                StoryStatus.READY: "Ready",
                StoryStatus.IN_PROGRESS: "In Progress",
                StoryStatus.IN_REVIEW: "In Review",
                StoryStatus.DONE: "Done",
            }
            status_filters = [
                {"property": "Status", "rich_text": {"equals": status_mapping.get(s, s.value)}} for s in request.status
            ]
            if len(status_filters) == 1:
                filter_conditions.append(status_filters[0])
            else:
                filter_conditions.append({"or": status_filters})

        filter_obj = None
        if filter_conditions:
            if len(filter_conditions) == 1:
                filter_obj = filter_conditions[0]
            else:
                filter_obj = {"and": filter_conditions}

        # Build query payload
        query_payload = {
            "page_size": request.limit,
            "sorts": [
                {"property": "Priority", "direction": "ascending"},
                {"timestamp": "created_time", "direction": "descending"},
            ],
        }

        # Only add filter if we have one
        if filter_obj is not None:
            query_payload["filter"] = filter_obj

        print(f"[NotionTool] Query payload: {json.dumps(query_payload, indent=2)}")

        # Query database
        response = await self.client.post(f"/databases/{self.stories_db_id}/query", json=query_payload)

        if response.status_code != 200:
            print(f"[NotionTool] Notion API error: {response.status_code}")
            print(f"[NotionTool] Response: {response.text}")

        response.raise_for_status()
        data = response.json()

        # Parse results
        stories = []
        for page in data["results"]:
            props = page["properties"]

            # Map Notion status back to enum (Status is now rich_text)
            notion_status = self._extract_text(props.get("Status", {}))
            status_map = {
                "Backlog": StoryStatus.BACKLOG,
                "Ready": StoryStatus.READY,
                "In Progress": StoryStatus.IN_PROGRESS,
                "In Review": StoryStatus.IN_REVIEW,
                "Done": StoryStatus.DONE,
            }

            # Extract story data
            story = StoryItem(
                id=page["id"],
                title=self._extract_text(props.get("Title", {})),
                epic_title=self._extract_text(props.get("Epic", {})),  # Epic is now text field
                priority=Priority(props.get("Priority", {}).get("select", {}).get("name", "P3")),
                status=status_map.get(notion_status, StoryStatus.BACKLOG),
                url=page["url"],
                github_issue_url=self._extract_url(props.get("GitHub Issue", {})),
                created_at=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00")),
            )
            stories.append(story)

        return ListStoriesResponse(stories=stories, total_count=len(stories), has_more=data.get("has_more", False))

    async def _find_or_create_epic(self, title: str) -> str | None:
        """Find an existing epic or create a new one."""
        if not title:
            return None

        # First try to find existing epic
        epic_id = await self._find_epic_by_title(title)
        if epic_id:
            return epic_id

        # Create new epic if not found
        return await self._create_epic(title)

    async def _find_epic_by_title(self, title: str) -> str | None:
        """Find an epic by title."""
        if not self.epics_db_id:
            return None

        response = await self.client.post(
            f"/databases/{self.epics_db_id}/query",
            json={"filter": {"property": "Title", "title": {"equals": title}}, "page_size": 1},
        )

        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                return data["results"][0]["id"]
        return None

    async def _create_epic(self, title: str, description: str = "") -> str:
        """Create a new epic with full schema support."""
        if not self.epics_db_id:
            raise ValueError("NOTION_DATABASE_EPICS_ID not configured")

        # Determine priority based on title keywords
        priority = "P2"  # Default
        if any(word in title.lower() for word in ["auth", "security", "core", "api"]):
            priority = "P0"
        elif any(word in title.lower() for word in ["dashboard", "ui", "frontend"]):
            priority = "P1"

        # Determine technical area based on title
        tech_areas = []
        if "auth" in title.lower():
            tech_areas = ["Backend", "Security"]
        elif "api" in title.lower():
            tech_areas = ["Backend", "API", "Infrastructure"]
        elif "dashboard" in title.lower() or "frontend" in title.lower():
            tech_areas = ["Frontend", "Data"]
        elif "devops" in title.lower() or "deploy" in title.lower():
            tech_areas = ["DevOps", "Infrastructure"]
        else:
            tech_areas = ["Backend"]

        epic_properties = {
            "parent": {"database_id": self.epics_db_id},
            "properties": {
                "Title": {"title": [{"text": {"content": title}}]},
                "Description": {"rich_text": [{"text": {"content": description or f"Epic for {title}"}}]},
                "Status": {"select": {"name": "Active"}},
                "Priority": {
                    "rich_text": [{"text": {"content": priority}}]  # Changed from select to rich_text
                },
                "Target Quarter": {
                    "rich_text": [{"text": {"content": "Q1 2025"}}]  # Changed from select to rich_text
                },
                "Business Value": {"select": {"name": "High" if priority in ["P0", "P1"] else "Medium"}},
                "Technical Area": {"rich_text": [{"text": {"content": ",".join(tech_areas)}}]},
                "Created By": {
                    "select": {"name": "PM Agent"}  # Changed from rich_text to select
                },
            },
        }

        try:
            response = await self.client.post("/pages", json=epic_properties)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[NotionTool] Error creating epic: {e.response.status_code}")
            print(f"[NotionTool] Error response: {e.response.text}")
            print(f"[NotionTool] Request properties: {json.dumps(epic_properties, indent=2)}")
            raise
        return response.json()["id"]

    async def _get_epic_title(self, epic_relation: dict) -> str | None:
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

    def _determine_technical_type(self, title: str, description: str | None) -> str:
        """Determine technical type based on story content."""
        combined = f"{title} {description or ''}".lower()

        if any(word in combined for word in ["bug", "fix", "error", "issue", "problem"]):
            return "Bug Fix"
        elif any(word in combined for word in ["doc", "documentation", "readme", "guide"]):
            return "Documentation"
        elif any(word in combined for word in ["debt", "refactor", "cleanup", "optimize"]):
            return "Tech Debt"
        else:
            return "Feature"

    def _estimate_story_points(self, request: CreateStoryRequest) -> int:
        """Estimate story points based on request complexity."""
        points = 3  # Default

        # Adjust based on acceptance criteria count
        if request.acceptance_criteria:
            if len(request.acceptance_criteria) <= 2:
                points = 2
            elif len(request.acceptance_criteria) >= 5:
                points = 5
            elif len(request.acceptance_criteria) >= 7:
                points = 8

        # Adjust based on keywords
        if request.description:
            desc_lower = request.description.lower()
            if any(word in desc_lower for word in ["complex", "integrate", "migration", "refactor"]):
                points = max(points, 5)
            elif any(word in desc_lower for word in ["simple", "minor", "small", "quick"]):
                points = min(points, 2)

        return points

    def _format_user_story(self, request: CreateStoryRequest) -> str:
        """Format user story in standard format if not already formatted."""
        # Check if description already contains user story format
        if request.description and "as a" in request.description.lower():
            return request.description

        # Generate user story format
        if request.epic_title:
            if "auth" in request.epic_title.lower():
                return f"As a user, I want {request.story_title.lower()} so that my account is secure and accessible"
            elif "api" in request.epic_title.lower():
                return f"As a developer, I want {request.story_title.lower()} so that I can integrate with the system efficiently"
            elif "dashboard" in request.epic_title.lower() or "frontend" in request.epic_title.lower():
                return (
                    f"As a user, I want {request.story_title.lower()} so that I can monitor and understand the system"
                )
            elif "devops" in request.epic_title.lower():
                return f"As a developer, I want {request.story_title.lower()} so that deployments are reliable and efficient"

        # Default format
        return f"As a user, I want {request.story_title.lower()} so that I can achieve my goals"

    def _extract_text(self, prop: dict) -> str:
        """Extract text from Notion property."""
        if "title" in prop:
            return "".join(t["text"]["content"] for t in prop["title"])
        elif "rich_text" in prop:
            return "".join(t["text"]["content"] for t in prop["rich_text"])
        return ""

    def _extract_url(self, prop: dict) -> str | None:
        """Extract URL from Notion property."""
        if "url" in prop:
            return prop["url"]
        return None

    def _build_story_content(self, request: CreateStoryRequest) -> list[dict]:
        """Build story page content blocks."""
        blocks = []

        # Technical Details Section
        blocks.append(
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": [{"text": {"content": "Story Details"}}]},
            }
        )

        # Epic Context
        if request.epic_title:
            blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"Epic: {request.epic_title}"}}],
                        "icon": {"emoji": "🎯"},
                    },
                }
            )

        # Technical Implementation
        blocks.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "Technical Implementation"}}]},
            }
        )

        if request.description:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": request.description}}]},
                }
            )

        # Acceptance Criteria (formatted as checklist)
        if request.acceptance_criteria:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Acceptance Criteria"}}]},
                }
            )
            for ac in request.acceptance_criteria:
                blocks.append(
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {"rich_text": [{"text": {"content": ac}}], "checked": False},
                    }
                )

        # Definition of Done
        if request.definition_of_done:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "Definition of Done"}}]},
                }
            )
            for dod in request.definition_of_done:
                blocks.append(
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {"rich_text": [{"text": {"content": dod}}], "checked": False},
                    }
                )

        # Notes Section
        blocks.append(
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "Notes"}}]}}
        )
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "AI-generated story - review and refine as needed"}}]},
            }
        )

        return blocks

    async def update_story_github_url(self, story_id: str, github_url: str) -> None:
        """Update a story with its GitHub issue URL."""
        try:
            response = await self.client.patch(
                f"/pages/{story_id}", json={"properties": {"GitHub Issue": {"url": github_url}}}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"[NotionTool] Error updating story GitHub URL: {e.response.status_code}")
            print(f"[NotionTool] Error response: {e.response.text}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
