"""
LiveKit Voice Agent Worker - Modern Implementation
Connects to LiveKit rooms using the Agent + AgentSession pattern.

Architecture:
- Uses Agent class for instructions and tool definitions
- Uses AgentSession for VAD/STT/LLM/TTS pipeline
- Integrates with IOAgent for multi-agent orchestration
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
from livekit.plugins import deepgram, openai, silero

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
    # For now, return mock data
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
    # For now, return mock confirmation
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
    Voice agent entrypoint using modern Agent + AgentSession pattern.
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
    
    # Create agent session with VAD, STT, TTS, LLM pipeline
    session = AgentSession(
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=deepgram.STT(),     # Speech-to-Text (Deepgram)
        llm=openai.LLM(         # Language Model (OpenAI)
            model="gpt-4o-mini",
            temperature=0.7,
        ),
        tts=openai.TTS(         # Text-to-Speech (OpenAI)
            voice="alloy",
        ),
    )

    # Start the session with agent and room
    await session.start(room=ctx.room, agent=agent)
    
    # Optional: Send initial greeting
    # Note: We don't use session.say() here to avoid race conditions
    # The agent will greet naturally when user speaks first
    
    logger.info(f"✅ Voice agent session active for room: {room_name}")
    
    # Keep the agent running until the room closes
    await asyncio.Future()  # Run indefinitely


# ============================================================================
# WORKER MAIN
# ============================================================================

def main():
    """
    Run the voice agent worker.
    
    The worker:
    1. Connects to LiveKit server
    2. Listens for job assignments (room joins)
    3. Spawns agent sessions for each job
    """
    logger.info("🚀 Starting LiveKit Voice Agent Worker")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # Worker will automatically connect to LIVEKIT_URL
            # and authenticate with LIVEKIT_API_KEY/SECRET from env
        )
    )


if __name__ == "__main__":
    main()
