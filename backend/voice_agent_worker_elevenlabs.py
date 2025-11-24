"""
LiveKit Voice Agent Worker - ElevenLabs TTS Integration
Uses ElevenLabs for high-quality, natural-sounding text-to-speech.

Architecture:
- Uses Agent class for instructions and tool definitions
- Uses AgentSession for VAD/STT/LLM/TTS pipeline
- ElevenLabs TTS for superior voice quality
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    RunContext,
    WorkerOptions,
    cli,
    function_tool,
)
from livekit.plugins import deepgram, elevenlabs, openai, silero

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger("voice-agent-worker")
logger.setLevel(logging.INFO)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


@function_tool
async def get_project_status(ctx: RunContext, project_name: str) -> str:
    """
    Get the current status of a project.

    Args:
        project_name: Name of the project to check

    Returns:
        Project status information
    """
    logger.info(f"Tool called: get_project_status(project_name={project_name})")

    # TODO: Integrate with IOAgent to fetch real project data
    return f"Project '{project_name}' is currently in progress. Last updated 2 days ago."


@function_tool
async def create_task(ctx: RunContext, task_description: str, priority: str = "medium") -> str:
    """
    Create a new task in the project management system.

    Args:
        task_description: Description of the task to create
        priority: Task priority (low, medium, high)

    Returns:
        Confirmation with task ID
    """
    logger.info(f"Tool called: create_task(description={task_description}, priority={priority})")

    # TODO: Integrate with IOAgent to create real tasks
    task_id = f"TASK-{hash(task_description) % 10000}"
    return f"Created task {task_id} with priority {priority}: {task_description}"


@function_tool
async def search_documentation(ctx: RunContext, query: str) -> str:
    """
    Search through project documentation.

    Args:
        query: Search query

    Returns:
        Relevant documentation snippets
    """
    logger.info(f"Tool called: search_documentation(query={query})")

    # TODO: Integrate with IOAgent documentation search
    return f"Documentation search results for '{query}' would appear here."


# ============================================================================
# AGENT ENTRYPOINT
# ============================================================================


async def entrypoint(ctx: JobContext):
    """
    Voice agent entrypoint with ElevenLabs TTS.
    Called when a participant joins a LiveKit room.
    """
    # Connect to the room via WebRTC
    await ctx.connect()

    room_name = ctx.room.name or "unknown-room"
    logger.info(f"🎙️  Voice agent connected to room: {room_name}")

    # Define agent with instructions and tools
    agent = Agent(
        instructions="""
        You are a helpful project management assistant for Agent Foundry.

        Your role:
        - Help users understand project status
        - Create and manage tasks
        - Answer questions about documentation
        - Provide clear, concise responses

        Guidelines:
        - Be professional but friendly
        - Keep responses brief and actionable
        - Use tools when appropriate
        - Ask clarifying questions if needed
        """,
        tools=[
            get_project_status,
            create_task,
            search_documentation,
        ],
    )

    # ============================================================================
    # ELEVENLABS TTS CONFIGURATION
    # ============================================================================
    # Options for voice selection:
    #
    # Professional voices:
    # - "Rachel" - Calm, professional female voice (good for assistants)
    # - "Josh" - Deep, authoritative male voice
    # - "Antoni" - Well-rounded male voice
    # - "Bella" - Soft, friendly female voice
    # - "Elli" - Energetic female voice
    # - "Arnold" - Crisp, clear male voice
    # - "Adam" - Deep, confident male voice
    # - "Sam" - Dynamic, versatile male voice
    #
    # Model options:
    # - "eleven_multilingual_v2" - Best quality, supports 29 languages (default)
    # - "eleven_turbo_v2" - Faster, lower latency, English only
    # - "eleven_turbo_v2_5" - Fastest, lowest latency, English only
    #
    # For real-time voice agents, use eleven_turbo_v2_5 for best latency
    # ============================================================================

    # Create agent session with VAD, STT, TTS, LLM pipeline
    session = AgentSession(
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=deepgram.STT(),  # Speech-to-Text (Deepgram)
        llm=openai.LLM(  # Language Model (OpenAI)
            model="gpt-4o-mini",
            temperature=0.7,
        ),
        tts=elevenlabs.TTS(  # Text-to-Speech (ElevenLabs)
            # Basic configuration - fastest, lowest latency
            model_id="eleven_turbo_v2_5",
            voice="Rachel",  # Professional, friendly female voice
            # Optional: Fine-tune voice settings
            # stability=0.5,           # 0-1, higher = more consistent, lower = more expressive
            # similarity_boost=0.75,   # 0-1, higher = closer to original voice
            # optimize_streaming_latency=4,  # 0-4, higher = lower latency but may affect quality
            # Optional: Enable word-level timestamps for better lip sync
            # enable_ssml_parsing=False,  # Set to True if using SSML tags
        ),
    )

    # Start the session with agent and room
    await session.start(room=ctx.room, agent=agent)

    logger.info(f"✅ Voice agent session active with ElevenLabs TTS for room: {room_name}")

    # Keep the agent running until the room closes
    await asyncio.Future()  # Run indefinitely


# ============================================================================
# WORKER MAIN
# ============================================================================


def main():
    """
    Run the voice agent worker with ElevenLabs TTS.

    Environment variables required:
    - LIVEKIT_URL: LiveKit server URL
    - LIVEKIT_API_KEY: LiveKit API key
    - LIVEKIT_API_SECRET: LiveKit API secret
    - ELEVENLABS_API_KEY: ElevenLabs API key

    The worker:
    1. Connects to LiveKit server
    2. Listens for job assignments (room joins)
    3. Spawns agent sessions with ElevenLabs TTS for each job
    """
    logger.info("🚀 Starting LiveKit Voice Agent Worker with ElevenLabs TTS")

    # Validate ElevenLabs API key is set
    if not os.getenv("ELEVENLABS_API_KEY"):
        logger.error("❌ ELEVENLABS_API_KEY environment variable not set!")
        logger.error("   Get your API key from: https://elevenlabs.io/app/settings/api-keys")
        sys.exit(1)

    logger.info("✓ ElevenLabs API key configured")

    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Worker will automatically connect to LIVEKIT_URL
            # and authenticate with LIVEKIT_API_KEY/SECRET from env
        )
    )


if __name__ == "__main__":
    main()
