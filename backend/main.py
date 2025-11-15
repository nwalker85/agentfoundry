"""
Agent Foundry Backend
FastAPI server integrating:
- MCP server (existing Engineering Department code)
- LiveKit voice sessions
- LangGraph agent orchestration
- WebSocket for text chat
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.livekit_service import get_livekit_service, LiveKitService, VoiceSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class VoiceSessionRequest(BaseModel):
    user_id: str
    agent_id: str
    session_duration_hours: int = 4


class VoiceSessionResponse(BaseModel):
    session_id: str
    room_name: str
    token: str
    livekit_url: str
    expires_at: datetime


class AgentListResponse(BaseModel):
    agents: list[Dict]


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Agent Foundry API",
    description="LangGraph agents with LiveKit voice integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# VOICE ENDPOINTS
# ============================================================================

@app.post("/api/voice/session", response_model=VoiceSessionResponse)
async def create_voice_session(
    request: VoiceSessionRequest,
    livekit: LiveKitService = Depends(get_livekit_service)
):
    """
    Create a new voice session for user-agent interaction.
    Returns LiveKit room token and connection details.
    """
    try:
        # CRITICAL: Await the async method
        session = await livekit.create_voice_session(
            user_id=request.user_id,
            agent_id=request.agent_id,
            session_duration_hours=request.session_duration_hours
        )
        
        return VoiceSessionResponse(
            session_id=session.session_id,
            room_name=session.room_name,
            token=session.token,
            livekit_url=livekit.url.replace("ws://livekit", "ws://localhost"),
            expires_at=session.expires_at
        )
    except Exception as e:
        logger.error(f"Failed to create voice session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/room/{room_name}")
async def get_room_info(
    room_name: str,
    livekit: LiveKitService = Depends(get_livekit_service)
):
    """Get information about a LiveKit room"""
    # CRITICAL: Await the async method
    info = await livekit.get_room_info(room_name)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.delete("/api/voice/session/{room_name}")
async def end_voice_session(
    room_name: str,
    livekit: LiveKitService = Depends(get_livekit_service)
):
    """End a voice session"""
    # CRITICAL: Await the async method
    success = await livekit.end_session(room_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to end session")
    return {"status": "session_ended", "room_name": room_name}


# ============================================================================
# AGENT REGISTRY ENDPOINTS
# ============================================================================

@app.get("/api/agents", response_model=AgentListResponse)
async def list_agents():
    """
    List all available agents from the agent registry.
    Agents are loaded from YAML files in /app/agents/
    """
    # TODO: Implement agent registry file watcher
    # For now, return hardcoded PM agent
    return AgentListResponse(
        agents=[
            {
                "id": "pm-agent",
                "name": "Project Manager Agent",
                "description": "Translates requirements into actionable stories",
                "capabilities": ["requirement_analysis", "story_creation", "clarification"],
                "status": "active",
                "version": "1.0.0"
            }
        ]
    )


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get details about a specific agent"""
    # TODO: Load from YAML registry
    if agent_id != "pm-agent":
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "id": "pm-agent",
        "name": "Project Manager Agent",
        "description": "Translates requirements into actionable stories",
        "yaml_path": "/app/agents/pm-agent.agent.yaml",
        "capabilities": ["requirement_analysis", "story_creation", "clarification"],
        "status": "active"
    }


# ============================================================================
# WEBSOCKET FOR TEXT CHAT
# ============================================================================

@app.websocket("/ws/chat/{user_id}/{agent_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    agent_id: str
):
    """
    WebSocket endpoint for text-based chat.
    Maintains separate transport from LiveKit voice.
    """
    await websocket.accept()
    
    try:
        # TODO: Load LangGraph agent for this agent_id
        # TODO: Initialize checkpointed state for user_id
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # TODO: Process through LangGraph agent
            # For now, echo back
            response = {
                "type": "agent_response",
                "message": f"Echo from {agent_id}: {message}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()


# ============================================================================
# HEALTH & STATUS
# ============================================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "agent-foundry-backend",
        "status": "operational",
        "version": "1.0.0",
        "livekit_url": os.getenv("LIVEKIT_URL", "ws://livekit:7880")
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "livekit": {
            "url": os.getenv("LIVEKIT_URL"),
            "configured": bool(os.getenv("LIVEKIT_API_KEY"))
        },
        "redis": {
            "url": os.getenv("REDIS_URL"),
            "configured": bool(os.getenv("REDIS_URL"))
        }
    }


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    livekit = get_livekit_service()
    await livekit.close()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
