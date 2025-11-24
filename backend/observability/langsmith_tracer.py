"""
LangSmith Tracer Integration
============================
Provides LangSmith callback handlers for tracing LangGraph agent executions
and capturing token usage for cost tracking.

Environment Variables:
    LANGSMITH_API_KEY: API key for LangSmith
    LANGSMITH_PROJECT: Project name in LangSmith (default: agent-foundry)
    LANGSMITH_TRACING: Enable/disable tracing (default: true)
    LANGSMITH_ENDPOINT: LangSmith API endpoint

Usage:
    from backend.observability.langsmith_tracer import get_langsmith_callbacks

    # Get callbacks for agent execution
    callbacks = get_langsmith_callbacks(
        session_id="session-123",
        agent_id="my-agent",
        metadata={"user_id": "user-456"}
    )

    # Use with LangGraph
    result = await agent.ainvoke(input_state, config={"callbacks": callbacks})
"""

import logging
import os
from datetime import datetime
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)


def langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled"""
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    tracing = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    return bool(api_key) and tracing


def get_langsmith_callbacks(
    session_id: str | None = None,
    agent_id: str | None = None,
    run_name: str | None = None,
    metadata: dict[str, Any] | None = None,
    include_token_callback: bool = True,
) -> list[BaseCallbackHandler]:
    """
    Get LangSmith callback handlers for agent tracing.

    Args:
        session_id: Session identifier for grouping traces
        agent_id: Agent identifier
        run_name: Custom run name for this trace
        metadata: Additional metadata to attach to trace
        include_token_callback: Include token usage callback

    Returns:
        List of callback handlers to pass to LangChain/LangGraph
    """
    callbacks: list[BaseCallbackHandler] = []

    # Add token tracking callback first (always)
    if include_token_callback:
        callbacks.append(LangSmithTokenCallback(session_id=session_id, agent_id=agent_id))

    # Add LangSmith tracer if enabled
    if langsmith_enabled():
        try:
            from langchain_core.tracers import LangChainTracer
            from langsmith import Client

            # Create LangSmith client
            client = Client(
                api_key=os.getenv("LANGSMITH_API_KEY"),
                api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
            )

            # Configure tracer
            project_name = os.getenv("LANGSMITH_PROJECT", "agent-foundry")
            tracer = LangChainTracer(
                project_name=project_name,
                client=client,
            )

            # Set run metadata
            if run_name:
                tracer.name = run_name

            callbacks.append(tracer)
            logger.debug(f"LangSmith tracer enabled for project: {project_name}")

        except ImportError:
            logger.warning("langsmith package not installed, skipping LangSmith integration")
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith tracer: {e}")

    return callbacks


class LangSmithTokenCallback(BaseCallbackHandler):
    """
    Callback handler that tracks token usage from LLM calls.
    Captures prompt tokens, completion tokens, and total tokens
    for cost calculation.
    """

    def __init__(self, session_id: str | None = None, agent_id: str | None = None):
        super().__init__()
        self.session_id = session_id
        self.agent_id = agent_id
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.model_usage: dict[str, dict[str, int]] = {}
        self._start_time: datetime | None = None

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        """Called when LLM starts generating"""
        self._start_time = datetime.utcnow()
        self.call_count += 1

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        **kwargs: Any,
    ) -> None:
        """Called when chat model starts"""
        self._start_time = datetime.utcnow()
        self.call_count += 1

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Called when LLM finishes generating. Extract token usage.
        """
        if not response.llm_output:
            return

        # Extract token usage from response
        token_usage = response.llm_output.get("token_usage", {})
        model_name = response.llm_output.get("model_name", "unknown")

        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        total_tokens = token_usage.get("total_tokens", prompt_tokens + completion_tokens)

        # Update totals
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total_tokens

        # Track by model
        if model_name not in self.model_usage:
            self.model_usage[model_name] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "calls": 0}

        self.model_usage[model_name]["prompt_tokens"] += prompt_tokens
        self.model_usage[model_name]["completion_tokens"] += completion_tokens
        self.model_usage[model_name]["total_tokens"] += total_tokens
        self.model_usage[model_name]["calls"] += 1

        # Log token usage
        logger.debug(
            f"LLM tokens - model: {model_name}, "
            f"prompt: {prompt_tokens}, "
            f"completion: {completion_tokens}, "
            f"total: {total_tokens}"
        )

        # Persist to observability database (fire-and-forget)
        self._persist_token_usage(model_name, prompt_tokens, completion_tokens, total_tokens)

    def on_llm_error(self, error: Exception | KeyboardInterrupt, **kwargs: Any) -> None:
        """Called when LLM errors"""
        logger.error(f"LLM error in session {self.session_id}: {error}")

    def _persist_token_usage(
        self, model_name: str, prompt_tokens: int, completion_tokens: int, total_tokens: int
    ) -> None:
        """
        Persist token usage to the observability database.
        This is a fire-and-forget operation.
        """
        try:
            import asyncio

            from mcp.tools.observability_tools import save_activity

            # Calculate duration if we have start time
            duration_ms = None
            if self._start_time:
                duration_ms = int((datetime.utcnow() - self._start_time).total_seconds() * 1000)

            # Save as activity with token metadata
            asyncio.create_task(
                asyncio.to_thread(
                    save_activity,
                    session_id=self.session_id or "unknown",
                    agent_id=self.agent_id or "unknown",
                    agent_name=self.agent_id or "Unknown Agent",
                    event_type="llm_call",
                    message=f"LLM call to {model_name}",
                    metadata={
                        "model": model_name,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "duration_ms": duration_ms,
                    },
                )
            )
        except Exception as e:
            # Don't let persistence errors break the flow
            logger.warning(f"Failed to persist token usage: {e}")

    def get_usage_summary(self) -> dict[str, Any]:
        """Get summary of token usage for this callback instance"""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "by_model": self.model_usage,
        }


# Convenience function to get tracer config for LangGraph
def get_langchain_config(
    session_id: str | None = None,
    agent_id: str | None = None,
    run_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Get a complete LangChain config dict with callbacks configured.

    Usage:
        config = get_langchain_config(session_id="...", agent_id="...")
        result = await agent.ainvoke(state, config=config)
    """
    callbacks = get_langsmith_callbacks(session_id=session_id, agent_id=agent_id, run_name=run_name, metadata=metadata)

    config: dict[str, Any] = {"callbacks": callbacks}

    if metadata:
        config["metadata"] = metadata

    if run_name:
        config["run_name"] = run_name

    # Add tags for LangSmith filtering
    tags = []
    if session_id:
        tags.append(f"session:{session_id}")
    if agent_id:
        tags.append(f"agent:{agent_id}")
    if tags:
        config["tags"] = tags

    return config
