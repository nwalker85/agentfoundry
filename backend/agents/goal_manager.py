"""
Goal Management System for Agent Foundry
Handles goal decomposition, hierarchy tracking, and lifecycle management
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


class GoalStatus(str, Enum):
    """Goal lifecycle status"""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class SubGoal:
    """Represents a decomposed sub-goal"""

    id: str
    description: str
    status: GoalStatus = GoalStatus.PENDING
    assigned_agent: str | None = None
    result: dict[str, Any] | None = None
    parent_goal_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "result": self.result,
            "parent_goal_id": self.parent_goal_id,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error": self.error,
        }


@dataclass
class Goal:
    """Represents a primary goal with sub-goals"""

    id: str
    description: str
    session_id: str
    user_input: str
    sub_goals: list[SubGoal] = field(default_factory=list)
    status: GoalStatus = GoalStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "session_id": self.session_id,
            "user_input": self.user_input,
            "sub_goals": [sg.to_dict() for sg in self.sub_goals],
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    def get_active_sub_goal(self) -> SubGoal | None:
        """Get the currently active sub-goal"""
        for sg in self.sub_goals:
            if sg.status == GoalStatus.ACTIVE:
                return sg
        return None

    def get_next_pending_sub_goal(self) -> SubGoal | None:
        """Get the next pending sub-goal to execute"""
        for sg in self.sub_goals:
            if sg.status == GoalStatus.PENDING:
                return sg
        return None


class GoalManager:
    """
    Manages goal decomposition, tracking, and execution coordination
    """

    def __init__(self):
        """Initialize GoalManager with LLM for decomposition"""
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3, api_key=os.getenv("OPENAI_API_KEY"))

        # In-memory cache for performance
        self.goals: dict[str, Goal] = {}

    def _persist_goal(self, goal: Goal):
        """Persist goal to database"""
        import json

        from backend.db import get_connection

        conn = get_connection()
        cur = conn.cursor()

        # Insert goal
        cur.execute(
            """
            INSERT OR REPLACE INTO goals (id, session_id, user_id, description, user_input, status, metadata, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                goal.id,
                goal.session_id,
                goal.metadata.get("user_id"),
                goal.description,
                goal.user_input,
                goal.status.value,
                json.dumps(goal.metadata),
                goal.created_at,
                goal.completed_at,
            ),
        )

        # Insert sub-goals
        for sg in goal.sub_goals:
            cur.execute(
                """
                INSERT OR REPLACE INTO sub_goals (id, goal_id, description, status, assigned_agent, result, error, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sg.id,
                    goal.id,
                    sg.description,
                    sg.status.value,
                    sg.assigned_agent,
                    json.dumps(sg.result) if sg.result else None,
                    sg.error,
                    sg.created_at,
                    sg.completed_at,
                ),
            )

        conn.commit()
        conn.close()

    def _load_goal_from_db(self, goal_id: str) -> Goal | None:
        """Load goal from database"""
        import json

        from backend.db import get_connection

        conn = get_connection()
        cur = conn.cursor()

        # Load goal
        cur.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        goal_row = cur.fetchone()

        if not goal_row:
            conn.close()
            return None

        # Load sub-goals
        cur.execute("SELECT * FROM sub_goals WHERE goal_id = ?", (goal_id,))
        sub_goal_rows = cur.fetchall()

        conn.close()

        # Reconstruct goal
        sub_goals = [
            SubGoal(
                id=row["id"],
                description=row["description"],
                status=GoalStatus(row["status"]),
                assigned_agent=row["assigned_agent"],
                result=json.loads(row["result"]) if row["result"] else None,
                parent_goal_id=goal_id,
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                error=row["error"],
            )
            for row in sub_goal_rows
        ]

        goal = Goal(
            id=goal_row["id"],
            description=goal_row["description"],
            session_id=goal_row["session_id"],
            user_input=goal_row["user_input"],
            sub_goals=sub_goals,
            status=GoalStatus(goal_row["status"]),
            created_at=goal_row["created_at"],
            completed_at=goal_row["completed_at"],
            metadata=json.loads(goal_row["metadata"]) if goal_row["metadata"] else {},
        )

        return goal

    async def create_goal_from_user_input(
        self, user_input: str, session_id: str, metadata: dict[str, Any] | None = None
    ) -> Goal:
        """
        Create a primary goal from user input and decompose into sub-goals

        Args:
            user_input: The user's original request
            session_id: Session identifier
            metadata: Additional context/metadata

        Returns:
            Goal object with decomposed sub-goals
        """
        goal_id = str(uuid.uuid4())

        # Extract primary goal description
        primary_goal_desc = await self._extract_primary_goal(user_input)

        # Create goal object
        goal = Goal(
            id=goal_id,
            description=primary_goal_desc,
            session_id=session_id,
            user_input=user_input,
            metadata=metadata or {},
        )

        # Decompose into sub-goals
        sub_goals = await self._decompose_goal(goal)
        goal.sub_goals = sub_goals

        # Store in cache and database
        self.goals[goal_id] = goal
        self._persist_goal(goal)

        return goal

    async def _extract_primary_goal(self, user_input: str) -> str:
        """
        Extract a concise primary goal description from user input

        Args:
            user_input: User's request

        Returns:
            Primary goal description
        """
        system_prompt = """You are a goal extraction assistant.
Given a user's request, extract and state the primary goal in a single concise sentence.
Focus on the main objective, not the implementation details.

Examples:
User: "I need to build an authentication system with JWT tokens and refresh logic"
Goal: "Implement user authentication system"

User: "Create a project management dashboard that shows tasks, milestones, and team members"
Goal: "Build project management dashboard"

User: "Help me set up CI/CD pipeline with GitHub Actions, Docker, and AWS deployment"
Goal: "Set up CI/CD pipeline"

Return only the goal statement, nothing else."""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]

        response = await self.llm.ainvoke(messages)
        return response.content.strip()

    async def _decompose_goal(self, goal: Goal) -> list[SubGoal]:
        """
        Decompose a primary goal into actionable sub-goals

        Args:
            goal: The primary goal to decompose

        Returns:
            List of SubGoal objects
        """
        system_prompt = """You are a goal decomposition assistant for an AI agent system.
Given a primary goal, break it down into 2-5 actionable sub-goals that can be executed by specialized AI agents.

Sub-goals should be:
- Specific and actionable
- Ordered logically (sequential if dependencies exist)
- Independent enough to be handled by different agents
- Complete (cover all aspects of the primary goal)

Available agent types:
- pm-agent: Project planning, task creation, story management, Notion integration
- data-agent: Data analysis, SQL queries, reporting, insights
- storage-agent: File operations, data persistence, document management
- code-agent: Code generation, refactoring, technical implementation

Format your response as a JSON array of sub-goals:
[
  {
    "description": "Sub-goal 1 description",
    "suggested_agent": "agent-type"
  },
  {
    "description": "Sub-goal 2 description",
    "suggested_agent": "agent-type"
  }
]

Return ONLY valid JSON, no other text."""

        user_prompt = f"""Primary Goal: {goal.description}

Original User Input: {goal.user_input}

Decompose this into sub-goals:"""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        response = await self.llm.ainvoke(messages)

        # Parse JSON response
        import json

        try:
            sub_goals_data = json.loads(response.content.strip())
        except json.JSONDecodeError:
            # Fallback: create single sub-goal if decomposition fails
            sub_goals_data = [{"description": goal.description, "suggested_agent": "pm-agent"}]

        # Create SubGoal objects
        sub_goals = []
        for idx, sg_data in enumerate(sub_goals_data):
            sub_goal = SubGoal(
                id=f"{goal.id}_sub_{idx}",
                description=sg_data["description"],
                parent_goal_id=goal.id,
                assigned_agent=sg_data.get("suggested_agent"),
            )
            sub_goals.append(sub_goal)

        return sub_goals

    def get_goal(self, goal_id: str) -> Goal | None:
        """Retrieve a goal by ID (checks cache first, then DB)"""
        # Check cache first
        if goal_id in self.goals:
            return self.goals[goal_id]

        # Load from database
        goal = self._load_goal_from_db(goal_id)
        if goal:
            self.goals[goal_id] = goal
        return goal

    def get_goals_by_session(self, session_id: str) -> list[Goal]:
        """Get all goals for a session"""
        return [g for g in self.goals.values() if g.session_id == session_id]

    def update_sub_goal_status(
        self,
        goal_id: str,
        sub_goal_id: str,
        status: GoalStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> bool:
        """
        Update the status of a sub-goal

        Args:
            goal_id: Parent goal ID
            sub_goal_id: Sub-goal ID
            status: New status
            result: Result data if completed
            error: Error message if failed

        Returns:
            True if updated successfully
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        for sub_goal in goal.sub_goals:
            if sub_goal.id == sub_goal_id:
                sub_goal.status = status
                if result:
                    sub_goal.result = result
                if error:
                    sub_goal.error = error
                if status == GoalStatus.COMPLETED:
                    sub_goal.completed_at = datetime.utcnow().isoformat()

                # Persist updated state
                self._persist_goal(goal)
                return True

        return False

    def check_goal_completion(self, goal_id: str) -> bool:
        """
        Check if all sub-goals are completed and update goal status

        Returns:
            True if goal is complete
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False

        # Check if all sub-goals are completed
        all_completed = all(sg.status == GoalStatus.COMPLETED for sg in goal.sub_goals)

        any_failed = any(sg.status == GoalStatus.FAILED for sg in goal.sub_goals)

        if all_completed:
            goal.status = GoalStatus.COMPLETED
            goal.completed_at = datetime.utcnow().isoformat()
            self._persist_goal(goal)
            return True
        elif any_failed:
            goal.status = GoalStatus.FAILED
            self._persist_goal(goal)
            return False

        return False

    def get_goal_summary(self, goal_id: str) -> dict[str, Any]:
        """
        Get a summary of goal progress

        Returns:
            Dictionary with progress statistics
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return {}

        total = len(goal.sub_goals)
        completed = sum(1 for sg in goal.sub_goals if sg.status == GoalStatus.COMPLETED)
        failed = sum(1 for sg in goal.sub_goals if sg.status == GoalStatus.FAILED)
        active = sum(1 for sg in goal.sub_goals if sg.status == GoalStatus.ACTIVE)
        pending = sum(1 for sg in goal.sub_goals if sg.status == GoalStatus.PENDING)

        return {
            "goal_id": goal.id,
            "description": goal.description,
            "status": goal.status.value,
            "total_sub_goals": total,
            "completed": completed,
            "failed": failed,
            "active": active,
            "pending": pending,
            "progress_percentage": (completed / total * 100) if total > 0 else 0,
        }


# Global instance
goal_manager = GoalManager()
