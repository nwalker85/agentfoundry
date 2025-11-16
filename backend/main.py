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
from agents import MarshalAgent, AgentYAML, ValidationResult

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


class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    version: str
    state: str
    phase: str
    uptime_seconds: int
    total_executions: int
    success_rate: float
    last_heartbeat: Optional[str]


class ValidationRequest(BaseModel):
    yaml_content: str


class HealthSummaryResponse(BaseModel):
    timestamp: str
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    overall_health_rate: float


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Agent Foundry API",
    description="LangGraph agents with LiveKit voice integration",
    version="0.8.1-dev"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Marshal Agent instance
marshal: Optional[MarshalAgent] = None


def get_marshal() -> MarshalAgent:
    """Get the global Marshal Agent instance."""
    if marshal is None:
        raise HTTPException(
            status_code=503,
            detail="Marshal Agent not initialized. Server may be starting up."
        )
    return marshal


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
        
        # Use LIVEKIT_PUBLIC_URL from environment (defined in .env.local)
        public_url = os.getenv("LIVEKIT_PUBLIC_URL", "ws://localhost:7880")
        
        return VoiceSessionResponse(
            session_id=session.session_id,
            room_name=session.room_name,
            token=session.token,
            livekit_url=public_url,
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
async def list_agents(m: MarshalAgent = Depends(get_marshal)):
    """
    List all available agents from the agent registry.
    Agents are loaded from YAML files in /app/agents/
    """
    agents = await m.registry.list_all()
    
    return AgentListResponse(
        agents=[
            {
                "id": agent_id,
                "name": instance.metadata.name,
                "version": instance.metadata.version,
                "description": instance.metadata.description,
                "capabilities": instance.config.spec.capabilities,
                "status": instance.status.state,
                "phase": instance.status.phase,
                "tags": instance.metadata.tags
            }
            for agent_id, instance in agents.items()
        ]
    )


@app.get("/api/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    m: MarshalAgent = Depends(get_marshal)
):
    """Get detailed information about a specific agent"""
    instance = await m.registry.get(agent_id)
    
    if not instance:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return {
        "id": agent_id,
        "name": instance.metadata.name,
        "version": instance.metadata.version,
        "description": instance.metadata.description,
        "capabilities": instance.config.spec.capabilities,
        "status": instance.status.state,
        "phase": instance.status.phase,
        "tags": instance.metadata.tags,
        "workflow": {
            "type": instance.config.spec.workflow.type,
            "entry_point": instance.config.spec.workflow.entry_point,
            "node_count": len(instance.config.spec.workflow.nodes)
        },
        "metrics": {
            "uptime_seconds": instance.status.uptime_seconds,
            "total_executions": instance.status.total_executions,
            "success_rate": instance.status.success_rate,
            "invocation_count": instance.invocation_count,
            "error_count": instance.error_count
        },
        "loaded_at": instance.loaded_at.isoformat(),
        "last_invoked": instance.last_invoked.isoformat() if instance.last_invoked else None
    }


@app.get("/api/agents/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str,
    m: MarshalAgent = Depends(get_marshal)
):
    """Get status and metrics for a specific agent"""
    instance = await m.registry.get(agent_id)
    
    if not instance:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    
    return AgentStatusResponse(
        agent_id=agent_id,
        name=instance.metadata.name,
        version=instance.metadata.version,
        state=instance.status.state,
        phase=instance.status.phase,
        uptime_seconds=instance.status.uptime_seconds,
        total_executions=instance.status.total_executions,
        success_rate=instance.status.success_rate,
        last_heartbeat=instance.status.last_heartbeat
    )


@app.post("/api/agents/{agent_id}/reload")
async def reload_agent(
    agent_id: str,
    m: MarshalAgent = Depends(get_marshal)
):
    """Hot-reload a specific agent from its YAML file"""
    success = await m.reload_agent(agent_id)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload agent '{agent_id}'. Check logs for details."
        )
    
    return {"status": "reloaded", "agent_id": agent_id}


@app.post("/api/agents/validate")
async def validate_agent_yaml(
    request: ValidationRequest,
    m: MarshalAgent = Depends(get_marshal)
):
    """Validate agent YAML without loading it"""
    import yaml
    import tempfile
    from pathlib import Path
    
    try:
        # Parse YAML content
        yaml_data = yaml.safe_load(request.yaml_content)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.agent.yaml',
            delete=False
        ) as f:
            yaml.dump(yaml_data, f)
            temp_path = Path(f.name)
        
        try:
            # Load and validate
            agent_config = AgentYAML.from_yaml_file(str(temp_path))
            result = await m.loader.validate_yaml(agent_config)
            
            return {
                "valid": result.valid,
                "agent_id": result.agent_id,
                "errors": result.errors,
                "warnings": result.warnings
            }
        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)
    
    except Exception as e:
        return {
            "valid": False,
            "agent_id": None,
            "errors": [f"Failed to parse YAML: {str(e)}"],
            "warnings": []
        }


@app.get("/api/agents/{agent_id}/health")
async def get_agent_health(
    agent_id: str,
    m: MarshalAgent = Depends(get_marshal)
):
    """Get health check history and metrics for an agent"""
    # Get metrics from health monitor
    metrics = m.health_monitor.get_metrics(agent_id)
    
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No health data available for '{agent_id}'"
        )
    
    # Get recent checks
    recent_checks = m.health_monitor.get_recent_checks(agent_id=agent_id, limit=10)
    
    return {
        "agent_id": agent_id,
        "metrics": {
            "uptime_seconds": metrics.uptime_seconds,
            "total_checks": metrics.total_checks,
            "successful_checks": metrics.successful_checks,
            "failed_checks": metrics.failed_checks,
            "health_rate": metrics.health_rate,
            "avg_latency_ms": metrics.avg_latency_ms,
            "consecutive_failures": metrics.consecutive_failures,
            "last_check": metrics.last_check.isoformat() if metrics.last_check else None
        },
        "recent_checks": [
            {
                "timestamp": check.timestamp.isoformat(),
                "healthy": check.healthy,
                "latency_ms": check.latency_ms,
                "error": check.error_message
            }
            for check in recent_checks
        ]
    }


@app.get("/api/agents/health/summary", response_model=HealthSummaryResponse)
async def get_health_summary(m: MarshalAgent = Depends(get_marshal)):
    """Get overall health summary for all agents"""
    summary = m.health_monitor.get_health_summary()
    
    return HealthSummaryResponse(
        timestamp=summary["timestamp"],
        total_agents=summary["total_agents"],
        healthy_agents=summary["healthy_agents"],
        unhealthy_agents=summary["unhealthy_agents"],
        overall_health_rate=summary["overall_health_rate"]
    )


# ============================================================================
# WEBSOCKET FOR TEXT CHAT
# ============================================================================

@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    """
    WebSocket endpoint for text-based chat.
    Maintains separate transport from LiveKit voice.
    """
    await websocket.accept()
    
    # Get session_id from query params if provided
    if not session_id and websocket.query_params.get("session_id"):
        session_id = websocket.query_params.get("session_id")
    
    logger.info(f"WebSocket connected for session {session_id}")
    
    try:
        # TODO: Load LangGraph agent based on session context
        # TODO: Initialize checkpointed state for session
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")
            msg_data = data.get("data", {})
            
            # Handle ping/pong for heartbeat
            if msg_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                continue
            
            # Handle chat messages
            if msg_type == "message":
                content = msg_data.get("content", "")
                
                # TODO: Process through LangGraph agent
                # For now, echo back
                response = {
                    "type": "message",
                    "data": {
                        "content": f"Echo: {content}",
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send_json(response)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
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
        "version": "0.8.1-dev",
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

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global marshal
    
    logger.info("🚀 Initializing Agent Foundry Backend...")
    
    # Initialize Marshal Agent
    agents_dir = Path(__file__).parent.parent / "agents"
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True,
        health_check_interval=60
    )
    
    # Start Marshal in background
    await marshal.start()
    
    logger.info("✅ Agent Foundry Backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global marshal
    
    logger.info("🛑 Shutting down Agent Foundry Backend...")
    
    # Stop Marshal Agent
    if marshal:
        await marshal.stop()
    
    # Close LiveKit service
    livekit = get_livekit_service()
    await livekit.close()
    
    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
