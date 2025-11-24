"""
PM Agent - Project Management Worker

Responsibilities:
- Create stories, epics, tasks
- Manage backlog
- Define acceptance criteria
- Set priorities
- Definition of done

This is a WORKER agent - called by supervisor, never directly by user.
"""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class PMAgent:
    """
    Project Management worker agent.
    Handles all PM-related tasks.
    """

    def __init__(self):
        """Initialize PM Agent with LLM."""
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.3)

        self.system_prompt = """You are a Project Management specialist agent.

Your expertise:
- Creating well-defined user stories and epics
- Defining clear acceptance criteria
- Setting appropriate priorities
- Writing definition of done
- Managing backlogs

When users describe features or tasks:
1. Ask clarifying questions if needed
2. Structure as: Epic → Story → Acceptance Criteria → Definition of Done
3. Use industry best practices (INVEST criteria for stories)
4. Keep responses conversational and helpful

Always maintain professional PM terminology but explain concepts when helpful.
Respond concisely for voice conversations when appropriate."""

        logger.info("PMAgent initialized")

    async def process(self, user_message: str) -> str:
        """
        Process a PM-related request.

        Args:
            user_message: The user's request (routed from supervisor)

        Returns:
            Response text with PM guidance/artifacts
        """
        logger.info(f"PMAgent processing: {user_message[:100]}...")

        try:
            # Invoke LLM with PM system prompt
            response = await self.llm.ainvoke(
                [SystemMessage(content=self.system_prompt), HumanMessage(content=user_message)]
            )

            result = response.content.strip()
            logger.info(f"PMAgent response generated ({len(result)} chars)")

            return result

        except Exception as e:
            logger.error(f"Error in PMAgent: {e}", exc_info=True)
            return "I encountered an error processing that PM request. Could you try rephrasing?"

    async def create_story(
        self, title: str, description: str, epic: str | None = None, priority: str | None = None
    ) -> dict:
        """
        Create a structured user story.

        Args:
            title: Story title
            description: Story description
            epic: Parent epic (optional)
            priority: Priority level (optional)

        Returns:
            Structured story dict

        Note: This is a helper method for future API integration.
        Currently returns dict format that could be saved to backlog.
        """
        prompt = f"""Create a complete user story from this information:

Title: {title}
Description: {description}
Epic: {epic or "Not specified"}
Priority: {priority or "Not specified"}

Format as:
- User Story (As a... I want... So that...)
- Acceptance Criteria (Given/When/Then format)
- Definition of Done (checklist)
- Estimated Effort (story points)

Be specific and actionable."""

        response = await self.llm.ainvoke([SystemMessage(content=self.system_prompt), HumanMessage(content=prompt)])

        # Return structured format
        # In future, this could integrate with Jira/Linear/etc.
        return {
            "title": title,
            "description": description,
            "epic": epic,
            "priority": priority,
            "full_story": response.content.strip(),
            "status": "draft",
        }
