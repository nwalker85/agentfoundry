"""
MCP Server for Engineering Department
A FastAPI-based server implementing Model Context Protocol with tool endpoints.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
from livekit.api import AccessToken, VideoGrants

from backend.db import init_db
from mcp.schemas import (
    CreateStoryRequest,
    CreateStoryResponse,
    CreateIssueRequest,
    CreateIssueResponse,
    ListStoriesRequest,
    ListStoriesResponse,
    ToolResponse,
    AuditEntry,
)
from mcp.tools import NotionTool, GitHubTool, AuditTool, ManifestTool, DataTool, AdminTool
from mcp.tools.manifest import RegisterAgentRequest
from mcp.tools.data import DataQueryRequest
from mcp.tools.admin import ListObjectsRequest, GetObjectRequest
from agent.form_data_agent import FormDataAgent
from agent.pm_graph import PMAgent
from mcp.websocket_handler import manager, handle_websocket_message

# Load environment variables
load_dotenv('.env.local')

# Initialize tools globally
notion_tool: Optional[NotionTool] = None
github_tool: Optional[GitHubTool] = None
audit_tool: Optional[AuditTool] = None
manifest_tool: Optional[ManifestTool] = None
data_tool: Optional[DataTool] = None
admin_tool: Optional[AdminTool] = None
pm_agent: Optional[PMAgent] = None
form_data_agent: Optional[FormDataAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global notion_tool, github_tool, audit_tool, manifest_tool, data_tool, admin_tool, pm_agent, form_data_agent
    
    print("🚀 Starting Engineering Department MCP Server...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🏢 Tenant ID: {os.getenv('TENANT_ID', 'unknown')}")
    
    # Initialize database schema (PostgreSQL)
    try:
        init_db()
    except Exception as e:
        print(f"⚠️ Database initialization failed: {e}")

    # Initialize tools
    try:
        notion_tool = NotionTool()
        print("✅ Notion tool initialized")
    except Exception as e:
        print(f"⚠️ Notion tool initialization failed: {e}")
    
    try:
        github_tool = GitHubTool()
        print("✅ GitHub tool initialized")
    except Exception as e:
        print(f"⚠️ GitHub tool initialization failed: {e}")
    
    audit_tool = AuditTool()
    print("✅ Audit tool initialized")

    # Initialize Manifest tool
    try:
        manifest_tool = ManifestTool()
        print("✅ Manifest tool initialized")
    except Exception as e:
        print(f"⚠️ Manifest tool initialization failed: {e}")

    # Initialize Data tool
    try:
        data_tool = DataTool()
        print("✅ Data tool initialized")
    except Exception as e:
        print(f"⚠️ Data tool initialization failed: {e}")

    # Initialize Admin tool
    try:
        admin_tool = AdminTool()
        print("✅ Admin tool initialized")
    except Exception as e:
        print(f"⚠️ Admin tool initialization failed: {e}")

    # Initialize Form Data agent
    try:
        form_data_agent = FormDataAgent()
        print("✅ Form Data agent initialized")
    except Exception as e:
        print(f"⚠️ Form Data agent initialization failed: {e}")
    
    # Initialize PM Agent (LangGraph)
    try:
        pm_agent = PMAgent()
        print("✅ LangGraph PM Agent initialized")
    except Exception as e:
        print(f"⚠️ PM Agent initialization failed: {e}")
    
    yield
    
    # Cleanup
    print("🛑 Shutting down MCP Server...")
    if notion_tool:
        await notion_tool.close()
    if github_tool:
        await github_tool.close()
    if pm_agent:
        await pm_agent.close()


# Initialize FastAPI app
app = FastAPI(
    title="Engineering Department MCP Server",
    description="Model Context Protocol server for engineering workflows",
    version="0.4.0",  # Using LangGraph agent
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request tracking
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request timing and add request ID."""
    start_time = time.time()
    request_id = f"{datetime.utcnow().isoformat()}-{hash(str(request.url))}"
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Dependency for authorization (basic for now)
async def verify_auth(authorization: Optional[str] = Header(None)):
    """Verify authorization header."""
    if not authorization:
        # In development, allow no auth
        if os.getenv("ENVIRONMENT") == "development":
            return "dev-user"
        raise HTTPException(status_code=401, detail="Authorization required")
    
    # Extract bearer token (simplified for PoC)
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        # TODO: Validate token
        return "authenticated-user"
    
    raise HTTPException(status_code=401, detail="Invalid authorization")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "service": "Engineering Department MCP Server",
        "version": "0.4.0",  # LangGraph agent active
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "tenant_id": os.getenv("TENANT_ID", "unknown"),
        "tools": {
            "notion": notion_tool is not None,
            "github": github_tool is not None,
            "audit": audit_tool is not None,
            "manifest": manifest_tool is not None,
            "agent": pm_agent is not None
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-server"}


@app.get("/api/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "integrations": {
            "notion": bool(os.getenv("NOTION_API_TOKEN")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "github": bool(os.getenv("GITHUB_TOKEN")),
        },
        "tools_available": {
            "notion": notion_tool is not None,
            "github": github_tool is not None,
            "audit": audit_tool is not None,
            "manifest": manifest_tool is not None,
            "data": data_tool is not None,
            "agent": pm_agent is not None
        }
    }


# ============= PM Agent Chat Endpoints =============

@app.post("/api/agent/chat")
async def agent_chat(
    request: Request,
    actor: str = Depends(verify_auth)
):
    """Chat with the PM Agent."""
    if not pm_agent:
        raise HTTPException(status_code=503, detail="PM Agent not available")
    
    try:
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id", "default")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Process message through agent
        result = await pm_agent.process_message(message)
        
        # Log the conversation
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="pm_agent",
                action="chat",
                input_data={"message": message, "session_id": session_id},
                output_data=result,
                result="success" if result.get("status") != "error" else "failure"
            )
        
        return result
        
    except Exception as e:
        # Log failure
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="pm_agent", 
                action="chat",
                input_data={"message": message if 'message' in locals() else None},
                output_data=None,
                result="failure",
                error=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))


# ============= LiveKit Voice Endpoints =============

class VoiceSessionRequest(BaseModel):
    user_id: str
    agent_id: str
    session_duration_hours: int = 4


class VoiceSessionResponse(BaseModel):
    token: str
    livekit_url: str
    room_name: str


@app.post("/api/voice/session", response_model=VoiceSessionResponse)
async def create_voice_session(
    request: VoiceSessionRequest,
    actor: str = Depends(verify_auth)
):
    """Create a LiveKit voice session for agent conversation."""
    try:
        # Get LiveKit credentials from environment
        livekit_url = os.getenv("LIVEKIT_PUBLIC_URL", "ws://localhost:7880")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        
        # Generate unique room name
        room_name = f"foundry-{request.agent_id}-{request.user_id}-{int(time.time())}"
        
        # Create access token
        token = AccessToken(livekit_api_key, livekit_api_secret)
        token.with_identity(request.user_id)
        token.with_name(f"User {request.user_id}")
        token.with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            )
        )
        
        # Set token TTL
        token.with_ttl(timedelta(hours=request.session_duration_hours))
        
        # Log session creation
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="livekit",
                action="create_session",
                input_data={
                    "user_id": request.user_id,
                    "agent_id": request.agent_id,
                    "room_name": room_name
                },
                output_data={"room_name": room_name},
                result="success"
            )
        
        return VoiceSessionResponse(
            token=token.to_jwt(),
            livekit_url=livekit_url,
            room_name=room_name
        )
        
    except Exception as e:
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="livekit",
                action="create_session",
                input_data={"user_id": request.user_id, "agent_id": request.agent_id},
                output_data=None,
                result="failure",
                error=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/voice/session/{room_name}")
async def delete_voice_session(
    room_name: str,
    actor: str = Depends(verify_auth)
):
    """End a LiveKit voice session."""
    try:
        # Log session end
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="livekit",
                action="delete_session",
                input_data={"room_name": room_name},
                output_data=None,
                result="success"
            )
        
        return {"status": "session_ended", "room_name": room_name}
        
    except Exception as e:
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="livekit",
                action="delete_session",
                input_data={"room_name": room_name},
                output_data=None,
                result="failure",
                error=str(e)
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agent/process")
async def process_agent_message(
    request: Request,
    actor: str = Depends(verify_auth)
):
    """Process a message through the PM agent (frontend API)."""
    if not pm_agent:
        raise HTTPException(status_code=503, detail="PM Agent not available")
    
    try:
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id", "default")
        message_history = body.get("message_history", [])
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Process message through agent
        result = await pm_agent.process_message(message)
        
        # Extract artifacts if any
        artifacts = []
        if result.get("story_created"):
            artifacts.append({
                "type": "story",
                "data": result["story_created"]
            })
        if result.get("issue_created"):
            artifacts.append({
                "type": "issue", 
                "data": result["issue_created"]
            })
        
        # Log the conversation
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="pm_agent",
                action="process",
                input_data={"message": message, "session_id": session_id},
                output_data=result,
                result="success" if result.get("status") != "error" else "failure"
            )
        
        return {
            "success": True,
            "response": result.get("response", "Processing your request..."),
            "artifacts": artifacts,
            "requires_clarification": result.get("requires_clarification", False),
            "clarification_prompt": result.get("clarification_prompt"),
            "current_state": result.get("state"),
            "session_id": session_id
        }
        
    except Exception as e:
        # Log failure
        if audit_tool:
            await audit_tool.log_action(
                actor=actor,
                tool="pm_agent", 
                action="process",
                input_data={"message": message if 'message' in locals() else None},
                output_data=None,
                result="failure",
                error=str(e)
            )
        
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id if 'session_id' in locals() else "default"
        }


# ============= Notion Tool Endpoints =============

@app.post("/api/tools/notion/create-story", response_model=CreateStoryResponse)
async def create_story(
    request: CreateStoryRequest,
    req: Request,
    actor: str = Depends(verify_auth)
):
    """Create a story in Notion."""
    if not notion_tool:
        raise HTTPException(status_code=503, detail="Notion tool not available")
    
    start_time = datetime.utcnow()
    
    try:
        # Execute tool
        response = await notion_tool.create_story(request)
        
        # Audit log
        await audit_tool.log_tool_call(
            tool_name="notion",
            method="create_story",
            request=request,
            response=response,
            start_time=start_time
        )
        
        return response
        
    except Exception as e:
        # Audit failure
        await audit_tool.log_tool_call(
            tool_name="notion",
            method="create_story",
            request=request,
            error=e,
            start_time=start_time
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tools/notion/list-stories", response_model=ListStoriesResponse)
async def list_stories(
    request: ListStoriesRequest,
    req: Request,
    actor: str = Depends(verify_auth)
):
    """List stories from Notion."""
    if not notion_tool:
        raise HTTPException(status_code=503, detail="Notion tool not available")
    
    start_time = datetime.utcnow()
    
    try:
        # Execute tool
        response = await notion_tool.list_top_stories(request)
        
        # Audit log
        await audit_tool.log_tool_call(
            tool_name="notion",
            method="list_stories",
            request=request,
            response=response,
            start_time=start_time
        )
        
        return response
        
    except Exception as e:
        # Audit failure
        await audit_tool.log_tool_call(
            tool_name="notion",
            method="list_stories",
            request=request,
            error=e,
            start_time=start_time
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============= GitHub Tool Endpoints =============

@app.post("/api/tools/github/create-issue", response_model=CreateIssueResponse)
async def create_issue(
    request: CreateIssueRequest,
    req: Request,
    actor: str = Depends(verify_auth)
):
    """Create an issue in GitHub."""
    if not github_tool:
        raise HTTPException(status_code=503, detail="GitHub tool not available")
    
    start_time = datetime.utcnow()
    
    try:
        # Execute tool
        response = await github_tool.create_issue(request)
        
        # Audit log
        await audit_tool.log_tool_call(
            tool_name="github",
            method="create_issue",
            request=request,
            response=response,
            start_time=start_time
        )
        
        return response
        
    except Exception as e:
        # Audit failure
        await audit_tool.log_tool_call(
            tool_name="github",
            method="create_issue",
            request=request,
            error=e,
            start_time=start_time
        )
        raise HTTPException(status_code=500, detail=str(e))


# ============= Audit Tool Endpoints =============

@app.get("/api/tools/audit/query")
async def query_audit(
    actor: Optional[str] = None,
    tool: Optional[str] = None,
    action: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 100,
    auth: str = Depends(verify_auth)
):
    """Query the audit log."""
    if not audit_tool:
        raise HTTPException(status_code=503, detail="Audit tool not available")
    
    try:
        entries = await audit_tool.query_audit_log(
            actor=actor,
            tool=tool,
            action=action,
            result=result,
            limit=limit
        )
        
        return {"entries": entries, "count": len(entries)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============= Manifest Tool Endpoints =============

@app.post("/api/tools/manifest/register-agent", response_model=ToolResponse)
async def register_manifest_agent(
    request: RegisterAgentRequest,
    req: Request,
    actor: str = Depends(verify_auth),
):
    """Register or update an agent binding in the manifest (control plane)."""
    if not manifest_tool:
        raise HTTPException(status_code=503, detail="Manifest tool not available")

    start_time = datetime.utcnow()

    try:
        response = await manifest_tool.register_agent(request)

        # Audit log
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="manifest",
                method="register_agent",
                request=request,
                response=response,
                start_time=start_time,
            )

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error or "Manifest operation failed")

        return response

    except HTTPException:
        raise
    except Exception as e:
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="manifest",
                method="register_agent",
                request=request,
                error=e,
                start_time=start_time,
            )
        raise HTTPException(status_code=500, detail=str(e))


# ============= Data Tool Endpoints =============

@app.post("/api/tools/data/query", response_model=ToolResponse)
async def data_query(
    request: DataQueryRequest,
    req: Request,
    actor: str = Depends(verify_auth),
):
    """Run a natural-language data query against the control-plane DB."""
    if not data_tool:
        raise HTTPException(status_code=503, detail="Data tool not available")

    start_time = datetime.utcnow()

    try:
        response = await data_tool.query(request)

        # Audit log
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="data",
                method="query",
                request=request,
                response=response,
                start_time=start_time,
            )

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error or "Data query failed")

        return response

    except HTTPException:
        raise
    except Exception as e:
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="data",
                method="query",
                request=request,
                error=e,
                start_time=start_time,
            )
        raise HTTPException(status_code=500, detail=str(e))


# ============= Admin Tool Endpoints =============

@app.post("/api/tools/admin/list", response_model=ToolResponse)
async def admin_list_objects(
    request: ListObjectsRequest,
    req: Request,
    actor: str = Depends(verify_auth),
):
    """List organizations/domains/instances/users for admin views."""
    if not admin_tool:
        raise HTTPException(status_code=503, detail="Admin tool not available")

    start_time = datetime.utcnow()

    try:
        response = await admin_tool.list_objects(request)

        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="admin",
                method="list_objects",
                request=request,
                response=response,
                start_time=start_time,
            )

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error or "Admin list failed")

        return response

    except HTTPException:
        raise
    except Exception as e:
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="admin",
                method="list_objects",
                request=request,
                error=e,
                start_time=start_time,
            )
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tools/admin/get", response_model=ToolResponse)
async def admin_get_object(
    request: GetObjectRequest,
    req: Request,
    actor: str = Depends(verify_auth),
):
    """Get a single organization/domain/instance/user for admin detail view."""
    if not admin_tool:
        raise HTTPException(status_code=503, detail="Admin tool not available")

    start_time = datetime.utcnow()

    try:
        response = await admin_tool.get_object(request)

        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="admin",
                method="get_object",
                request=request,
                response=response,
                start_time=start_time,
            )

        if not response.success:
            raise HTTPException(status_code=400, detail=response.error or "Admin get failed")

        return response

    except HTTPException:
        raise
    except Exception as e:
        if audit_tool:
            await audit_tool.log_tool_call(
                tool_name="admin",
                method="get_object",
                request=request,
                error=e,
                start_time=start_time,
            )
        raise HTTPException(status_code=500, detail=str(e))


# ============= OpenAPI Schema Endpoint =============

@app.get("/api/tools/schema")
async def get_tool_schemas():
    """Get OpenAPI schemas for all tools."""
    return {
        "notion": {
            "create_story": CreateStoryRequest.schema(),
            "list_stories": ListStoriesRequest.schema()
        },
        "github": {
            "create_issue": CreateIssueRequest.schema()
        },
        "responses": {
            "create_story": CreateStoryResponse.schema(),
            "list_stories": ListStoriesResponse.schema(),
            "create_issue": CreateIssueResponse.schema()
        }
    }


# ============= WebSocket Endpoint =============

@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    """WebSocket endpoint for real-time chat."""
    if not session_id:
        session_id = f"ws-{datetime.utcnow().timestamp()}"
    
    await manager.connect(websocket, session_id)
    
    try:
        # Send initial connection message
        await manager.send_message(session_id, {
            "type": "status",
            "data": {
                "status": "connected",
                "session_id": session_id,
                "message": "Connected to Engineering Department"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(
                websocket=websocket,
                session_id=session_id,
                message=data,
                pm_agent=pm_agent,
                audit_tool=audit_tool,
                manager=manager,
                form_data_agent=form_data_agent,
            )
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"WebSocket disconnected: {session_id}")
        
        # Log disconnection
        if audit_tool:
            await audit_tool.log_action(
                actor=f"ws-{session_id}",
                tool="websocket",
                action="disconnect",
                input_data={"session_id": session_id},
                output_data=None,
                result="success"
            )
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(session_id)
        
        # Log error
        if audit_tool:
            await audit_tool.log_action(
                actor=f"ws-{session_id}",
                tool="websocket",
                action="error",
                input_data={"session_id": session_id},
                output_data=None,
                result="failure",
                error=str(e)
            )


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8001))
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
