"""
LangGraph State Definitions for Agent Foundry Multi-Agent System
"""

from collections.abc import Sequence
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """
    Shared state for the supervisor + worker agent graph.

    Tracks:
    - User messages (accumulated history)
    - Current user input
    - Worker agent responses
    - Final aggregated response
    - Next agent to route to
    - Session context (enriched by context_agent)
    """

    # Conversation history (accumulates)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Current user input being processed
    current_input: str

    # Which worker(s) the supervisor routed to
    routed_to: list[str]

    # Responses from individual worker agents
    worker_responses: dict[str, str]

    # Final aggregated response from supervisor
    final_response: str

    # Next agent in workflow (for routing)
    next_agent: Literal["supervisor", "pm_agent", "ticket_agent", "FINISH"]

    # Session context (enriched by context_agent)
    session_context: dict[str, Any] | None

    # User context (profile, history, etc.)
    user_context: dict[str, Any] | None

    # Goal tracking (new for UI event-driven workflow)
    goal_id: str | None
    primary_goal: str | None
    sub_goals: list[dict[str, Any]] | None
    current_sub_goal_id: str | None

    # CIBC Card Services workflow fields
    workflow_type: str | None  # "activation" or "replacement"
    workflow_status: str | None  # "in_progress", "completed"

    # Enhanced verification fields (5-question protocol)
    verification_score: int | None  # Activation verification score (0-5, was 0-3)
    verification_answers: dict[str, str] | None  # All 5 answers stored
    verification_results: dict[str, bool] | None  # Each question result
    verification_status: str | None  # "pass", "cross_check_dob", "update_phone", "fail"

    # Individual question verification
    phone_provided: str | None  # Customer's provided phone
    phone_verified: bool | None  # Phone verification status
    dob_provided: str | None  # Date of birth provided
    dob_verified: bool | None  # DOB verification status
    security_question_1: str | None  # Mother's maiden / first school
    security_question_1_verified: bool | None
    security_question_2: str | None  # Last 4 SIN/account
    security_question_2_verified: bool | None
    address_provided: str | None  # Address confirmation
    address_verified: bool | None  # Address verification status

    # Enhanced card replacement fields
    replacement_reason: str | None  # Reason for replacement
    card_type: str | None  # "credit" or "debit"
    card_number_change: bool | None  # Will card number change?
    police_report_filed: bool | None  # For stolen cards
    damage_type: str | None  # "faulty" or "customer"
    fee_charged: bool | None  # Is fee charged?
    fee_amount: float | None  # Fee amount
    fee_waived: bool | None  # Is fee waived?
    fee_waiver_reason: str | None  # Reason for waiver


class IOState(TypedDict):
    """
    State for io_agent communication with supervisor.
    Simpler state focused on input/output.
    """

    # User's current message
    user_message: str

    # Response to deliver to user
    assistant_response: str

    # Session metadata
    session_id: str
    user_id: str

    # Channel type (chat, voice, api)
    channel: str | None


class ContextState(TypedDict):
    """
    State for context_agent enrichment.
    Manages session state and user context loading.
    """

    # Session ID
    session_id: str

    # User ID
    user_id: str

    # Current request
    current_input: str

    # Loaded session state from Redis
    session_state: dict[str, Any] | None

    # Loaded user context (profile, history)
    user_context: dict[str, Any] | None

    # Enriched context (combined session + user)
    enriched_context: dict[str, Any] | None


class CoherenceState(TypedDict):
    """
    State for coherence_agent response assembly.
    Handles deduplication and conflict resolution.
    """

    # Raw responses from workers
    worker_responses: dict[str, str]

    # Buffered responses (async collection)
    buffered_responses: list[dict[str, Any]]

    # Deduplicated responses
    deduplicated_responses: list[str]

    # Resolved conflicts (if any)
    resolved_conflicts: dict[str, Any] | None

    # Final compiled response
    compiled_response: str


class DeepAgentState(TypedDict):
    """
    State for deep agent workflows with planning, execution, and criticism.

    Supports:
    - Task decomposition via TodoList middleware
    - Filesystem operations for context management
    - Sub-agent delegation for specialized tasks
    - Quality validation and replanning
    """

    # Base message history
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Planning state
    todos: list[dict[str, Any]]  # Task list from TodoList middleware
    current_task_id: str | None  # Currently executing task
    completed_tasks: list[str]  # IDs of completed tasks

    # Execution state
    filesystem_context: dict[str, str]  # File references {key: path}
    tool_results: dict[str, Any]  # Results from tool executions
    workspace_path: str  # Base path for filesystem operations

    # Sub-agent state
    subagent_results: dict[str, Any]  # Results from spawned sub-agents
    active_subagents: list[str]  # Currently running sub-agent IDs

    # Critic state
    critic_feedback: str | None  # Feedback from quality validation
    validation_results: dict[str, float]  # Quality scores by criteria
    plan_revision_count: int  # Number of times plan was revised

    # Context management
    offloaded_files: list[str]  # Files created for context offloading
    summarized_content: dict[str, str]  # Summaries of offloaded content

    # Execution control
    max_iterations: int  # Max planning iterations
    current_iteration: int  # Current iteration count
    should_replan: bool  # Whether to trigger replanning
