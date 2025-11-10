"""Base models and schemas for MCP tools."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
import hashlib
import json
from enum import Enum


class Priority(str, Enum):
    """Task priority levels."""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class StoryStatus(str, Enum):
    """Story status states."""
    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    IN_QA = "In QA"
    DONE = "Done"


class CreateStoryRequest(BaseModel):
    """Request schema for creating a Notion story."""
    epic_title: str = Field(..., description="Title of the parent epic")
    story_title: str = Field(..., description="Title of the story")
    priority: Priority = Field(..., description="Story priority (P0-P3)")
    acceptance_criteria: List[str] = Field(
        default_factory=list, 
        description="List of acceptance criteria"
    )
    definition_of_done: List[str] = Field(
        default_factory=list,
        description="List of DoD items"
    )
    description: Optional[str] = Field(None, description="Story description")
    
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
    epic_id: Optional[str] = None
    idempotency_key: str
    created_at: datetime
    status: StoryStatus = StoryStatus.BACKLOG


class CreateIssueRequest(BaseModel):
    """Request schema for creating a GitHub issue."""
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body in Markdown")
    labels: List[str] = Field(
        default_factory=list,
        description="Issue labels"
    )
    assignees: List[str] = Field(
        default_factory=list,
        description="GitHub usernames to assign"
    )
    milestone: Optional[str] = Field(None, description="Milestone name")
    story_url: Optional[str] = Field(None, description="Related Notion story URL")
    
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
    priorities: Optional[List[Priority]] = Field(
        None,
        description="Filter by priorities"
    )
    status: Optional[List[StoryStatus]] = Field(
        None,
        description="Filter by status"
    )
    epic_title: Optional[str] = Field(None, description="Filter by epic")


class StoryItem(BaseModel):
    """Individual story item in list response."""
    id: str
    title: str
    epic_title: Optional[str]
    priority: Priority
    status: StoryStatus
    url: str
    github_issue_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ListStoriesResponse(BaseModel):
    """Response schema for story listing."""
    stories: List[StoryItem]
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
    output_hash: Optional[str] = None
    result: Literal["success", "failure", "partial"]
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format for audit log."""
        data = self.dict()
        data["timestamp"] = data["timestamp"].isoformat()
        return json.dumps(data)


class ToolResponse(BaseModel):
    """Generic tool response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    audit_entry: Optional[AuditEntry] = None
