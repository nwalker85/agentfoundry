"""
OpenFGA Middleware for FastAPI
-------------------------------
Provides permission checking and authorization for FastAPI routes using OpenFGA.

This replaces the traditional RBAC middleware with relationship-based authorization.
Token validation is performed via Zitadel JWKS (RS256) for production auth,
with fallback to HS256 for legacy/internal tokens.

Usage:
    from backend.middleware.openfga_middleware import RequirePermission, get_current_user

    @app.get("/api/agents/{agent_id}")
    async def get_agent(
        agent_id: str,
        context: AuthContext = Depends(RequirePermission("agent", "can_read"))
    ):
        # Permission automatically checked by dependency
        ...
"""

import logging
import os

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.openfga_client import fga_client

logger = logging.getLogger(__name__)

# Security scheme for bearer tokens
security = HTTPBearer(auto_error=False)


# ============================================================================
# AUTHENTICATION CONTEXT
# ============================================================================


class AuthContext(BaseModel):
    """
    Authentication context containing user identity.

    Unlike traditional RBAC, this doesn't preload permissions.
    Permissions are checked on-demand via OpenFGA.
    """

    user_id: str
    organization_id: str
    email: str
    name: str
    is_service_account: bool = False
    ip_address: str | None = None

    def get_fga_user(self) -> str:
        """Get OpenFGA user identifier."""
        return f"user:{self.user_id}"

    async def can(self, relation: str, object: str) -> bool:
        """
        Check if this user has permission on object.

        Args:
            relation: Permission to check (e.g., "can_execute")
            object: Full object identifier (e.g., "agent:my-agent")

        Returns:
            True if allowed

        Example:
            >>> if await context.can("can_execute", "agent:my-agent"):
            ...     # Execute the agent
        """
        return await fga_client.check(user=self.get_fga_user(), relation=relation, object=object)

    async def list_accessible(self, resource_type: str, relation: str) -> list[str]:
        """
        List all resources of a type that this user can access.

        Args:
            resource_type: Type of resource (e.g., "agent", "secret")
            relation: Permission to check (e.g., "can_execute")

        Returns:
            List of resource IDs (without type prefix)

        Example:
            >>> agent_ids = await context.list_accessible("agent", "can_execute")
            ["my-agent", "shared-agent"]
        """
        objects = await fga_client.list_objects(user=self.get_fga_user(), relation=relation, type=resource_type)

        # Strip type prefix
        return [obj.split(":", 1)[1] for obj in objects if ":" in obj]


# ============================================================================
# AUTHENTICATION
# ============================================================================


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> AuthContext:
    """
    Extract and validate user from JWT token.

    This is a FastAPI dependency that extracts user identity.
    Permissions are NOT preloaded - they're checked via OpenFGA on demand.

    Token validation order:
    1. Try Zitadel JWKS (RS256) - production auth
    2. Fall back to HS256 with JWT_SECRET - legacy/internal auth
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = None

    # Try Zitadel RS256 validation first
    try:
        from backend.config.zitadel import zitadel_client

        if zitadel_client.is_available or await zitadel_client.initialize():
            payload = await zitadel_client.validate_token(token)
            if payload:
                logger.debug("Token validated via Zitadel JWKS")
    except Exception as e:
        logger.debug(f"Zitadel validation skipped: {e}")

    # Fall back to HS256 legacy validation
    if not payload:
        try:
            JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
            JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.debug("Token validated via HS256 fallback")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e!s}")

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed")

    # Extract user info from payload
    user_id = payload.get("sub")
    org_id = payload.get("org_id") or payload.get("urn:zitadel:iam:user:resourceowner:id")
    email = payload.get("email")
    name = payload.get("name", email)

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing subject")

    # For Zitadel tokens without org_id, default to user's org
    if not org_id:
        org_id = payload.get("urn:zitadel:iam:org:id", "default")

    # Get client IP
    ip_address = request.client.host if request.client else None

    context = AuthContext(
        user_id=user_id,
        organization_id=org_id,
        email=email or "",
        name=name or email or user_id,
        is_service_account=False,
        ip_address=ip_address,
    )

    # Attach to request state
    request.state.auth = context

    return context


async def get_optional_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> AuthContext | None:
    """
    Optional authentication - returns None if no valid credentials.
    """
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


# ============================================================================
# PERMISSION CHECKING DEPENDENCIES
# ============================================================================


class RequirePermission:
    """
    Dependency to require permission on a resource.

    Usage (static resource):
        @app.get("/api/secrets/org-settings")
        async def get_org_secrets(
            context: AuthContext = Depends(RequirePermission("organization", "can_manage_secrets"))
        ):
            # org_id from context
            ...

    Usage (dynamic resource from path):
        @app.get("/api/agents/{agent_id}")
        async def get_agent(
            agent_id: str,
            context: AuthContext = Depends(RequirePermission("agent", "can_read", resource_id_param="agent_id"))
        ):
            # Permission checked on specific agent
            ...

    Usage (check in handler):
        @app.post("/api/agents/{agent_id}/execute")
        async def execute_agent(
            agent_id: str,
            context: AuthContext = Depends(get_current_user)
        ):
            # Manual check
            if not await context.can("can_execute", f"agent:{agent_id}"):
                raise HTTPException(403, "Cannot execute this agent")
            ...
    """

    def __init__(
        self,
        resource_type: str,
        relation: str,
        resource_id_param: str | None = None,
        resource_id_from_context: bool = False,
    ):
        """
        Args:
            resource_type: Type of resource (e.g., "agent", "secret", "domain")
            relation: Permission to check (e.g., "can_read", "can_execute")
            resource_id_param: Name of path/query parameter containing resource ID
            resource_id_from_context: If True, use organization_id from context
        """
        self.resource_type = resource_type
        self.relation = relation
        self.resource_id_param = resource_id_param
        self.resource_id_from_context = resource_id_from_context

    async def __call__(self, request: Request, context: AuthContext = Depends(get_current_user)) -> AuthContext:
        """Check if user has required permission."""

        # Determine resource ID
        if self.resource_id_from_context:
            # Use organization from context
            resource_id = context.organization_id
        elif self.resource_id_param:
            # Extract from path/query parameters
            resource_id = request.path_params.get(self.resource_id_param)
            if not resource_id:
                # Try query params
                resource_id = request.query_params.get(self.resource_id_param)

            if not resource_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required parameter: {self.resource_id_param}",
                )
        else:
            raise ValueError("Either resource_id_param or resource_id_from_context must be set")

        # Build object identifier
        object_id = f"{self.resource_type}:{resource_id}"

        # Check permission via OpenFGA
        allowed = await fga_client.check(user=context.get_fga_user(), relation=self.relation, object=object_id)

        if not allowed:
            logger.warning(f"Permission denied: {context.user_id} cannot {self.relation} {object_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to {self.relation} {self.resource_type}",
            )

        return context


# ============================================================================
# AUDIT LOGGING
# ============================================================================


async def log_auth_event(
    request: Request,
    action: str,
    resource_type: str,
    resource_id: str,
    result: str = "success",
    metadata: dict | None = None,
):
    """
    Log an authorization event for audit trail.

    Args:
        request: FastAPI request
        action: Action performed (e.g., "agent.execute", "secret.update")
        resource_type: Type of resource
        resource_id: Resource ID
        result: "success" or "failure"
        metadata: Additional data
    """
    context: AuthContext | None = getattr(request.state, "auth", None)

    if not context:
        return

    from backend.audit_service import AuditLogCreate, audit_service

    audit_log = AuditLogCreate(
        organization_id=context.organization_id,
        user_id=context.user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        ip_address=context.ip_address,
        user_agent=request.headers.get("user-agent"),
        metadata=metadata,
    )

    audit_service.log_safe(audit_log)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_auth_context(request: Request) -> AuthContext | None:
    """Get the authentication context from FastAPI request state."""
    return getattr(request.state, "auth", None)


async def require_org_admin(
    request: Request, org_id: str, context: AuthContext = Depends(get_current_user)
) -> AuthContext:
    """
    Helper dependency to require org admin permission.

    Usage:
        @app.post("/api/orgs/{org_id}/settings")
        async def update_settings(
            org_id: str,
            context: AuthContext = Depends(require_org_admin)
        ):
            ...
    """
    allowed = await fga_client.check(user=context.get_fga_user(), relation="admin", object=f"organization:{org_id}")

    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization admin access required")

    return context


# Note: os is imported at module top
