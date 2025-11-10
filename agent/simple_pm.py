"""Simple PM Agent without LangGraph complexity."""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json
import re


class TaskState(Enum):
    """State of task processing."""
    UNDERSTANDING = "understanding"
    NEEDS_CLARIFICATION = "needs_clarification"
    PLANNING = "planning"
    CREATING_STORY = "creating_story"
    CREATING_ISSUE = "creating_issue"
    COMPLETED = "completed"
    ERROR = "error"


class SimplePMAgent:
    """Simplified PM Agent for story creation."""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8001"):
        self.mcp_base_url = mcp_base_url
        self.client = httpx.AsyncClient(
            base_url=mcp_base_url,
            headers={
                "Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN', 'dev-token')}"
            },
            timeout=30.0
        )
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message to create a story."""
        
        # Parse the message to extract story details
        task = self._parse_message(message)
        
        # Apply defaults if missing
        if not task.get("acceptance_criteria"):
            task["acceptance_criteria"] = [
                "Functionality works as specified",
                "Unit tests pass",
                "No regression in existing features"
            ]
        
        if not task.get("definition_of_done"):
            task["definition_of_done"] = [
                "Code reviewed and approved",
                "Tests written and passing",
                "Documentation updated",
                "No critical security vulnerabilities"
            ]
        
        response_messages = []
        story_url = None
        issue_url = None
        status = TaskState.PLANNING
        
        try:
            # Create story in Notion
            status = TaskState.CREATING_STORY
            response_messages.append("Creating story in Notion...")
            
            story_response = await self.client.post(
                "/api/tools/notion/create-story",
                json={
                    "epic_title": task["epic_title"],
                    "story_title": task["story_title"],
                    "priority": task["priority"],
                    "acceptance_criteria": task["acceptance_criteria"],
                    "definition_of_done": task["definition_of_done"],
                    "description": task.get("description", "")
                }
            )
            story_response.raise_for_status()
            story_data = story_response.json()
            story_url = story_data["story_url"]
            response_messages.append(f"✅ Story created: {story_url}")
            
            # Create GitHub issue
            status = TaskState.CREATING_ISSUE
            response_messages.append("Creating GitHub issue...")
            
            issue_body = self._build_issue_body(task, story_url)
            
            issue_response = await self.client.post(
                "/api/tools/github/create-issue",
                json={
                    "title": f"[{task['priority']}] {task['story_title']}",
                    "body": issue_body,
                    "labels": [f"priority/{task['priority']}", "source/agent-pm"],
                    "story_url": story_url
                }
            )
            issue_response.raise_for_status()
            issue_data = issue_response.json()
            issue_url = issue_data["issue_url"]
            response_messages.append(f"✅ Issue created: {issue_url}")
            
            status = TaskState.COMPLETED
            response_messages.append(f"\n✨ Story successfully created!\nNotion: {story_url}\nGitHub: {issue_url}")
            
        except Exception as e:
            status = TaskState.ERROR
            response_messages.append(f"❌ Error: {str(e)}")
        
        return {
            "messages": response_messages,
            "story_url": story_url,
            "issue_url": issue_url,
            "status": status.value,
            "task": task
        }
    
    def _parse_message(self, message: str) -> Dict[str, Any]:
        """Parse message to extract story details."""
        
        # Simple pattern matching for common phrases
        task = {
            "epic_title": None,
            "story_title": None,
            "priority": "P2",
            "description": None
        }
        
        # Extract epic
        epic_patterns = [
            r"(?:part of|in|under|for)(?: the)? ([A-Z][^.]*?) epic",
            r"epic[:\s]+([A-Z][^.]*?)(?:\.|,|$)"
        ]
        for pattern in epic_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                task["epic_title"] = match.group(1).strip()
                break
        
        # Extract story title
        title_patterns = [
            r"story (?:for|about|to|called) ([^.]+)",
            r"create (?:a )?(?:story for )?([^.]+)",
            r"add (?:a )?(?:story for )?([^.]+)"
        ]
        for pattern in title_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                task["story_title"] = match.group(1).strip()
                # Clean up title
                task["story_title"] = task["story_title"].replace(" to our service", "")
                task["story_title"] = task["story_title"].replace(" to the service", "")
                break
        
        # Extract priority
        priority_match = re.search(r"\b(P[0-3])\b", message)
        if priority_match:
            task["priority"] = priority_match.group(1)
        
        # Extract description (everything after "should")
        desc_match = re.search(r"(?:should|must|needs to) (.+)", message, re.IGNORECASE)
        if desc_match:
            task["description"] = desc_match.group(1).strip()
        
        # Default values if not found
        if not task["epic_title"]:
            task["epic_title"] = "General"
        if not task["story_title"]:
            task["story_title"] = "New Story"
        
        return task
    
    def _build_issue_body(self, task: Dict[str, Any], story_url: Optional[str]) -> str:
        """Build GitHub issue body."""
        parts = []
        
        if task.get("description"):
            parts.append(f"## Description\n{task['description']}\n")
        
        parts.append("## Acceptance Criteria")
        for ac in task["acceptance_criteria"]:
            parts.append(f"- [ ] {ac}")
        
        parts.append("\n## Definition of Done")
        for dod in task["definition_of_done"]:
            parts.append(f"- [ ] {dod}")
        
        if story_url:
            parts.append(f"\n## Links\n- [Notion Story]({story_url})")
        
        return "\n".join(parts)
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
