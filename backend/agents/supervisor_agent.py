"""
Supervisor Agent - Central Router
Routes user requests to appropriate domain agents based on intent analysis.

Flow:
  IO Agent → Supervisor Agent → Domain Agent (pm-agent, etc.) → Response
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent that analyzes user intent and routes to appropriate agents.
    """

    def __init__(self):
        self.agent_id = "supervisor_agent"
        self.agent_name = "Supervisor Agent"

        # Agent routing map: intent keywords → agent_id
        self.routing_map = {
            "pm-agent": [
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
            ],
            # Add more agents here as they're implemented
            # "data-agent": ["data", "query", "database", "report"],
            # "code-agent": ["code", "debug", "implement", "refactor"],
        }

    async def route(self, user_input: str, session_id: str, target_agent_id: str | None = None) -> dict[str, Any]:
        """
        Route user input to the appropriate agent.

        Args:
            user_input: User's message/request
            session_id: Session ID for tracking
            target_agent_id: Optional specific agent to route to

        Returns:
            Dict with agent response
        """
        import time

        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        logger.info(f"🎯 Supervisor routing request from session {session_id}")
        logger.info(f"   Input: '{user_input[:100]}...'")

        # Broadcast user message to activity stream
        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id="user",
                agent_name="User",
                event_type="user_message",
                timestamp=time.time(),
                message=user_input,
                metadata={"full_text": user_input},
            ),
        )

        # Determine which agent to use
        if target_agent_id:
            # Explicit routing
            selected_agent = target_agent_id
            logger.info(f"   → Explicit routing to: {selected_agent}")
        else:
            # Intent-based routing
            selected_agent = self._analyze_intent(user_input)
            logger.info(f"   → Intent-based routing to: {selected_agent}")

        # Route to the selected agent
        try:
            response = await self._invoke_agent(agent_id=selected_agent, user_input=user_input, session_id=session_id)

            # Broadcast agent message to activity stream
            if response and response.get("output"):
                await observability_agent.broadcast_activity(
                    session_id,
                    AgentActivity(
                        agent_id=response.get("agent_id", selected_agent),
                        agent_name=selected_agent.replace("-", " ").replace("_", " ").title(),
                        event_type="agent_message",
                        timestamp=time.time(),
                        message=response["output"],
                        metadata={"full_text": response["output"], "interrupted": response.get("interrupted", False)},
                    ),
                )

            return response
        except Exception as e:
            logger.error(f"❌ Error routing to {selected_agent}: {e}", exc_info=True)
            # Re-raise exceptions to propagate up to the HTTP handler
            raise

    def _analyze_intent(self, user_input: str) -> str:
        """
        Analyze user input to determine which agent should handle it.

        Args:
            user_input: User's message

        Returns:
            Agent ID to route to
        """
        user_input_lower = user_input.lower()

        # Check each agent's keywords
        scores = {}
        for agent_id, keywords in self.routing_map.items():
            score = sum(1 for keyword in keywords if keyword in user_input_lower)
            if score > 0:
                scores[agent_id] = score

        if scores:
            # Return agent with highest score
            best_agent = max(scores.items(), key=lambda x: x[1])[0]
            logger.info(f"   Intent analysis scores: {scores} → {best_agent}")
            return best_agent

        # Default to pm-agent if no clear intent
        logger.info("   No clear intent match, defaulting to pm-agent")
        return "pm-agent"

    async def _invoke_agent(self, agent_id: str, user_input: str, session_id: str) -> dict[str, Any]:
        """
        Invoke a specific domain agent via Marshal registry.

        Args:
            agent_id: ID of the agent to invoke
            user_input: User's request
            session_id: Session ID

        Returns:
            Agent response dict
        """
        logger.info(f"📞 Invoking agent: {agent_id}")

        import time

        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        # Broadcast activity: started
        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="started",
                timestamp=time.time(),
                message=f"Routing to {agent_id}",
            ),
        )

        # Try to load agent dynamically from Marshal registry
        response_text = None
        interrupted = False
        try:
            # Import marshal instance from main.py
            from backend.main import marshal

            if marshal is not None:
                # Check if agent exists in registry
                # Try both hyphen and underscore versions for compatibility
                agent_instance = await marshal.registry.get(agent_id)

                # If not found, try alternate format (hyphens vs underscores)
                if not agent_instance:
                    alternate_id = agent_id.replace("_", "-") if "_" in agent_id else agent_id.replace("-", "_")
                    agent_instance = await marshal.registry.get(alternate_id)
                    if agent_instance:
                        logger.info(f"✅ Found agent using alternate ID format: {alternate_id}")
                        agent_id = alternate_id  # Use the found ID for subsequent calls

                if agent_instance:
                    logger.info(f"✅ Found agent in registry: {agent_id}")
                    # Agent exists - invoke it directly via registry
                    response_text, interrupted = await self._invoke_registry_agent(
                        agent_instance=agent_instance, agent_id=agent_id, user_input=user_input, session_id=session_id
                    )
                else:
                    logger.warning(f"⚠️  Agent {agent_id} not found in registry")

        except Exception as e:
            logger.warning(f"⚠️  Could not load agent from registry: {e}")

        # Fail fast if agent not found - no silent fallbacks
        if response_text is None:
            error_msg = f"Agent '{agent_id}' not found in registry. The agent may not be deployed or the backend is still initializing."
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # Broadcast activity: completed
        await observability_agent.broadcast_activity(
            session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="completed",
                timestamp=time.time(),
                message=f"Routed to {agent_id}, response ready",
                metadata={"target_agent": agent_id},
            ),
        )

        return {
            "output": response_text,
            "agent_id": agent_id,
            "supervisor": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "interrupted": interrupted,
        }

    async def _invoke_registry_agent(
        self, agent_instance: Any, agent_id: str, user_input: str, session_id: str
    ) -> tuple[str, bool]:
        """
        Invoke an agent from the Marshal registry with interrupt support.

        Args:
            agent_instance: The compiled agent graph from registry
            agent_id: Agent ID
            user_input: User input
            session_id: Session ID

        Returns:
            Tuple of (response_text, interrupted_flag)
        """
        import time

        from langchain_core.messages import HumanMessage
        from langgraph.errors import GraphInterrupt

        from backend.agents.system.observability_agent import AgentActivity, observability_agent
        from backend.middleware.observability_middleware import ObservabilityMiddleware

        try:
            # Create observability middleware for this agent execution
            agent_name = agent_id.replace("-", " ").replace("_", " ").title()
            middleware = ObservabilityMiddleware(session_id=session_id, agent_id=agent_id, agent_name=agent_name)

            # Broadcast agent activity: started
            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    event_type="started",
                    timestamp=time.time(),
                    message="Processing request",
                ),
            )

            # Thread configuration for checkpointing (use session_id as thread_id)
            thread_config = {"configurable": {"thread_id": session_id}}

            # Check if conversation is already in progress (interrupted state exists)
            try:
                existing_state = await agent_instance.graph.aget_state(thread_config)
                has_interrupted_workflow = len(existing_state.next) > 0
            except:
                has_interrupted_workflow = False

            # Invoke the agent graph from registry (wrapped with observability middleware)
            if has_interrupted_workflow:
                # Resume from interrupt using Command
                from langgraph.types import Command

                logger.info(f"🔄 Resuming interrupted workflow for session {session_id}")

                # Wrap with middleware for observability
                result = await middleware.wrap_graph_execution(
                    agent_instance.graph.ainvoke, Command(resume=user_input), thread_config
                )
            else:
                # Fresh start - pass messages
                logger.info(f"🆕 Starting fresh workflow for session {session_id}")

                # Wrap with middleware for observability
                result = await middleware.wrap_graph_execution(
                    agent_instance.graph.ainvoke, {"messages": [HumanMessage(content=user_input)]}, thread_config
                )

            # Check if graph is interrupted by examining the state
            # With checkpointers, interrupts don't raise exceptions - they just pause execution
            state = await agent_instance.graph.aget_state(thread_config)
            interrupted = len(state.next) > 0  # If there are pending nodes, it's interrupted

            # Extract response
            response_text = result.get("final_response", "")
            if not response_text and result.get("messages"):
                last_message = result["messages"][-1]
                response_text = last_message.content if hasattr(last_message, "content") else str(last_message)

            # If interrupted and no final_response, get the interrupt prompt from state
            if interrupted and not response_text:
                # Get interrupt value from state
                if hasattr(state, "tasks") and state.tasks:
                    for task in state.tasks:
                        if hasattr(task, "interrupts") and task.interrupts:
                            interrupt_value = task.interrupts[0].value
                            response_text = interrupt_value.get("prompt", "I need more information to continue.")
                            logger.info(f"🔄 Using interrupt prompt: {response_text}")
                            break

            if interrupted:
                # Broadcast interrupt event
                logger.info(f"🔄 Graph interrupted for session {session_id}")
                await observability_agent.broadcast_activity(
                    session_id,
                    AgentActivity(
                        agent_id=agent_id,
                        agent_name=agent_id.replace("-", " ").replace("_", " ").title(),
                        event_type="interrupted",
                        timestamp=time.time(),
                        message="Waiting for user input",
                        metadata={"next_nodes": state.next},
                    ),
                )
                return response_text, True  # Interrupted!
            else:
                # Broadcast agent activity: completed
                await observability_agent.broadcast_activity(
                    session_id,
                    AgentActivity(
                        agent_id=agent_id,
                        agent_name=agent_id.replace("-", " ").replace("_", " ").title(),
                        event_type="completed",
                        timestamp=time.time(),
                        message="Response generated",
                        metadata={"response_length": len(response_text)},
                    ),
                )
                return response_text, False  # Not interrupted

        except GraphInterrupt as e:
            # Graph interrupted - waiting for user input
            logger.info(f"🔄 Graph interrupted for session {session_id}, waiting for user input")

            # Extract interrupt data
            interrupt_data = e.value if hasattr(e, "value") else {}

            # Broadcast interrupt event
            await observability_agent.broadcast_activity(
                session_id,
                AgentActivity(
                    agent_id=agent_id,
                    agent_name=agent_id.replace("-", " ").replace("_", " ").title(),
                    event_type="interrupted",
                    timestamp=time.time(),
                    message="Waiting for user input",
                    metadata=interrupt_data,
                ),
            )

            # Return interrupt prompt to user
            prompt = interrupt_data.get("prompt", "I need more information to continue.")
            logger.info(f"Returning interrupt prompt: {prompt}")
            return prompt, True  # Interrupted!

        except Exception as e:
            logger.error(f"❌ Failed to invoke registry agent {agent_id}: {e}")
            raise

    async def _invoke_dynamic_agent(self, agent_id: str, user_input: str, session_id: str) -> str:
        """
        Dynamically invoke an agent loaded from the file system.

        This loads the agent's Python module and executes its graph.

        Args:
            agent_id: Agent ID (maps to agents/{agent_id}.py)
            user_input: User input
            session_id: Session ID

        Returns:
            Agent response text
        """
        import importlib.util
        import time
        from pathlib import Path

        from backend.agents.system.observability_agent import AgentActivity, observability_agent

        try:
            # Load agent module dynamically
            # Sanitize agent_id (replace hyphens with underscores for Python module name)
            sanitized_id = agent_id.replace("-", "_")
            agent_file = Path(__file__).parent.parent.parent / "agents" / f"{sanitized_id}.py"

            if not agent_file.exists():
                raise FileNotFoundError(f"Agent file not found: {agent_file}")

            # Import the module
            spec = importlib.util.spec_from_file_location(agent_id, agent_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for 'graph' or 'agent' attribute in module
                if hasattr(module, "graph"):
                    agent_graph = module.graph
                elif hasattr(module, "agent"):
                    agent_graph = module.agent
                else:
                    raise AttributeError(f"No 'graph' or 'agent' found in {agent_id}.py")

                # Broadcast agent activity
                await observability_agent.broadcast_activity(
                    session_id,
                    AgentActivity(
                        agent_id=agent_id,
                        agent_name=agent_id.replace("-", " ").title(),
                        event_type="started",
                        timestamp=time.time(),
                        message="Processing request",
                    ),
                )

                # Invoke the agent graph
                from langchain_core.messages import HumanMessage

                result = await agent_graph.ainvoke({"messages": [HumanMessage(content=user_input)]})

                # Extract response
                response_text = result["messages"][-1].content if result.get("messages") else "No response generated"

                # Broadcast completion
                await observability_agent.broadcast_activity(
                    session_id,
                    AgentActivity(
                        agent_id=agent_id,
                        agent_name=agent_id.replace("-", " ").title(),
                        event_type="completed",
                        timestamp=time.time(),
                        message="Response generated",
                    ),
                )

                return response_text

        except Exception as e:
            logger.error(f"❌ Failed to invoke dynamic agent {agent_id}: {e}", exc_info=True)
            raise

# Singleton instance
import asyncio

supervisor_agent = SupervisorAgent()
