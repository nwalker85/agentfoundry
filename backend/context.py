"""
Tenant Context Management for Agent Foundry

This module provides thread-safe and async-safe context propagation
for tenant isolation using Python's contextvars.

Usage:
    from backend.context import tenant_context, set_context, get_tenant_id

    # In middleware (after auth):
    set_context(tenant_id="cibc", user_id="user-123")

    # In any function:
    current_tenant = get_tenant_id()  # Returns "cibc"

The context is automatically propagated through async calls and thread pools.
"""

import logging
from contextvars import ContextVar

logger = logging.getLogger(__name__)

# =============================================================================
# CONTEXT VARIABLES
# =============================================================================

# Tenant ID (organization_id) - used for RLS filtering
tenant_id: ContextVar[str | None] = ContextVar("tenant_id", default=None)

# User ID - used for audit logging and ownership checks
user_id: ContextVar[str | None] = ContextVar("user_id", default=None)

# Session ID - used for request tracing
session_id: ContextVar[str | None] = ContextVar("session_id", default=None)


# =============================================================================
# CONTEXT SETTERS
# =============================================================================


def set_context(*, tenant: str | None = None, user: str | None = None, session: str | None = None) -> None:
    """
    Set the current request context.

    This should be called in middleware after authentication.
    All values are optional - only provided values will be set.

    Args:
        tenant: Organization ID for tenant isolation
        user: User ID for audit/ownership
        session: Session ID for request tracing
    """
    if tenant is not None:
        tenant_id.set(tenant)
        logger.debug(f"Context: tenant_id set to {tenant}")

    if user is not None:
        user_id.set(user)
        logger.debug(f"Context: user_id set to {user}")

    if session is not None:
        session_id.set(session)


def clear_context() -> None:
    """
    Clear all context variables.

    This should be called at the end of request handling or in error cleanup.
    """
    tenant_id.set(None)
    user_id.set(None)
    session_id.set(None)


# =============================================================================
# CONTEXT GETTERS
# =============================================================================


def get_tenant_id() -> str | None:
    """Get the current tenant (organization) ID."""
    return tenant_id.get()


def get_user_id() -> str | None:
    """Get the current user ID."""
    return user_id.get()


def get_session_id() -> str | None:
    """Get the current session ID."""
    return session_id.get()


def require_tenant_id() -> str:
    """
    Get the current tenant ID or raise an error.

    Use this when tenant context is required for the operation.

    Returns:
        The tenant ID

    Raises:
        ValueError: If no tenant context is set
    """
    tid = tenant_id.get()
    if tid is None:
        raise ValueError("No tenant context set - authentication required")
    return tid


def require_user_id() -> str:
    """
    Get the current user ID or raise an error.

    Use this when user context is required for the operation.

    Returns:
        The user ID

    Raises:
        ValueError: If no user context is set
    """
    uid = user_id.get()
    if uid is None:
        raise ValueError("No user context set - authentication required")
    return uid


# =============================================================================
# CONTEXT MANAGER FOR TEMPORARY OVERRIDES
# =============================================================================


class TenantContextOverride:
    """
    Context manager for temporarily overriding tenant context.

    Useful for admin operations or cross-tenant queries.

    Usage:
        with TenantContextOverride(tenant="admin-tenant"):
            # Operations run with admin-tenant context
            pass
        # Original context restored
    """

    def __init__(self, *, tenant: str | None = None, user: str | None = None, session: str | None = None):
        self.new_tenant = tenant
        self.new_user = user
        self.new_session = session
        self.old_tenant: str | None = None
        self.old_user: str | None = None
        self.old_session: str | None = None

    def __enter__(self):
        # Save current values
        self.old_tenant = tenant_id.get()
        self.old_user = user_id.get()
        self.old_session = session_id.get()

        # Set new values
        if self.new_tenant is not None:
            tenant_id.set(self.new_tenant)
        if self.new_user is not None:
            user_id.set(self.new_user)
        if self.new_session is not None:
            session_id.set(self.new_session)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old values
        tenant_id.set(self.old_tenant)
        user_id.set(self.old_user)
        session_id.set(self.old_session)
        return False  # Don't suppress exceptions


# =============================================================================
# ASYNC CONTEXT MANAGER
# =============================================================================


class AsyncTenantContextOverride:
    """
    Async context manager for temporarily overriding tenant context.

    Usage:
        async with AsyncTenantContextOverride(tenant="admin-tenant"):
            await some_async_operation()
    """

    def __init__(self, *, tenant: str | None = None, user: str | None = None, session: str | None = None):
        self.new_tenant = tenant
        self.new_user = user
        self.new_session = session
        self.old_tenant: str | None = None
        self.old_user: str | None = None
        self.old_session: str | None = None

    async def __aenter__(self):
        # Save current values
        self.old_tenant = tenant_id.get()
        self.old_user = user_id.get()
        self.old_session = session_id.get()

        # Set new values
        if self.new_tenant is not None:
            tenant_id.set(self.new_tenant)
        if self.new_user is not None:
            user_id.set(self.new_user)
        if self.new_session is not None:
            session_id.set(self.new_session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Restore old values
        tenant_id.set(self.old_tenant)
        user_id.set(self.old_user)
        session_id.set(self.old_session)
        return False
