"""
LangGraph State Definitions for Agent Foundry Multi-Agent System
"""

from typing import Annotated, Literal, TypedDict, Sequence, Optional, Any
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


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
    session_context: Optional[dict[str, Any]]
    
    # User context (profile, history, etc.)
    user_context: Optional[dict[str, Any]]


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
    channel: Optional[str]


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
    session_state: Optional[dict[str, Any]]
    
    # Loaded user context (profile, history)
    user_context: Optional[dict[str, Any]]
    
    # Enriched context (combined session + user)
    enriched_context: Optional[dict[str, Any]]


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
    resolved_conflicts: Optional[dict[str, Any]]
    
    # Final compiled response
    compiled_response: str
