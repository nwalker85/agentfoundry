"""PM Agent using LangGraph 1.0 with create_react_agent pattern."""

import os
from typing import Any

import httpx
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field


# Pydantic models for structured outputs
class StoryRequest(BaseModel):
    """Structured story creation request."""

    epic_title: str = Field(description="Epic title (e.g., 'User Authentication', 'Infrastructure')")
    story_title: str = Field(description="Story title - brief, clear description")
    priority: str = Field(description="Priority: P0=Critical, P1=High, P2=Medium, P3=Low")
    description: str = Field(description="Detailed description of what needs to be done")
    acceptance_criteria: list[str] = Field(
        default_factory=lambda: [
            "Functionality works as specified",
            "Unit tests pass",
            "No regression in existing features",
        ],
        description="List of acceptance criteria",
    )
    definition_of_done: list[str] = Field(
        default_factory=lambda: [
            "Code reviewed and approved",
            "Tests written and passing",
            "Documentation updated",
            "No critical security vulnerabilities",
        ],
        description="Definition of done checklist",
    )


class PMAgent:
    """Project Manager Agent using LangGraph 1.0 create_react_agent."""

    def __init__(self, mcp_base_url: str = "http://localhost:8000"):
        self.mcp_base_url = mcp_base_url

        # Initialize LLM with structured output support
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3, api_key=os.getenv("OPENAI_API_KEY"))

        # HTTP client for MCP server
        self.client = httpx.AsyncClient(
            base_url=mcp_base_url,
            headers={"Authorization": f"Bearer {os.getenv('MCP_AUTH_TOKEN', 'dev-token')}"},
            timeout=30.0,
        )

        # Define tools for the agent
        self.tools = [self._create_story_tool()]

        # Build the agent using create_react_agent
        self.graph = self._build_agent()

    def _create_story_tool(self):
        """Create the story creation tool."""

        @tool
        async def create_notion_story(
            epic_title: str,
            story_title: str,
            priority: str,
            description: str,
            acceptance_criteria: list[str] = None,
            definition_of_done: list[str] = None,
        ) -> str:
            """Create a story in Notion with the given details.

            Args:
                epic_title: The epic this story belongs to
                story_title: Title of the story
                priority: Priority level (P0-P3)
                description: Detailed description
                acceptance_criteria: List of acceptance criteria (optional)
                definition_of_done: List of DoD items (optional)

            Returns:
                Confirmation message with story URL
            """
            # Apply defaults
            if acceptance_criteria is None:
                acceptance_criteria = [
                    "Functionality works as specified",
                    "Unit tests pass",
                    "No regression in existing features",
                ]

            if definition_of_done is None:
                definition_of_done = [
                    "Code reviewed and approved",
                    "Tests written and passing",
                    "Documentation updated",
                    "No critical security vulnerabilities",
                ]

            try:
                response = await self.client.post(
                    "/api/tools/notion/create-story",
                    json={
                        "epic_title": epic_title,
                        "story_title": story_title,
                        "priority": priority,
                        "acceptance_criteria": acceptance_criteria,
                        "definition_of_done": definition_of_done,
                        "description": description,
                    },
                )
                response.raise_for_status()
                data = response.json()

                return f"✅ Story created successfully!\n\nNotion Story: {data['story_url']}\n\nThe story '{story_title}' has been added to the '{epic_title}' epic with priority {priority}."

            except Exception as e:
                return f"❌ Failed to create story: {e!s}"

        return create_notion_story

    def _build_agent(self):
        """Build the ReAct agent using LangGraph 1.0."""

        system_prompt = """You are a Project Manager agent helping to create engineering stories in Notion.

Your role:
1. Understand what the user wants to accomplish
2. Extract key details: epic, story title, priority, description
3. Use the create_notion_story tool to create the story
4. Confirm successful creation

Guidelines:
- If details are missing, make reasonable assumptions:
  - Default epic: "Engineering Tasks"
  - Default priority: "P2" 
  - Use user's message for description
- Ask for clarification only if absolutely necessary
- Always use the tool to create the story
- Provide clear confirmation when done

Priority levels:
- P0: Critical, blocking issues
- P1: High priority, should be done soon
- P2: Medium priority, normal work
- P3: Low priority, nice to have"""

        # Create the ReAct agent with tools
        graph = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
        )

        return graph

    async def process_message(self, message: str) -> dict[str, Any]:
        """Process a user message through the agent.

        Args:
            message: User's input message

        Returns:
            Dict with response, status, and any created artifacts
        """

        print(f"[PMAgent] Processing message: {message[:100]}...")

        try:
            # Invoke the agent
            result = await self.graph.ainvoke({"messages": [HumanMessage(content=message)]})

            # Extract messages
            messages = result.get("messages", [])

            # Get the last AI message as response
            response_text = "Processing your request..."
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    response_text = msg.content
                    break

            # Build response
            response = {
                "response": response_text,
                "status": "completed",
                "state": "completed",
                "requires_clarification": False,
            }

            # Check if story was created (look for confirmation in response)
            if "✅ Story created successfully" in response_text and "Notion Story:" in response_text:
                # Extract URL from response
                lines = response_text.split("\n")
                story_url = None
                for line in lines:
                    if "Notion Story:" in line:
                        story_url = line.replace("Notion Story:", "").strip()
                        break

                if story_url:
                    response["story_created"] = {
                        "url": story_url,
                        "title": "Story",  # Could extract from message if needed
                        "epic": "Engineering",
                        "priority": "P2",
                    }

            return response

        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"Agent error: {error_details}")

            return {
                "response": f"I encountered an error processing your request: {e!s}",
                "status": "error",
                "state": "error",
                "error": str(e),
                "requires_clarification": False,
            }

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
