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
        workflow.add_node("create_issue", self.create_issue)
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
        
        # From clarify
        workflow.add_edge("clarify", "understand")
        
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
        
        # From create_story
        workflow.add_conditional_edges(
            "create_story",
            self.route_after_story,
            {
                "create_issue": "create_issue",
                "complete": "complete",
                "error": "error"
            }
        )
        
        # From create_issue
        workflow.add_edge("create_issue", "complete")
        
        # Terminal nodes
        workflow.add_edge("complete", END)
        workflow.add_edge("error", END)
        
        return workflow.compile()
    
    async def understand_task(self, state: AgentState) -> AgentState:
        """Understand the user's task request."""
        
        messages = state["messages"]
        
        # Extract task details using LLM
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a Project Manager agent helping to create stories.
Extract the following information from the user's request:
- Epic title
- Story title  
- Priority (P0, P1, P2, or P3)
- Description
- Any mentioned acceptance criteria
- Any mentioned definition of done items

If any critical information is missing, note what needs clarification.
Respond in JSON format."""),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        chain = prompt | self.llm
        response = await chain.ainvoke({"messages": messages})
        
        # Parse response (simplified - would use structured output in production)
        # For now, we'll extract manually
        content = response.content
        
        # Extract fields (this would be more robust in production)
        state["epic_title"] = self._extract_field(content, "epic_title")
        state["story_title"] = self._extract_field(content, "story_title")
        state["priority"] = self._extract_field(content, "priority") or "P2"
        state["description"] = self._extract_field(content, "description")
        
        # Check what's missing
        clarifications = []
        if not state.get("epic_title"):
            clarifications.append("Which epic should this story belong to?")
        if not state.get("story_title"):
            clarifications.append("What should the story title be?")
        if not state.get("acceptance_criteria"):
            clarifications.append("What are the acceptance criteria for this story?")
        if not state.get("definition_of_done"):
            clarifications.append("What is the definition of done?")
        
        state["clarifications_needed"] = clarifications
        
        return state
    
    async def request_clarification(self, state: AgentState) -> AgentState:
        """Request clarification from the user."""
        
        # Limit clarification rounds
        state["clarification_count"] = state.get("clarification_count", 0) + 1
        
        if state["clarification_count"] > 2:
            # Use defaults after 2 rounds
            if not state.get("acceptance_criteria"):
                state["acceptance_criteria"] = ["Functionality implemented as described", "Tests passing"]
            if not state.get("definition_of_done"):
                state["definition_of_done"] = ["Code reviewed", "Tests written", "Documentation updated"]
            # Clear clarifications so we proceed to validation
            state["clarifications_needed"] = []
            return state
        
        # Add clarification message
        clarification_msg = "I need some clarification:\n"
        for q in state["clarifications_needed"]:
            clarification_msg += f"- {q}\n"
        
        state["messages"].append(AIMessage(content=clarification_msg))
        state["next_action"] = "awaiting_clarification"
        
        return state
    
    async def validate_requirements(self, state: AgentState) -> AgentState:
        """Validate that we have all required information."""
        
        # Check required fields
        missing = []
        if not state.get("epic_title"):
            missing.append("epic_title")
        if not state.get("story_title"):
            missing.append("story_title")
        
        if missing:
            state["clarifications_needed"] = [f"Missing required field: {field}" for field in missing]
            return state
        
        # Apply defaults if needed
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

Creating in Notion first, then GitHub issue..."""
        
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
    
    async def create_issue(self, state: AgentState) -> AgentState:
        """Create issue in GitHub via MCP."""
        
        # Build issue body
        body_parts = []
        
        if state["description"]:
            body_parts.append(f"## Description\n{state['description']}\n")
        
        body_parts.append("## Acceptance Criteria")
        for ac in state["acceptance_criteria"]:
            body_parts.append(f"- [ ] {ac}")
        
        body_parts.append("\n## Definition of Done")
        for dod in state["definition_of_done"]:
            body_parts.append(f"- [ ] {dod}")
        
        if state["story_url"]:
            body_parts.append(f"\n## Links\n- [Notion Story]({state['story_url']})")
        
        body = "\n".join(body_parts)
        
        try:
            response = await self.client.post(
                "/api/tools/github/create-issue",
                json={
                    "title": f"[{state['priority']}] {state['story_title']}",
                    "body": body,
                    "labels": [f"priority/{state['priority']}", "source/agent-pm"],
                    "story_url": state["story_url"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            state["issue_url"] = data["issue_url"]
            state["messages"].append(
                AIMessage(content=f"✅ GitHub issue created: {data['issue_url']}")
            )
            
        except Exception as e:
            state["error_message"] = f"Failed to create GitHub issue: {str(e)}"
            
        return state
    
    async def complete_task(self, state: AgentState) -> AgentState:
        """Complete the task and provide summary."""
        
        summary = f"""✨ Story successfully created!

**Notion Story:** {state['story_url']}
**GitHub Issue:** {state['issue_url']}

The story "{state['story_title']}" has been added to the "{state['epic_title']}" epic with priority {state['priority']}.

The team can now pick this up from the backlog."""
        
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
            return "error"
        if state.get("clarifications_needed"):
            return "clarify"
        return "validate"
    
    def route_after_validate(self, state: AgentState) -> str:
        """Determine next step after validation."""
        if state.get("error_message"):
            return "error"
        if state.get("clarifications_needed"):
            return "clarify"
        return "plan"
    
    def route_after_story(self, state: AgentState) -> str:
        """Determine next step after story creation."""
        if state.get("error_message"):
            return "error"
        if not state.get("story_url"):
            return "error"
        return "create_issue"
    
    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """Extract a field from text (simplified)."""
        # This would use proper JSON parsing in production
        import re
        pattern = f'"{field}"\\s*:\\s*"([^"]+)"'
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message through the agent."""
        
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "clarification_count": 0
        }
        
        # Run the graph with increased recursion limit
        final_state = await self.graph.ainvoke(
            initial_state,
            config={"recursion_limit": 50}
        )
        
        return {
            "messages": final_state["messages"],
            "story_url": final_state.get("story_url"),
            "issue_url": final_state.get("issue_url"),
            "status": final_state.get("next_action", "unknown"),
            "error": final_state.get("error_message")
        }
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
