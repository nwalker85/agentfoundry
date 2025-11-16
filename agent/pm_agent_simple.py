"""
Simplified PM Agent for testing - bypasses complex LangGraph flow
This is a temporary solution while fixing the recursion issue
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime


class SimplifiedPMAgent:
    """Simplified PM Agent that directly processes messages."""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url
        self.client = httpx.AsyncClient(
            base_url=mcp_base_url,
            headers={
                "Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN', 'dev-token')}"
            },
            timeout=30.0
        )
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message with simplified logic."""
        
        # Simple keyword extraction for testing
        message_lower = message.lower()
        
        # Default values
        epic_title = "Engineering Tasks"
        story_title = message[:100]  # Use message as title
        priority = "P2"
        description = message
        
        # Extract priority if mentioned
        if "p0" in message_lower or "critical" in message_lower or "urgent" in message_lower:
            priority = "P0"
        elif "p1" in message_lower or "high" in message_lower:
            priority = "P1"
        elif "p3" in message_lower or "low" in message_lower:
            priority = "P3"
        
        # Extract story type
        if "healthcheck" in message_lower or "health check" in message_lower:
            epic_title = "Infrastructure"
            story_title = "Add healthcheck endpoint"
            description = "Implement a healthcheck endpoint for monitoring"
        elif "authentication" in message_lower or "auth" in message_lower:
            epic_title = "Security"
            story_title = "Implement user authentication"
            description = "Add authentication system for users"
        elif "database" in message_lower or "db" in message_lower:
            epic_title = "Backend"
            story_title = "Database implementation task"
            description = message
        
        # Default AC and DoD
        acceptance_criteria = [
            "Functionality works as specified",
            "Unit tests pass",
            "No regression in existing features"
        ]
        
        definition_of_done = [
            "Code reviewed and approved",
            "Tests written and passing",
            "Documentation updated"
        ]
        
        try:
            # Try to create story in Notion
            story_response = await self.client.post(
                "/api/tools/notion/create-story",
                json={
                    "epic_title": epic_title,
                    "story_title": story_title,
                    "priority": priority,
                    "acceptance_criteria": acceptance_criteria,
                    "definition_of_done": definition_of_done,
                    "description": description
                }
            )
            story_response.raise_for_status()
            story_data = story_response.json()
            story_url = story_data.get("story_url", "")
            
            # Try to create GitHub issue
            issue_body = f"""## Description
{description}

## Acceptance Criteria
- [ ] Functionality works as specified
- [ ] Unit tests pass
- [ ] No regression in existing features

## Definition of Done
- [ ] Code reviewed and approved
- [ ] Tests written and passing
- [ ] Documentation updated

## Links
- [Notion Story]({story_url})
"""
            
            issue_response = await self.client.post(
                "/api/tools/github/create-issue",
                json={
                    "title": f"[{priority}] {story_title}",
                    "body": issue_body,
                    "labels": [f"priority/{priority}", "source/agent-pm"],
                    "story_url": story_url
                }
            )
            issue_response.raise_for_status()
            issue_data = issue_response.json()
            issue_url = issue_data.get("issue_url", "")
            
            # Success response
            response_text = f"""✅ Successfully created your story!

📝 **Story Details:**
- Epic: {epic_title}
- Title: {story_title}
- Priority: {priority}

🔗 **Links:**
- Notion: {story_url}
- GitHub: {issue_url}

The story has been added to the backlog and the team can now pick it up!"""
            
            return {
                "response": response_text,
                "status": "success",
                "state": "completed",
                "requires_clarification": False,
                "story_created": {
                    "url": story_url,
                    "title": story_title,
                    "epic": epic_title,
                    "priority": priority
                },
                "issue_created": {
                    "url": issue_url,
                    "title": story_title
                }
            }
            
        except Exception as e:
            # Error response
            return {
                "response": f"I encountered an error: {str(e)}. Let me try a simpler approach...",
                "status": "error",
                "state": "error",
                "error": str(e),
                "requires_clarification": False
            }
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Export as PMAgent for compatibility
PMAgent = SimplifiedPMAgent
