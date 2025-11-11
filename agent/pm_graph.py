"""PM Agent Graph using LangGraph."""

from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import httpx
import os

from langgraph.graph import StateGraph, Graph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field


# State definition
class AgentState(TypedDict):
    """State for the PM agent."""
    messages: Sequence[BaseMessage]
    current_task: Optional[Dict[str, Any]]
    epic_title: Optional[str]
    story_title: Optional[str]
    priority: Optional[str]
    acceptance_criteria: Optional[List[str]]
    definition_of_done: Optional[List[str]]
    description: Optional[str]
    clarifications_needed: Optional[List[str]]
    clarification_count: int
    story_url: Optional[str]
    issue_url: Optional[str]
    error_message: Optional[str]
    next_action: Optional[str]


class PMAgent:
    """Project Manager Agent for story creation and management."""
    
    def __init__(self, mcp_base_url: str = "http://localhost:8001"):
        self.mcp_base_url = mcp_base_url
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # HTTP client for MCP server
        self.client = httpx.AsyncClient(
            base_url=mcp_base_url,
            headers={
                "Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN', 'dev-token')}"
            },
            timeout=30.0
        )
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> Graph:
        """Build the LangGraph workflow."""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("understand", self.understand_task)
        workflow.add_node("clarify", self.request_clarification)
        workflow.add_node("validate", self.validate_requirements)
        workflow.add_node("plan", self.plan_execution)
        workflow.add_node("create_story", self.create_story)
        # Removed create_issue node - not needed anymore
        workflow.add_node("complete", self.complete_task)
        workflow.add_node("error", self.handle_error)
        
        # Add edges
        workflow.set_entry_point("understand")
        
        # From understand
        workflow.add_conditional_edges(
            "understand",
            self.route_after_understand,
            {
                "clarify": "clarify",
                "validate": "validate",
                "error": "error"
            }
        )
        
        # From clarify - go to validate instead of understand to prevent loop
        workflow.add_edge("clarify", "validate")
        
        # From validate
        workflow.add_conditional_edges(
            "validate",
            self.route_after_validate,
            {
                "plan": "plan",
                "clarify": "clarify",
                "error": "error"
            }
        )
        
        # From plan
        workflow.add_edge("plan", "create_story")
        
        # From create_story - go directly to complete (no GitHub issues)
        workflow.add_conditional_edges(
            "create_story",
            self.route_after_story,
            {
                "complete": "complete",  # Skip GitHub, go to complete
                "error": "error"
            }
        )
        
        # No more create_issue edge needed
        
        # Terminal nodes
        workflow.add_edge("complete", END)
        workflow.add_edge("error", END)
        
        return workflow.compile()
    
    async def understand_task(self, state: AgentState) -> AgentState:
        """Understand the user's task request."""
        print("[Node: understand] Starting...")  # Debug
        
        messages = state["messages"]
        
        # Extract task details using LLM with structured output
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Project Manager agent helping to create stories.
            
Analyze the user's request and extract:
            1. Epic title (e.g., "User Authentication", "Infrastructure", "API Development")
            2. Story title (brief, clear title for the story)
            3. Priority (P0=Critical, P1=High, P2=Medium, P3=Low)
            4. Description (detailed description of what needs to be done)
            
            If information is missing, use reasonable defaults:
            - Epic: "Engineering Tasks"
            - Priority: "P2"
            - Description: Use the user's message
            - Story title: Create from the user's message
            
            Respond with ONLY a JSON object like:
            {
                "epic_title": "Infrastructure",
                "story_title": "Add healthcheck endpoint",
                "priority": "P2",
                "description": "Implement a healthcheck endpoint for monitoring",
                "needs_clarification": false
            }"""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"messages": messages})
        
        # Parse JSON response
        try:
            import json
            # Clean the response content to get just JSON
            content = response.content
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content.strip())
            
            # Update state with extracted values
            state["epic_title"] = parsed.get("epic_title", "Engineering Tasks")
            state["story_title"] = parsed.get("story_title", "")
            state["priority"] = parsed.get("priority", "P2")
            state["description"] = parsed.get("description", "")
            
            # Clear clarifications if we have what we need
            if state["epic_title"] and state["story_title"]:
                state["clarifications_needed"] = []
            else:
                # Set clarifications needed
                clarifications = []
                if not state["story_title"]:
                    clarifications.append("What should the story title be?")
                state["clarifications_needed"] = clarifications
            
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback to basic extraction
            print(f"JSON parsing error: {e}, content: {response.content}")
            
            # Use the message as basis
            user_message = messages[-1].content if messages else ""
            
            # Simple extraction based on keywords
            state["epic_title"] = "Engineering Tasks"
            state["story_title"] = user_message[:100] if user_message else "New Story"
            state["priority"] = "P2"
            state["description"] = user_message
            state["clarifications_needed"] = []
        
        print(f"[Node: understand] State after processing:")
        print(f"  - epic_title: {state.get('epic_title')}")
        print(f"  - story_title: {state.get('story_title')}")
        print(f"  - priority: {state.get('priority')}")
        print(f"  - clarifications_needed: {state.get('clarifications_needed')}")
        
        return state
    
    async def request_clarification(self, state: AgentState) -> AgentState:
        """Request clarification from the user."""
        print("[Node: clarify] Starting...")  # Debug
        
        # Limit clarification rounds
        state["clarification_count"] = state.get("clarification_count", 0) + 1
        print(f"[Node: clarify] Clarification count: {state['clarification_count']}")  # Debug
        
        if state["clarification_count"] > 2:
            # After 2 rounds, just proceed with defaults
            print("[Node: clarify] Max clarifications reached, clearing and proceeding")  # Debug
            state["clarifications_needed"] = []
            # Set defaults if still missing
            if not state.get("story_title"):
                state["story_title"] = "New Story Task"
            if not state.get("epic_title"):
                state["epic_title"] = "Engineering Tasks"
            return state
        
        # Build clarification message
        clarifications = state.get("clarifications_needed", [])
        if clarifications:
            clarification_msg = "I need some clarification:\n"
            for q in clarifications:
                clarification_msg += f"- {q}\n"
            
            state["messages"].append(AIMessage(content=clarification_msg))
            state["next_action"] = "awaiting_clarification"
        
        # IMPORTANT: Clear clarifications after asking to prevent infinite loop
        state["clarifications_needed"] = []
        
        return state
    
    async def validate_requirements(self, state: AgentState) -> AgentState:
        """Validate that we have all required information."""
        print("[Node: validate] Starting...")  # Debug
        
        # Check absolutely required fields
        if not state.get("epic_title"):
            state["epic_title"] = "Engineering Tasks"  # Default
        
        if not state.get("story_title"):
            # Try to create from description or messages
            if state.get("description"):
                state["story_title"] = state["description"][:100]
            else:
                state["story_title"] = "New Story Task"
        
        if not state.get("priority"):
            state["priority"] = "P2"  # Default priority
        
        if not state.get("description"):
            state["description"] = state.get("story_title", "Task to be completed")
        
        # Always apply defaults for AC and DoD - don't ask for clarification
        if not state.get("acceptance_criteria"):
            state["acceptance_criteria"] = [
                "Functionality works as specified",
                "Unit tests pass",
                "No regression in existing features"
            ]
        
        if not state.get("definition_of_done"):
            state["definition_of_done"] = [
                "Code reviewed and approved",
                "Tests written and passing",
                "Documentation updated",
                "No critical security vulnerabilities"
            ]
        
        # Clear any clarifications - we have everything we need
        state["clarifications_needed"] = []
        
        return state
    
    async def plan_execution(self, state: AgentState) -> AgentState:
        """Plan the execution steps."""
        
        state["next_action"] = "create_story"
        
        # Add planning message
        plan_msg = f"""I'll create the story with these details:
- Epic: {state['epic_title']}
- Title: {state['story_title']}
- Priority: {state['priority']}
- AC: {len(state['acceptance_criteria'])} criteria defined
- DoD: {len(state['definition_of_done'])} items defined

Creating in Notion..."""
        
        state["messages"].append(AIMessage(content=plan_msg))
        
        return state
    
    async def create_story(self, state: AgentState) -> AgentState:
        """Create story in Notion via MCP."""
        
        try:
            response = await self.client.post(
                "/api/tools/notion/create-story",
                json={
                    "epic_title": state["epic_title"],
                    "story_title": state["story_title"],
                    "priority": state["priority"],
                    "acceptance_criteria": state["acceptance_criteria"],
                    "definition_of_done": state["definition_of_done"],
                    "description": state["description"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            state["story_url"] = data["story_url"]
            state["messages"].append(
                AIMessage(content=f"✅ Story created in Notion: {data['story_url']}")
            )
            
        except Exception as e:
            state["error_message"] = f"Failed to create Notion story: {str(e)}"
            
        return state
    
    # Removed create_issue method - not needed
    # Issues are managed exclusively in Notion
    
    async def complete_task(self, state: AgentState) -> AgentState:
        """Complete the task and provide summary."""
        
        summary = f"""✨ Story successfully created in Notion!

**Notion Story:** {state['story_url']}

The story "{state['story_title']}" has been added to the "{state['epic_title']}" epic with priority {state['priority']}.

The team can now pick this up from the backlog in Notion."""
        
        state["messages"].append(AIMessage(content=summary))
        state["next_action"] = "completed"
        
        return state
    
    async def handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow."""
        
        error_msg = f"❌ An error occurred: {state['error_message']}"
        state["messages"].append(AIMessage(content=error_msg))
        state["next_action"] = "error_occurred"
        
        return state
    
    def route_after_understand(self, state: AgentState) -> str:
        """Determine next step after understanding."""
        if state.get("error_message"):
            print(f"[Route: understand] Error detected, going to error node")  # Debug
            return "error"
        # Check if we have non-empty clarifications list
        clarifications = state.get("clarifications_needed", [])
        print(f"[Route: understand] Clarifications needed: {clarifications}")  # Debug
        if clarifications and len(clarifications) > 0:
            print(f"[Route: understand] Going to clarify node")  # Debug
            return "clarify"
        print(f"[Route: understand] Going to validate node")  # Debug
        return "validate"
    
    def route_after_validate(self, state: AgentState) -> str:
        """Determine next step after validation."""
        if state.get("error_message"):
            return "error"
        # Check if we have non-empty clarifications list
        clarifications = state.get("clarifications_needed", [])
        if clarifications and len(clarifications) > 0:
            return "clarify"
        return "plan"
    
    def route_after_story(self, state: AgentState) -> str:
        """Determine next step after story creation."""
        if state.get("error_message"):
            return "error"
        if not state.get("story_url"):
            return "error"
        # Skip GitHub issues - go directly to complete
        return "complete"

    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message through the agent."""
        
        print(f"[PMAgent] Processing message: {message[:100]}...")  # Debug log
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "clarification_count": 0,
            "clarifications_needed": [],
            "error_message": None
        }
        
        try:
            # Add debug configuration
            import logging
            logging.basicConfig(level=logging.INFO)
            
            # Run the graph with increased recursion limit
            print("[PMAgent] Starting graph execution...")  # Debug log
            final_state = await self.graph.ainvoke(
                initial_state,
                config={
                    "recursion_limit": 100,
                    "callbacks": []  # Could add callbacks for debugging
                }
            )
            print("[PMAgent] Graph execution completed")  # Debug log
            
            # Extract the last AI message as response
            response_text = "Processing your request..."
            for msg in reversed(final_state.get("messages", [])):
                if isinstance(msg, AIMessage):
                    response_text = msg.content
                    break
            
            # Build response
            result = {
                "response": response_text,
                "status": final_state.get("next_action", "unknown"),
                "state": final_state.get("next_action", "unknown"),
                "requires_clarification": bool(final_state.get("clarifications_needed")),
                "clarification_prompt": final_state.get("clarifications_needed", [])
            }
            
            # Add created artifacts
            if final_state.get("story_url"):
                result["story_created"] = {
                    "url": final_state["story_url"],
                    "title": final_state.get("story_title"),
                    "epic": final_state.get("epic_title"),
                    "priority": final_state.get("priority")
                }
            
            if final_state.get("issue_url"):
                result["issue_created"] = {
                    "url": final_state["issue_url"],
                    "title": final_state.get("story_title")
                }
            
            if final_state.get("error_message"):
                result["error"] = final_state["error_message"]
            
            return result
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Agent error: {error_details}")  # Log for debugging
            
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "status": "error",
                "state": "error",
                "error": str(e),
                "requires_clarification": False
            }
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
