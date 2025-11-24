"""
RBAC Models for Agent Foundry
Pydantic models for Role-Based Access Control entities.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# ============================================================================
# PERMISSION MODELS
# ============================================================================


class Permission(BaseModel):
    """Atomic permission/authority."""

    id: UUID
    code: str
    resource_type: str
    action: str
    scope: str | None = None
    description: str | None = None
    created_at: datetime


class PermissionCreate(BaseModel):
    """Create a new permission."""

    code: str
    resource_type: str
    action: str
    scope: str | None = None
    description: str | None = None


# ============================================================================
# ROLE MODELS
# ============================================================================


class Role(BaseModel):
    """Role definition with associated permissions."""

    id: UUID
    name: str
    description: str | None = None
    is_system: bool = False
    permissions: list[Permission] = []
    created_at: datetime
    updated_at: datetime


class RoleCreate(BaseModel):
    """Create a new role."""

    name: str
    description: str | None = None
    is_system: bool = False
    permission_codes: list[str] = []


class RoleSummary(BaseModel):
    """Lightweight role summary without permissions."""

    id: UUID
    name: str
    description: str | None = None
    is_system: bool


# ============================================================================
# USER ROLE ASSIGNMENT MODELS
# ============================================================================


class UserRoleAssignment(BaseModel):
    """User to role assignment in an organization."""

    id: UUID
    user_id: str
    role_id: UUID
    organization_id: str
    granted_by: str | None = None
    granted_at: datetime
    expires_at: datetime | None = None


class UserRoleAssignmentCreate(BaseModel):
    """Create a user role assignment."""

    user_id: str
    role_name: str  # Will be looked up to get role_id
    organization_id: str
    granted_by: str | None = None
    expires_at: datetime | None = None


class UserRoleAssignmentDelete(BaseModel):
    """Remove a user role assignment."""

    user_id: str
    role_name: str
    organization_id: str


# ============================================================================
# USER WITH PERMISSIONS
# ============================================================================


class UserPermissions(BaseModel):
    """User identity with their computed permissions."""

    user_id: str
    organization_id: str
    email: str
    name: str
    roles: list[RoleSummary] = []
    permissions: list[str] = []  # List of permission codes


# ============================================================================
# API KEY MODELS
# ============================================================================


class APIKey(BaseModel):
    """API key for programmatic access."""

    id: UUID
    key_prefix: str  # Only show prefix, never the full key
    name: str
    user_id: str
    organization_id: str
    role_id: UUID | None = None
    scopes: list[str] = []
    last_used_at: datetime | None = None
    last_used_ip: str | None = None
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool


class APIKeyCreate(BaseModel):
    """Create a new API key."""

    name: str
    user_id: str
    organization_id: str
    role_name: str = "api_client"
    scopes: list[str] = []
    expires_at: datetime | None = None


class APIKeyResponse(BaseModel):
    """Response when creating an API key (includes full key once)."""

    id: UUID
    key: str  # Full key, only shown once
    key_prefix: str
    name: str
    created_at: datetime
    expires_at: datetime | None = None


# ============================================================================
# SERVICE ACCOUNT MODELS
# ============================================================================


class ServiceAccount(BaseModel):
    """Service account (non-human identity)."""

    id: UUID
    name: str
    service_type: str
    organization_id: str | None = None
    role_id: UUID | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ServiceAccountCreate(BaseModel):
    """Create a new service account."""

    name: str
    service_type: str
    organization_id: str | None = None
    role_name: str
    credentials: str  # Will be hashed


# ============================================================================
# AUDIT LOG MODELS
# ============================================================================


class AuditLog(BaseModel):
    """Audit log entry."""

    id: int
    organization_id: str | None = None
    user_id: str | None = None
    service_account_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    result: str
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict | None = None
    created_at: datetime


class AuditLogCreate(BaseModel):
    """Create an audit log entry."""

    organization_id: str | None = None
    user_id: str | None = None
    service_account_id: UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    result: str = "success"
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict | None = None


# ============================================================================
# LLM USAGE & QUOTA MODELS
# ============================================================================


class LLMUsage(BaseModel):
    """LLM usage record."""

    id: int
    organization_id: str
    user_id: str | None = None
    session_id: UUID | None = None
    agent_id: str | None = None
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None = None
    created_at: datetime


class LLMUsageCreate(BaseModel):
    """Create an LLM usage record."""

    organization_id: str
    user_id: str | None = None
    session_id: UUID | None = None
    agent_id: str | None = None
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None = None


class LLMQuota(BaseModel):
    """LLM quota definition."""

    id: UUID
    organization_id: str
    quota_type: str
    limit_value: int
    current_usage: int
    period_start: datetime
    period_end: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LLMQuotaCreate(BaseModel):
    """Create an LLM quota."""

    organization_id: str
    quota_type: str
    limit_value: int
    period_start: datetime
    period_end: datetime


class LLMQuotaUpdate(BaseModel):
    """Update an LLM quota."""

    limit_value: int | None = None
    current_usage: int | None = None
    is_active: bool | None = None


# ============================================================================
# SESSION MODELS (for RBAC tracking)
# ============================================================================


class Session(BaseModel):
    """Agent execution session."""

    id: UUID
    organization_id: str
    user_id: str | None = None
    agent_id: str | None = None
    session_type: str
    livekit_room: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "active"
    metadata: dict | None = None
    created_at: datetime
    updated_at: datetime


class SessionCreate(BaseModel):
    """Create a new session."""

    organization_id: str
    user_id: str | None = None
    agent_id: str | None = None
    session_type: str
    livekit_room: str | None = None
    metadata: dict | None = None


class SessionUpdate(BaseModel):
    """Update a session."""

    ended_at: datetime | None = None
    status: str | None = None
    metadata: dict | None = None
