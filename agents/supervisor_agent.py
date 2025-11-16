"""
Supervisor Agent - LangGraph orchestrator for worker agents

Responsibilities:
- Receive message from io_agent
- Load context via context_agent
- Analyze intent and route to appropriate worker agent(s)
- Aggregate responses via coherence_agent
- Return unified response to io_agent

Uses LangGraph StateGraph for coordination.
"""

import logging
import asyncio
from typing import Literal, List, Any, Callable, Dict

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

from .state import AgentState, IOState
from .workers.pm_agent import PMAgent
from .workers.context_agent import ContextAgent
from .workers.coherence_agent import CoherenceAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor orchestrates worker agents via LangGraph.
    Coordinates context enrichment, worker routing, and response coherence.
    """
    
    def __init__(self):
        """Initialize supervisor with LangGraph workflow."""
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        
        # Initialize platform agents
        self.context_agent = ContextAgent()
        self.coherence_agent = CoherenceAgent()
        
        # Initialize worker agents
        self.pm_agent = PMAgent()
        
        # Build LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info("SupervisorAgent initialized with LangGraph (context + coherence enabled)")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for agent coordination.
        
        Flow:
        1. load_context: Get session + user context
        2. analyze_request: Determine routing strategy
        3. route_workers: Execute appropriate worker(s)
        4. compile_response: Use coherence agent to assemble final response
        5. END: Return to io_agent
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("load_context", self._load_context_node)
        workflow.add_node("analyze_request", self._analyze_request_node)
        workflow.add_node("pm_agent", self._pm_agent_node)
        workflow.add_node("compile_response", self._compile_response_node)
        
        # Set entry point
        workflow.set_entry_point("load_context")
        
        # Linear flow: context → analysis → routing → compilation
        workflow.add_edge("load_context", "analyze_request")
        
        # Add conditional routing from analysis
        workflow.add_conditional_edges(
            "analyze_request",
            self._route_worker,
            {
                "pm_agent": "pm_agent",
                "FINISH": "compile_response"
            }
        )
        
        # Workers return to compiler
        workflow.add_edge("pm_agent", "compile_response")
        
        # Compiler ends the flow
        workflow.add_edge("compile_response", END)
        
        return workflow.compile()
    
    async def _load_context_node(self, state: AgentState) -> AgentState:
        """
        Load context node: Enriches request with session + user context.
        Delegates to context_agent.
        """
        current_input = state["current_input"]
        session_id = state.get("session_context", {}).get("session_id", "default_session")
        user_id = state.get("user_context", {}).get("user_id", "default_user")
        
        logger.info(f"Loading context for session: {session_id}")
        
        # Get enriched context from context_agent
        enriched_context = await self.context_agent.process(
            session_id=session_id,
            user_id=user_id,
            current_input=current_input
        )
        
        return {
            **state,
            "session_context": enriched_context.get("session", {}),
            "user_context": enriched_context.get("user", {})
        }
    
    async def _analyze_request_node(self, state: AgentState) -> AgentState:
        """
        Analysis node: Determines which worker(s) should handle the request.
        Uses LLM to classify intent and route appropriately.
        """
        user_input = state["current_input"]
        
        # Use LLM to classify intent
        system_prompt = """You are a supervisor agent. Analyze the user's message and determine which worker agent should handle it.

Available workers:
- pm_agent: Handles project management tasks (stories, epics, backlog, priorities, acceptance criteria)
- ticket_agent: Handles tickets, bugs, issues (NOT YET IMPLEMENTED)
- qa_agent: Handles testing, quality assurance (NOT YET IMPLEMENTED)

Respond with ONLY the worker name (pm_agent, ticket_agent, qa_agent) or FINISH if no worker is needed.

User message: {message}

Your response (one word only):"""
        
        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt.format(message=user_input))
        ])
        
        next_agent = response.content.strip().lower()
        
        # Validate and default
        valid_agents = ["pm_agent", "ticket_agent", "qa_agent", "FINISH"]
        if next_agent not in [a.lower() for a in valid_agents]:
            next_agent = "pm_agent"  # Default to PM agent
        
        logger.info(f"Supervisor routing to: {next_agent}")
        
        return {
            **state,
            "next_agent": next_agent,
            "routed_to": [next_agent]
        }
    
    def _route_worker(self, state: AgentState) -> Literal["pm_agent", "ticket_agent", "FINISH"]:
        """
        Router function for conditional edges.
        Returns which worker node to execute next.
        """
        next_agent = state["next_agent"]
        
        if next_agent == "FINISH":
            return "FINISH"
        
        return next_agent
    
    async def _pm_agent_node(self, state: AgentState) -> AgentState:
        """PM Agent worker node."""
        user_input = state["current_input"]
        
        logger.info("Invoking PM Agent")
        response = await self.pm_agent.process(user_input)
        
        # Store worker response
        worker_responses = state.get("worker_responses", {})
        worker_responses["pm_agent"] = response
        
        return {
            **state,
            "worker_responses": worker_responses
        }
    
    async def _compile_response_node(self, state: AgentState) -> AgentState:
        """
        Compilation node: Uses coherence agent to assemble final response.
        Handles deduplication, conflict resolution, and response assembly.
        """
        worker_responses = state.get("worker_responses", {})
        
        logger.info(f"Compiling response from {len(worker_responses)} worker(s)")
        
        if not worker_responses:
            # No workers were called (supervisor returned FINISH)
            final_response = "I'm not sure how to help with that. Could you rephrase?"
        else:
            # Use coherence agent to compile responses
            final_response = await self.coherence_agent.process(worker_responses)
        
        logger.info(f"Final response compiled: {final_response[:100]}...")
        
        return {
            **state,
            "final_response": final_response
        }
    
    async def process(self, io_state: IOState) -> str:
        """
        Process a message from io_agent.
        
        Args:
            io_state: State from io_agent containing user message
        
        Returns:
            Final response string to send back to user
        """
        # Convert IOState to AgentState
        agent_state = AgentState(
            messages=[HumanMessage(content=io_state["user_message"])],
            current_input=io_state["user_message"],
            routed_to=[],
            worker_responses={},
            final_response="",
            next_agent="supervisor",
            session_context={
                "session_id": io_state.get("session_id", "default_session")
            },
            user_context={
                "user_id": io_state.get("user_id", "default_user")
            }
        )
        
        # Run the graph
        result = await self.graph.ainvoke(agent_state)
        
        # Update context_agent with final response for session tracking
        await self.context_agent.update_session_state(
            session_id=io_state.get("session_id", "default_session"),
            user_message=io_state["user_message"],
            assistant_response=result["final_response"]
        )
        
        # Extract final response
        return result["final_response"]
    
    async def execute_parallel_workers(
        self,
        worker_agents: List[Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple worker agents in parallel (for map-reduce patterns).
        
        Args:
            worker_agents: List of worker agent instances
            state: Current state to pass to workers
        
        Returns:
            Dict mapping worker names to their responses
        """
        logger.info(f"Executing {len(worker_agents)} workers in parallel")
        
        # Create tasks for parallel execution
        tasks = []
        worker_names = []
        
        for worker in worker_agents:
            worker_name = worker.__class__.__name__
            worker_names.append(worker_name)
            tasks.append(worker.process(state.get("current_input", "")))
        
        # Execute all workers in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Map results to worker names
            worker_responses = {}
            for name, result in zip(worker_names, results):
                if isinstance(result, Exception):
                    logger.error(f"Worker {name} failed: {result}")
                    worker_responses[name] = f"Error: {result}"
                else:
                    worker_responses[name] = result
            
            logger.info(f"Parallel execution completed: {len(worker_responses)} responses")
            return worker_responses
            
        except Exception as e:
            logger.error(f"Error during parallel execution: {e}", exc_info=True)
            return {}
    
    async def execute_with_timeout(
        self,
        node_func: Callable,
        state: Dict[str, Any],
        timeout_seconds: float = 60.0
    ) -> Any:
        """
        Execute a node function with timeout enforcement.
        
        Args:
            node_func: Node function to execute
            state: State to pass to function
            timeout_seconds: Timeout in seconds
        
        Returns:
            Function result
        
        Raises:
            asyncio.TimeoutError: If execution exceeds timeout
        """
        logger.debug(f"Executing with timeout: {timeout_seconds}s")
        
        try:
            return await asyncio.wait_for(
                node_func(state),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Node execution timed out after {timeout_seconds}s")
            raise
    
    async def enforce_recursion_limit(
        self,
        current_depth: int,
        max_depth: int
    ) -> bool:
        """
        Check if recursion limit has been exceeded (prevent infinite loops).
        
        Args:
            current_depth: Current recursion depth
            max_depth: Maximum allowed depth
        
        Returns:
            True if within limit, False if exceeded
        """
        if current_depth >= max_depth:
            logger.error(f"Recursion limit exceeded: {current_depth}/{max_depth}")
            return False
        return True
    
    async def execute_with_streaming(
        self,
        state: Dict[str, Any],
        stream_mode: bool = False
    ) -> Any:
        """
        Execute graph with optional streaming mode.
        
        Args:
            state: Initial state
            stream_mode: Whether to stream results
        
        Returns:
            Final result (or stream iterator if streaming)
        """
        if stream_mode:
            logger.info("Executing in streaming mode")
            # Return async generator for streaming
            async def stream_results():
                async for chunk in self.graph.astream(state):
                    yield chunk
            return stream_results()
        else:
            logger.info("Executing in batch mode")
            return await self.graph.ainvoke(state)