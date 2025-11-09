"""
Engineering Department - State Definitions
Software development workflow with proper SDLC
"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import add_messages
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    BACKLOG = "Backlog"
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    IN_QA = "In QA"
    QA_FAILED = "QA Failed"
    BLOCKED = "Blocked"
    DONE = "Done"
    CANCELLED = "Cancelled"


class TaskPriority(str, Enum):
    """Priority levels - numeric for easy comparison"""
    CRITICAL = "P0 - Critical"      # Production down, security issue
    HIGH = "P1 - High"              # Major feature, important bug
    MEDIUM = "P2 - Medium"          # Standard work
    LOW = "P3 - Low"                # Nice to have
    
    @property
    def value_numeric(self) -> int:
        return {"P0 - Critical": 0, "P1 - High": 1, "P2 - Medium": 2, "P3 - Low": 3}[self.value]


class TaskType(str, Enum):
    """Work item types"""
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    SPIKE = "Spike"          # Research/investigation
    TECH_DEBT = "Tech Debt"


class AgentRole(str, Enum):
    """Engineering department roles"""
    # Management
    PRODUCT_OWNER = "product_owner"
    PROJECT_MANAGER = "project_manager"
    
    # Engineering
    FASTMCP_ENGINEER = "fastmcp_engineer"
    STREAMLIT_ENGINEER = "streamlit_engineer"
    TERRAFORM_ENGINEER = "terraform_engineer"
    GCP_ENGINEER = "gcp_engineer"
    PYTHON_ENGINEER = "python_engineer"
    REACTFLOW_ENGINEER = "reactflow_engineer"
    DNS_SSL_ENGINEER = "dns_ssl_engineer"
    
    # Architecture & Advisory
    ENTERPRISE_ARCHITECT = "enterprise_architect"
    SECURITY_ARCHITECT = "security_architect"
    UI_UX_DESIGNER = "ui_ux_designer"
    
    # Quality Assurance
    QA_FUNCTIONAL = "qa_functional"
    QA_SECURITY = "qa_security"
    QA_PERFORMANCE = "qa_performance"


@dataclass
class DefinitionOfDone:
    """Acceptance criteria and validation requirements"""
    acceptance_criteria: list[str]
    validation_steps: list[str]
    test_cases: list[str] = field(default_factory=list)
    documentation_required: bool = False
    security_review_required: bool = False
    performance_benchmarks: dict[str, float] = field(default_factory=dict)


@dataclass
class Task:
    """Individual work item"""
    id: str | None
    title: str
    description: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    
    # Assignment
    assigned_agent: str | None
    reviewer: str | None
    qa_assigned: str | None
    
    # Relationships
    parent_epic: str | None
    parent_story: str | None
    dependencies: list[str]  # Task IDs that must complete first
    blocks: list[str]        # Task IDs that depend on this
    
    # Definition of Done
    definition_of_done: DefinitionOfDone
    
    # Execution
    estimated_hours: float
    actual_hours: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    
    # Tracking
    notes: list[str] = field(default_factory=list)
    qa_notes: list[str] = field(default_factory=list)
    iteration: int = 1  # Increment on QA failures
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "product_owner"
    tags: list[str] = field(default_factory=list)


@dataclass
class Epic:
    """Large body of work that can be broken down into stories"""
    id: str | None
    title: str
    description: str
    business_value: str
    success_metrics: list[str]
    
    status: TaskStatus
    priority: TaskPriority
    
    # Relationships
    parent_release: str | None
    stories: list[str]  # Story IDs
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    target_completion: datetime | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class Story:
    """User-facing feature or functionality"""
    id: str | None
    title: str
    user_story: str  # "As a [user], I want [goal] so that [benefit]"
    
    status: TaskStatus
    priority: TaskPriority
    
    # Relationships
    parent_epic: str | None
    tasks: list[str]  # Task IDs
    
    # Acceptance
    acceptance_criteria: list[str]
    story_points: int | None = None
    
    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)


@dataclass
class Release:
    """Collection of epics/stories for a release"""
    id: str | None
    version: str  # e.g., "v1.2.0"
    title: str
    description: str
    
    epics: list[str]
    release_date: datetime | None = None
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentQueue:
    """Task queue for an individual agent"""
    agent_role: AgentRole
    tasks: list[str]  # Task IDs, ordered by priority
    active_task: str | None = None
    last_polled: datetime = field(default_factory=datetime.now)


class GlobalState(TypedDict):
    """Main state for Engineering Department"""
    
    # Conversation
    messages: Annotated[Sequence, add_messages]
    session_id: str
    director_request: str  # Latest request from Director (user)
    
    # Work Items
    releases: dict[str, Release]
    epics: dict[str, Epic]
    stories: dict[str, Story]
    tasks: dict[str, Task]
    
    # Backlog & Queues
    backlog: list[str]  # Task IDs not yet assigned
    agent_queues: dict[str, AgentQueue]  # {agent_role: queue}
    
    # Active Work
    in_progress: list[str]  # Task IDs currently being worked
    blocked_tasks: dict[str, str]  # {task_id: reason}
    
    # Project Management
    pm_priorities: dict[str, int]  # Manual priority overrides by PM
    
    # Coordination
    current_phase: Literal["requirements", "planning", "execution", "qa", "done"]
    needs_pm_attention: list[str]  # Task IDs needing PM decision
    needs_director_input: bool
    
    # Metrics
    velocity: dict[str, float]  # {agent_role: tasks_per_day}
    quality_metrics: dict[str, float]  # {metric_name: value}


class ProductOwnerState(TypedDict):
    """State for Product Owner during requirements gathering"""
    
    director_request: str
    interview_transcript: list[dict]  # Q&A with director
    
    # Generated work items
    proposed_release: Release | None
    proposed_epics: list[Epic]
    proposed_stories: list[Story]
    proposed_tasks: list[Task]
    
    # Validation
    director_approved: bool
    needs_clarification: list[str]


class ProjectManagerState(TypedDict):
    """State for Project Manager"""
    
    # Current view
    backlog_snapshot: list[str]
    queue_snapshot: dict[str, AgentQueue]
    
    # Prioritization
    priority_decisions: list[dict]  # History of priority calls
    
    # Capacity planning
    agent_utilization: dict[str, float]  # {agent_role: utilization_pct}
    estimated_completion: dict[str, datetime]  # {task_id: eta}
    
    # Blockers
    critical_blockers: list[dict]
    escalations: list[dict]


class EngineerState(TypedDict):
    """State for individual engineering agents"""
    
    # Agent info
    agent_role: AgentRole
    my_queue: AgentQueue
    
    # Current task
    active_task: Task | None
    task_context: dict  # Files, dependencies, etc.
    
    # Execution
    tool_calls_made: list[dict]
    files_modified: list[str]
    notes_log: list[str]
    
    # Quality
    self_review_passed: bool
    ready_for_qa: bool


class QAState(TypedDict):
    """State for QA agents"""
    
    # QA agent info
    qa_type: Literal["functional", "security", "performance"]
    
    # Task under test
    task: Task
    test_results: dict[str, bool]  # {test_case: passed}
    
    # Results
    passed: bool
    issues_found: list[str]
    severity_ratings: dict[str, str]  # {issue: severity}
    
    # Feedback
    feedback_for_engineer: str
    recommended_action: Literal["pass", "fail", "needs_review"]
