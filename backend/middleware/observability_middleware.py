"""
LangGraph Observability Middleware
Intercepts graph execution to emit real-time activity events for monitoring.
Includes OpenTelemetry span instrumentation for distributed tracing.
"""

import time
from collections.abc import Callable
from typing import Any

from backend.agents.system.observability_agent import AgentActivity, observability_agent


class ObservabilityMiddleware:
    """
    Middleware that wraps LangGraph node execution to broadcast activity events.

    Usage:
        middleware = ObservabilityMiddleware(
            session_id="session-123",
            agent_id="my-agent",
            agent_name="My Agent"
        )

        # Wrap graph with middleware
        result = await middleware.wrap_graph_execution(graph.ainvoke, input_data, config)
    """

    def __init__(self, session_id: str, agent_id: str, agent_name: str):
        self.session_id = session_id
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.node_start_times: dict[str, float] = {}

    async def on_node_start(self, node_name: str, state: dict[str, Any]):
        """Called when a node starts executing"""
        self.node_start_times[node_name] = time.time()

        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message=f"Executing node: {node_name}",
                metadata={"node": node_name, "state_keys": list(state.keys()) if state else []},
            ),
        )

    async def on_node_end(self, node_name: str, result: Any, error: Exception | None = None):
        """Called when a node finishes executing"""
        duration = None
        if node_name in self.node_start_times:
            duration = time.time() - self.node_start_times[node_name]
            del self.node_start_times[node_name]

        if error:
            await observability_agent.broadcast_activity(
                self.session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="error",
                    timestamp=time.time(),
                    message=f"Node {node_name} failed: {str(error)[:100]}",
                    metadata={"node": node_name, "error": str(error), "duration": duration},
                ),
            )
        else:
            await observability_agent.broadcast_activity(
                self.session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="processing",
                    timestamp=time.time(),
                    message=f"Completed node: {node_name}",
                    metadata={"node": node_name, "duration": duration, "status": "completed"},
                ),
            )

    async def on_tool_call_start(self, tool_name: str, tool_input: dict[str, Any]):
        """Called before a tool is executed"""
        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="tool_call",
                timestamp=time.time(),
                message=f"Calling tool: {tool_name}",
                metadata={"tool": tool_name, "input": tool_input, "status": "started"},
            ),
        )

    async def on_tool_call_end(self, tool_name: str, tool_output: Any, duration: float, error: Exception | None = None):
        """Called after a tool finishes executing"""
        if error:
            await observability_agent.broadcast_activity(
                self.session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="error",
                    timestamp=time.time(),
                    message=f"Tool {tool_name} failed: {str(error)[:100]}",
                    metadata={"tool": tool_name, "error": str(error), "duration": duration, "status": "failed"},
                ),
            )
        else:
            await observability_agent.broadcast_activity(
                self.session_id,
                AgentActivity(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    event_type="tool_call",
                    timestamp=time.time(),
                    message=f"Tool {tool_name} completed",
                    metadata={
                        "tool": tool_name,
                        "output": str(tool_output)[:200] if tool_output else None,  # Truncate output
                        "duration": duration,
                        "status": "completed",
                    },
                ),
            )

    async def on_llm_call(self, prompt: str, model: str = "unknown"):
        """Called when an LLM is invoked"""
        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message=f"Calling LLM model: {model}",
                metadata={"model": model, "prompt_length": len(prompt), "type": "llm_call"},
            ),
        )

    async def wrap_graph_execution(self, graph_invoke: Callable, input_data: Any, config: dict[str, Any]) -> Any:
        """
        Wrap a graph execution to intercept and broadcast activities.

        This wrapper:
        1. Broadcasts start/end events
        2. Injects tool tracking callbacks for granular visibility
        3. Injects LangSmith tracing callbacks for distributed tracing
        4. Handles errors and broadcasts them
        """
        from backend.middleware.tool_tracking_callback import ToolTrackingCallback
        from backend.observability import create_span, get_langsmith_callbacks, record_agent_execution, record_exception

        # Broadcast processing start
        await observability_agent.broadcast_activity(
            self.session_id,
            AgentActivity(
                agent_id=self.agent_id,
                agent_name=self.agent_name,
                event_type="processing",
                timestamp=time.time(),
                message="Starting agent execution",
                metadata={"config": config},
            ),
        )

        start_time = time.time()

        # Create OTEL span for distributed tracing
        with create_span(
            f"agent.{self.agent_id}.execute",
            {
                "agent.id": self.agent_id,
                "agent.name": self.agent_name,
                "session.id": self.session_id,
            },
        ) as span:
            try:
                # Create tool tracking callback
                tool_callback = ToolTrackingCallback(
                    session_id=self.session_id, agent_id=self.agent_id, agent_name=self.agent_name
                )

                # Get LangSmith callbacks (includes token tracking)
                langsmith_callbacks = get_langsmith_callbacks(
                    session_id=self.session_id, agent_id=self.agent_id, run_name=f"{self.agent_name} execution"
                )

                # Inject callbacks into config
                # LangGraph accepts callbacks in the config dict
                if "callbacks" not in config:
                    config["callbacks"] = []
                config["callbacks"].append(tool_callback)
                config["callbacks"].extend(langsmith_callbacks)

                # Execute the graph with callbacks
                result = await graph_invoke(input_data, config)

                duration = time.time() - start_time

                # Record metrics
                record_agent_execution(self.agent_id, "success", duration)

                # Set span attributes
                span.set_attribute("agent.duration_ms", int(duration * 1000))
                span.set_attribute("agent.status", "success")

                # Broadcast completion
                await observability_agent.broadcast_activity(
                    self.session_id,
                    AgentActivity(
                        agent_id=self.agent_id,
                        agent_name=self.agent_name,
                        event_type="completed",
                        timestamp=time.time(),
                        message="Agent execution completed",
                        metadata={
                            "duration": duration,
                            "result_keys": list(result.keys()) if isinstance(result, dict) else None,
                        },
                    ),
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                # Record error metrics
                record_agent_execution(self.agent_id, "error", duration)

                # Record exception in span
                record_exception(span, e, {"agent.id": self.agent_id})
                span.set_attribute("agent.status", "error")
                span.set_attribute("agent.duration_ms", int(duration * 1000))

                # Broadcast error
                await observability_agent.broadcast_activity(
                    self.session_id,
                    AgentActivity(
                        agent_id=self.agent_id,
                        agent_name=self.agent_name,
                        event_type="error",
                        timestamp=time.time(),
                        message=f"Agent execution failed: {str(e)[:100]}",
                        metadata={"duration": duration, "error": str(e)},
                    ),
                )

                raise


def create_observability_callbacks(middleware: ObservabilityMiddleware) -> dict[str, Any]:
    """
    Create LangGraph callback handlers from middleware.

    Returns a dictionary that can be added to the graph config:
        config = {"configurable": {...}, "callbacks": [...]}
    """
    # TODO: Implement LangGraph-specific callbacks
    # This will depend on the LangGraph callback API
    # For now, return empty dict
    return {}
