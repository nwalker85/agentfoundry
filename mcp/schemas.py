"""Base models and schemas for MCP tools."""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, validator


class Priority(str, Enum):
    """Task priority levels."""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class StoryStatus(str, Enum):
    """Story status states matching Notion schema."""

    BACKLOG = "Backlog"
    READY = "Ready"  # Stories ready to start
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"


class CreateStoryRequest(BaseModel):
    """Request schema for creating a Notion story."""

    epic_title: str = Field(..., description="Title of the parent epic")
    story_title: str = Field(..., description="Title of the story")
    priority: Priority = Field(..., description="Story priority (P0-P3)")
    acceptance_criteria: list[str] = Field(default_factory=list, description="List of acceptance criteria")
    definition_of_done: list[str] = Field(default_factory=list, description="List of DoD items")
    description: str | None = Field(None, description="Story description")

    @validator("story_title")
    def validate_title(cls, v):
        if len(v) < 3:
            raise ValueError("Story title must be at least 3 characters")
        if len(v) > 200:
            raise ValueError("Story title must be less than 200 characters")
        return v

    def idempotency_key(self) -> str:
        """Generate idempotency key for this request."""
        data = f"{self.epic_title}:{self.story_title}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class CreateStoryResponse(BaseModel):
    """Response schema for story creation."""

    story_id: str
    story_url: str
    epic_id: str | None = None
    idempotency_key: str
    created_at: datetime
    status: StoryStatus = StoryStatus.BACKLOG


class CreateIssueRequest(BaseModel):
    """Request schema for creating a GitHub issue."""

    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body in Markdown")
    labels: list[str] = Field(default_factory=list, description="Issue labels")
    assignees: list[str] = Field(default_factory=list, description="GitHub usernames to assign")
    milestone: str | None = Field(None, description="Milestone name")
    story_url: str | None = Field(None, description="Related Notion story URL")

    def idempotency_key(self) -> str:
        """Generate idempotency key for this request."""
        data = f"{self.title}:{self.story_url or 'none'}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class CreateIssueResponse(BaseModel):
    """Response schema for issue creation."""

    issue_number: int
    issue_url: str
    issue_id: str
    idempotency_key: str
    created_at: datetime


class ListStoriesRequest(BaseModel):
    """Request schema for listing top stories."""

    limit: int = Field(default=10, ge=1, le=50, description="Number of stories to return")
    priorities: list[Priority] | None = Field(None, description="Filter by priorities")
    status: list[StoryStatus] | None = Field(None, description="Filter by status")
    epic_title: str | None = Field(None, description="Filter by epic")


class StoryItem(BaseModel):
    """Individual story item in list response."""

    id: str
    title: str
    epic_title: str | None
    priority: Priority
    status: StoryStatus
    url: str
    github_issue_url: str | None = None
    created_at: datetime
    updated_at: datetime


class ListStoriesResponse(BaseModel):
    """Response schema for story listing."""

    stories: list[StoryItem]
    total_count: int
    has_more: bool


class AuditEntry(BaseModel):
    """Audit log entry schema."""

    timestamp: datetime
    request_id: str
    actor: str
    tenant_id: str
    tool: str
    action: str
    input_hash: str
    output_hash: str | None = None
    result: Literal["success", "failure", "partial"]
    error: str | None = None
    duration_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Convert to JSONL format for audit log."""
        data = self.dict()
        data["timestamp"] = data["timestamp"].isoformat()
        return json.dumps(data)


class ToolResponse(BaseModel):
    """Generic tool response wrapper."""

    success: bool
    data: Any | None = None
    error: str | None = None
    audit_entry: AuditEntry | None = None
