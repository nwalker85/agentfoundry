"""
PM Agent State Definitions
Focused subset for project management operations
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import add_messages
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    IN_REVIEW = "In Review"
    DONE = "Done"


class TaskPriority(str, Enum):
    """Priority levels"""
    CRITICAL = "P0"
    HIGH = "P1"
    MEDIUM = "P2"
    LOW = "P3"


class ResourceType(str, Enum):
    """Available engineering resources"""
    FASTMCP_ENGINEER = "fastmcp_engineer"
    STREAMLIT_ENGINEER = "streamlit_engineer"
    PYTHON_ENGINEER = "python_engineer"
    QA_FUNCTIONAL = "qa_functional"


@dataclass
class Task:
    """Individual work item for Notion"""
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assigned_to: str | None
    story_id: str | None
    dependencies: list[str]
    estimate_hours: float
    notion_id: str | None = None
    blocked_reason: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Story:
    """User story"""
    title: str
    description: str
    user_story: str
    acceptance_criteria: list[str]
    epic_id: str | None
    tasks: list[str]
    priority: TaskPriority
    notion_id: str | None = None
    story_points: int | None = None


@dataclass
class Epic:
    """Large body of work"""
    title: str
    description: str
    business_value: str
    success_metrics: list[str]
    stories: list[str]
    priority: TaskPriority
    notion_id: str | None = None
    target_date: datetime | None = None


class PMState(TypedDict):
    """PM Agent working state"""
    messages: Annotated[Sequence, add_messages]
    user_input: str
    operation: Literal["breakdown", "assign", "track", "report", "idle"]
    current_epic: Epic | None
    current_stories: list[Story]
    current_tasks: list[Task]
    available_resources: list[str]
    resource_capacity: dict[str, float]
    blockers: list[dict]
    overdue_tasks: list[str]
    dependencies_unmet: list[dict]
    needs_user_input: bool
    has_critical_blocker: bool
    current_sprint: str | None
    sprint_end_date: datetime | None


class PMToolResult(TypedDict):
    """Standardized tool execution result"""
    success: bool
    data: dict | list | None
    error: str | None
    notion_id: str | None
