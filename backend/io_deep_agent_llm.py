"""
DeepAgentLLM - LiveKit LLM Wrapper for Deep Agent Orchestration

This custom LLM wrapper enables deep agent orchestration in voice conversations:
- Proactive greeting before user speaks
- Routes to deep agent backend for planning/execution/criticism
- Manages task loop until all user requests are complete
- Integrates with CIBC orchestrator for card operations

Usage:
    deep_llm = DeepAgentLLM(
        session_id="session_123",
        agent_id="cibc-orchestrator",
        greeting="Thank you for calling CIBC. How can I help you today?"
    )
"""

import logging
import uuid
from collections.abc import AsyncGenerator

import httpx
from livekit.agents import llm

logger = logging.getLogger("deep-agent-llm")
logger.setLevel(logging.INFO)

# Backend API URL for deep agent routing
# Use service discovery (Infrastructure as Registry pattern)
from backend.config.services import SERVICES

BACKEND_API_URL = SERVICES.get_service_url("BACKEND")


class ChatStream:
    """Async context manager that wraps an async generator for LiveKit compatibility."""

    def __init__(self, generator: AsyncGenerator):
        self._generator = generator

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._generator.__anext__()


class DeepAgentLLM(llm.LLM):
    """
    Custom LLM that routes through Deep Agent backend for orchestration.

    Features:
    - Proactive greeting on session start
    - Deep agent planning/execution/criticism cycle
    - Task list management and iteration
    - CIBC tool and agent discovery
    - Continuous loop until all tasks complete
    """

    def __init__(self, session_id: str, agent_id: str, greeting: str | None = None, proactive_greeting: bool = True):
        super().__init__()
        self._session_id = session_id
        self._agent_id = agent_id
        self._greeting = greeting or "Hello! How can I help you today?"
        self._proactive_greeting = proactive_greeting
        self._greeting_sent = False
        self._conversation_active = False

        logger.info(f"🤖 DeepAgentLLM initialized for session {session_id}")
        logger.info(f"🎯 Agent: {agent_id}")
        logger.info(f"👋 Greeting: {self._greeting}")
        logger.info(f"🚀 Proactive greeting: {proactive_greeting}")

    async def send_greeting(self) -> str:
        """
        Send proactive greeting before user speaks.
        Returns the greeting message.
        """
        if self._greeting_sent:
            logger.warning("⚠️ Greeting already sent, skipping")
            return ""

        self._greeting_sent = True
        self._conversation_active = True

        logger.info(f"👋 Sending proactive greeting: {self._greeting}")
        return self._greeting

    def chat(self, *, chat_ctx: llm.ChatContext, **kwargs):
        """
        Override chat() to route through Deep Agent backend.
        Returns an async context manager that yields chat chunks.
        """
        return ChatStream(self._chat_impl(chat_ctx=chat_ctx, **kwargs))

    async def _chat_impl(self, *, chat_ctx: llm.ChatContext, **kwargs) -> AsyncGenerator[llm.ChatChunk, None]:
        """
        Implementation of chat that yields chunks.

        Flow:
        1. If greeting not sent and proactive_greeting enabled → send greeting
        2. Extract user message from chat context
        3. Route to deep agent backend for processing
        4. Stream response back as chunks for TTS
        """
        chunk_id = str(uuid.uuid4())

        # Handle proactive greeting
        if not self._greeting_sent and self._proactive_greeting:
            greeting_text = await self.send_greeting()

            # Stream greeting as chunks
            words = greeting_text.split()
            for i, word in enumerate(words):
                text = word if i == len(words) - 1 else word + " "

                if i == 0:
                    yield llm.ChatChunk(
                        id=chunk_id,
                        delta=llm.ChoiceDelta(role="assistant", content=text),
                    )
                else:
                    yield llm.ChatChunk(
                        id=chunk_id,
                        delta=llm.ChoiceDelta(content=text),
                    )

            # After greeting, wait for user input
            return

        # Extract user message from chat context
        user_message = self._extract_user_message(chat_ctx)

        if not user_message:
            logger.warning("⚠️ No user message found in chat context")
            yield llm.ChatChunk(
                id=chunk_id,
                delta=llm.ChoiceDelta(role="assistant", content="I didn't catch that. Could you please repeat?"),
            )
            return

        logger.info(f"🎤 User said: {user_message}")

        # Route to deep agent backend
        response_text = await self._route_to_deep_agent(user_message)

        logger.info(f"📥 Deep agent response: {response_text[:100]}...")

        # Stream response as word-level chunks to trigger TTS
        words = response_text.split()
        for i, word in enumerate(words):
            text = word if i == len(words) - 1 else word + " "

            if i == 0:
                yield llm.ChatChunk(
                    id=chunk_id,
                    delta=llm.ChoiceDelta(role="assistant", content=text),
                )
            else:
                yield llm.ChatChunk(
                    id=chunk_id,
                    delta=llm.ChoiceDelta(content=text),
                )

    def _extract_user_message(self, chat_ctx: llm.ChatContext) -> str:
        """
        Extract the last user message from chat context.
        """
        if not chat_ctx.messages:
            return ""

        # Get the last message
        last_message = chat_ctx.messages[-1]

        # Check if it's a user message
        if hasattr(last_message, "role") and last_message.role == "user":
            if hasattr(last_message, "content"):
                return last_message.content

        # Fallback: try to get content from last message
        if hasattr(last_message, "content"):
            return last_message.content

        return ""

    async def _route_to_deep_agent(self, user_input: str) -> str:
        """
        Route user input to Deep Agent backend for processing.

        Deep Agent Flow:
        1. Planning: Break down request into tasks
        2. Execution: Execute tasks using CIBC tools/agents
        3. Criticism: Validate quality and completeness
        4. Loop: Continue until all tasks complete or escalate

        Returns:
            str: Agent response to speak to user via TTS
        """
        try:
            logger.info(f"📤 Routing to Deep Agent: '{user_input[:50]}...'")

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BACKEND_API_URL}/api/agent/deep-invoke",
                    json={
                        "agent_id": self._agent_id,
                        "input": user_input,
                        "session_id": self._session_id,
                        "mode": "deep",
                        "enable_planning": True,
                        "enable_execution": True,
                        "enable_criticism": True,
                        "max_iterations": 20,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"❌ Deep agent returned {response.status_code}: {response.text}")
                    return self._handle_error_response(response.status_code)

                result = response.json()

                # Extract response from deep agent result
                output = self._extract_deep_agent_output(result)

                logger.info("✅ Deep agent completed successfully")
                return output

        except httpx.TimeoutException:
            logger.error("❌ Timeout waiting for deep agent response")
            return "I'm taking longer than expected to process your request. Please hold on while I complete this task."

        except httpx.ConnectError as e:
            logger.error(f"❌ Connection error to deep agent backend: {e}")
            return "I'm having trouble connecting to our systems. Please try again in a moment."

        except Exception as e:
            logger.error(f"❌ Error routing to deep agent: {e}", exc_info=True)
            return "I encountered an error processing your request. Could you please try asking that again?"

    def _extract_deep_agent_output(self, result: dict) -> str:
        """
        Extract user-facing output from deep agent result.

        Deep agent results include:
        - output: Main response text for user
        - tasks: Task list with status
        - validation: Critic feedback
        - metadata: Session info
        """
        # Primary output field
        if result.get("output"):
            return result["output"]

        # Fallback to tasks summary if no output
        if "tasks" in result:
            completed_tasks = [t for t in result["tasks"] if t.get("status") == "completed"]
            if completed_tasks:
                return f"I've completed {len(completed_tasks)} task(s) for you. Is there anything else I can help you with?"

        # Fallback to validation message
        if "validation" in result and result["validation"].get("message"):
            return result["validation"]["message"]

        # Final fallback
        return "I've processed your request. How else can I assist you?"

    def _handle_error_response(self, status_code: int) -> str:
        """
        Generate user-friendly error messages based on status code.
        """
        if status_code == 404:
            return "I couldn't find the agent configuration. Please contact support."
        elif status_code == 400:
            return "I didn't understand that request. Could you please rephrase it?"
        elif status_code == 500:
            return "I encountered a system error. Let me try a different approach. Could you tell me more about what you need?"
        elif status_code == 503:
            return "Our systems are temporarily busy. Please try again in a moment."
        else:
            return "I encountered an unexpected error. Please try again or speak with a representative."

    def is_greeting_sent(self) -> bool:
        """Check if greeting has been sent."""
        return self._greeting_sent

    def is_conversation_active(self) -> bool:
        """Check if conversation is active."""
        return self._conversation_active

    async def end_conversation(self):
        """Mark conversation as ended."""
        self._conversation_active = False
        logger.info(f"👋 Conversation ended for session {self._session_id}")
