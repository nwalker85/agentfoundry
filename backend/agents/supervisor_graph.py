"""
Enhanced Supervisor Agent with LangGraph StateGraph
Implements UI event-driven workflow with goal decomposition and hybrid intent routing.

Flow:
  UI Event → Analyze Intent → Set Primary Goal → Decompose Goals →
  Route Sub-Goals → Execute Workflows → Aggregate Results → Complete
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from agents.state import AgentState
from backend.agents.goal_manager import GoalStatus, goal_manager
from backend.agents.system.observability_agent import AgentActivity, observability_agent

logger = logging.getLogger(__name__)


class SupervisorGraph:
    """
    Enhanced Supervisor with LangGraph StateGraph for goal-driven workflow orchestration
    """

    def __init__(self):
        self.agent_id = "supervisor_graph"
        self.agent_name = "Supervisor Workflow Graph"

        # LLM for intent classification (fallback)
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3, api_key=os.getenv("OPENAI_API_KEY"))

        # Agent capability metadata (for routing)
        self.agent_capabilities = {
            "pm-agent": {
                "keywords": [
                    "project",
                    "task",
                    "story",
                    "epic",
                    "requirement",
                    "plan",
                    "manage",
                    "organize",
                    "notion",
                    "timeline",
                    "create task",
                    "track",
                    "dependency",
                    "sprint",
                    "backlog",
                    "milestone",
                    "roadmap",
                ],
                "description": "Project management, task creation, Notion integration",
                "priority": 1,  # Default agent
            },
            "data-agent": {
                "keywords": [
                    "data",
                    "query",
                    "database",
                    "report",
                    "analytics",
                    "sql",
                    "chart",
                    "dashboard",
                    "metrics",
                    "insights",
                    "analyze",
                    "aggregate",
                    "filter",
                ],
                "description": "Data analysis, SQL queries, reporting",
                "priority": 2,
            },
            "storage-agent": {
                "keywords": [
                    "file",
                    "upload",
                    "download",
                    "document",
                    "storage",
                    "save",
                    "retrieve",
                    "archive",
                    "persist",
                    "store",
                ],
                "description": "File operations, document management, data persistence",
                "priority": 3,
            },
            "code-agent": {
                "keywords": [
                    "code",
                    "debug",
                    "implement",
                    "refactor",
                    "function",
                    "class",
                    "api",
                    "endpoint",
                    "test",
                    "deploy",
                ],
                "description": "Code generation, debugging, technical implementation",
                "priority": 4,
            },
        }

        # Build the StateGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph StateGraph for supervisor workflow"""

        # Create graph
        graph = StateGraph(AgentState)

        # Add nodes
        graph.add_node("analyze_intent", self._analyze_intent)
        graph.add_node("set_primary_goal", self._set_primary_goal)
        graph.add_node("decompose_goals", self._decompose_goals)
        graph.add_node("route_sub_goal", self._route_sub_goal)
        graph.add_node("execute_agent", self._execute_agent)
        graph.add_node("check_completion", self._check_completion)
        graph.add_node("aggregate_results", self._aggregate_results)
        graph.add_node("complete", self._complete)
        graph.add_node("error", self._error)

        # Add edges
        graph.add_edge("analyze_intent", "set_primary_goal")
        graph.add_edge("set_primary_goal", "decompose_goals")
        graph.add_conditional_edges(
            "decompose_goals", self._should_continue_to_routing, {"route": "route_sub_goal", "error": "error"}
        )
        graph.add_edge("route_sub_goal", "execute_agent")
        graph.add_edge("execute_agent", "check_completion")
        graph.add_conditional_edges(
            "check_completion",
            self._should_continue_execution,
            {"continue": "route_sub_goal", "complete": "aggregate_results", "error": "error"},
        )
        graph.add_edge("aggregate_results", "complete")
        graph.add_edge("complete", END)
        graph.add_edge("error", END)

        # Set entry point
        graph.set_entry_point("analyze_intent")

        return graph.compile()

    async def invoke(
        self, user_input: str, session_id: str, user_id: str | None = None, metadata: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Invoke the supervisor workflow

        Args:
            user_input: User's request
            session_id: Session ID
            user_id: Optional user ID
            metadata: Additional context

        Returns:
            Workflow result with aggregated agent responses
        """
        logger.info(f"🚀 Starting Supervisor Workflow for session {session_id}")
        logger.info(f"   Input: '{user_input[:100]}...'")

        # Broadcast workflow started
        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="started",
                timestamp=time.time(),
                message="Workflow started: analyzing request",
            ),
        )

        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_input)],
            "current_input": user_input,
            "routed_to": [],
            "worker_responses": {},
            "final_response": "",
            "next_agent": "supervisor",
            "session_context": {"session_id": session_id, "user_id": user_id, **(metadata or {})},
            "user_context": None,
            "goal_id": None,
            "primary_goal": None,
            "sub_goals": None,
            "current_sub_goal_id": None,
        }

        try:
            # Execute graph
            result = await self.graph.ainvoke(initial_state)

            # Broadcast completion
            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="completed",
                    timestamp=time.time(),
                    message="Workflow completed successfully",
                ),
            )

            return {
                "output": result.get("final_response", "No response generated"),
                "goal_id": result.get("goal_id"),
                "sub_goals_completed": len(
                    [sg for sg in (result.get("sub_goals") or []) if sg.get("status") == "completed"]
                ),
                "total_sub_goals": len(result.get("sub_goals") or []),
                "agents_used": result.get("routed_to", []),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Workflow error: {e}", exc_info=True)

            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="error",
                    timestamp=time.time(),
                    message=f"Workflow error: {e!s}",
                ),
            )

            return {
                "output": "I encountered an error processing your request. Please try again.",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    # === Graph Nodes ===

    async def _analyze_intent(self, state: AgentState) -> AgentState:
        """
        Node: Analyze user intent (hybrid: keywords + LLM fallback)
        """
        user_input = state["current_input"]
        session_id = state["session_context"]["session_id"]

        logger.info("📊 Analyzing intent...")

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message="Analyzing request intent",
            ),
        )

        # Try keyword matching first (fast path)
        keyword_match = self._keyword_based_intent(user_input)

        if keyword_match["confidence"] >= 2:  # High confidence threshold
            intent = keyword_match["agent_id"]
            logger.info(f"   ✓ Keyword match: {intent} (confidence: {keyword_match['confidence']})")
        else:
            # Fallback to LLM classification
            logger.info("   → Using LLM for intent classification")
            intent = await self._llm_based_intent(user_input)
            logger.info(f"   ✓ LLM classified: {intent}")

        # Store in state metadata
        state["session_context"]["primary_intent"] = intent
        state["session_context"]["intent_method"] = "keyword" if keyword_match["confidence"] >= 2 else "llm"

        return state

    def _keyword_based_intent(self, user_input: str) -> dict[str, Any]:
        """Keyword-based intent matching"""
        user_input_lower = user_input.lower()

        scores = {}
        for agent_id, config in self.agent_capabilities.items():
            score = sum(1 for keyword in config["keywords"] if keyword in user_input_lower)
            if score > 0:
                scores[agent_id] = score

        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            return {"agent_id": best_agent[0], "confidence": best_agent[1], "all_scores": scores}

        return {"agent_id": "pm-agent", "confidence": 0, "all_scores": {}}

    async def _llm_based_intent(self, user_input: str) -> str:
        """LLM-based intent classification (fallback)"""
        system_prompt = f"""You are an intent classification assistant.
Given a user request, classify which agent should handle it.

Available agents:
{chr(10).join(f"- {aid}: {config['description']}" for aid, config in self.agent_capabilities.items())}

Return ONLY the agent ID, nothing else."""

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]

        response = await self.llm.ainvoke(messages)
        intent = response.content.strip().lower()

        # Validate intent
        if intent not in self.agent_capabilities:
            intent = "pm-agent"  # Default

        return intent

    async def _set_primary_goal(self, state: AgentState) -> AgentState:
        """
        Node: Set primary goal from user input
        """
        user_input = state["current_input"]
        session_id = state["session_context"]["session_id"]
        user_id = state["session_context"].get("user_id")

        logger.info("🎯 Setting primary goal...")

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message="Extracting primary goal",
            ),
        )

        # Create goal with goal_manager
        goal = await goal_manager.create_goal_from_user_input(
            user_input=user_input,
            session_id=session_id,
            metadata={"user_id": user_id, "intent": state["session_context"].get("primary_intent")},
        )

        # Update state
        state["goal_id"] = goal.id
        state["primary_goal"] = goal.description
        state["sub_goals"] = [sg.to_dict() for sg in goal.sub_goals]

        logger.info(f"   ✓ Primary goal: {goal.description}")
        logger.info(f"   ✓ Sub-goals: {len(goal.sub_goals)}")

        return state

    async def _decompose_goals(self, state: AgentState) -> AgentState:
        """
        Node: Goals are already decomposed by goal_manager, just validate
        """
        session_id = state["session_context"]["session_id"]

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message=f"Decomposed into {len(state['sub_goals'])} sub-goals",
            ),
        )

        logger.info(f"   ✓ {len(state['sub_goals'])} sub-goals ready for routing")

        return state

    async def _route_sub_goal(self, state: AgentState) -> AgentState:
        """
        Node: Route the next pending sub-goal to appropriate agent
        """
        goal_id = state["goal_id"]
        session_id = state["session_context"]["session_id"]

        # Get next pending sub-goal
        goal = goal_manager.get_goal(goal_id)
        next_sub_goal = goal.get_next_pending_sub_goal()

        if not next_sub_goal:
            logger.warning("No pending sub-goals found")
            return state

        # Mark as active
        goal_manager.update_sub_goal_status(goal_id, next_sub_goal.id, GoalStatus.ACTIVE)

        # Determine which agent to use
        agent_id = next_sub_goal.assigned_agent or self._route_sub_goal_to_agent(next_sub_goal.description)

        logger.info(f"   → Routing sub-goal '{next_sub_goal.description}' to {agent_id}")

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message=f"Routing to {agent_id}: {next_sub_goal.description}",
            ),
        )

        # Update state
        state["current_sub_goal_id"] = next_sub_goal.id
        state["session_context"]["current_sub_goal_agent"] = agent_id

        if agent_id not in state["routed_to"]:
            state["routed_to"].append(agent_id)

        return state

    def _route_sub_goal_to_agent(self, sub_goal_description: str) -> str:
        """Match sub-goal to agent based on keywords"""
        match_result = self._keyword_based_intent(sub_goal_description)
        return match_result["agent_id"]

    async def _execute_agent(self, state: AgentState) -> AgentState:
        """
        Node: Execute the assigned agent for current sub-goal
        """
        goal_id = state["goal_id"]
        sub_goal_id = state["current_sub_goal_id"]
        agent_id = state["session_context"]["current_sub_goal_agent"]
        session_id = state["session_context"]["session_id"]

        logger.info(f"   🤖 Executing {agent_id}...")

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=agent_id,
                agent_name=self.agent_capabilities.get(agent_id, {}).get("description", agent_id),
                event_type="started",
                timestamp=time.time(),
                message="Processing sub-goal",
            ),
        )

        try:
            # Get sub-goal
            goal = goal_manager.get_goal(goal_id)
            sub_goal = next((sg for sg in goal.sub_goals if sg.id == sub_goal_id), None)

            if not sub_goal:
                raise ValueError(f"Sub-goal {sub_goal_id} not found")

            # Invoke agent (TODO: Replace with actual marshal agent invocation)
            result = await self._invoke_domain_agent(
                agent_id=agent_id, task=sub_goal.description, session_id=session_id
            )

            # Mark sub-goal as completed
            goal_manager.update_sub_goal_status(goal_id, sub_goal_id, GoalStatus.COMPLETED, result={"output": result})

            # Store result in state
            state["worker_responses"][sub_goal_id] = result

            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=agent_id,
                    agent_name=self.agent_capabilities.get(agent_id, {}).get("description", agent_id),
                    event_type="completed",
                    timestamp=time.time(),
                    message="Sub-goal completed",
                ),
            )

        except Exception as e:
            logger.error(f"   ❌ Agent execution error: {e}", exc_info=True)

            # Mark sub-goal as failed
            goal_manager.update_sub_goal_status(goal_id, sub_goal_id, GoalStatus.FAILED, error=str(e))

            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=agent_id,
                    agent_name=self.agent_capabilities.get(agent_id, {}).get("description", agent_id),
                    event_type="error",
                    timestamp=time.time(),
                    message=f"Error: {e!s}",
                ),
            )

        return state

    async def _invoke_domain_agent(self, agent_id: str, task: str, session_id: str) -> str:
        """
        Invoke a domain agent (placeholder - will be replaced with actual marshal agent invocation)
        """
        # TODO: Replace with actual agent invocation via marshal_agent.registry.get(agent_id)
        await asyncio.sleep(0.3)  # Simulate processing

        return f"[{agent_id}] Completed task: {task}"

    async def _check_completion(self, state: AgentState) -> AgentState:
        """
        Node: Check if all sub-goals are completed
        """
        goal_id = state["goal_id"]

        # Check completion status
        is_complete = goal_manager.check_goal_completion(goal_id)

        goal = goal_manager.get_goal(goal_id)
        state["sub_goals"] = [sg.to_dict() for sg in goal.sub_goals]

        logger.info(f"   Completion check: {goal.status.value}")

        return state

    async def _aggregate_results(self, state: AgentState) -> AgentState:
        """
        Node: Aggregate all sub-goal results into final response
        """
        goal_id = state["goal_id"]
        session_id = state["session_context"]["session_id"]

        logger.info("📦 Aggregating results...")

        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message="Aggregating results from all agents",
            ),
        )

        # Get goal with results
        goal = goal_manager.get_goal(goal_id)

        # Build final response
        response_parts = [f"**Goal:** {goal.description}\n"]

        for i, sg in enumerate(goal.sub_goals, 1):
            status_emoji = (
                "✅" if sg.status == GoalStatus.COMPLETED else "❌" if sg.status == GoalStatus.FAILED else "⏳"
            )
            response_parts.append(f"\n{i}. {status_emoji} {sg.description}")

            if sg.result:
                response_parts.append(f"   {sg.result.get('output', '')}")
            elif sg.error:
                response_parts.append(f"   Error: {sg.error}")

        final_response = "\n".join(response_parts)
        state["final_response"] = final_response

        logger.info("   ✓ Results aggregated")

        return state

    async def _complete(self, state: AgentState) -> AgentState:
        """
        Node: Workflow complete
        """
        logger.info("✅ Workflow complete")
        return state

    async def _error(self, state: AgentState) -> AgentState:
        """
        Node: Error handling
        """
        logger.error("❌ Workflow error state reached")
        state["final_response"] = "An error occurred while processing your request."
        return state

    # === Conditional Edges ===

    def _should_continue_to_routing(self, state: AgentState) -> Literal["route", "error"]:
        """Conditional: Check if we have sub-goals to route"""
        if state.get("sub_goals") and len(state["sub_goals"]) > 0:
            return "route"
        return "error"

    def _should_continue_execution(self, state: AgentState) -> Literal["continue", "complete", "error"]:
        """Conditional: Check if there are more sub-goals to execute"""
        goal_id = state.get("goal_id")
        if not goal_id:
            return "error"

        goal = goal_manager.get_goal(goal_id)
        if not goal:
            return "error"

        # Check if there are more pending sub-goals
        if goal.get_next_pending_sub_goal():
            return "continue"

        # Check if goal is complete
        if goal.status == GoalStatus.COMPLETED:
            return "complete"

        # If we have failed sub-goals but nothing pending, still complete
        return "complete"


# Singleton instance
supervisor_graph = SupervisorGraph()
