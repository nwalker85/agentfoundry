"""
IO Agent Worker - Voice/Text Input/Output Handler
Lives in the LiveKit room and routes all user input to the Supervisor Agent.

Architecture:
- IO Agent is ALWAYS in the room (handles STT/TTS via LiveKit)
- Routes user "thoughts" → Supervisor Agent
- Supervisor determines intent → routes to domain agents (pm-agent, etc.)
- Response flows back through IO Agent → TTS → user
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import httpx
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.plugins import deepgram, elevenlabs, silero

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("io-agent-worker")
logger.setLevel(logging.INFO)

# Backend API URL for routing to Supervisor
# Use service discovery (Infrastructure as Registry pattern)
from backend.config.services import SERVICES

BACKEND_API_URL = SERVICES.get_service_url("BACKEND")


# ============================================================================
# SUPERVISOR-ROUTING LLM (Wrapper that intercepts LLM calls)
# ============================================================================


class ChatStream:
    """Async context manager that wraps an async generator for LiveKit compatibility."""

    def __init__(self, generator):
        self._generator = generator

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._generator.__anext__()


class SupervisorRoutingLLM(llm.LLM):
    """
    Custom LLM that routes through Supervisor Agent instead of calling OpenAI directly.
    Intercepts chat() calls and delegates to Supervisor.
    """

    def __init__(self, session_id: str, agent_id: str):
        super().__init__()
        self._session_id = session_id
        self._agent_id = agent_id
        self._interrupted = False  # Track if agent is waiting for resume
        logger.info(f"🎯 SupervisorRoutingLLM initialized for session {session_id}, agent {agent_id}")

    def chat(self, *, chat_ctx: llm.ChatContext, **kwargs):
        """
        Override chat() to route through Supervisor Agent.
        Returns an async context manager that yields chat chunks.
        """
        return ChatStream(self._chat_impl(chat_ctx=chat_ctx, **kwargs))

    async def _chat_impl(self, *, chat_ctx: llm.ChatContext, **kwargs):
        """
        Implementation of chat that yields chunks.
        """
        # Extract the last user message from chat history
        # The STT plugin adds items to chat_ctx.items
        user_message = "Hello"  # Default fallback

        logger.info(f"🔍 Chat context has {len(chat_ctx.items) if chat_ctx.items else 0} items")

        if chat_ctx.items:
            # Get the last message from the user
            for item in reversed(chat_ctx.items):
                logger.info(f"🔍 Item type: {type(item)}, has role: {hasattr(item, 'role')}")
                # Check if item is a ChatMessage with role "user"
                if hasattr(item, "role") and item.role == "user":
                    logger.info(f"🔍 Found user message, has content: {hasattr(item, 'content')}")
                    # Extract text content from the message
                    if hasattr(item, "content"):
                        logger.info(f"🔍 Content items: {len(item.content)}")
                        for content in item.content:
                            logger.info(f"🔍 Content type: {type(content)}, is string: {isinstance(content, str)}")
                            # Content can be a string directly or an object with .text
                            if isinstance(content, str):
                                user_message = content
                                logger.info(f"✅ Extracted STT (string): {user_message}")
                                break
                            elif hasattr(content, "text"):
                                user_message = content.text
                                logger.info(f"✅ Extracted STT (object): {user_message}")
                                break
                    break
        else:
            logger.warning("⚠️ No items in chat context, using fallback")

        logger.info(f"🎤 User said: {user_message}")

        # Route to Supervisor Agent
        response_text = await self._route_to_supervisor(user_message)

        logger.info(f"📥 Supervisor response: {response_text[:100]}...")

        # Stream response as word-level chunks to trigger TTS properly
        # Split into words and yield each as a delta chunk
        import uuid

        chunk_id = str(uuid.uuid4())

        words = response_text.split()
        for i, word in enumerate(words):
            # Add space after each word except the last
            text = word if i == len(words) - 1 else word + " "

            # First chunk includes role, subsequent chunks only have content
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

    async def _route_to_supervisor(self, user_input: str) -> str:
        """
        Route user input to Supervisor Agent for processing.
        Detects interrupts and automatically calls resume on next input.
        """
        try:
            # Decide which endpoint to call based on interrupt state
            if self._interrupted:
                # Agent is waiting for user input - call resume
                endpoint = f"{BACKEND_API_URL}/api/agent/resume"
                payload = {"agent_id": self._agent_id, "session_id": self._session_id, "user_input": user_input}
                logger.info(f"🔄 Resuming interrupted agent: '{user_input[:50]}...'")
            else:
                # Normal invocation
                endpoint = f"{BACKEND_API_URL}/api/agent/invoke"
                payload = {
                    "agent_id": self._agent_id,
                    "input": user_input,
                    "session_id": self._session_id,
                    "route_via_supervisor": True,
                }
                logger.info(f"📤 Routing to Supervisor: '{user_input[:50]}...'")

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(endpoint, json=payload)

                if response.status_code != 200:
                    logger.error(f"❌ API returned {response.status_code}: {response.text}")
                    self._interrupted = False  # Reset on error
                    return "I apologize, but I encountered an error processing your request. Please try again."

                result = response.json()
                output = result.get("output", "I received your message but couldn't generate a response.")

                # Update interrupted state based on response
                self._interrupted = result.get("interrupted", False)

                if self._interrupted:
                    logger.info("🔄 Agent interrupted, waiting for user input")
                else:
                    logger.info("✅ Agent completed successfully")

                return output

        except httpx.TimeoutException:
            logger.error("❌ Timeout waiting for Supervisor response")
            return "I'm taking longer than expected to process that. Let me try to help you differently - could you rephrase your request?"
        except Exception as e:
            logger.error(f"❌ Error routing to Supervisor: {e}", exc_info=True)
            return "I encountered an error. Could you please try asking that again?"


# ============================================================================
# IO AGENT ENTRYPOINT
# ============================================================================


async def entrypoint(ctx: JobContext):
    """
    IO Agent entrypoint - always in the room, routes to Supervisor.
    Called when a participant joins a LiveKit room.
    """
    # Connect to the room via WebRTC
    await ctx.connect()

    room_name = ctx.room.name or "unknown-room"
    logger.info(f"🎙️  IO Agent connected to room: {room_name}")

    # Extract session_id and agent_id from room metadata
    session_id = room_name  # Fallback to room name
    agent_id = "pm-agent"  # Default

    logger.info(f"🔍 Room metadata: {ctx.room.metadata}")
    logger.info(f"🔍 Has metadata attr: {hasattr(ctx.room, 'metadata')}")

    if hasattr(ctx.room, "metadata") and ctx.room.metadata:
        import json

        try:
            metadata = json.loads(ctx.room.metadata)
            logger.info(f"🔍 Parsed metadata: {metadata}")
            # Use frontend session_id from metadata for activity streaming
            session_id = metadata.get("session_id", room_name)
            agent_id = metadata.get("agent_id", "pm-agent")
            logger.info(f"📋 Using session_id from room metadata: {session_id}")
            logger.info(f"📋 Using agent_id from room metadata: {agent_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse room metadata: {e}")
            logger.warning(f"⚠️ Raw metadata: {ctx.room.metadata}")
    else:
        logger.warning("⚠️ No room metadata available, using room name as session_id")

    # Define IO Agent with minimal instructions (delegate to Supervisor or Deep Agent)
    agent = Agent(
        instructions=f"""
        You are the IO Agent - the voice interface for Agent Foundry.

        Your role:
        - Listen to the user
        - Pass their request to the appropriate agent
        - Speak the response back

        The agent you're routing to: {agent_id}
        """,
        # No tools - IO Agent delegates everything to Supervisor or Deep Agent
        tools=[],
    )

    # Detect if this is a deep agent orchestrator (e.g., CIBC Orchestrator)
    is_deep_agent = agent_id == "cibc-orchestrator" or agent_id.startswith("deep-")

    if is_deep_agent:
        logger.info(f"🤖 Using Deep Agent LLM for orchestrator: {agent_id}")

        # Import DeepAgentLLM
        from io_deep_agent_llm import DeepAgentLLM

        # Get greeting from agent configuration if available
        # For CIBC orchestrator, use CIBC greeting
        greeting = "Thank you for calling CIBC. How can I help you today?"
        if agent_id == "cibc-orchestrator":
            greeting = "Thank you for calling CIBC. How can I help you today?"

        # Create Deep Agent LLM
        llm_instance = DeepAgentLLM(
            session_id=session_id, agent_id=agent_id, greeting=greeting, proactive_greeting=True
        )
    else:
        logger.info(f"📤 Using Supervisor LLM for agent: {agent_id}")

        # Create Supervisor routing LLM (standard path)
        llm_instance = SupervisorRoutingLLM(session_id=session_id, agent_id=agent_id)

    # Create agent session with appropriate LLM
    session = AgentSession(
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=deepgram.STT(),  # Speech-to-Text (Deepgram)
        llm=llm_instance,  # Deep Agent LLM or Supervisor LLM
        tts=elevenlabs.TTS(),  # Text-to-Speech (ElevenLabs)
    )

    # Start the session with agent and room
    await session.start(room=ctx.room, agent=agent)

    # For deep agents, send proactive greeting after session starts
    if is_deep_agent and hasattr(llm_instance, "send_greeting"):
        logger.info("👋 Sending proactive greeting to user...")
        greeting_text = await llm_instance.send_greeting()
        if greeting_text:
            # Use session.say() to speak the greeting
            await session.say(greeting_text)

    logger.info("✅ IO Agent session active")
    logger.info(f"   Room: {room_name}")
    logger.info(f"   Session ID: {session_id}")
    logger.info(f"   Routing to: {agent_id} via Supervisor")

    # Keep the agent running until the room closes
    await asyncio.Future()  # Run indefinitely


# ============================================================================
# WORKER MAIN
# ============================================================================


def main():
    """
    Run the IO Agent worker.

    Environment variables required:
    - LIVEKIT_URL: LiveKit server URL
    - LIVEKIT_API_KEY: LiveKit API key
    - LIVEKIT_API_SECRET: LiveKit API secret
    - OPENAI_API_KEY: OpenAI API key (for TTS)
    - DEEPGRAM_API_KEY: Deepgram API key (for STT)
    - BACKEND_API_URL: Backend API URL for Supervisor routing

    The worker:
    1. Connects to LiveKit server
    2. Listens for job assignments (room joins)
    3. Spawns IO Agent sessions that route through Supervisor
    """
    logger.info("🚀 Starting IO Agent Worker (routes via Supervisor)")

    # Validate OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY environment variable not set!")
        logger.error("   Get your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)

    logger.info("✓ OpenAI API key configured")
    logger.info(f"✓ Backend API: {BACKEND_API_URL}")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Worker will automatically connect to LIVEKIT_URL
            # and authenticate with LIVEKIT_API_KEY/SECRET from env
        )
    )


if __name__ == "__main__":
    main()
