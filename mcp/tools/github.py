"""GitHub MCP Tool Implementation."""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

from mcp.schemas import (
    CreateIssueRequest, CreateIssueResponse,
    Priority, AuditEntry
)


class GitHubTool:
    """GitHub integration tool for issue and PR management."""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPO")
        self.default_branch = os.getenv("GITHUB_DEFAULT_BRANCH", "main")
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not configured")
        if not self.repo:
            raise ValueError("GITHUB_REPO not configured")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )
        
        # Parse owner and repo name
        parts = self.repo.split("/")
        if len(parts) != 2:
            raise ValueError(f"GITHUB_REPO must be in format 'owner/repo', got: {self.repo}")
        self.owner, self.repo_name = parts
        
        # In-memory idempotency cache (production would use Redis)
        self.idempotency_cache: Dict[str, CreateIssueResponse] = {}
    
    async def create_issue(self, request: CreateIssueRequest) -> CreateIssueResponse:
        """Create a GitHub issue with idempotency protection."""
        
        # Check idempotency
        idempotency_key = request.idempotency_key()
        if idempotency_key in self.idempotency_cache:
            return self.idempotency_cache[idempotency_key]
        
        # Check if issue already exists with this idempotency key
        existing = await self._find_issue_by_idempotency_key(idempotency_key)
        if existing:
            return existing
        
        # Build issue body with metadata
        body_parts = [request.body]
        
        # Add metadata section
        body_parts.append("\n\n---\n")
        body_parts.append("<!-- Engineering Department Metadata - DO NOT EDIT")
        body_parts.append(f"idempotency_key: {idempotency_key}")
        if request.story_url:
            body_parts.append(f"notion_story: {request.story_url}")
        body_parts.append(f"created_by: engineering-department-agent")
        body_parts.append(f"created_at: {datetime.utcnow().isoformat()}")
        body_parts.append("-->")
        
        full_body = "\n".join(body_parts)
        
        # Add default labels if not provided
        labels = request.labels.copy()
        if "source/agent-pm" not in labels:
            labels.append("source/agent-pm")
        
        # Map priority to label if provided
        if "Priority: " in request.title:
            for priority in ["P0", "P1", "P2", "P3"]:
                if f"Priority: {priority}" in request.title:
                    labels.append(f"priority/{priority}")
                    break
        
        # Create the issue
        response = await self.client.post(
            f"/repos/{self.owner}/{self.repo_name}/issues",
            json={
                "title": request.title,
                "body": full_body,
                "labels": labels,
                "assignees": request.assignees if request.assignees else None,
                "milestone": await self._get_milestone_number(request.milestone) if request.milestone else None
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Build response
        issue_response = CreateIssueResponse(
            issue_number=data["number"],
            issue_url=data["html_url"],
            issue_id=str(data["id"]),
            idempotency_key=idempotency_key,
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        )
        
        # Cache for idempotency
        self.idempotency_cache[idempotency_key] = issue_response
        
        # If we have a Notion story URL, update it with the GitHub URL
        # (This would be done via the Notion tool in practice)
        
        return issue_response
    
    async def create_pr(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: Optional[str] = None,
        draft: bool = True,
        issue_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a pull request."""
        
        base = base_branch or self.default_branch
        
        # Build PR body
        pr_body = body
        if issue_number:
            pr_body += f"\n\nCloses #{issue_number}"
        
        response = await self.client.post(
            f"/repos/{self.owner}/{self.repo_name}/pulls",
            json={
                "title": title,
                "body": pr_body,
                "head": head_branch,
                "base": base,
                "draft": draft
            }
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "pr_number": data["number"],
            "pr_url": data["html_url"],
            "pr_id": str(data["id"]),
            "created_at": data["created_at"],
            "draft": data["draft"]
        }
    
    async def _find_issue_by_idempotency_key(self, key: str) -> Optional[CreateIssueResponse]:
        """Find an existing issue by idempotency key."""
        
        # Search for issues with the idempotency key in the body
        # GitHub search is limited, so we'll search for recent issues
        response = await self.client.get(
            f"/repos/{self.owner}/{self.repo_name}/issues",
            params={
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": 100
            }
        )
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        for issue in data:
            if f"idempotency_key: {key}" in issue.get("body", ""):
                return CreateIssueResponse(
                    issue_number=issue["number"],
                    issue_url=issue["html_url"],
                    issue_id=str(issue["id"]),
                    idempotency_key=key,
                    created_at=datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                )
        
        return None
    
    async def _get_milestone_number(self, title: str) -> Optional[int]:
        """Get milestone number by title."""
        
        response = await self.client.get(
            f"/repos/{self.owner}/{self.repo_name}/milestones",
            params={"state": "open"}
        )
        
        if response.status_code == 200:
            data = response.json()
            for milestone in data:
                if milestone["title"] == title:
                    return milestone["number"]
        
        # Create milestone if it doesn't exist
        create_response = await self.client.post(
            f"/repos/{self.owner}/{self.repo_name}/milestones",
            json={"title": title}
        )
        
        if create_response.status_code == 201:
            return create_response.json()["number"]
        
        return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
