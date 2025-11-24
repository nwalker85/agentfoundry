#!/usr/bin/env python3
"""
Seed RBAC data for PostgreSQL database.
This script populates permissions, roles, and role-permission mappings.

PostgreSQL version - uses psycopg2 and proper parameterized queries.
"""

import logging
import uuid

logger = logging.getLogger(__name__)


def seed_rbac_data():
    """Seed RBAC permissions, roles, and mappings into PostgreSQL database"""
    from backend.db_postgres import DictCursor, get_connection_no_rls

    print("Seeding RBAC data...")

    with get_connection_no_rls() as conn:
        cursor = conn.cursor(cursor_factory=DictCursor)

        # =========================================================================
        # PERMISSIONS
        # =========================================================================

        permissions_data: list[tuple[str, str, str, str, str]] = [
            # Organization Management
            ("org:read", "org", "read", "self", "View organization details"),
            ("org:update", "org", "update", "self", "Update organization settings"),
            ("org:read:platform", "org", "read", "platform", "View all organizations (platform admin only)"),
            ("org:update:platform", "org", "update", "platform", "Update any organization (platform admin only)"),
            ("org:delete:platform", "org", "delete", "platform", "Delete organizations (platform admin only)"),
            ("org:tier:update", "org", "tier_update", "platform", "Update organization tier (platform admin only)"),
            # User Management
            ("user:read", "user", "read", "org", "View users in organization"),
            ("user:invite", "user", "create", "org", "Invite new users to organization"),
            ("user:update", "user", "update", "org", "Update user details in organization"),
            ("user:revoke", "user", "delete", "org", "Remove users from organization"),
            ("user:read:platform", "user", "read", "platform", "View all users (platform admin only)"),
            # Agent Management
            ("agent:create", "agent", "create", "org", "Create new agents"),
            ("agent:read:self", "agent", "read", "self", "View own agents"),
            ("agent:read:org", "agent", "read", "org", "View all agents in organization"),
            ("agent:update:self", "agent", "update", "self", "Update own agents"),
            ("agent:update:org", "agent", "update", "org", "Update any agent in organization"),
            ("agent:delete:self", "agent", "delete", "self", "Delete own agents"),
            ("agent:delete:org", "agent", "delete", "org", "Delete any agent in organization"),
            ("agent:publish", "agent", "publish", "org", "Publish agents to gallery"),
            ("agent:execute", "agent", "execute", "org", "Execute agent sessions"),
            # Session Management
            ("session:read:self", "session", "read", "self", "View own sessions"),
            ("session:read:org", "session", "read", "org", "View all sessions in organization"),
            ("session:terminate:self", "session", "terminate", "self", "Terminate own sessions"),
            ("session:terminate:org", "session", "terminate", "org", "Terminate any session in organization"),
            # Artifact Management
            ("artifact:read:self", "artifact", "read", "self", "View own artifacts"),
            ("artifact:read:org", "artifact", "read", "org", "View all artifacts in organization"),
            ("artifact:delete:org", "artifact", "delete", "org", "Delete artifacts in organization"),
            # LLM Usage & Quotas
            ("llm:invoke", "llm", "invoke", "org", "Make LLM API calls"),
            ("llm:quota:read:self", "llm_quota", "read", "self", "View own LLM usage and quotas"),
            ("llm:quota:read:org", "llm_quota", "read", "org", "View organization LLM usage and quotas"),
            ("llm:quota:update:org", "llm_quota", "update", "org", "Update organization LLM quotas"),
            # Audit Logs
            ("audit:read:self", "audit", "read", "self", "View own audit logs"),
            ("audit:read:org", "audit", "read", "org", "View organization audit logs"),
            ("audit:read:platform", "audit", "read", "platform", "View all audit logs (platform admin only)"),
            # Settings & Configuration
            ("settings:read", "settings", "read", "org", "View organization settings"),
            ("settings:update", "settings", "update", "org", "Update organization settings"),
            ("settings:read:platform", "settings", "read", "platform", "View platform settings"),
            ("settings:update:platform", "settings", "update", "platform", "Update platform settings"),
            # API Key Management
            ("api_key:create:self", "api_key", "create", "self", "Create own API keys"),
            ("api_key:read:self", "api_key", "read", "self", "View own API keys"),
            ("api_key:revoke:self", "api_key", "revoke", "self", "Revoke own API keys"),
            ("api_key:create:org", "api_key", "create", "org", "Create API keys for organization"),
            ("api_key:revoke:org", "api_key", "revoke", "org", "Revoke any API key in organization"),
            # Domain & Instance Management
            ("domain:create", "domain", "create", "org", "Create new domains"),
            ("domain:read", "domain", "read", "org", "View domains"),
            ("domain:update", "domain", "update", "org", "Update domains"),
            ("domain:delete", "domain", "delete", "org", "Delete domains"),
            ("instance:create", "instance", "create", "org", "Create new instances"),
            ("instance:read", "instance", "read", "org", "View instances"),
            ("instance:update", "instance", "update", "org", "Update instances"),
            ("instance:delete", "instance", "delete", "org", "Delete instances"),
            # Platform Support
            (
                "support:impersonate:org",
                "support",
                "impersonate",
                "platform",
                "Impersonate users for support (platform only)",
            ),
        ]

        permission_uuids = {}
        for code, resource_type, action, scope, description in permissions_data:
            perm_id = str(uuid.uuid4())
            permission_uuids[code] = perm_id
            cursor.execute(
                """
                INSERT INTO permissions (id, code, resource_type, action, scope, description)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
                """,
                (perm_id, code, resource_type, action, scope, description),
            )

        print(f"  Inserted {len(permissions_data)} permissions")

        # =========================================================================
        # ROLES
        # =========================================================================

        roles_data: list[tuple[str, str, bool]] = [
            # Platform-level roles
            ("platform_owner", "Platform owner with full administrative access", True),
            ("platform_support", "Platform support team with limited admin access", True),
            # Org-level roles
            ("org_admin", "Organization administrator with full org-level permissions", False),
            ("org_developer", "Developer who can create and manage agents", False),
            ("org_viewer", "Read-only access to organization resources", False),
            ("org_operator", "Operational access to execute agents and view sessions", False),
            ("api_client", "Programmatic API access for integrations", False),
            # Service roles
            ("backend_service", "Internal backend service account", True),
            ("compiler_service", "Agent compiler service account", True),
            ("job_runner_service", "Background job runner service account", True),
        ]

        role_uuids = {}
        for name, description, is_system in roles_data:
            role_id = str(uuid.uuid4())
            role_uuids[name] = role_id
            cursor.execute(
                """
                INSERT INTO roles (id, name, description, is_system)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                """,
                (role_id, name, description, is_system),
            )

        print(f"  Inserted {len(roles_data)} roles")

        # =========================================================================
        # ROLE-PERMISSION MAPPINGS
        # =========================================================================

        role_permissions = {
            "platform_owner": [
                # All permissions for platform owner
                code
                for code, _, _, _, _ in permissions_data
            ],
            "platform_support": [
                "org:read:platform",
                "user:read:platform",
                "agent:read:org",
                "session:read:org",
                "audit:read:platform",
                "settings:read:platform",
                "support:impersonate:org",
            ],
            "org_admin": [
                "org:read",
                "org:update",
                "user:read",
                "user:invite",
                "user:update",
                "user:revoke",
                "agent:create",
                "agent:read:org",
                "agent:update:org",
                "agent:delete:org",
                "agent:publish",
                "agent:execute",
                "session:read:org",
                "session:terminate:org",
                "artifact:read:org",
                "artifact:delete:org",
                "llm:invoke",
                "llm:quota:read:org",
                "llm:quota:update:org",
                "audit:read:org",
                "settings:read",
                "settings:update",
                "api_key:create:org",
                "api_key:read:self",
                "api_key:revoke:org",
                "domain:create",
                "domain:read",
                "domain:update",
                "domain:delete",
                "instance:create",
                "instance:read",
                "instance:update",
                "instance:delete",
            ],
            "org_developer": [
                "agent:create",
                "agent:read:self",
                "agent:read:org",
                "agent:update:self",
                "agent:delete:self",
                "agent:execute",
                "session:read:self",
                "session:terminate:self",
                "artifact:read:self",
                "llm:invoke",
                "llm:quota:read:self",
                "api_key:create:self",
                "api_key:read:self",
                "api_key:revoke:self",
                "domain:read",
                "instance:read",
            ],
            "org_operator": [
                "agent:read:org",
                "agent:execute",
                "session:read:org",
                "session:terminate:self",
                "artifact:read:org",
                "llm:invoke",
                "llm:quota:read:self",
                "domain:read",
                "instance:read",
            ],
            "org_viewer": [
                "agent:read:org",
                "session:read:org",
                "artifact:read:org",
                "llm:quota:read:self",
                "domain:read",
                "instance:read",
            ],
            "api_client": [
                "agent:create",
                "agent:read:org",
                "agent:update:self",
                "agent:execute",
                "session:read:self",
                "llm:invoke",
                "domain:read",
                "instance:read",
            ],
            "backend_service": [
                # Backend service gets most permissions
                code
                for code, _, _, _, _ in permissions_data
                if ":platform" not in code
            ],
            "compiler_service": [
                "agent:read:org",
                "agent:update:org",
                "domain:read",
                "instance:read",
            ],
            "job_runner_service": [
                "agent:read:org",
                "agent:execute",
                "session:read:org",
                "llm:invoke",
            ],
        }

        # Get existing permission IDs (in case ON CONFLICT skipped some)
        cursor.execute("SELECT id, code FROM permissions")
        for row in cursor.fetchall():
            permission_uuids[row["code"]] = row["id"]

        # Get existing role IDs (in case ON CONFLICT skipped some)
        cursor.execute("SELECT id, name FROM roles")
        for row in cursor.fetchall():
            role_uuids[row["name"]] = row["id"]

        mapping_count = 0
        for role_name, perm_codes in role_permissions.items():
            if role_name not in role_uuids:
                continue

            role_id = role_uuids[role_name]
            for perm_code in perm_codes:
                if perm_code in permission_uuids:
                    perm_id = permission_uuids[perm_code]
                    cursor.execute(
                        """
                        INSERT INTO role_permissions (role_id, permission_id)
                        VALUES (%s, %s)
                        ON CONFLICT (role_id, permission_id) DO NOTHING
                        """,
                        (role_id, perm_id),
                    )
                    mapping_count += 1

        print(f"  Inserted {mapping_count} role-permission mappings")

        conn.commit()

    print("RBAC data seeded successfully")
    return True


if __name__ == "__main__":
    seed_rbac_data()
