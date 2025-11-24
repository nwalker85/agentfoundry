"""
Audit Service for Agent Foundry (PostgreSQL Version)
Provides audit logging functionality.
"""

import json
import logging
from uuid import UUID

from pydantic import BaseModel

from backend.db_postgres import DictCursor, get_connection_no_rls

logger = logging.getLogger(__name__)


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================


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
# AUDIT SERVICE
# ============================================================================


class AuditService:
    """
    Standalone audit logging service.
    Handles writing audit logs to PostgreSQL.
    """

    def log(self, audit_log: AuditLogCreate) -> None:
        """
        Create an audit log entry.

        Args:
            audit_log: Audit log data to record
        """
        metadata_json = json.dumps(audit_log.metadata) if audit_log.metadata else None

        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

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

    def log_safe(self, audit_log: AuditLogCreate) -> bool:
        """
        Create an audit log entry, catching and logging any errors.

        Args:
            audit_log: Audit log data to record

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log(audit_log)
            return True
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")
            return False


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

audit_service = AuditService()
