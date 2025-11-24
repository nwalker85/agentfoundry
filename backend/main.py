"""
Agent Foundry Backend
FastAPI server integrating:
- MCP server (existing Engineering Department code)
- LiveKit voice sessions
- LangGraph agent orchestration
- WebSocket for text chat
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml
from fastapi import Depends, FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.admin_assistant_agent import AdminAssistantAgent
from agent.data_agent import DataAgent
from agents import AgentYAML, MarshalAgent
from backend import db
from backend.agents.system.observability_agent import AgentActivity, observability_agent
from backend.api import monitoring
from backend.events import event_bus
from backend.livekit_service import LiveKitService, get_livekit_service
from backend.routes.storage_routes import router as storage_router
from backend.utils.sqlite_backup import (
    create_backup as create_sqlite_backup,
    get_backup_file,
    list_backups as list_sqlite_backups,
    restore_backup as restore_sqlite_backup,
)
from backend.websocket_manager import websocket_manager

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
    session_id: str | None = None  # Frontend session ID for activity streaming


class VoiceSessionResponse(BaseModel):
    session_id: str
    room_name: str
    token: str
    livekit_url: str
    expires_at: datetime


class AgentListResponse(BaseModel):
    agents: list[dict]


class AgentStatusResponse(BaseModel):
    agent_id: str
    name: str
    version: str
    state: str
    phase: str
    uptime_seconds: int
    total_executions: int
    success_rate: float
    last_heartbeat: str | None


class ValidationRequest(BaseModel):
    yaml_content: str


class HealthSummaryResponse(BaseModel):
    timestamp: str
    total_agents: int
    healthy_agents: int
    unhealthy_agents: int
    overall_health_rate: float


class IntegrationToolHealth(BaseModel):
    success: int = 0
    failure: int = 0
    last_error: str | None = None


class IntegrationTool(BaseModel):
    toolName: str
    displayName: str
    description: str
    category: str
    logo: str
    tags: list[str] = []
    metadata: dict[str, Any] = {}
    health: IntegrationToolHealth | None = None


class IntegrationCatalogResponse(BaseModel):
    items: list[IntegrationTool]


class IntegrationConfigBase(BaseModel):
    organization_id: str
    project_id: str | None = None
    domain_id: str
    environment: str = "dev"
    instance_name: str
    base_url: str
    auth_method: str
    credentials: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    user_id: str | None = None


class IntegrationConfigResponse(IntegrationConfigBase):
    id: str
    tool_name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DomainSummary(BaseModel):
    id: str
    name: str
    organization_id: str


class OrganizationSummary(BaseModel):
    id: str
    name: str
    domains: list[DomainSummary]


class DataAgentQueryRequest(BaseModel):
    question: str


class DataAgentQueryResponse(BaseModel):
    sql: str | None = None
    rows: list[dict] | None = None
    error: str | None = None


class StateFieldModel(BaseModel):
    name: str
    type: str
    reducer: str | None = None
    description: str | None = None
    default_value: Any = None
    required: bool = True
    sensitive: bool = False


class StateSchemaModel(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    version: str = "1.0.0"
    fields: list[StateFieldModel] = []
    initial_state: dict[str, Any] = {}
    tags: list[str] = []
    created_by: str | None = "system"
    updated_by: str | None = None


class TriggerModel(BaseModel):
    id: str | None = None
    name: str
    type: str
    description: str | None = None
    channel: str | None = None
    config: dict[str, Any] = {}
    is_active: bool = True
    created_by: str | None = "system"
    updated_by: str | None = None


class ChannelWorkflowModel(BaseModel):
    id: str | None = None
    channel: str
    name: str
    description: str | None = None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    state_schema_id: str | None = None
    metadata: dict[str, Any] = {}
    created_by: str | None = "system"
    updated_by: str | None = None


class GraphTriggerAssignment(BaseModel):
    target_type: str  # agent | channel
    target_id: str
    trigger_ids: list[str]
    start_node_id: str | None = None


class SqliteBackupResponse(BaseModel):
    filename: str
    size_bytes: int
    created_at: datetime
    label: str | None = None
    created_by: str | None = None
    created_by_email: str | None = None


class SqliteBackupCreateRequest(BaseModel):
    label: str | None = None


class SqliteBackupRestoreRequest(BaseModel):
    filename: str


class SqliteTableInfo(BaseModel):
    name: str
    row_count: int


class SqliteColumnInfo(BaseModel):
    cid: int
    name: str
    type: str | None = None
    notnull: int
    dflt_value: Any | None = None
    pk: int


class SqliteRowMutation(BaseModel):
    data: dict[str, Any]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def load_agent_yaml_content(yaml_path: str) -> dict | None:
    """
    Load and parse YAML content from agent file.

    Args:
        yaml_path: Path to YAML file (e.g., "/app/agents/cibc-card-activation.agent.yaml")

    Returns:
        Parsed YAML as dictionary, or None if file doesn't exist or parsing fails
    """
    try:
        # Handle both absolute paths and relative paths
        if yaml_path.startswith("/app/"):
            full_path = yaml_path
        else:
            # Remove leading slash if present
            clean_path = yaml_path.lstrip("/")
            full_path = f"/app/{clean_path}"

        if os.path.exists(full_path):
            with open(full_path) as f:
                return yaml.safe_load(f)
        else:
            logger.warning(f"YAML file not found: {full_path}")
            return None
    except Exception as e:
        logger.error(f"Failed to load YAML from {yaml_path}: {e}")
        return None


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Agent Foundry API", description="LangGraph agents with LiveKit voice integration", version="0.8.1-dev"
)

# Register function catalog routes
try:
    from backend.routes.function_catalog import get_function_catalog_routes

    function_catalog_router = get_function_catalog_routes(db.get_connection())
    app.include_router(function_catalog_router)
except Exception as e:
    logger.warning(f"Failed to register function catalog routes: {e}")

# Register hierarchy routes (orgs/projects/domains)
try:
    from backend.routes.hierarchy import get_hierarchy_routes

    hierarchy_router = get_hierarchy_routes(db.get_connection())
    app.include_router(hierarchy_router)
except Exception as e:
    logger.warning(f"Failed to register hierarchy routes: {e}")

# Register favorites routes
try:
    from backend.routes.favorites import get_favorites_routes

    favorites_router = get_favorites_routes(db.get_connection())
    app.include_router(favorites_router)
except Exception as e:
    logger.warning(f"Failed to register favorites routes: {e}")

# Register admin database routes (Redis, PostgreSQL, MongoDB)
try:
    from backend.routes.admin_databases import router as admin_db_router

    app.include_router(admin_db_router)
except Exception as e:
    logger.warning(f"Failed to register admin database routes: {e}")

# Register agent logic extraction routes
try:
    from backend.routes.agent_logic import router as agent_logic_router

    app.include_router(agent_logic_router)
except Exception as e:
    logger.warning(f"Failed to register agent logic routes: {e}")

# Register secrets management routes
try:
    from backend.routes.secrets import router as secrets_router

    app.include_router(secrets_router)
except Exception as e:
    logger.warning(f"Failed to register secrets routes: {e}")

# Register integration gateway routes (MCP tool catalog)
try:
    from backend.routes.integrations import router as integrations_router

    app.include_router(integrations_router)
except Exception as e:
    logger.warning(f"Failed to register integration routes: {e}")

# Include routers
app.include_router(storage_router)
app.include_router(monitoring.router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTP request tracking middleware for Prometheus metrics
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track HTTP request metrics for Prometheus"""
    import time

    start_time = time.time()

    # Track in-progress requests
    method = request.method
    path = request.url.path

    # Normalize path to avoid high cardinality (remove IDs)
    import re

    normalized_path = re.sub(r"/[0-9a-f-]{36}", "/{id}", path)  # UUIDs
    normalized_path = re.sub(r"/\d+", "/{id}", normalized_path)  # Numeric IDs

    try:
        from backend.observability import http_requests_in_progress, record_http_request

        http_requests_in_progress.labels(method=method, endpoint=normalized_path).inc()

        response = await call_next(request)
        duration = time.time() - start_time

        record_http_request(method, normalized_path, response.status_code, duration)

        http_requests_in_progress.labels(method=method, endpoint=normalized_path).dec()
        return response

    except Exception:
        duration = time.time() - start_time
        try:
            from backend.observability import http_requests_in_progress, record_http_request

            record_http_request(method, normalized_path, 500, duration)
            http_requests_in_progress.labels(method=method, endpoint=normalized_path).dec()
        except:
            pass
        raise


# Global agents
marshal: MarshalAgent | None = None
data_agent: DataAgent | None = None
admin_assistant: AdminAssistantAgent | None = None

INTEGRATION_TIMEOUT_SECONDS = float(os.getenv("MCP_INTEGRATION_TIMEOUT", "15"))


def get_marshal() -> MarshalAgent:
    """Get the global Marshal Agent instance."""
    if marshal is None:
        raise HTTPException(
            status_code=503,
            detail="Marshal Agent not initialized. Server may be starting up.",
        )
    return marshal


def get_data_agent() -> DataAgent:
    """Lazy-init global DataAgent for control-plane queries."""
    global data_agent
    if data_agent is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="DataAgent requires ANTHROPIC_API_KEY to be set",
            )
        data_agent = DataAgent()
    return data_agent


def get_admin_assistant() -> AdminAssistantAgent:
    """Lazy-init global AdminAssistantAgent."""
    global admin_assistant
    if admin_assistant is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="Admin assistant requires OPENAI_API_KEY to be set",
            )
        admin_assistant = AdminAssistantAgent()
    return admin_assistant


def get_integration_base_url() -> str:
    """
    Return MCP integration gateway base URL.
    Uses service discovery (DNS) by default.
    """
    from backend.config.services import SERVICES

    return SERVICES.get_service_url("MCP_INTEGRATION").rstrip("/")


async def _integration_request(method: str, path: str, **kwargs) -> Any:
    """
    Helper to talk to the MCP integration gateway.

    Raises httpx.HTTPError on failure.
    """
    if not path.startswith("/"):
        path = f"/{path}"

    url = f"{get_integration_base_url()}{path}"

    async with httpx.AsyncClient(timeout=INTEGRATION_TIMEOUT_SECONDS) as client:
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text


# ============================================================================
# RBAC / AUTH ENDPOINTS
# ============================================================================


@app.post("/api/auth/user-permissions")
async def get_user_permissions(request: dict):
    """
    Get user RBAC permissions by email.
    Called by NextAuth during sign-in to load user permissions.
    """
    from backend.db import get_connection
    from backend.rbac_service import rbac_service

    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    try:
        # Look up user by email
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, organization_id, email, name FROM users WHERE email = ?", (email,))
            user_row = cur.fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail=f"User not found: {email}")

        user_id = user_row[0]
        org_id = user_row[1]

        # Get user permissions
        user_perms = rbac_service.get_user_with_permissions(user_id, org_id)

        if not user_perms:
            raise HTTPException(status_code=404, detail="User permissions not found")

        return {
            "user_id": user_perms.user_id,
            "organization_id": user_perms.organization_id,
            "email": user_perms.email,
            "name": user_perms.name,
            "permissions": user_perms.permissions,
            "roles": [{"name": r.name, "description": r.description} for r in user_perms.roles],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user_info():
    """
    Get current user info (requires authentication).
    This is a placeholder - should be protected with RBAC middleware.
    """
    # TODO: Add authentication middleware
    return {"message": "Protected endpoint - implement RBAC middleware"}


@app.post("/api/auth/validate-credentials")
async def validate_credentials(request: dict):
    """
    Validate user credentials for local authentication.
    Called by NextAuth CredentialsProvider.

    Request body:
        email: User email
        password: Plain text password

    Returns:
        User info if credentials valid, 401 if invalid
    """
    import bcrypt
    from backend.db import get_connection

    email = request.get("email")
    password = request.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, organization_id, email, name, password_hash FROM users WHERE email = ?",
                (email,),
            )
            user_row = cur.fetchone()

        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id, org_id, user_email, user_name, password_hash = user_row

        # Check if user has a password set (SSO-only users won't)
        if not password_hash:
            raise HTTPException(
                status_code=401,
                detail="This account uses SSO. Please sign in with Google.",
            )

        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Return user info for NextAuth session
        return {
            "id": user_id,
            "email": user_email,
            "name": user_name,
            "organizationId": org_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Credential validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.post("/api/auth/set-password")
async def set_user_password(request: dict):
    """
    Set or update a user's password.
    Should be protected - only allow for own account or admin.

    Request body:
        email: User email
        password: New password (will be hashed)
    """
    import bcrypt
    from backend.db import get_connection

    email = request.get("email")
    password = request.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    try:
        # Hash the password
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET password_hash = ?, updated_at = datetime('now', 'utc') WHERE email = ?",
                (password_hash, email),
            )
            conn.commit()

            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found")

        return {"message": "Password updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set password: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update password")


# ============================================================================
# VOICE ENDPOINTS
# ============================================================================


@app.post("/api/voice/session", response_model=VoiceSessionResponse)
async def create_voice_session(request: VoiceSessionRequest, livekit: LiveKitService = Depends(get_livekit_service)):
    """
    Create a new voice session for user-agent interaction.
    Returns LiveKit room token and connection details.
    """
    try:
        # CRITICAL: Await the async method
        session = await livekit.create_voice_session(
            user_id=request.user_id,
            agent_id=request.agent_id,
            session_duration_hours=request.session_duration_hours,
            session_id=request.session_id,  # Pass frontend session ID to store in room metadata
        )

        # Use LIVEKIT_PUBLIC_URL from service config (for browser access)
        from backend.config.services import SERVICES

        public_url = SERVICES.get_public_livekit_url()

        return VoiceSessionResponse(
            session_id=session.session_id,
            room_name=session.room_name,
            token=session.token,
            livekit_url=public_url,
            expires_at=session.expires_at,
        )
    except Exception as e:
        logger.error(f"Failed to create voice session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/room/{room_name}")
async def get_room_info(room_name: str, livekit: LiveKitService = Depends(get_livekit_service)):
    """Get information about a LiveKit room"""
    # CRITICAL: Await the async method
    info = await livekit.get_room_info(room_name)
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    return info


@app.delete("/api/voice/session/{room_name}")
async def end_voice_session(room_name: str, livekit: LiveKitService = Depends(get_livekit_service)):
    """End a voice session"""
    # CRITICAL: Await the async method
    success = await livekit.end_session(room_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to end session")
    return {"status": "session_ended", "room_name": room_name}


# ============================================================================
# AGENT INVOCATION ENDPOINT (IO Agent → Supervisor → Domain Agents)
# ============================================================================


class AgentInvokeRequest(BaseModel):
    agent_id: str
    input: str
    session_id: str
    route_via_supervisor: bool = True


class AgentInvokeResponse(BaseModel):
    output: str
    agent_id: str
    supervisor: str | None = None
    timestamp: str
    interrupted: bool = False
    error: str | None = None


@app.post("/api/agent/invoke", response_model=AgentInvokeResponse)
async def invoke_agent(request: AgentInvokeRequest):
    """
    Invoke an agent via the Supervisor Agent.
    Called by IO Agent to route user input through the agent workflow.

    Flow: IO Agent → Supervisor Agent → Domain Agent → Response
    """
    from backend.agents.supervisor_agent import supervisor_agent

    try:
        logger.info("🎯 Agent invocation request:")
        logger.info(f"   Agent ID: {request.agent_id}")
        logger.info(f"   Session: {request.session_id}")
        logger.info(f"   Via Supervisor: {request.route_via_supervisor}")

        if request.route_via_supervisor:
            # Route through Supervisor Agent
            result = await supervisor_agent.route(
                user_input=request.input, session_id=request.session_id, target_agent_id=request.agent_id
            )
        else:
            # Direct invocation (not implemented yet)
            result = {
                "output": "Direct agent invocation not yet implemented",
                "agent_id": request.agent_id,
                "error": "Use route_via_supervisor=true",
            }

        return AgentInvokeResponse(**result)

    except ValueError as e:
        # Agent not found or configuration error - return 404
        logger.error(f"❌ Agent not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        # Unexpected error - return 500
        logger.error(f"❌ Agent invocation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent invocation failed: {e!s}",
        )


# ============================================================================
# AGENT RESUME ENDPOINT (Resume from interrupt)
# ============================================================================


class AgentResumeRequest(BaseModel):
    agent_id: str
    session_id: str
    user_input: Any  # The value to resume with


class AgentResumeResponse(BaseModel):
    output: str
    agent_id: str
    session_id: str
    timestamp: str
    error: str | None = None


@app.post("/api/agent/resume", response_model=AgentResumeResponse)
async def resume_agent(request: AgentResumeRequest):
    """
    Resume an interrupted agent execution with user input.

    Called when a user responds to an interrupt prompt (human input node).
    The graph will resume from the interrupt point with the user's input.
    """
    from langgraph.types import Command

    try:
        logger.info("🔄 Agent resume request:")
        logger.info(f"   Agent ID: {request.agent_id}")
        logger.info(f"   Session: {request.session_id}")
        logger.info(f"   User input: {request.user_input}")

        # Get agent from registry
        agent_instance = await marshal.registry.get(request.agent_id)

        if not agent_instance:
            raise HTTPException(404, f"Agent {request.agent_id} not found in registry")

        # Broadcast user message (the resume input)
        import time

        await observability_agent.broadcast_activity(
            request.session_id,
            AgentActivity(
                agent_id="user",
                agent_name="User",
                event_type="user_message",
                timestamp=time.time(),
                message=str(request.user_input),
                metadata={"full_text": str(request.user_input), "context": "resume"},
            ),
        )

        # Broadcast resumed activity
        await observability_agent.broadcast_activity(
            request.session_id,
            AgentActivity(
                agent_id=request.agent_id,
                agent_name=agent_instance.metadata.name,
                event_type="resumed",
                timestamp=time.time(),
                message="Resuming workflow with user input",
                metadata={"user_input": str(request.user_input)[:100]},  # Truncate for safety
            ),
        )

        # Thread configuration (use same session_id as thread_id)
        thread_config = {"configurable": {"thread_id": request.session_id}}

        # Add tool tracking callback for observability
        from backend.middleware.tool_tracking_callback import ToolTrackingCallback

        tool_callback = ToolTrackingCallback(
            session_id=request.session_id, agent_id=request.agent_id, agent_name=agent_instance.metadata.name
        )

        # Add LangSmith callbacks for distributed tracing and token tracking
        from backend.observability import get_langsmith_callbacks

        langsmith_callbacks = get_langsmith_callbacks(
            session_id=request.session_id, agent_id=request.agent_id, run_name=f"{agent_instance.metadata.name} resume"
        )

        thread_config["callbacks"] = [tool_callback] + langsmith_callbacks

        # Resume with user input
        result = await agent_instance.graph.ainvoke(Command(resume=request.user_input), thread_config)

        # Extract response
        response_text = result.get("final_response", "")
        if not response_text and result.get("messages"):
            last_message = result["messages"][-1]
            response_text = last_message.content if hasattr(last_message, "content") else str(last_message)

        logger.info(f"✅ Agent resumed successfully, response length: {len(response_text)}")

        # Broadcast completion
        await observability_agent.broadcast_activity(
            request.session_id,
            AgentActivity(
                agent_id=request.agent_id,
                agent_name=agent_instance.metadata.name,
                event_type="completed",
                timestamp=time.time(),
                message="Workflow resumed and completed successfully",
                metadata={"response_length": len(response_text)},
            ),
        )

        # Broadcast agent message (the response)
        await observability_agent.broadcast_activity(
            request.session_id,
            AgentActivity(
                agent_id=request.agent_id,
                agent_name=agent_instance.metadata.name,
                event_type="agent_message",
                timestamp=time.time(),
                message=response_text,
                metadata={"full_text": response_text, "context": "resume"},
            ),
        )

        return AgentResumeResponse(
            output=response_text,
            agent_id=request.agent_id,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"❌ Agent resume error: {e}", exc_info=True)

        # Broadcast error activity
        import time

        try:
            agent_name = request.agent_id  # Fallback to ID if we can't get the instance
            try:
                agent_instance = await marshal.registry.get(request.agent_id)
                if agent_instance:
                    agent_name = agent_instance.metadata.name
            except:
                pass

            await observability_agent.broadcast_activity(
                request.session_id,
                AgentActivity(
                    agent_id=request.agent_id,
                    agent_name=agent_name,
                    event_type="error",
                    timestamp=time.time(),
                    message=f"Error resuming workflow: {str(e)[:100]}",
                    metadata={"error": str(e)},
                ),
            )
        except Exception as broadcast_error:
            logger.error(f"Failed to broadcast error activity: {broadcast_error}")

        return AgentResumeResponse(
            output="I encountered an error resuming the conversation.",
            agent_id=request.agent_id,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e),
        )


# ============================================================================
# DEEP AGENT INVOCATION ENDPOINT (Planning → Execution → Criticism)
# ============================================================================


class DeepAgentInvokeRequest(BaseModel):
    agent_id: str
    input: str
    session_id: str
    mode: str = "deep"  # "deep" for full cycle
    enable_planning: bool = True
    enable_execution: bool = True
    enable_criticism: bool = True
    max_iterations: int = 20


class DeepAgentInvokeResponse(BaseModel):
    output: str
    agent_id: str
    session_id: str
    timestamp: str
    tasks: list[dict[str, Any]] | None = None
    validation: dict[str, Any] | None = None
    error: str | None = None


@app.post("/api/agent/deep-invoke", response_model=DeepAgentInvokeResponse)
async def invoke_deep_agent(request: DeepAgentInvokeRequest):
    """
    Invoke a deep agent for orchestrated task execution.

    Deep Agent Flow:
    1. Planning: Break down request into tasks (using TodoList + discovery)
    2. Execution: Execute tasks using CIBC tools/agents (max_iterations loop)
    3. Criticism: Validate quality and completeness
    4. Replan: If validation fails, replan and retry

    Used by: CIBC Orchestrator for voice-based card operations
    """
    try:
        logger.info("🤖 Deep agent invocation request:")
        logger.info(f"   Agent ID: {request.agent_id}")
        logger.info(f"   Session: {request.session_id}")
        logger.info(f"   Mode: {request.mode}")
        logger.info(f"   Max Iterations: {request.max_iterations}")

        # Import deep agent components
        from backend.middleware.deep_agent_middleware import (
            SummarizationMiddleware,
            TodoListMiddleware,
        )

        # Initialize middleware
        todo_middleware = TodoListMiddleware()
        summarization_middleware = SummarizationMiddleware()

        # Phase 1: Planning - Discover tools and agents
        logger.info("📋 Phase 1: Planning with tool/agent discovery")

        # Discover CIBC tools and agents
        cibc_tools = todo_middleware.discover_cibc_tools()
        cibc_agents = todo_middleware.discover_cibc_agents()

        logger.info(f"   Discovered {len(cibc_tools)} CIBC tools")
        logger.info(f"   Discovered {len(cibc_agents)} CIBC agents")

        # Create initial task plan (simplified - actual implementation would use LLM)
        # For now, create a placeholder task structure
        initial_tasks = [
            {"id": "task-1", "description": f"Process user request: {request.input[:100]}", "status": "pending"}
        ]

        todo_middleware.write_todos(initial_tasks)

        # Phase 2: Execution - Execute tasks
        logger.info("⚙️  Phase 2: Execution")

        # Simplified execution - actual implementation would:
        # 1. Iterate through tasks
        # 2. Call appropriate CIBC tools/agents
        # 3. Update task status
        # 4. Handle errors and retries

        executed_tasks = []
        for task in todo_middleware.read_todos():
            task["status"] = "completed"
            executed_tasks.append(task)
            logger.info(f"   ✓ Completed: {task['description']}")

        # Phase 3: Criticism - Validate completion
        logger.info("🎯 Phase 3: Validation")

        validation_result = {
            "quality_score": 0.9,  # Placeholder
            "completeness": True,
            "security_compliance": True,
            "customer_satisfaction": True,
            "audit_trail": True,
            "message": "Request processed successfully",
        }

        # Generate user-facing response
        output = _generate_user_response(request.input, executed_tasks, validation_result)

        logger.info("✅ Deep agent execution completed")

        return DeepAgentInvokeResponse(
            output=output,
            agent_id=request.agent_id,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            tasks=executed_tasks,
            validation=validation_result,
        )

    except Exception as e:
        logger.error(f"❌ Deep agent invocation error: {e}", exc_info=True)
        return DeepAgentInvokeResponse(
            output="I encountered an error processing your request. Please try again or speak with a representative.",
            agent_id=request.agent_id,
            session_id=request.session_id,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e),
        )


def _generate_user_response(user_input: str, tasks: list[dict[str, Any]], validation: dict[str, Any]) -> str:
    """
    Generate natural language response for user based on task execution.

    Args:
        user_input: Original user request
        tasks: List of executed tasks
        validation: Validation result from critic

    Returns:
        User-facing response text for TTS
    """
    # Simplified response generation
    # Actual implementation would use LLM to generate natural response

    completed_count = len([t for t in tasks if t.get("status") == "completed"])

    if completed_count == 0:
        return "I'm sorry, I wasn't able to complete your request. Could you please try rephrasing it?"

    if validation.get("completeness"):
        return "I've processed your request successfully. Is there anything else I can help you with?"

    return "I've made progress on your request, but there are a few more steps needed. Let me continue working on that."


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
                "tags": instance.metadata.tags,
            }
            for agent_id, instance in agents.items()
        ]
    )


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, m: MarshalAgent = Depends(get_marshal)):
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
            "node_count": len(instance.config.spec.workflow.nodes),
        },
        "metrics": {
            "uptime_seconds": instance.status.uptime_seconds,
            "total_executions": instance.status.total_executions,
            "success_rate": instance.status.success_rate,
            "invocation_count": instance.invocation_count,
            "error_count": instance.error_count,
        },
        "loaded_at": instance.loaded_at.isoformat(),
        "last_invoked": instance.last_invoked.isoformat() if instance.last_invoked else None,
    }


@app.get("/api/agents/{agent_id}/status", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str, m: MarshalAgent = Depends(get_marshal)):
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
        last_heartbeat=instance.status.last_heartbeat,
    )


# ============================================================================
# CONTROL-PLANE (ORG / DOMAIN) ENDPOINTS
# ============================================================================


@app.get("/api/control/organizations", response_model=list[OrganizationSummary])
async def list_organizations() -> list[OrganizationSummary]:
    """
    List organizations and their domains for the UI header and Forge.

    Data comes from the control-plane Postgres database via backend.db.
    """
    try:
        raw_orgs = db.get_organizations_with_domains()
    except Exception as e:
        logger.error("Failed to load organizations from database: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load organizations")

    return [
        OrganizationSummary(
            id=o["id"],
            name=o["name"],
            domains=[
                DomainSummary(
                    id=d["id"],
                    name=d["name"],
                    organization_id=d["organization_id"],
                )
                for d in o.get("domains", [])
            ],
        )
        for o in raw_orgs
    ]


@app.get("/api/control/agents")
async def list_agents(organization_id: str | None = None, domain_id: str | None = None, environment: str | None = None):
    """
    List agents from the control-plane database.
    Filters by organization_id and domain_id if provided.
    Excludes system agents (is_system_agent=true).
    """
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT
                    id, organization_id, domain_id, name, display_name,
                    description, version, status, environment, created_by,
                    tags, created_at, updated_at
                FROM agents
                WHERE is_system_agent = FALSE
            """
            params = []

            if organization_id:
                query += " AND organization_id = ?"
                params.append(organization_id)

            if domain_id:
                query += " AND domain_id = ?"
                params.append(domain_id)

            if environment:
                query += " AND environment = ?"
                params.append(environment)

            query += " ORDER BY created_at DESC"

            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            agents = []
            for row in rows:
                agent = dict(zip(columns, row))
                # Convert timestamps to ISO format
                if agent.get("created_at"):
                    agent["created_at"] = agent["created_at"].isoformat()
                if agent.get("updated_at"):
                    agent["updated_at"] = agent["updated_at"].isoformat()
                agents.append(agent)

            return {"agents": agents}
    except Exception as e:
        logger.error("Failed to list agents: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list agents")


@app.websocket("/api/events/subscribe")
async def websocket_events(websocket: WebSocket):
    """
    WebSocket endpoint for subscribing to real-time events.

    Usage from frontend:
    ```typescript
    const ws = new WebSocket('ws://localhost:8000/api/events/subscribe')

    // Subscribe to agent events for Quant org
    ws.send(JSON.stringify({
      action: 'subscribe',
      filter: {
        type: 'agent.*',
        organization_id: 'quant',
        domain_id: 'demo'
      }
    }))

    // Receive events
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      console.log('Event received:', data.type, data.data)
    }
    ```
    """
    await websocket_manager.connect(websocket)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            await websocket_manager.handle_message(websocket, message)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        websocket_manager.disconnect(websocket)


@app.post("/api/control/query", response_model=DataAgentQueryResponse)
async def query_control_plane(request: DataAgentQueryRequest) -> DataAgentQueryResponse:
    """
    Query control-plane data (organizations, domains, instances, deployments)
    using the LangGraph DataAgent (NL → SQL → rows).
    """
    agent = get_data_agent()
    state = await agent.query(request.question)
    return DataAgentQueryResponse(
        sql=state.get("sql"),
        rows=state.get("rows"),
        error=state.get("error"),
    )


@app.post("/api/admin/assistant/chat")
async def admin_assistant_chat(request: DataAgentQueryRequest):
    """
    Chat endpoint for the Admin Assistant.

    For v1, we reuse DataAgentQueryRequest ('question') as the message field.
    """
    assistant = get_admin_assistant()
    result = await assistant.chat(request.question)
    return result


# ============================================================================
# INTEGRATIONS / TOOL CATALOG
# ============================================================================


@app.get("/api/integrations/tools", response_model=IntegrationCatalogResponse)
async def get_integration_catalog():
    try:
        raw_catalog = await _integration_request("GET", "/tools")
    except httpx.HTTPError as exc:
        logger.error("Failed to load integration catalog: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Integration gateway unavailable",
        )

    health_data: dict[str, Any] = {}
    try:
        raw_health = await _integration_request("GET", "/health")
        if isinstance(raw_health, dict):
            health_data = raw_health.get("tools", {}) or {}
    except httpx.HTTPError as exc:
        logger.warning("Failed to fetch integration health metrics: %s", exc)
        health_data = {}

    catalog_items: list[IntegrationTool] = []
    for item in raw_catalog.get("items", []):
        metrics = None
        tool_name = item.get("toolName")
        if tool_name and isinstance(health_data, dict):
            metrics = health_data.get(tool_name)

        if isinstance(metrics, dict):
            catalog_items.append(
                IntegrationTool(
                    **item,
                    health=IntegrationToolHealth(
                        success=metrics.get("success", 0),
                        failure=metrics.get("failure", 0),
                        last_error=metrics.get("last_error"),
                    ),
                )
            )
        else:
            catalog_items.append(IntegrationTool(**item))

    return IntegrationCatalogResponse(items=catalog_items)


@app.get("/api/integrations/tools/{tool_name}")
async def get_integration_tool_detail(tool_name: str):
    try:
        data = await _integration_request("GET", f"/tools/{tool_name}")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Tool not found")
        logger.error("Integration tool detail failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail="Integration gateway error")
    except httpx.HTTPError as exc:
        logger.error("Integration tool detail unavailable: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail="Integration gateway unavailable")

    try:
        health = await _integration_request("GET", "/health")
        if isinstance(health, dict):
            metrics = (health.get("tools") or {}).get(tool_name)
            if metrics:
                data["health"] = metrics
    except httpx.HTTPError:
        pass

    return data


@app.post("/api/integrations/tools/{tool_name}/invoke")
async def invoke_integration_tool(tool_name: str, payload: dict[str, Any] | None = None):
    payload = payload or {}

    try:
        data = await _integration_request("POST", f"/tools/{tool_name}/invoke", json=payload)
        return data
    except httpx.HTTPStatusError as exc:
        logger.warning("Integration tool invocation failed: %s", exc)
        detail: Any
        content_type = exc.response.headers.get("content-type", "")
        if "application/json" in content_type:
            detail = exc.response.json()
        else:
            detail = exc.response.text
        raise HTTPException(status_code=exc.response.status_code, detail=detail)
    except httpx.HTTPError as exc:
        logger.error("Integration tool invocation unavailable: %s", exc, exc_info=True)
        raise HTTPException(status_code=502, detail="Integration gateway unavailable")


@app.get("/api/integrations/configs")
async def list_integration_configs(
    organization_id: str | None = None,
    domain_id: str | None = None,
    environment: str = "dev",
):
    if not organization_id or not domain_id:
        raise HTTPException(status_code=400, detail="organization_id and domain_id are required")

    try:
        configs = db.list_integration_configs(organization_id, domain_id, environment)
        return {"items": configs}
    except Exception as exc:
        logger.error("Failed to list integration configs: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load integration configurations")


@app.get("/api/integrations/configs/{tool_name}", response_model=Optional[IntegrationConfigResponse])
async def get_integration_config_endpoint(
    tool_name: str,
    organization_id: str | None = None,
    domain_id: str | None = None,
    environment: str = "dev",
):
    if not organization_id or not domain_id:
        raise HTTPException(status_code=400, detail="organization_id and domain_id are required")

    try:
        config = db.get_integration_config(tool_name, organization_id, domain_id, environment)
        return config
    except Exception as exc:
        logger.error("Failed to fetch integration config: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load integration configuration")


@app.post("/api/integrations/configs/{tool_name}", response_model=IntegrationConfigResponse)
async def upsert_integration_config_endpoint(tool_name: str, payload: IntegrationConfigBase):
    try:
        config = db.upsert_integration_config(
            tool_name=tool_name,
            organization_id=payload.organization_id,
            project_id=payload.project_id,
            domain_id=payload.domain_id,
            environment=payload.environment,
            instance_name=payload.instance_name,
            base_url=payload.base_url,
            auth_method=payload.auth_method,
            credentials=payload.credentials,
            metadata=payload.metadata,
            user_id=payload.user_id,
        )
        return config
    except Exception as exc:
        logger.error("Failed to save integration config: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save integration configuration")


# ============================================================================
# PUBLIC CONFIG - Non-secret configuration for frontend (Service Registry)
# ============================================================================
# NOTE: Auth config endpoint (/api/config/auth) is defined near the end of this file
# and reads from the PostgreSQL settings table for Zitadel configuration.


@app.get("/api/system/metrics")
async def get_system_metrics():
    """
    Get system metrics for the status footer and system tab.
    Returns backend health, agent counts, deployment info, etc.
    """
    try:
        # Get agent count from database
        agent_count = 0
        try:
            with db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) as count FROM agents WHERE is_system_agent = FALSE")
                result = cur.fetchone()
                if result:
                    agent_count = result["count"]
        except Exception as e:
            logger.warning(f"Failed to get agent count: {e}")

        # Mock service statuses - in production, these would be real health checks
        services = [
            {"name": "FastAPI Server", "status": "healthy", "latency": 5, "memory": "256 MB", "uptime": "2h 34m"},
            {"name": "PostgreSQL", "status": "healthy", "latency": 12, "memory": "512 MB", "uptime": "2h 34m"},
            {"name": "Redis", "status": "healthy", "latency": 3, "memory": "128 MB", "uptime": "2h 34m"},
            {"name": "LiveKit Server", "status": "healthy", "latency": 45, "memory": "1.1 GB", "uptime": "2h 34m"},
        ]

        return {
            "services": services,
            "agentCount": agent_count,
            "activeDeployments": 0,  # TODO: Get from deployments table
            "eventRate": 0,  # TODO: Calculate from event bus
            "successRate": 100,  # TODO: Calculate from metrics
            "cpuUsage": 0,  # TODO: Get from system metrics
            "memoryUsage": 0,  # TODO: Get from system metrics
            "diskUsage": 0,  # TODO: Get from system metrics
            "dbLatency": 12,  # TODO: Measure actual DB latency
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@app.get("/api/system/logs")
async def get_system_logs(limit: int = 100):
    """
    Get recent application logs for the logs tab.
    Returns last N log entries with level, timestamp, message, etc.
    """
    try:
        # In a production system, this would read from a log file or log aggregation service
        # For now, we'll return mock logs
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Agent Foundry backend started",
                "module": "main",
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Event bus initialized",
                "module": "events",
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Database connection established",
                "module": "db",
            },
        ]

        return {"logs": logs[-limit:]}
    except Exception as e:
        logger.error(f"Failed to get system logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get system logs")


@app.post("/api/agents/{agent_id}/reload")
async def reload_agent(agent_id: str, m: MarshalAgent = Depends(get_marshal)):
    """Hot-reload a specific agent from its YAML file"""
    success = await m.reload_agent(agent_id)

    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to reload agent '{agent_id}'. Check logs for details.")

    return {"status": "reloaded", "agent_id": agent_id}


@app.post("/api/agents/validate")
async def validate_agent_yaml(request: ValidationRequest, m: MarshalAgent = Depends(get_marshal)):
    """Validate agent YAML without loading it"""
    import tempfile
    from pathlib import Path

    import yaml

    try:
        # Parse YAML content
        yaml_data = yaml.safe_load(request.yaml_content)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".agent.yaml", delete=False) as f:
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
                "warnings": result.warnings,
            }
        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)

    except Exception as e:
        return {"valid": False, "agent_id": None, "errors": [f"Failed to parse YAML: {e!s}"], "warnings": []}


@app.get("/api/agents/{agent_id}/health")
async def get_agent_health(agent_id: str, m: MarshalAgent = Depends(get_marshal)):
    """Get health check history and metrics for an agent"""
    # Get metrics from health monitor
    metrics = m.health_monitor.get_metrics(agent_id)

    if not metrics:
        raise HTTPException(status_code=404, detail=f"No health data available for '{agent_id}'")

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
            "last_check": metrics.last_check.isoformat() if metrics.last_check else None,
        },
        "recent_checks": [
            {
                "timestamp": check.timestamp.isoformat(),
                "healthy": check.healthy,
                "latency_ms": check.latency_ms,
                "error": check.error_message,
            }
            for check in recent_checks
        ],
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
        overall_health_rate=summary["overall_health_rate"],
    )


# ============================================================================
# WEBSOCKET FOR TEXT CHAT
# ============================================================================


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, session_id: str | None = None):
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
        from backend.agents.supervisor_agent import supervisor_agent

        # Track the current agent_id for this session (can be changed via messages)
        current_agent_id: str | None = None

        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "message")
            msg_data = data.get("data", {})

            # Handle ping/pong for heartbeat
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                continue

            # Handle agent selection
            if msg_type == "select_agent":
                current_agent_id = msg_data.get("agent_id")
                logger.info(f"WebSocket session {session_id} selected agent: {current_agent_id}")
                await websocket.send_json({
                    "type": "agent_selected",
                    "data": {"agent_id": current_agent_id},
                    "timestamp": datetime.utcnow().isoformat(),
                })
                continue

            # Handle chat messages
            if msg_type == "message":
                content = msg_data.get("content", "")
                agent_id = msg_data.get("agent_id") or current_agent_id

                if not agent_id:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"error": "No agent selected. Please select an agent first."},
                        "timestamp": datetime.utcnow().isoformat(),
                    })
                    continue

                # Send processing status
                await websocket.send_json({
                    "type": "status",
                    "data": {"status": "processing", "message": "Processing your request..."},
                    "timestamp": datetime.utcnow().isoformat(),
                })

                try:
                    # Route through Supervisor Agent
                    result = await supervisor_agent.route(
                        user_input=content,
                        session_id=session_id,
                        target_agent_id=agent_id,
                    )

                    # Send response
                    response = {
                        "type": "message",
                        "data": {
                            "content": result.get("output", "Processing complete."),
                            "agent_id": result.get("agent_id"),
                            "interrupted": result.get("interrupted", False),
                            "artifacts": result.get("artifacts", []),
                        },
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    await websocket.send_json(response)

                except Exception as agent_error:
                    logger.error(f"Agent processing error: {agent_error}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "data": {"error": str(agent_error)},
                        "timestamp": datetime.utcnow().isoformat(),
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed


# ============================================================================
# HEALTH & STATUS
# ============================================================================

# ============================================================================
# DESIGNER / FORGE ENDPOINTS
# ============================================================================


@app.get("/api/admin/sqlite/backups")
async def list_sqlite_backups_endpoint():
    """List SQLite backup files."""
    try:
        backups = [
            SqliteBackupResponse(
                filename=backup.filename,
                size_bytes=backup.size_bytes,
                created_at=backup.created_at,
                label=backup.label,
                created_by=backup.created_by,
                created_by_email=backup.created_by_email,
            )
            for backup in list_sqlite_backups()
        ]
        return {"items": backups}
    except Exception as e:
        logger.error(f"Failed to list SQLite backups: {e}")
        raise HTTPException(status_code=500, detail="Unable to list SQLite backups")


@app.post("/api/admin/sqlite/backups")
async def create_sqlite_backup_endpoint(payload: SqliteBackupCreateRequest, request: Request):
    """Create a new SQLite backup."""
    try:
        # Extract user info from headers (set by NextAuth frontend)
        user_name = request.headers.get("x-user-name")
        user_email = request.headers.get("x-user-email")

        backup = create_sqlite_backup(label=payload.label, user_name=user_name, user_email=user_email)
        return SqliteBackupResponse(
            filename=backup.filename,
            size_bytes=backup.size_bytes,
            created_at=backup.created_at,
            label=backup.label,
        )
    except Exception as e:
        logger.error(f"Failed to create SQLite backup: {e}")
        raise HTTPException(status_code=500, detail="Unable to create backup")


@app.post("/api/admin/sqlite/backups/restore")
async def restore_sqlite_backup_endpoint(request: SqliteBackupRestoreRequest):
    """Restore the SQLite database from an existing backup."""
    try:
        restore_sqlite_backup(request.filename)
        return {"status": "restored", "filename": request.filename}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        logger.error(f"Failed to restore SQLite backup: {e}")
        raise HTTPException(status_code=500, detail="Unable to restore backup")


@app.get("/api/admin/sqlite/backups/download")
async def download_sqlite_backup(filename: str = Query(..., description="Backup filename")):
    """Download a specific SQLite backup file."""
    try:
        path = get_backup_file(filename)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")
        return FileResponse(path, filename=path.name, media_type="application/octet-stream")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download SQLite backup: {e}")
        raise HTTPException(status_code=500, detail="Unable to download backup")


@app.get("/api/admin/sqlite/tables")
async def list_sqlite_tables_endpoint():
    """List tables in the SQLite control-plane database."""
    try:
        tables = db.list_sqlite_tables()
        return {"items": [SqliteTableInfo(**table) for table in tables]}
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        raise HTTPException(status_code=500, detail="Unable to list tables")


@app.get("/api/admin/sqlite/tables/{table_name}/schema")
async def get_sqlite_table_schema(table_name: str):
    """Return schema information for a specific table."""
    try:
        schema = db.get_table_schema(table_name)
        return {"columns": [SqliteColumnInfo(**column) for column in schema]}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid table name")
    except Exception as e:
        logger.error(f"Failed to fetch table schema: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch schema")


@app.get("/api/admin/sqlite/tables/{table_name}/rows")
async def get_sqlite_table_rows(
    table_name: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return rows from a table (with internal rowid)."""
    try:
        rows = db.get_table_rows(table_name, limit, offset)
        return {"items": rows}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid table name")
    except Exception as e:
        logger.error(f"Failed to fetch rows: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch rows")


@app.post("/api/admin/sqlite/tables/{table_name}/rows")
async def insert_sqlite_row(table_name: str, payload: SqliteRowMutation):
    """Insert a row into a table."""
    try:
        rowid = db.insert_table_row(table_name, payload.data)
        return {"rowid": rowid}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to insert row: {e}")
        raise HTTPException(status_code=500, detail="Unable to insert row")


@app.patch("/api/admin/sqlite/tables/{table_name}/rows/{rowid}")
async def update_sqlite_row(table_name: str, rowid: int, payload: SqliteRowMutation):
    """Update a row via its rowid."""
    try:
        db.update_table_row(table_name, rowid, payload.data)
        return {"status": "updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update row: {e}")
        raise HTTPException(status_code=500, detail="Unable to update row")


@app.delete("/api/admin/sqlite/tables/{table_name}/rows/{rowid}")
async def delete_sqlite_row(table_name: str, rowid: int):
    """Delete a row from a table via its rowid."""
    try:
        db.delete_table_row(table_name, rowid)
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete row: {e}")
        raise HTTPException(status_code=500, detail="Unable to delete row")


@app.get("/api/forge/state-schemas")
async def get_state_schemas():
    """List all state schemas for the visual designer."""
    try:
        return {"items": db.list_state_schemas()}
    except Exception as e:
        logger.error(f"Failed to list state schemas: {e}")
        raise HTTPException(status_code=500, detail="Unable to list state schemas")


@app.post("/api/forge/state-schemas")
async def create_or_update_state_schema(schema: StateSchemaModel):
    """Create or update a state schema."""
    try:
        saved = db.upsert_state_schema(schema.dict())
        return saved
    except Exception as e:
        logger.error(f"Failed to save state schema: {e}")
        raise HTTPException(status_code=500, detail="Unable to save state schema")


@app.delete("/api/forge/state-schemas/{schema_id}")
async def remove_state_schema(schema_id: str):
    """Delete a state schema."""
    try:
        db.delete_state_schema(schema_id)
        return {"status": "deleted", "id": schema_id}
    except Exception as e:
        logger.error(f"Failed to delete state schema: {e}")
        raise HTTPException(status_code=500, detail="Unable to delete state schema")


@app.get("/api/forge/triggers")
async def get_triggers(channel: str | None = None):
    """List trigger definitions."""
    try:
        return {"items": db.list_triggers(channel)}
    except Exception as e:
        logger.error(f"Failed to list triggers: {e}")
        raise HTTPException(status_code=500, detail="Unable to list triggers")


@app.post("/api/forge/triggers")
async def create_or_update_trigger(trigger: TriggerModel):
    """Create or update a trigger."""
    try:
        saved = db.upsert_trigger(trigger.dict())
        return saved
    except Exception as e:
        logger.error(f"Failed to save trigger: {e}")
        raise HTTPException(status_code=500, detail="Unable to save trigger")


@app.delete("/api/forge/triggers/{trigger_id}")
async def remove_trigger(trigger_id: str):
    """Delete a trigger from the registry."""
    try:
        db.delete_trigger(trigger_id)
        return {"status": "deleted", "id": trigger_id}
    except Exception as e:
        logger.error(f"Failed to delete trigger: {e}")
        raise HTTPException(status_code=500, detail="Unable to delete trigger")


@app.get("/api/forge/channel-workflows")
async def get_channel_workflows(channel: str | None = None):
    """List channel workflows (core orchestration graphs)."""
    try:
        return {"items": db.list_channel_workflows(channel)}
    except Exception as e:
        logger.error(f"Failed to list channel workflows: {e}")
        raise HTTPException(status_code=500, detail="Unable to list channel workflows")


@app.get("/api/forge/channel-workflows/{workflow_id}")
async def get_channel_workflow(workflow_id: str):
    """Get a single workflow."""
    workflow = db.get_channel_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.post("/api/forge/channel-workflows")
async def create_or_update_channel_workflow(workflow: ChannelWorkflowModel):
    """Create or update a workflow."""
    try:
        saved = db.upsert_channel_workflow(workflow.dict())
        return saved
    except Exception as e:
        logger.error(f"Failed to save channel workflow: {e}")
        raise HTTPException(status_code=500, detail="Unable to save channel workflow")


@app.delete("/api/forge/channel-workflows/{workflow_id}")
async def delete_channel_workflow(workflow_id: str):
    """Delete a workflow."""
    try:
        db.delete_channel_workflow(workflow_id)
        return {"status": "deleted", "id": workflow_id}
    except Exception as e:
        logger.error(f"Failed to delete channel workflow: {e}")
        raise HTTPException(status_code=500, detail="Unable to delete workflow")


@app.get("/api/forge/graph-triggers")
async def get_graph_triggers(target_type: str, target_id: str):
    """Return triggers currently attached to a graph."""
    try:
        return {"items": db.list_graph_triggers(target_type, target_id)}
    except Exception as e:
        logger.error(f"Failed to list graph triggers: {e}")
        raise HTTPException(status_code=500, detail="Unable to list graph triggers")


@app.post("/api/forge/graph-triggers")
async def save_graph_triggers(assignment: GraphTriggerAssignment):
    """Assign triggers to a graph (agent or channel)."""
    try:
        db.save_graph_triggers(
            assignment.target_type,
            assignment.target_id,
            assignment.trigger_ids,
            assignment.start_node_id,
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to save graph triggers: {e}")
        raise HTTPException(status_code=500, detail="Unable to save graph triggers")


# ============================================================================
# UNIFIED GRAPH API (User Agents, Channel Workflows, System Agents)
# ============================================================================


@app.get("/api/graphs")
async def list_graphs_endpoint(
    graph_type: str | None = None,
    channel: str | None = None,
    org_id: str | None = None,
    domain_id: str | None = None,
    environment: str = "dev",
):
    """
    List all graphs with optional filtering.

    Query parameters:
    - graph_type: Filter by 'user', 'channel', or 'system'
    - channel: Filter by channel (for channel workflows)
    - org_id: Filter by organization
    - domain_id: Filter by domain
    - environment: Filter by environment (default: dev)
    """
    try:
        # Get graphs from database
        graphs = db.list_graphs(
            graph_type=graph_type, channel=channel, org_id=org_id, domain_id=domain_id, environment=environment
        )

        # Also include agents from Marshal registry
        if marshal:
            marshal_agents = await marshal.registry.list_all()
            for agent_id, agent_instance in marshal_agents.items():
                # Convert Marshal agent to graph format
                config = agent_instance.config
                # Load YAML content for frontend graph rendering
                yaml_path = f"/app/agents/{agent_id}.agent.yaml"
                yaml_data = load_agent_yaml_content(yaml_path)

                marshal_graph = {
                    "id": config.metadata.id,
                    "organization_id": "cibc",  # Default, could be in metadata
                    "domain_id": "card-services",  # Default, could be in metadata
                    "name": config.metadata.name,
                    "display_name": config.metadata.name,
                    "description": config.metadata.description or "",
                    "version": config.metadata.version,
                    "status": config.status.phase if hasattr(config, "status") else "active",
                    "environment": "dev",
                    "yaml_path": yaml_path,
                    "is_system_agent": 0,
                    "system_tier": None,
                    "created_by": "marshal",
                    "tags": str(config.metadata.tags) if hasattr(config.metadata, "tags") else "[]",
                    "graph_type": "user",  # Could be inferred from metadata
                    "channel": None,
                    "yaml_content": json.dumps(yaml_data) if yaml_data else None,
                    "created_at": config.metadata.created if hasattr(config.metadata, "created") else None,
                    "updated_at": config.metadata.updated if hasattr(config.metadata, "updated") else None,
                }
                # Only add if not already in database (avoid duplicates)
                if not any(g["id"] == agent_id for g in graphs):
                    graphs.append(marshal_graph)

        return {"graphs": graphs}
    except Exception as e:
        logger.error(f"Failed to list graphs: {e}")
        raise HTTPException(status_code=500, detail="Unable to list graphs")


@app.get("/api/graphs/{graph_id}")
async def get_graph_endpoint(graph_id: str):
    """
    Get a single graph by ID.
    Checks both database and Marshal registry.
    """
    try:
        # First check database
        graph = db.get_graph(graph_id)
        if graph:
            return graph

        # If not in database, check Marshal registry
        if marshal:
            agent_instance = await marshal.registry.get(graph_id)
            if agent_instance:
                # Convert Marshal agent to graph format
                config = agent_instance.config

                # Load YAML content for frontend graph rendering
                yaml_path = f"/app/agents/{graph_id}.agent.yaml"
                yaml_data = load_agent_yaml_content(yaml_path)

                marshal_graph = {
                    "id": config.metadata.id,
                    "organization_id": "cibc",
                    "domain_id": "card-services",
                    "name": config.metadata.name,
                    "display_name": config.metadata.name,
                    "description": config.metadata.description or "",
                    "version": config.metadata.version,
                    "status": config.status.phase if hasattr(config, "status") else "active",
                    "environment": "dev",
                    "yaml_path": yaml_path,
                    "is_system_agent": 0,
                    "system_tier": None,
                    "created_by": "marshal",
                    "tags": str(config.metadata.tags) if hasattr(config.metadata, "tags") else "[]",
                    "graph_type": "user",
                    "channel": None,
                    "yaml_content": json.dumps(yaml_data) if yaml_data else None,
                    "created_at": config.metadata.created if hasattr(config.metadata, "created") else None,
                    "updated_at": config.metadata.updated if hasattr(config.metadata, "updated") else None,
                }
                return marshal_graph

        # Not found in either database or Marshal
        raise HTTPException(status_code=404, detail="Graph not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get graph {graph_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to get graph")


@app.post("/api/graphs")
async def upsert_graph_endpoint(request: dict):
    """
    Create or update a graph.

    Expects a graph dictionary with:
    - metadata: { id, name, type, version, organization_id, domain_id, channel, ... }
    - spec: { state_schema_id, triggers, graph: { nodes, edges } }
    """
    try:
        graph = db.upsert_graph(request)
        return graph
    except Exception as e:
        logger.error(f"Failed to upsert graph: {e}")
        raise HTTPException(status_code=500, detail=f"Unable to save graph: {e!s}")


@app.delete("/api/graphs/{graph_id}")
async def delete_graph_endpoint(graph_id: str):
    """
    Delete a graph from database, file system, and Marshal registry.
    """
    try:
        # 1. Delete from database and file system
        db.delete_graph(graph_id)

        # 2. Unregister from Marshal registry (if loaded)
        if marshal:
            try:
                unregistered = await marshal.registry.unregister(graph_id)
                if unregistered:
                    logger.info(f"Unregistered {graph_id} from Marshal registry")
            except Exception as e:
                logger.warning(f"Could not unregister from Marshal: {e}")

        return {"status": "ok", "message": f"Graph {graph_id} deleted"}
    except Exception as e:
        logger.error(f"Failed to delete graph {graph_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to delete graph")


# ============================================================================
# GRAPH VERSION MANAGEMENT
# ============================================================================


@app.get("/api/graphs/{graph_id}/versions")
async def list_graph_versions(graph_id: str):
    """
    List all versions for a graph/agent.
    Returns versions ordered by version_number descending (newest first).
    """
    try:
        versions = db.get_agent_versions(graph_id)
        return {"graph_id": graph_id, "versions": versions, "count": len(versions)}
    except Exception as e:
        logger.error(f"Failed to list versions for graph {graph_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to list versions")


@app.get("/api/graphs/{graph_id}/versions/{version_id}")
async def get_graph_version(graph_id: str, version_id: str):
    """
    Get a specific version of a graph/agent.
    """
    try:
        version = db.get_agent_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        if version["agent_id"] != graph_id:
            raise HTTPException(status_code=404, detail="Version does not belong to this graph")
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version {version_id} for graph {graph_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to get version")


@app.post("/api/graphs/{graph_id}/rollback/{version_id}")
async def rollback_graph_version(graph_id: str, version_id: str):
    """
    Rollback a graph/agent to a specific version.
    Creates a new version with the content from the specified version.
    """
    try:
        new_version = db.rollback_to_version(graph_id, version_id)
        return {
            "status": "ok",
            "message": f"Rolled back to version {version_id}",
            "new_version": new_version,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rollback graph {graph_id} to version {version_id}: {e}")
        raise HTTPException(status_code=500, detail="Unable to rollback version")


@app.post("/api/graphs/{graph_id}/deploy")
async def deploy_graph_endpoint(graph_id: str):
    """
    Deploy a graph to production.

    Creates Python + YAML files, saves to agents/ directory, triggers hot-reload.
    """
    try:
        import json

        from backend.services.agent_deployer import agent_deployer

        # First check database
        graph = db.get_graph(graph_id)

        # If not in database, check Marshal registry (same as GET endpoint)
        if not graph and marshal:
            agent_instance = await marshal.registry.get(graph_id)
            if agent_instance:
                config = agent_instance.config
                yaml_path = f"/app/agents/{graph_id}.agent.yaml"
                yaml_data = load_agent_yaml_content(yaml_path)

                graph = {
                    "id": config.metadata.id,
                    "organization_id": "cibc",
                    "domain_id": "card-services",
                    "name": config.metadata.name,
                    "display_name": config.metadata.name,
                    "description": config.metadata.description or "",
                    "version": config.metadata.version,
                    "yaml_content": json.dumps(yaml_data) if yaml_data else None,
                }

        if not graph:
            raise HTTPException(
                status_code=404,
                detail=f"Graph '{graph_id}' not found. Please save the graph before deploying.",
            )

        # Parse yaml_content JSON string
        yaml_content = graph.get("yaml_content", "{}")
        if isinstance(yaml_content, str):
            try:
                graph_obj = json.loads(yaml_content) if yaml_content else {}
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid graph content: Unable to parse YAML/JSON - {e}",
                )
        else:
            graph_obj = yaml_content or {}

        # Extract metadata
        metadata = graph_obj.get("metadata", {})
        agent_id = metadata.get("id") or graph_id
        agent_name = metadata.get("name") or graph.get("name") or f"Agent {graph_id}"

        # Extract graph spec - check both "graph" (ReactFlow format) and "workflow" (YAML format)
        spec = graph_obj.get("spec", {})
        graph_data = spec.get("graph", {})
        workflow_data = spec.get("workflow", {})

        # Determine if this is ReactFlow format or YAML/workflow format
        is_reactflow_format = bool(graph_data.get("nodes"))
        is_workflow_format = bool(workflow_data.get("nodes") or workflow_data.get("entry_point"))

        if is_reactflow_format:
            # ReactFlow format validation
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])

            if not nodes:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Graph has no nodes. Please add at least an Entry Point and one Process node in the visual editor.",
                )

            # Check for entry point
            has_entry_point = any(n.get("type") == "entryPoint" for n in nodes)
            if not has_entry_point:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Graph is missing an Entry Point node. Drag an 'Entry Point' node from the toolbar onto the canvas.",
                )

            # Check for at least one process node
            process_nodes = [n for n in nodes if n.get("type") not in ("entryPoint", "end")]
            if not process_nodes:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Graph needs at least one Process or Decision node. The Entry Point must connect to something.",
                )

            # Check for edges
            if not edges:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Graph has no connections between nodes. Connect the Entry Point to your process nodes.",
                )

            # Deploy via agent_deployer for ReactFlow format
            result = await agent_deployer.deploy_agent(
                agent_id=agent_id,
                agent_name=agent_name,
                graph_data=graph_data,
                metadata={
                    "description": metadata.get("description", ""),
                    "tags": metadata.get("tags", []),
                    "organization_id": metadata.get("organization_id") or graph.get("organization_id"),
                    "domain_id": metadata.get("domain_id") or graph.get("domain_id"),
                },
            )

            if not result["success"]:
                error_msg = result.get("error", "Deployment failed")
                # Make error messages more user-friendly
                if "No entry point" in error_msg:
                    error_msg = "Graph validation failed: Missing entry point node"
                elif "validation" in error_msg.lower():
                    error_msg = f"Graph validation failed: {error_msg}"
                raise HTTPException(status_code=400, detail=error_msg)

            return {
                "status": "deployed",
                "message": f"Agent {agent_name} deployed successfully",
                "agent_id": agent_id,
                "files": result["files"],
                "deployed_at": result["deployed_at"],
            }

        elif is_workflow_format:
            # YAML/workflow format - agent is already deployed via YAML
            nodes = workflow_data.get("nodes", [])
            entry_point = workflow_data.get("entry_point")

            if not nodes:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Workflow has no nodes defined.",
                )

            if not entry_point:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deploy: Workflow is missing an entry_point.",
                )

            # Verify entry_point references a valid node
            node_ids = {n.get("id") for n in nodes}
            if entry_point not in node_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot deploy: entry_point '{entry_point}' does not match any node id.",
                )

            # Graph is valid in workflow format - already deployed via YAML
            logger.info(f"Graph {graph_id} validated in workflow format: {len(nodes)} nodes, entry_point={entry_point}")

            # For workflow format, the agent is already deployed via YAML file
            # Just trigger a hot-reload to ensure Marshal picks up any changes
            if marshal:
                try:
                    await marshal.registry.reload_agent(agent_id)
                    logger.info(f"Triggered hot-reload for {agent_id}")
                except Exception as e:
                    logger.warning(f"Hot-reload trigger failed (agent may already be loaded): {e}")

            return {
                "status": "deployed",
                "message": f"Agent {agent_name} is already deployed via YAML",
                "agent_id": agent_id,
                "files": {
                    "yaml": graph.get("yaml_path") or f"/app/agents/{agent_id}.agent.yaml",
                },
                "deployed_at": datetime.utcnow().isoformat(),
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot deploy: Graph has no valid structure. Expected either spec.graph (ReactFlow) or spec.workflow (YAML) format.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy graph {graph_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unable to deploy graph: {e!s}")


# =============================================================================
# AGENT VERSION API ENDPOINTS
# =============================================================================


@app.get("/api/graphs/{graph_id}/versions")
async def list_graph_versions(graph_id: str):
    """
    List all versions for a graph/agent.

    Returns versions ordered by version_number descending (newest first).
    """
    try:
        versions = db.get_agent_versions(graph_id)
        return {
            "graph_id": graph_id,
            "versions": versions,
            "count": len(versions),
        }
    except Exception as e:
        logger.error(f"Failed to list versions for {graph_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list versions: {e!s}")


@app.get("/api/graphs/{graph_id}/versions/{version_id}")
async def get_graph_version(graph_id: str, version_id: str):
    """
    Get a specific version of a graph/agent.
    """
    try:
        version = db.get_agent_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail=f"Version {version_id} not found")

        if version["agent_id"] != graph_id:
            raise HTTPException(status_code=404, detail=f"Version {version_id} does not belong to graph {graph_id}")

        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get version: {e!s}")


@app.post("/api/graphs/{graph_id}/rollback/{version_id}")
async def rollback_graph_version(graph_id: str, version_id: str):
    """
    Rollback a graph/agent to a specific version.

    Creates a new version with the content from the specified version.
    """
    try:
        # Verify graph exists
        graph = db.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail=f"Graph {graph_id} not found")

        # Perform rollback
        new_version = db.rollback_to_version(graph_id, version_id)

        return {
            "status": "success",
            "message": f"Rolled back to version {new_version.get('version_number') - 1}",
            "new_version": new_version,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rollback {graph_id} to version {version_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e!s}")


@app.post("/api/graphs/{graph_id}/versions/{version_id}/deploy")
async def deploy_graph_version(graph_id: str, version_id: str):
    """
    Deploy a specific version of a graph/agent.

    Sets this version as the active deployed version for the environment.
    Only deployed versions will show in the graphs list and chat dropdown.
    """
    try:
        # Verify graph exists
        graph = db.get_graph(graph_id)
        if not graph:
            raise HTTPException(status_code=404, detail=f"Graph {graph_id} not found")

        # Deploy the version
        updated_agent = db.deploy_agent_version(graph_id, version_id)

        # Get version details
        version = db.get_agent_version(version_id)

        return {
            "status": "deployed",
            "message": f"Version {version.get('version_label', version_id)} deployed successfully",
            "agent_id": graph_id,
            "version_id": version_id,
            "version_label": version.get("version_label"),
            "deployed_at": updated_agent.get("updated_at"),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy version {version_id} for {graph_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Deploy failed: {e!s}")


@app.get("/api/graphs/deployed")
async def list_deployed_graphs(
    organization_id: str | None = None,
    environment: str = "dev",
):
    """
    List all deployed graphs/agents.

    Returns only agents that have a deployed_version_id set.
    This is what should be shown in the graphs list and chat dropdown.
    """
    try:
        agents = db.get_deployed_agents(
            organization_id=organization_id,
            environment=environment,
        )
        return {
            "agents": agents,
            "count": len(agents),
        }
    except Exception as e:
        logger.error(f"Failed to list deployed agents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list deployed agents: {e!s}")


@app.post("/api/designer/generate-python")
async def generate_python_code(request: dict):
    """
    Generate Python LangGraph code from ReactFlow graph.

    Converts visual agent designer graph into executable Python code.
    """
    try:
        from backend.converters.react_flow_to_python import reactflow_to_python, validate_graph

        # Validate graph structure first
        validation = validate_graph(request.get("nodes", []), request.get("edges", []))

        # Generate Python code
        python_code = reactflow_to_python(request)

        return {
            "code": python_code,
            "validation": validation,
            "agent_name": request.get("agentName", "untitled_agent"),
            "node_count": len(request.get("nodes", [])),
            "edge_count": len(request.get("edges", [])),
        }

    except Exception as e:
        logger.error(f"Failed to generate Python code: {e}")
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e!s}")


@app.post("/api/designer/validate-graph")
async def validate_graph_structure(request: dict):
    """
    Validate graph structure before code generation.

    Checks for entry points, disconnected nodes, and invalid edges.
    """
    try:
        from backend.converters.react_flow_to_python import validate_graph

        result = validate_graph(request.get("nodes", []), request.get("edges", []))

        # Add warnings
        warnings = []
        nodes = request.get("nodes", [])

        # Check for end nodes
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if not end_nodes:
            warnings.append("No end node found - workflow may not terminate properly")

        return {"valid": result["valid"], "errors": result["errors"], "warnings": warnings}

    except Exception as e:
        logger.error(f"Failed to validate graph: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")


# ============================================================================
# ROOT / HEALTH ENDPOINTS
# ============================================================================


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "agent-foundry-backend",
        "status": "operational",
        "version": "0.8.1-dev",
        "livekit_url": os.getenv("LIVEKIT_URL", "ws://livekit:7880"),
    }


@app.get("/health")
async def health():
    """
    Comprehensive health check endpoint.
    Returns 200 if all critical services are healthy, 503 if any are unhealthy.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.8.1-dev",
        "services": {},
    }

    all_healthy = True

    # Check Marshal Agent
    try:
        if marshal is None:
            health_status["services"]["marshal"] = {"status": "unhealthy", "error": "Not initialized"}
            all_healthy = False
        else:
            agents = await marshal.registry.list_all()
            health_status["services"]["marshal"] = {
                "status": "healthy",
                "agents_loaded": len(agents),
                "file_watcher_active": marshal.file_watcher is not None,
                "health_monitor_active": marshal.health_monitor is not None,
            }
    except Exception as e:
        health_status["services"]["marshal"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check LiveKit
    try:
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_key = os.getenv("LIVEKIT_API_KEY")
        livekit_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([livekit_url, livekit_key, livekit_secret]):
            # In local/dev environments, LiveKit misconfiguration should not mark
            # the whole backend as unhealthy. We surface it as degraded status.
            health_status["services"]["livekit"] = {
                "status": "misconfigured",
                "error": "Missing required environment variables",
                "url": livekit_url,
            }
            # Only mark unhealthy in non-development environments
            if os.getenv("ENVIRONMENT", "development") not in ("development", "dev", "local"):
                all_healthy = False
        else:
            # Try to get LiveKit service
            livekit_svc = get_livekit_service()
            health_status["services"]["livekit"] = {"status": "healthy", "url": livekit_url, "configured": True}
    except Exception as e:
        health_status["services"]["livekit"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Redis (optional)
    try:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            # TODO: Add actual Redis ping check when Redis client is implemented
            health_status["services"]["redis"] = {
                "status": "configured",
                "url": redis_url,
                "note": "Health check not implemented yet",
            }
        else:
            health_status["services"]["redis"] = {"status": "not_configured", "note": "Redis is optional"}
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e),
            "note": "Redis is optional, failure doesn't affect system health",
        }
        # Redis failure doesn't mark system as unhealthy since it's optional

    # Set overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail=health_status)

    return health_status


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global marshal

    logger.info("🚀 Initializing Agent Foundry Backend...")

    # Initialize observability (OTEL + Prometheus metrics)
    try:
        from backend.observability import setup_observability

        setup_observability()
        logger.info("📊 Observability initialized (OTEL + Prometheus)")
    except Exception as e:
        logger.warning(f"⚠️  Observability initialization failed (non-fatal): {e}")

    # Start event bus
    await event_bus.start()

    # Initialize database schema and seed data
    logger.info("📊 Initializing control-plane database...")
    db.init_db()

    # Initialize OpenFGA client
    try:
        from backend.openfga_client import fga_client

        await fga_client.initialize()
        logger.info("🔐 OpenFGA client initialized")
    except Exception as e:
        logger.warning(f"⚠️  OpenFGA initialization failed (non-fatal): {e}")

    # Initialize Marshal Agent
    agents_dir = Path(__file__).parent.parent / "agents"

    marshal = MarshalAgent(
        agents_dir=agents_dir, enable_file_watcher=True, enable_health_monitor=True, health_check_interval=60
    )

    # Start Marshal in background
    await marshal.start()

    logger.info("✅ Agent Foundry Backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global marshal

    logger.info("🛑 Shutting down Agent Foundry Backend...")

    # Stop event bus
    await event_bus.stop()

    # Stop Marshal Agent
    if marshal:
        await marshal.stop()

    # Close LiveKit service (only if it was initialized)
    try:
        from backend.livekit_service import _livekit_service
        if _livekit_service is not None:
            await _livekit_service.close()
    except Exception as e:
        logger.warning(f"LiveKit shutdown skipped: {e}")

    # Shutdown observability
    try:
        from backend.observability import shutdown_telemetry

        shutdown_telemetry()
    except Exception as e:
        logger.warning(f"Observability shutdown error: {e}")

    logger.info("✅ Shutdown complete")


# ============================================================================
# PROMETHEUS METRICS ENDPOINT
# ============================================================================


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """
    Expose Prometheus metrics endpoint.
    This endpoint is scraped by Prometheus to collect metrics.
    """
    from fastapi.responses import Response

    try:
        from backend.observability import get_metrics_response

        content, content_type = get_metrics_response()
        return Response(content=content, media_type=content_type)
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(content=f"# Error generating metrics: {e}", media_type="text/plain")


# ============================================================================
# READINESS ENDPOINT
# ============================================================================


class ReadinessResponse(BaseModel):
    """Backend readiness status for UI gating"""

    ready: bool
    marshal_initialized: bool
    agents_loaded: int
    database_connected: bool
    message: str


@app.get("/api/system/ready", response_model=ReadinessResponse, tags=["system"])
async def check_readiness() -> ReadinessResponse:
    """
    Check if the backend is ready to handle chat/voice requests.

    The UI should poll this endpoint and block interactions until ready=True.
    Returns detailed status of each subsystem.
    """
    # Check marshal initialization
    marshal_ok = marshal is not None
    agents_count = 0

    if marshal_ok:
        try:
            agents = await marshal.registry.list_all()
            agents_count = len(agents)
        except Exception:
            pass

    # Check database connection
    db_ok = False
    try:
        # Simple query to verify DB is accessible
        db.list_graphs(environment="dev", domain_id="card-services")
        db_ok = True
    except Exception:
        pass

    # Determine overall readiness
    # Ready if: marshal is initialized AND has at least one agent OR DB has agents
    ready = marshal_ok and (agents_count > 0 or db_ok)

    if ready:
        message = f"Backend ready with {agents_count} agents loaded"
    elif not marshal_ok:
        message = "Marshal agent not initialized - server is starting up"
    elif agents_count == 0:
        message = "No agents loaded in registry yet"
    else:
        message = "Backend initializing..."

    return ReadinessResponse(
        ready=ready,
        marshal_initialized=marshal_ok,
        agents_loaded=agents_count,
        database_connected=db_ok,
        message=message,
    )


# ============================================================================
# AUTH CONFIG ENDPOINT (Service Registry Pattern)
# ============================================================================


class AuthConfigResponse(BaseModel):
    """Auth configuration for NextAuth (public, non-secret values only)"""

    provider: str
    configured: bool
    client_id: str | None
    issuer_url: str | None
    internal_issuer_url: str | None = None


# Cache for auth config from database
_auth_config_cache: dict | None = None


@app.get("/api/config/auth", response_model=AuthConfigResponse, tags=["config"])
async def get_auth_config() -> AuthConfigResponse:
    """
    Get auth configuration for the frontend.

    This endpoint serves as the service registry for auth config.
    Config is stored in the database settings table and can be updated
    via admin UI or API without redeploying.

    Returns only public values (client_id, issuer_url) - never secrets.
    """
    from psycopg2.extras import RealDictCursor

    from backend.db_postgres import get_connection_no_rls

    # Try to get from database first
    try:
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Check if settings table exists and has zitadel config
            cur.execute("""
                SELECT key, value FROM settings
                WHERE key IN ('zitadel_client_id', 'zitadel_issuer_url')
            """)
            rows = cur.fetchall()
            logger.info(f"Auth config from DB: {rows}")

            if rows:
                config = {row["key"]: row["value"] for row in rows}
                client_id = config.get("zitadel_client_id")
                issuer_url = config.get("zitadel_issuer_url", "http://localhost:8082")

                if client_id:
                    logger.info(f"Auth config found: client_id={client_id[:10]}...")
                    return AuthConfigResponse(
                        provider="zitadel",
                        configured=True,
                        client_id=client_id,
                        issuer_url=issuer_url,
                        internal_issuer_url="http://zitadel:8080",
                    )
    except Exception as e:
        logger.warning(f"Failed to get auth config from database: {e}")

    # Fallback to environment variables
    client_id = os.getenv("ZITADEL_CLIENT_ID")
    issuer_url = os.getenv("ZITADEL_URL", "http://localhost:8082")

    return AuthConfigResponse(
        provider="zitadel",
        configured=bool(client_id),
        client_id=client_id,
        issuer_url=issuer_url,
        internal_issuer_url="http://zitadel:8080",
    )


@app.post("/api/config/auth", tags=["config"])
async def set_auth_config(client_id: str, issuer_url: str = "http://localhost:8082") -> dict:
    """
    Store auth configuration in database.

    This allows updating auth config without redeploying.
    Only stores public values - secrets should be in env vars.
    """
    from backend.db_postgres import get_connection_no_rls

    try:
        with get_connection_no_rls() as conn:
            conn.autocommit = False
            cur = conn.cursor()

            # Ensure settings table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Upsert settings
            cur.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES ('zitadel_client_id', %s, NOW())
                ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
            """, (client_id,))

            cur.execute("""
                INSERT INTO settings (key, value, updated_at)
                VALUES ('zitadel_issuer_url', %s, NOW())
                ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value, updated_at = EXCLUDED.updated_at
            """, (issuer_url,))

            conn.commit()

        logger.info(f"Auth config updated: client_id={client_id[:20]}...")

        return {"status": "ok", "message": "Auth config saved"}
    except Exception as e:
        logger.error(f"Failed to save auth config: {e}")
        raise HTTPException(500, f"Failed to save auth config: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
