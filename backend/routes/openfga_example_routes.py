"""
OpenFGA Example Routes
----------------------
Demonstrates how to use OpenFGA authorization in FastAPI routes.

This shows the new pattern replacing traditional RBAC.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from backend.middleware.openfga_middleware import AuthContext, get_current_user, log_auth_event
from backend.openfga_client import fga_client

router = APIRouter(prefix="/api/openfga-examples", tags=["openfga-examples"])


# ============================================================================
# EXAMPLE MODELS
# ============================================================================


class AgentCreate(BaseModel):
    name: str
    description: str
    domain_id: str


class ShareRequest(BaseModel):
    user_id: str
    relation: str  # "viewer", "executor", "editor"


# ============================================================================
# EXAMPLE 1: List Resources User Can Access
# ============================================================================


@router.get("/agents")
async def list_accessible_agents(context: AuthContext = Depends(get_current_user)):
    """
    List all agents the current user can execute.

    OpenFGA automatically filters based on relationships:
    - Direct ownership
    - Team membership
    - Domain/org inheritance
    """
    # OpenFGA returns filtered list
    agent_ids = await context.list_accessible("agent", "can_execute")

    # Fetch agent details from database
    # (In production, would join with agents table)
    agents = [{"id": agent_id, "name": f"Agent {agent_id}"} for agent_id in agent_ids]

    return {"agents": agents, "count": len(agents), "user_id": context.user_id}


# ============================================================================
# EXAMPLE 2: Check Permission Before Action
# ============================================================================


@router.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, request: Request, context: AuthContext = Depends(get_current_user)):
    """
    Execute an agent.

    Manual permission check in handler.
    """
    # Check permission
    if not await context.can("can_execute", f"agent:{agent_id}"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot execute agent '{agent_id}'")

    # Execute agent logic...
    result = {"status": "executed", "agent_id": agent_id}

    # Log audit event
    await log_auth_event(
        request=request, action="agent.execute", resource_type="agent", resource_id=agent_id, result="success"
    )

    return result


# ============================================================================
# EXAMPLE 3: Resource Creation (Sets Owner Relationship)
# ============================================================================


@router.post("/agents", status_code=status.HTTP_201_CREATED)
async def create_agent(request: Request, agent_data: AgentCreate, context: AuthContext = Depends(get_current_user)):
    """
    Create a new agent.

    Checks: can_create_agent on domain
    Sets: owner relationship on new agent
    """
    # Check if user can create agents in this domain
    if not await context.can("can_create_agent", f"domain:{agent_data.domain_id}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot create agents in domain '{agent_data.domain_id}'"
        )

    # Create agent (simplified)
    agent_id = f"agent_{agent_data.name.lower().replace(' ', '-')}"

    # Set up relationships in OpenFGA
    success = await fga_client.write(
        [
            # Link to domain (inheritance)
            {"user": f"domain:{agent_data.domain_id}", "relation": "parent_domain", "object": f"agent:{agent_id}"},
            # Set creator as owner
            {"user": context.get_fga_user(), "relation": "owner", "object": f"agent:{agent_id}"},
        ]
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set up agent permissions"
        )

    # Log audit
    await log_auth_event(
        request=request,
        action="agent.create",
        resource_type="agent",
        resource_id=agent_id,
        result="success",
        metadata={"name": agent_data.name, "domain_id": agent_data.domain_id},
    )

    return {"id": agent_id, "name": agent_data.name, "owner_id": context.user_id, "domain_id": agent_data.domain_id}


# ============================================================================
# EXAMPLE 4: Delegate Access (Share Resource)
# ============================================================================


@router.post("/agents/{agent_id}/share")
async def share_agent(
    agent_id: str, request: Request, share_request: ShareRequest, context: AuthContext = Depends(get_current_user)
):
    """
    Share an agent with another user.

    Requires: can_share permission on agent
    Grants: specified relation (viewer/executor/editor) to target user
    """
    # Check if current user can share this agent
    if not await context.can("can_share", f"agent:{agent_id}"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot share agent '{agent_id}'")

    # Validate relation
    valid_relations = ["viewer", "executor", "editor"]
    if share_request.relation not in valid_relations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid relation. Must be one of: {valid_relations}"
        )

    # Grant access
    success = await fga_client.write(
        [{"user": f"user:{share_request.user_id}", "relation": share_request.relation, "object": f"agent:{agent_id}"}]
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to share agent")

    # Log audit
    await log_auth_event(
        request=request,
        action="agent.share",
        resource_type="agent",
        resource_id=agent_id,
        result="success",
        metadata={"target_user": share_request.user_id, "relation": share_request.relation},
    )

    return {
        "status": "shared",
        "agent_id": agent_id,
        "shared_with": share_request.user_id,
        "relation": share_request.relation,
    }


# ============================================================================
# EXAMPLE 5: Revoke Access
# ============================================================================


@router.delete("/agents/{agent_id}/share/{user_id}")
async def revoke_agent_access(
    agent_id: str, user_id: str, relation: str, request: Request, context: AuthContext = Depends(get_current_user)
):
    """
    Revoke a user's access to an agent.

    Requires: can_share permission (owner or domain admin)
    """
    # Check permission
    if not await context.can("can_share", f"agent:{agent_id}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot manage access for agent '{agent_id}'"
        )

    # Revoke access
    success = await fga_client.write(
        writes=[], deletes=[{"user": f"user:{user_id}", "relation": relation, "object": f"agent:{agent_id}"}]
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke access")

    # Log audit
    await log_auth_event(
        request=request,
        action="agent.unshare",
        resource_type="agent",
        resource_id=agent_id,
        result="success",
        metadata={"target_user": user_id, "relation": relation},
    )

    return {"status": "revoked", "agent_id": agent_id, "user_id": user_id}


# ============================================================================
# EXAMPLE 6: List Users with Access to Resource
# ============================================================================


@router.get("/agents/{agent_id}/access")
async def list_agent_access(agent_id: str, context: AuthContext = Depends(get_current_user)):
    """
    List all users who have access to an agent.

    Requires: can_read permission on agent
    """
    # Check permission
    if not await context.can("can_read", f"agent:{agent_id}"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"Cannot view access list for agent '{agent_id}'"
        )

    # Read all relationships for this agent
    tuples = await fga_client.read(object=f"agent:{agent_id}")

    # Group by relation
    access_list = {}
    for tuple in tuples:
        relation = tuple.get("relation")
        user = tuple.get("user", "")

        if user.startswith("user:"):
            user_id = user.replace("user:", "")
            if relation not in access_list:
                access_list[relation] = []
            access_list[relation].append(user_id)

    return {
        "agent_id": agent_id,
        "access": access_list,
        "total_users": sum(len(users) for users in access_list.values()),
    }


# ============================================================================
# EXAMPLE 7: Hierarchical Permission Check
# ============================================================================


@router.get("/domains/{domain_id}/can-create-agents")
async def check_can_create_agents(domain_id: str, context: AuthContext = Depends(get_current_user)):
    """
    Check if user can create agents in a domain.

    This demonstrates hierarchical permission checking:
    - Domain editor: YES
    - Domain owner: YES
    - Org admin: YES (via parent_org relationship)
    - Org member: NO
    """
    allowed = await context.can("can_create_agent", f"domain:{domain_id}")

    return {"domain_id": domain_id, "user_id": context.user_id, "can_create_agent": allowed}


# ============================================================================
# HOW TO USE THESE PATTERNS
# ============================================================================
"""
In your main FastAPI app (backend/main.py), include this router:

from backend.routes.openfga_example_routes import router as openfga_example_router

app = FastAPI()
app.include_router(openfga_example_router)

Then test with JWT token:

# List agents you can execute
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/openfga-examples/agents

# Share an agent
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "bob", "relation": "executor"}' \
  http://localhost:8000/api/openfga-examples/agents/my-agent/share

# Check hierarchical permission
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/openfga-examples/domains/my-domain/can-create-agents
"""
