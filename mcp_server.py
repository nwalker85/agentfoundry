"""
MCP Server for Engineering Department
A FastAPI-based server implementing Model Context Protocol with tool endpoints.
"""

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

from mcp.schemas import (
    CreateStoryRequest, CreateStoryResponse,
    CreateIssueRequest, CreateIssueResponse,
    ListStoriesRequest, ListStoriesResponse,
    ToolResponse, AuditEntry
)
from mcp.tools import NotionTool, GitHubTool, AuditTool
from agent.pm_graph import PMAgent

# Load environment variables
load_dotenv('.env.local')

# Initialize tools globally
notion_tool: Optional[NotionTool] = None
github_tool: Optional[GitHubTool] = None
audit_tool: Optional[AuditTool] = None
pm_agent: Optional[PMAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global notion_tool, github_tool, audit_tool, pm_agent
    
    print("🚀 Starting Engineering Department MCP Server...")
    print(f"📊 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"🏢 Tenant ID: {os.getenv('TENANT_ID', 'unknown')}")
    
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
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
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


if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8001))
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
