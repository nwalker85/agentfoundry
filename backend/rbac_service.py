"""
RBAC Service for Agent Foundry (PostgreSQL Version)
Provides permission checking, role management, and audit logging.
"""

import json
import logging
import secrets
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import bcrypt

from backend.db_postgres import DictCursor, get_connection_no_rls
from backend.rbac_models import (
    APIKeyCreate,
    APIKeyResponse,
    AuditLogCreate,
    LLMUsageCreate,
    Permission,
    Role,
    RoleSummary,
    Session,
    SessionCreate,
    SessionUpdate,
    UserPermissions,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
)

logger = logging.getLogger(__name__)


class RBACService:
    """
    Core RBAC service for permission checking and role management.
    Uses PostgreSQL via db_postgres connection pool.
    """

    def __init__(self):
        self._permission_cache: dict[str, set[str]] = {}  # user_org_key -> set of permissions
        self._cache_ttl = timedelta(minutes=5)
        self._cache_timestamps: dict[str, datetime] = {}

    # ========================================================================
    # PERMISSION CHECKING
    # ========================================================================

    def get_user_permissions(self, user_id: str, org_id: str, use_cache: bool = True) -> set[str]:
        """
        Get all permission codes for a user in an organization.
        Returns a set of permission codes (e.g., {'agent:create', 'agent:read:org'}).
        """
        cache_key = f"{user_id}:{org_id}"

        # Check cache
        if use_cache and cache_key in self._permission_cache:
            if datetime.now() - self._cache_timestamps.get(cache_key, datetime.min) < self._cache_ttl:
                return self._permission_cache[cache_key]

        # Query from database
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(
                """
                SELECT DISTINCT p.code
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = %s
                  AND ur.organization_id = %s
                  AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
                """,
                (user_id, org_id),
            )
            permissions = {row["code"] for row in cur.fetchall()}

        # Update cache
        self._permission_cache[cache_key] = permissions
        self._cache_timestamps[cache_key] = datetime.now()

        return permissions

    def has_permission(self, user_id: str, org_id: str, permission_code: str) -> bool:
        """
        Check if a user has a specific permission in an organization.
        """
        permissions = self.get_user_permissions(user_id, org_id)
        return permission_code in permissions

    def has_any_permission(self, user_id: str, org_id: str, permission_codes: list[str]) -> bool:
        """
        Check if a user has ANY of the specified permissions.
        """
        permissions = self.get_user_permissions(user_id, org_id)
        return any(code in permissions for code in permission_codes)

    def has_all_permissions(self, user_id: str, org_id: str, permission_codes: list[str]) -> bool:
        """
        Check if a user has ALL of the specified permissions.
        """
        permissions = self.get_user_permissions(user_id, org_id)
        return all(code in permissions for code in permission_codes)

    def invalidate_cache(self, user_id: str, org_id: str):
        """Invalidate permission cache for a user."""
        cache_key = f"{user_id}:{org_id}"
        self._permission_cache.pop(cache_key, None)
        self._cache_timestamps.pop(cache_key, None)

    def get_user_with_permissions(self, user_id: str, org_id: str) -> UserPermissions | None:
        """
        Get user info with their roles and permissions.
        """
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            # Get user info
            cur.execute(
                """
                SELECT id, email, name, organization_id
                FROM users
                WHERE id = %s AND organization_id = %s
                """,
                (user_id, org_id),
            )
            user_row = cur.fetchone()
            if not user_row:
                return None

            # Get user's roles
            cur.execute(
                """
                SELECT DISTINCT r.id, r.name, r.description, r.is_system
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                WHERE ur.user_id = %s
                  AND ur.organization_id = %s
                  AND (ur.expires_at IS NULL OR ur.expires_at > NOW())
                """,
                (user_id, org_id),
            )
            roles = [RoleSummary(**row) for row in cur.fetchall()]

        permissions = list(self.get_user_permissions(user_id, org_id))

        return UserPermissions(
            user_id=user_row["id"],
            organization_id=user_row["organization_id"],
            email=user_row["email"],
            name=user_row["name"],
            roles=roles,
            permissions=permissions,
        )

    def get_user_by_id(self, user_id: str) -> dict | None:
        """
        Get user by ID.
        Used by rbac_middleware for authentication resolution.
        """
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(
                "SELECT id, email, name, organization_id, role FROM users WHERE id = %s",
                (user_id,),
            )
            return cur.fetchone()

    def get_user_by_email(self, email: str) -> dict | None:
        """
        Get user by email.
        Used by rbac_middleware for authentication resolution.
        """
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute(
                "SELECT id, email, name, organization_id, role FROM users WHERE email = %s",
                (email,),
            )
            return cur.fetchone()

    # ========================================================================
    # ROLE MANAGEMENT
    # ========================================================================

    def get_role_by_name(self, role_name: str) -> Role | None:
        """Get a role by name with its permissions."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            cur.execute(
                """
                SELECT id, name, description, is_system, created_at, updated_at
                FROM roles
                WHERE name = %s
                """,
                (role_name,),
            )
            role_row = cur.fetchone()
            if not role_row:
                return None

            # Get role permissions
            cur.execute(
                """
                SELECT p.id, p.code, p.resource_type, p.action, p.scope, p.description, p.created_at
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = %s
                """,
                (role_row["id"],),
            )
            permissions = [Permission(**row) for row in cur.fetchall()]

        return Role(**role_row, permissions=permissions)

    def list_roles(self, include_system: bool = True) -> list[RoleSummary]:
        """List all available roles."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            if include_system:
                cur.execute("SELECT id, name, description, is_system FROM roles ORDER BY name")
            else:
                cur.execute(
                    "SELECT id, name, description, is_system FROM roles WHERE is_system = FALSE ORDER BY name"
                )
            return [RoleSummary(**row) for row in cur.fetchall()]

    def assign_role(self, assignment: UserRoleAssignmentCreate) -> UserRoleAssignment:
        """
        Assign a role to a user in an organization.
        """
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            # Get role ID
            cur.execute("SELECT id FROM roles WHERE name = %s", (assignment.role_name,))
            role_row = cur.fetchone()
            if not role_row:
                raise ValueError(f"Role '{assignment.role_name}' not found")

            role_id = role_row["id"]
            assignment_id = str(uuid4())

            # Check if assignment already exists
            cur.execute(
                """
                SELECT id FROM user_roles
                WHERE user_id = %s AND role_id = %s AND organization_id = %s
                """,
                (assignment.user_id, role_id, assignment.organization_id),
            )
            existing = cur.fetchone()

            if existing:
                # Update existing assignment
                cur.execute(
                    """
                    UPDATE user_roles
                    SET granted_at = NOW(), granted_by = %s, expires_at = %s
                    WHERE id = %s
                    """,
                    (assignment.granted_by, assignment.expires_at, existing["id"]),
                )
                assignment_id = existing["id"]
            else:
                # Insert new assignment
                cur.execute(
                    """
                    INSERT INTO user_roles (id, user_id, role_id, organization_id, granted_by, expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        assignment_id,
                        assignment.user_id,
                        role_id,
                        assignment.organization_id,
                        assignment.granted_by,
                        assignment.expires_at,
                    ),
                )

            # Fetch the result
            cur.execute(
                "SELECT id, user_id, role_id, organization_id, granted_by, granted_at, expires_at FROM user_roles WHERE id = %s",
                (assignment_id,),
            )
            result = cur.fetchone()
            conn.commit()

        # Invalidate cache
        self.invalidate_cache(assignment.user_id, assignment.organization_id)

        return UserRoleAssignment(**result)

    def revoke_role(self, user_id: str, role_name: str, org_id: str):
        """Remove a role from a user."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            cur.execute(
                """
                DELETE FROM user_roles
                WHERE user_id = %s
                  AND organization_id = %s
                  AND role_id = (SELECT id FROM roles WHERE name = %s)
                """,
                (user_id, org_id, role_name),
            )
            conn.commit()

        # Invalidate cache
        self.invalidate_cache(user_id, org_id)

    # ========================================================================
    # API KEY MANAGEMENT
    # ========================================================================

    def create_api_key(self, api_key_create: APIKeyCreate) -> APIKeyResponse:
        """
        Create a new API key for a user.
        Returns the full key ONCE - it won't be retrievable again.
        """
        # Generate key: ak_live_<random_32_chars>
        random_part = secrets.token_urlsafe(24)
        full_key = f"ak_live_{random_part}"
        key_prefix = full_key[:12] + "..."

        # Hash the key
        key_hash = bcrypt.hashpw(full_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            # Get role ID
            cur.execute("SELECT id FROM roles WHERE name = %s", (api_key_create.role_name,))
            role_row = cur.fetchone()
            if not role_row:
                raise ValueError(f"Role '{api_key_create.role_name}' not found")

            role_id = role_row["id"]
            key_id = str(uuid4())
            now = datetime.utcnow()
            scopes_json = json.dumps(api_key_create.scopes) if api_key_create.scopes else "[]"

            # Insert API key
            cur.execute(
                """
                INSERT INTO api_keys (
                    id, key_hash, key_prefix, name, user_id, organization_id,
                    role_id, scopes, expires_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    key_id,
                    key_hash,
                    key_prefix,
                    api_key_create.name,
                    api_key_create.user_id,
                    api_key_create.organization_id,
                    role_id,
                    scopes_json,
                    api_key_create.expires_at,
                ),
            )
            conn.commit()

        return APIKeyResponse(
            id=key_id,
            key=full_key,
            key_prefix=key_prefix,
            name=api_key_create.name,
            created_at=now,
            expires_at=api_key_create.expires_at,
        )

    def verify_api_key(self, key: str) -> dict | None:
        """
        Verify an API key and return user/org info if valid.
        """
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            # Get all active keys (we need to check hash for each)
            cur.execute(
                """
                SELECT id, key_hash, user_id, organization_id, role_id, scopes
                FROM api_keys
                WHERE is_active = TRUE
                  AND (expires_at IS NULL OR expires_at > NOW())
                  AND revoked_at IS NULL
                """
            )

            for row in cur.fetchall():
                if bcrypt.checkpw(key.encode("utf-8"), row["key_hash"].encode("utf-8")):
                    # Update last used
                    cur.execute(
                        """
                        UPDATE api_keys
                        SET last_used_at = NOW()
                        WHERE id = %s
                        """,
                        (row["id"],),
                    )
                    conn.commit()

                    # Parse scopes JSON
                    scopes = json.loads(row["scopes"]) if row["scopes"] else []

                    return {
                        "user_id": row["user_id"],
                        "organization_id": row["organization_id"],
                        "role_id": row["role_id"],
                        "scopes": scopes,
                    }

        return None

    def revoke_api_key(self, key_id: UUID):
        """Revoke an API key."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            cur.execute(
                """
                UPDATE api_keys
                SET revoked_at = NOW(), is_active = FALSE
                WHERE id = %s
                """,
                (str(key_id),),
            )
            conn.commit()

    # ========================================================================
    # AUDIT LOGGING
    # ========================================================================

    def log_audit(self, audit_log: AuditLogCreate):
        """Create an audit log entry."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            metadata_json = json.dumps(audit_log.metadata) if audit_log.metadata else None

            cur.execute(
                """
                INSERT INTO audit_logs (
                    organization_id, user_id, service_account_id, action,
                    resource_type, resource_id, result, ip_address, user_agent, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    audit_log.organization_id,
                    audit_log.user_id,
                    str(audit_log.service_account_id) if audit_log.service_account_id else None,
                    audit_log.action,
                    audit_log.resource_type,
                    audit_log.resource_id,
                    audit_log.result,
                    audit_log.ip_address,
                    audit_log.user_agent,
                    metadata_json,
                ),
            )
            conn.commit()

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def create_session(self, session_create: SessionCreate) -> Session:
        """Create a new agent session."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            session_id = str(uuid4())
            metadata_json = json.dumps(session_create.metadata) if session_create.metadata else None

            cur.execute(
                """
                INSERT INTO sessions (
                    id, organization_id, user_id, agent_id, session_type,
                    livekit_room, metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    session_id,
                    session_create.organization_id,
                    session_create.user_id,
                    session_create.agent_id,
                    session_create.session_type,
                    session_create.livekit_room,
                    metadata_json,
                ),
            )
            result = cur.fetchone()
            conn.commit()

            # Parse metadata back to dict
            if result.get("metadata") and isinstance(result["metadata"], str):
                result["metadata"] = json.loads(result["metadata"])

        return Session(**result)

    def update_session(self, session_id: UUID, session_update: SessionUpdate):
        """Update a session."""
        updates = []
        params = []

        if session_update.ended_at is not None:
            updates.append("ended_at = %s")
            params.append(session_update.ended_at)

        if session_update.status is not None:
            updates.append("status = %s")
            params.append(session_update.status)

        if session_update.metadata is not None:
            updates.append("metadata = %s")
            params.append(json.dumps(session_update.metadata))

        if not updates:
            return

        updates.append("updated_at = NOW()")
        params.append(str(session_id))

        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            cur.execute(
                f"""
                UPDATE sessions
                SET {", ".join(updates)}
                WHERE id = %s
                """,
                params,
            )
            conn.commit()

    # ========================================================================
    # LLM USAGE TRACKING
    # ========================================================================

    def log_llm_usage(self, usage: LLMUsageCreate):
        """Log LLM usage for billing and quota tracking."""
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            cur.execute(
                """
                INSERT INTO llm_usage (
                    organization_id, user_id, session_id, agent_id,
                    model, provider, prompt_tokens, completion_tokens,
                    total_tokens, cost_usd
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    usage.organization_id,
                    usage.user_id,
                    str(usage.session_id) if usage.session_id else None,
                    usage.agent_id,
                    usage.model,
                    usage.provider,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    usage.cost_usd,
                ),
            )
            conn.commit()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

rbac_service = RBACService()
