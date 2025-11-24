"""
Database Access Layer for Agent Foundry

This module provides the data access layer for Agent Foundry.
Complete PostgreSQL implementation with Row-Level Security (RLS).

All queries automatically filter by tenant context set in backend.context.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from typing import Any

from backend.db_postgres import (
    DictCursor,
    get_connection,
    get_connection_no_rls,
    init_schema as pg_init_schema,
)

logger = logging.getLogger(__name__)

# Schema paths
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db_schema_postgres.sql")

# Database URL for backward compatibility
DB_URL = os.getenv("DATABASE_URL", "postgresql://foundry:foundry@postgres:5432/foundry")


def init_db() -> None:
    """Initialize the control-plane database (run schema migrations and seed)."""
    logger.info("Initializing PostgreSQL database...")

    # 1. Initialize main schema
    try:
        pg_init_schema(SCHEMA_PATH)
        print("PostgreSQL schema initialized")
    except Exception as e:
        print(f"Failed to initialize database schema: {e}")
        return

    # 2. Seed RBAC data
    print("Seeding RBAC roles and permissions...")
    try:
        from backend.seed_rbac_postgres import seed_rbac_data

        seed_rbac_data()
    except ImportError:
        # Fall back to SQLite seeder if postgres version doesn't exist yet
        logger.warning("PostgreSQL RBAC seeder not found, skipping RBAC seed")
    except Exception as e:
        print(f"Failed to seed RBAC data: {e}")

    # 3. Seed initial data (Quant / Demo / CIBC / Card Services)
    _seed_initial_data()


def _seed_initial_data() -> None:
    """Seed initial organizations, domains, instances, and sample agents."""
    try:
        with get_connection_no_rls() as conn:
            conn.autocommit = False
            cur = conn.cursor(cursor_factory=DictCursor)

            # Organization - Quant
            cur.execute(
                """
                INSERT INTO organizations (id, name, tier)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("quant", "Quant", "enterprise"),
            )

            # Domain - Demo
            cur.execute(
                """
                INSERT INTO domains (id, organization_id, name, display_name, version)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("demo", "quant", "demo", "Demo", "1.0.0"),
            )

            # Instance - dev
            cur.execute(
                """
                INSERT INTO instances (id, organization_id, domain_id, environment, instance_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("quant-demo-dev", "quant", "demo", "dev", "dev"),
            )

            # Organization - CIBC
            cur.execute(
                """
                INSERT INTO organizations (id, name, tier)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("cibc", "CIBC", "enterprise"),
            )

            # Domain - Card Services
            cur.execute(
                """
                INSERT INTO domains (id, organization_id, name, display_name, version)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("card-services", "cibc", "card-services", "Card Services", "1.0.0"),
            )

            # Instance - Card Services dev
            cur.execute(
                """
                INSERT INTO instances (id, organization_id, domain_id, environment, instance_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                ("cibc-card-services-dev", "cibc", "card-services", "dev", "dev"),
            )

            # Seed sample agents tied to Quant / Demo
            agents = [
                (
                    "agt-001",
                    "quant",
                    "demo",
                    "customer-support-agent",
                    "Customer Support Agent",
                    "Handles customer inquiries, order status, and basic troubleshooting",
                    "2.1.0",
                    "active",
                    "prod",
                    None,
                    False,
                    None,
                    "nwalker85",
                    ["customer-service", "support", "chat"],
                ),
                (
                    "agt-002",
                    "quant",
                    "demo",
                    "sales-qualifying-agent",
                    "Sales Qualifying Agent",
                    "Qualifies leads, schedules demos, and routes to sales team",
                    "1.8.3",
                    "active",
                    "prod",
                    None,
                    False,
                    None,
                    "sarah.chen",
                    ["sales", "lead-qualification", "crm"],
                ),
                (
                    "agt-003",
                    "quant",
                    "demo",
                    "data-analyst-agent",
                    "Data Analysis Agent",
                    "Performs SQL queries, generates reports, and provides data insights",
                    "3.0.1",
                    "active",
                    "staging",
                    None,
                    False,
                    None,
                    "mike.rodriguez",
                    ["analytics", "sql", "reporting"],
                ),
                (
                    "agt-004",
                    "quant",
                    "demo",
                    "hr-onboarding-agent",
                    "HR Onboarding Agent",
                    "Automates employee onboarding, document collection, and orientation scheduling",
                    "1.4.2",
                    "active",
                    "prod",
                    None,
                    False,
                    None,
                    "jessica.lee",
                    ["hr", "onboarding", "automation"],
                ),
                (
                    "agt-005",
                    "quant",
                    "demo",
                    "it-helpdesk-agent",
                    "IT Helpdesk Agent",
                    "Resolves common IT issues, resets passwords, and escalates complex problems",
                    "2.3.1",
                    "active",
                    "prod",
                    None,
                    False,
                    None,
                    "tom.mitchell",
                    ["it", "helpdesk", "troubleshooting"],
                ),
            ]

            for agent in agents:
                cur.execute(
                    """
                    INSERT INTO agents (
                        id, organization_id, domain_id, name, display_name,
                        description, version, status, environment, yaml_path,
                        is_system_agent, system_tier, created_by, tags
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    agent,
                )

            conn.commit()
            print("Seeded initial org/domain/instance (Quant/Demo + CIBC/Card Services)")
            print("Seeded 5 sample agents tied to Quant / Demo")
    except Exception as e:
        print(f"Failed to seed initial data: {e}")
        logger.exception("Seed data error")


def get_organizations_with_domains() -> list[dict]:
    """
    Return a list of organizations and their domains for the control-plane header.

    Shape:
    [
      {
        "id": "cibc",
        "name": "CIBC",
        "domains": [
          {"id": "card-services", "name": "Card Services", "organization_id": "cibc"},
          ...
        ]
      },
      ...
    ]
    """
    orgs: dict[str, dict] = {}

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            SELECT id, name
            FROM organizations
            ORDER BY name ASC
            """
        )
        for row in cur.fetchall():
            org_id, name = row["id"], row["name"]
            orgs[org_id] = {
                "id": org_id,
                "name": name,
                "domains": [],
            }

        cur.execute(
            """
            SELECT id, organization_id, display_name
            FROM domains
            ORDER BY display_name ASC
            """
        )
        for row in cur.fetchall():
            dom_id, org_id, display_name = row["id"], row["organization_id"], row["display_name"]
            if org_id in orgs:
                orgs[org_id]["domains"].append(
                    {
                        "id": dom_id,
                        "name": display_name,
                        "organization_id": org_id,
                    }
                )

        conn.commit()

    # Return list sorted by org name
    return list(orgs.values())


# ============================================================================
# HELPER FUNCTIONS WITH EVENT EMISSION
# ============================================================================


def _emit_event_sync(coro):
    """Helper to emit async events from sync context."""
    try:
        loop = asyncio.get_running_loop()
        asyncio.create_task(coro)
    except RuntimeError:
        # No event loop, skip event emission
        pass


def create_agent_with_event(
    agent_id: str,
    organization_id: str,
    domain_id: str,
    name: str,
    display_name: str,
    description: str,
    version: str = "1.0.0",
    status: str = "active",
    environment: str = "dev",
    created_by: str = "system",
    tags: list[str] = None,
) -> dict:
    """
    Create an agent and emit AGENT_CREATED event.
    """
    from backend.events import emit_agent_created

    with get_connection(organization_id) as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            INSERT INTO agents (
                id, organization_id, domain_id, name, display_name,
                description, version, status, environment, created_by, tags
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                agent_id,
                organization_id,
                domain_id,
                name,
                display_name,
                description,
                version,
                status,
                environment,
                created_by,
                tags or [],
            ),
        )
        agent_data = dict(cur.fetchone())
        conn.commit()

    # Emit event (async, non-blocking)
    _emit_event_sync(emit_agent_created(agent_data))

    return agent_data


def update_agent_with_event(agent_id: str, updates: dict) -> dict:
    """
    Update an agent and emit AGENT_UPDATED event.
    """
    from backend.events import emit_agent_updated

    # Build SET clause dynamically
    set_clauses = []
    params = []
    for key, value in updates.items():
        set_clauses.append(f"{key} = %s")
        params.append(value)

    set_clauses.append("updated_at = NOW()")
    params.append(agent_id)

    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            f"""
            UPDATE agents
            SET {", ".join(set_clauses)}
            WHERE id = %s
            RETURNING *
            """,
            params,
        )

        row = cur.fetchone()
        if not row:
            raise ValueError(f"Agent {agent_id} not found")

        agent_data = dict(row)
        conn.commit()

    # Emit event
    _emit_event_sync(emit_agent_updated(agent_data))

    return agent_data


def delete_agent_with_event(agent_id: str) -> None:
    """
    Delete an agent and emit AGENT_DELETED event.
    """
    from backend.events import emit_agent_deleted

    with get_connection() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        # Get agent info before deletion
        cur.execute("SELECT organization_id, domain_id FROM agents WHERE id = %s", (agent_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Agent {agent_id} not found")

        org_id, domain_id = row["organization_id"], row["domain_id"]

        # Delete agent
        cur.execute("DELETE FROM agents WHERE id = %s", (agent_id,))
        conn.commit()

    # Emit event
    _emit_event_sync(emit_agent_deleted(agent_id, org_id, domain_id))


def list_integration_configs(organization_id: str, domain_id: str, environment: str = "dev") -> list[dict]:
    with get_connection(organization_id) as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            SELECT *
            FROM integration_configs
            WHERE organization_id = %s
              AND domain_id = %s
              AND environment = %s
            ORDER BY tool_name
            """,
            (organization_id, domain_id, environment),
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.commit()

    return rows


def get_integration_config(
    tool_name: str, organization_id: str, domain_id: str, environment: str = "dev"
) -> dict | None:
    with get_connection(organization_id) as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            SELECT *
            FROM integration_configs
            WHERE tool_name = %s
              AND organization_id = %s
              AND domain_id = %s
              AND environment = %s
            """,
            (tool_name, organization_id, domain_id, environment),
        )
        row = cur.fetchone()
        conn.commit()

    return dict(row) if row else None


def upsert_integration_config(
    *,
    tool_name: str,
    organization_id: str,
    project_id: str | None = None,
    domain_id: str,
    environment: str,
    instance_name: str,
    base_url: str,
    auth_method: str,
    credentials: dict | None = None,
    metadata: dict | None = None,
    user_id: str | None = None,
) -> dict:
    config_id = str(uuid.uuid4())

    with get_connection(organization_id) as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        # Upsert using ON CONFLICT
        cur.execute(
            """
            INSERT INTO integration_configs (
                id, tool_name, organization_id, project_id, domain_id, environment,
                instance_name, base_url, auth_method, credentials, metadata,
                created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tool_name, organization_id, project_id, domain_id, environment)
            DO UPDATE SET
                instance_name = EXCLUDED.instance_name,
                base_url = EXCLUDED.base_url,
                auth_method = EXCLUDED.auth_method,
                credentials = EXCLUDED.credentials,
                metadata = EXCLUDED.metadata,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING *
            """,
            (
                config_id,
                tool_name,
                organization_id,
                project_id,
                domain_id,
                environment,
                instance_name,
                base_url,
                auth_method,
                credentials or {},
                metadata or {},
                user_id,
                user_id,
            ),
        )

        row = cur.fetchone()
        conn.commit()

    return dict(row)


# ============================================================================
# FORGE VISUAL DESIGNER DATA ACCESS
# ============================================================================


def _deserialize_state_schema(row: dict | None) -> dict | None:
    if not row:
        return None
    result = dict(row)
    # JSONB columns are already parsed by psycopg2
    result["fields"] = result.pop("fields_json", [])
    result["initial_state"] = result.pop("initial_state_json", {})
    return result


def list_state_schemas() -> list[dict]:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT *
            FROM state_schemas
            ORDER BY updated_at DESC
            """
        )
        rows = cur.fetchall()
        conn.commit()
    return [_deserialize_state_schema(dict(row)) for row in rows]


def get_state_schema(schema_id: str) -> dict | None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM state_schemas WHERE id = %s", (schema_id,))
        row = cur.fetchone()
        conn.commit()
    return _deserialize_state_schema(dict(row)) if row else None


def upsert_state_schema(schema: dict) -> dict:
    schema_id = schema.get("id") or str(uuid.uuid4())

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            INSERT INTO state_schemas (
                id, name, description, version, fields_json,
                initial_state_json, tags, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                version = EXCLUDED.version,
                fields_json = EXCLUDED.fields_json,
                initial_state_json = EXCLUDED.initial_state_json,
                tags = EXCLUDED.tags,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING *
            """,
            (
                schema_id,
                schema.get("name"),
                schema.get("description"),
                schema.get("version", "1.0.0"),
                schema.get("fields", []),
                schema.get("initial_state", {}),
                schema.get("tags", []),
                schema.get("created_by"),
                schema.get("updated_by") or schema.get("created_by"),
            ),
        )

        row = cur.fetchone()
        conn.commit()

    return _deserialize_state_schema(dict(row))


def delete_state_schema(schema_id: str) -> None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM state_schemas WHERE id = %s", (schema_id,))
        conn.commit()


def _deserialize_trigger(row: dict | None) -> dict | None:
    if not row:
        return None
    result = dict(row)
    result["config"] = result.pop("config_json", {})
    return result


def list_triggers(channel: str | None = None) -> list[dict]:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        if channel:
            cur.execute(
                """
                SELECT *
                FROM triggers
                WHERE channel = %s OR channel IS NULL
                ORDER BY name ASC
                """,
                (channel,),
            )
        else:
            cur.execute(
                """
                SELECT *
                FROM triggers
                ORDER BY name ASC
                """
            )
        rows = cur.fetchall()
        conn.commit()
    return [_deserialize_trigger(dict(row)) for row in rows]


def upsert_trigger(trigger: dict) -> dict:
    trigger_id = trigger.get("id") or str(uuid.uuid4())

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            INSERT INTO triggers (
                id, name, type, description, channel, config_json,
                is_active, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                type = EXCLUDED.type,
                description = EXCLUDED.description,
                channel = EXCLUDED.channel,
                config_json = EXCLUDED.config_json,
                is_active = EXCLUDED.is_active,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING *
            """,
            (
                trigger_id,
                trigger.get("name"),
                trigger.get("type"),
                trigger.get("description"),
                trigger.get("channel"),
                trigger.get("config", {}),
                trigger.get("is_active", True),
                trigger.get("created_by"),
                trigger.get("updated_by") or trigger.get("created_by"),
            ),
        )

        row = cur.fetchone()
        conn.commit()

    return _deserialize_trigger(dict(row))


def get_trigger(trigger_id: str) -> dict | None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM triggers WHERE id = %s", (trigger_id,))
        row = cur.fetchone()
        conn.commit()
    return _deserialize_trigger(dict(row)) if row else None


def delete_trigger(trigger_id: str) -> None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM triggers WHERE id = %s", (trigger_id,))
        conn.commit()


def _deserialize_workflow(row: dict | None) -> dict | None:
    if not row:
        return None
    result = dict(row)
    result["nodes"] = result.pop("nodes_json", [])
    result["edges"] = result.pop("edges_json", [])
    result["metadata"] = result.pop("metadata_json", {})
    return result


def list_channel_workflows(channel: str | None = None) -> list[dict]:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        if channel:
            cur.execute(
                """
                SELECT *
                FROM channel_workflows
                WHERE channel = %s
                ORDER BY updated_at DESC
                """,
                (channel,),
            )
        else:
            cur.execute(
                """
                SELECT *
                FROM channel_workflows
                ORDER BY updated_at DESC
                """
            )
        rows = cur.fetchall()
        conn.commit()
    return [_deserialize_workflow(dict(row)) for row in rows]


def get_channel_workflow(workflow_id: str) -> dict | None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute("SELECT * FROM channel_workflows WHERE id = %s", (workflow_id,))
        row = cur.fetchone()
        conn.commit()
    return _deserialize_workflow(dict(row)) if row else None


def upsert_channel_workflow(workflow: dict) -> dict:
    workflow_id = workflow.get("id") or str(uuid.uuid4())

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        cur.execute(
            """
            INSERT INTO channel_workflows (
                id, channel, name, description, nodes_json, edges_json,
                state_schema_id, metadata_json, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                channel = EXCLUDED.channel,
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                nodes_json = EXCLUDED.nodes_json,
                edges_json = EXCLUDED.edges_json,
                state_schema_id = EXCLUDED.state_schema_id,
                metadata_json = EXCLUDED.metadata_json,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            RETURNING *
            """,
            (
                workflow_id,
                workflow.get("channel"),
                workflow.get("name"),
                workflow.get("description"),
                workflow.get("nodes", []),
                workflow.get("edges", []),
                workflow.get("state_schema_id"),
                workflow.get("metadata", {}),
                workflow.get("created_by"),
                workflow.get("updated_by") or workflow.get("created_by"),
            ),
        )

        row = cur.fetchone()
        conn.commit()

    return _deserialize_workflow(dict(row))


def delete_channel_workflow(workflow_id: str) -> None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM channel_workflows WHERE id = %s", (workflow_id,))
        conn.commit()


def list_graph_triggers(target_type: str, target_id: str) -> list[dict]:
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT gt.id, gt.target_type, gt.target_id, gt.trigger_id, gt.start_node_id, gt.config_json,
                   t.name as trigger_name, t.type as trigger_type
            FROM graph_triggers gt
            JOIN triggers t ON gt.trigger_id = t.id
            WHERE gt.target_type = %s AND gt.target_id = %s
            ORDER BY t.name ASC
            """,
            (target_type, target_id),
        )
        rows = cur.fetchall()
        conn.commit()

    result = []
    for row in rows:
        r = dict(row)
        r["config"] = r.pop("config_json", {})
        result.append(r)
    return result


def save_graph_triggers(
    target_type: str, target_id: str, trigger_ids: list[str], start_node_id: str | None = None
) -> None:
    with get_connection_no_rls() as conn:
        cur = conn.cursor()

        # Remove existing mappings
        cur.execute(
            "DELETE FROM graph_triggers WHERE target_type = %s AND target_id = %s",
            (target_type, target_id),
        )

        for trigger_id in trigger_ids:
            mapping_id = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO graph_triggers (id, target_type, target_id, trigger_id, start_node_id, config_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (mapping_id, target_type, target_id, trigger_id, start_node_id, {}),
            )

        conn.commit()


# ============================================================================
# AGENT VERSION MANAGEMENT
# ============================================================================


def get_agent_versions(agent_id: str) -> list[dict[str, Any]]:
    """
    Get all versions for an agent, ordered by version_number descending.
    """
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT id, agent_id, version_number, version_label, yaml_content,
                   reactflow_data, change_summary, created_by, created_at
            FROM agent_versions
            WHERE agent_id = %s
            ORDER BY version_number DESC
            """,
            (agent_id,),
        )
        rows = cur.fetchall()
        conn.commit()
    return [dict(row) for row in rows]


def get_agent_version(version_id: str) -> dict[str, Any] | None:
    """
    Get a specific version by its ID.
    """
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT id, agent_id, version_number, version_label, yaml_content,
                   reactflow_data, change_summary, created_by, created_at
            FROM agent_versions
            WHERE id = %s
            """,
            (version_id,),
        )
        row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


def create_agent_version(
    agent_id: str,
    yaml_content: str | None = None,
    reactflow_data: dict | None = None,
    change_summary: str | None = None,
    created_by: str | None = None,
    version_label: str = "1.0.0",
) -> dict[str, Any]:
    """
    Create a new version for an agent. Auto-increments version_number.
    """
    version_id = str(uuid.uuid4())

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        # Get next version number
        cur.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 as next_version FROM agent_versions WHERE agent_id = %s",
            (agent_id,),
        )
        next_version = cur.fetchone()["next_version"]

        # Insert new version
        cur.execute(
            """
            INSERT INTO agent_versions (
                id, agent_id, version_number, version_label, yaml_content,
                reactflow_data, change_summary, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                version_id,
                agent_id,
                next_version,
                version_label,
                yaml_content,
                json.dumps(reactflow_data) if reactflow_data else None,
                change_summary,
                created_by,
            ),
        )
        version_row = dict(cur.fetchone())

        # Update agent's latest_version_id and version_count
        cur.execute(
            """
            UPDATE agents
            SET latest_version_id = %s,
                version_count = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (version_id, next_version, agent_id),
        )

        conn.commit()

    return version_row


def rollback_to_version(agent_id: str, version_id: str) -> dict[str, Any]:
    """
    Rollback an agent to a specific version.
    Creates a new version with the content from the specified version.
    """
    # Get the version to rollback to
    old_version = get_agent_version(version_id)
    if not old_version:
        raise ValueError(f"Version {version_id} not found")

    if old_version["agent_id"] != agent_id:
        raise ValueError(f"Version {version_id} does not belong to agent {agent_id}")

    # Create a new version with the old content
    return create_agent_version(
        agent_id=agent_id,
        yaml_content=old_version.get("yaml_content"),
        reactflow_data=old_version.get("reactflow_data"),
        change_summary=f"Rollback to version {old_version['version_number']}",
        created_by="system",
        version_label=old_version.get("version_label", "1.0.0"),
    )


def deploy_agent_version(agent_id: str, version_id: str) -> dict[str, Any]:
    """
    Deploy a specific version of an agent.
    Sets the deployed_version_id to mark which version is active.
    """
    # Verify the version exists and belongs to this agent
    version = get_agent_version(version_id)
    if not version:
        raise ValueError(f"Version {version_id} not found")
    if version["agent_id"] != agent_id:
        raise ValueError(f"Version {version_id} does not belong to agent {agent_id}")

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            UPDATE agents
            SET deployed_version_id = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING *
            """,
            (version_id, agent_id),
        )
        row = cur.fetchone()
        conn.commit()

    if not row:
        raise ValueError(f"Agent {agent_id} not found")

    return dict(row)


def get_deployed_agents(
    organization_id: str | None = None,
    environment: str = "dev",
) -> list[dict[str, Any]]:
    """
    Get all agents that have a deployed version.
    Returns only agents where deployed_version_id is set.
    """
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        query = """
            SELECT a.*, v.version_label as deployed_version_label, v.created_at as deployed_at
            FROM agents a
            LEFT JOIN agent_versions v ON a.deployed_version_id = v.id
            WHERE a.deployed_version_id IS NOT NULL
        """
        params = []

        if organization_id:
            query += " AND a.organization_id = %s"
            params.append(organization_id)

        query += " AND a.environment = %s"
        params.append(environment)

        query += " ORDER BY a.updated_at DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.commit()

    return [dict(row) for row in rows]


def find_agent_by_name(
    name: str,
    organization_id: str,
    domain_id: str,
    environment: str = "dev",
) -> dict[str, Any] | None:
    """
    Find an existing agent by name within the same org/domain/environment.
    Used to check if we should update an existing agent or create a new one.
    """
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT *
            FROM agents
            WHERE name = %s
              AND organization_id = %s
              AND domain_id = %s
              AND environment = %s
              AND is_system_agent = FALSE
            """,
            (name, organization_id, domain_id, environment),
        )
        row = cur.fetchone()
        conn.commit()
    return dict(row) if row else None


# ============================================================================
# UNIFIED GRAPH CRUD (User Agents, Channel Workflows, System Agents)
# ============================================================================


def list_graphs(
    graph_type: str | None = None,
    channel: str | None = None,
    org_id: str | None = None,
    domain_id: str | None = None,
    environment: str = "dev",
) -> list[dict[str, Any]]:
    """
    List all graphs with optional filtering.
    """
    params = [environment]
    query = """
        SELECT
            id, organization_id, domain_id, name, display_name, description,
            version, status, environment, yaml_path, is_system_agent, system_tier,
            created_by, tags, graph_type, channel, yaml_content,
            created_at, updated_at
        FROM agents
        WHERE environment = %s
    """

    if graph_type:
        query += " AND graph_type = %s"
        params.append(graph_type)

    if channel:
        query += " AND channel = %s"
        params.append(channel)

    if org_id:
        query += " AND organization_id = %s"
        params.append(org_id)

    if domain_id:
        query += " AND domain_id = %s"
        params.append(domain_id)

    query += " ORDER BY updated_at DESC"

    # Use RLS if org_id provided, otherwise no RLS
    ctx_manager = get_connection(org_id) if org_id else get_connection_no_rls()
    with ctx_manager as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.commit()

    return [dict(row) for row in rows]


def get_graph(graph_id: str) -> dict[str, Any] | None:
    """
    Get a single graph by ID.
    """
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT
                id, organization_id, domain_id, name, display_name, description,
                version, status, environment, yaml_path, is_system_agent, system_tier,
                created_by, tags, graph_type, channel, yaml_content,
                created_at, updated_at
            FROM agents
            WHERE id = %s
        """,
            (graph_id,),
        )
        row = cur.fetchone()
        conn.commit()

    return dict(row) if row else None


def upsert_graph(graph_data: dict[str, Any], change_summary: str | None = None) -> dict[str, Any]:
    """
    Create or update a graph (agent) with version tracking.

    - If agent exists by name+org+domain+env: creates new version, updates agent
    - If new agent: creates agent + first version
    """
    from backend.utils import yaml_storage

    metadata = graph_data.get("metadata", {})

    name = metadata.get("name", "Untitled Graph")
    display_name = metadata.get("display_name", name)
    description = metadata.get("description", "")
    version_label = metadata.get("version", "1.0.0")
    status = metadata.get("status", "draft")
    environment = metadata.get("environment", "dev")
    graph_type = metadata.get("type", "user")
    channel = metadata.get("channel")
    org_id = metadata.get("organization_id")
    domain_id = metadata.get("domain_id")
    is_system_agent = graph_type == "system"
    system_tier = metadata.get("system_tier", 0 if graph_type == "system" else None)
    created_by = metadata.get("created_by", "system")
    tags = metadata.get("tags", [])

    # First, check if we have an explicit ID for an existing agent
    explicit_id = graph_data.get("id") or metadata.get("id")
    existing_agent = None

    if explicit_id:
        # Check if agent with this ID exists
        existing_agent = get_graph(explicit_id)
        if existing_agent:
            logger.info(f"Found existing agent by ID '{explicit_id}', creating new version")

    # If not found by ID, check by name in the same org/domain/env
    if not existing_agent and org_id and domain_id and not is_system_agent:
        existing_agent = find_agent_by_name(name, org_id, domain_id, environment)
        if existing_agent:
            logger.info(f"Found existing agent by name '{name}' ({existing_agent['id']}), creating new version")

    # Determine the agent ID
    if existing_agent:
        # Use existing agent ID - we're creating a new version
        graph_id = existing_agent["id"]
    else:
        # New agent - use provided ID or generate new one
        graph_id = explicit_id or str(uuid.uuid4())
        logger.info(f"Creating new agent '{name}' ({graph_id})")

    # Update metadata with resolved ID
    if "metadata" in graph_data:
        graph_data["metadata"]["id"] = graph_id
    else:
        graph_data["id"] = graph_id

    # Write YAML file
    yaml_path = yaml_storage.write_graph_yaml(graph_data)

    # Store full content as JSON
    yaml_content = json.dumps(graph_data)

    # Extract ReactFlow data for version snapshot
    spec = graph_data.get("spec", {})
    graph_spec = spec.get("graph", {})
    reactflow_data = {
        "nodes": graph_spec.get("nodes", []),
        "edges": graph_spec.get("edges", []),
    }

    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)

        if existing_agent:
            # Update existing agent record
            cur.execute(
                """
                UPDATE agents SET
                    display_name = %s,
                    description = %s,
                    version = %s,
                    status = %s,
                    yaml_path = %s,
                    tags = %s,
                    yaml_content = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    display_name,
                    description,
                    version_label,
                    status,
                    yaml_path,
                    tags,
                    yaml_content,
                    graph_id,
                ),
            )
        else:
            # Insert new agent
            cur.execute(
                """
                INSERT INTO agents (
                    id, organization_id, domain_id, name, display_name, description,
                    version, status, environment, yaml_path, is_system_agent, system_tier,
                    created_by, tags, graph_type, channel, yaml_content, version_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                ON CONFLICT (id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    description = EXCLUDED.description,
                    version = EXCLUDED.version,
                    status = EXCLUDED.status,
                    yaml_path = EXCLUDED.yaml_path,
                    tags = EXCLUDED.tags,
                    yaml_content = EXCLUDED.yaml_content,
                    updated_at = NOW()
                """,
                (
                    graph_id,
                    org_id,
                    domain_id,
                    name,
                    display_name,
                    description,
                    version_label,
                    status,
                    environment,
                    yaml_path,
                    is_system_agent,
                    system_tier,
                    created_by,
                    tags,
                    graph_type,
                    channel,
                    yaml_content,
                ),
            )

        # Create version record
        version_id = str(uuid.uuid4())
        cur.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 as next_version FROM agent_versions WHERE agent_id = %s",
            (graph_id,),
        )
        next_version = cur.fetchone()["next_version"]

        cur.execute(
            """
            INSERT INTO agent_versions (
                id, agent_id, version_number, version_label, yaml_content,
                reactflow_data, change_summary, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id,
                graph_id,
                next_version,
                version_label,
                yaml_content,
                json.dumps(reactflow_data),
                change_summary or f"Version {next_version}",
                created_by,
            ),
        )

        # Update agent with latest version info
        cur.execute(
            """
            UPDATE agents
            SET latest_version_id = %s,
                version_count = %s
            WHERE id = %s
            """,
            (version_id, next_version, graph_id),
        )

        # Sync entry point triggers
        nodes = graph_spec.get("nodes", [])

        entry_points_with_triggers = [
            (node["id"], node["data"].get("trigger_id"))
            for node in nodes
            if node.get("type") == "entryPoint" and node.get("data", {}).get("trigger_id")
        ]

        if entry_points_with_triggers:
            cur.execute("DELETE FROM graph_triggers WHERE target_type = 'agent' AND target_id = %s", (graph_id,))
            for node_id, trigger_id in entry_points_with_triggers:
                cur.execute(
                    """
                    INSERT INTO graph_triggers (target_type, target_id, trigger_id, start_node_id)
                    VALUES ('agent', %s, %s, %s)
                    """,
                    (graph_id, trigger_id, node_id),
                )

        conn.commit()

    logger.info(f"Saved agent '{name}' ({graph_id}) - version {next_version}")
    return get_graph(graph_id)


def delete_graph(graph_id: str) -> None:
    """
    Delete a graph from database and file system.
    Cleans up:
    - Structured YAML path (from yaml_path column)
    - Deployment artifacts ({uuid}.agent.yaml, {sanitized_uuid}.py)
    - Agent versions from database
    """
    from pathlib import Path

    from backend.utils import yaml_storage

    graph = get_graph(graph_id)
    if not graph:
        return

    # 1. Delete structured YAML file (from yaml_path column)
    if graph.get("yaml_path"):
        try:
            yaml_storage.delete_graph_yaml(graph["yaml_path"])
        except Exception as e:
            logger.warning(f"Could not delete structured YAML file: {e}")

    # 2. Delete deployment artifacts (UUID-based files in agents root)
    agents_dir = Path(__file__).parent.parent / "agents"

    # Delete {uuid}.agent.yaml
    deployment_yaml = agents_dir / f"{graph_id}.agent.yaml"
    if deployment_yaml.exists():
        try:
            deployment_yaml.unlink()
            logger.info(f"Deleted deployment YAML: {deployment_yaml}")
        except Exception as e:
            logger.warning(f"Could not delete deployment YAML: {e}")

    # Delete {sanitized_uuid}.py (underscores instead of hyphens)
    sanitized_id = graph_id.replace("-", "_")
    deployment_py = agents_dir / f"{sanitized_id}.py"
    if deployment_py.exists():
        try:
            deployment_py.unlink()
            logger.info(f"Deleted deployment Python: {deployment_py}")
        except Exception as e:
            logger.warning(f"Could not delete deployment Python: {e}")

    # 3. Delete agent versions from database
    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        # Delete versions first (foreign key constraint)
        cur.execute("DELETE FROM agent_versions WHERE agent_id = %s", (graph_id,))
        # Delete the agent
        cur.execute("DELETE FROM agents WHERE id = %s", (graph_id,))
        conn.commit()

    logger.info(f"Deleted graph and all artifacts: {graph_id}")


# ============================================================================
# GENERIC POSTGRES ADMIN HELPERS
# ============================================================================

TABLE_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def _sanitize_table_name(table_name: str) -> str:
    if not TABLE_PATTERN.match(table_name):
        raise ValueError("Invalid table name")
    return table_name


def list_tables() -> list[dict[str, Any]]:
    """List all tables with row counts (admin function)."""
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT tablename as name
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        rows = cur.fetchall()

        tables = []
        for row in rows:
            name = row["name"]
            cur.execute(f'SELECT COUNT(*) as count FROM "{name}"')
            count = cur.fetchone()["count"]
            tables.append({"name": name, "row_count": count})

        conn.commit()
    return tables


def get_table_schema(table_name: str) -> list[dict[str, Any]]:
    """Get table schema (column info)."""
    table = _sanitize_table_name(table_name)
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            """
            SELECT column_name as name, data_type as type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        schema = [dict(row) for row in cur.fetchall()]
        conn.commit()
    return schema


def get_table_rows(table_name: str, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """Get rows from a table (admin function)."""
    table = _sanitize_table_name(table_name)
    with get_connection_no_rls() as conn:
        cur = conn.cursor(cursor_factory=DictCursor)
        cur.execute(
            f'SELECT * FROM "{table}" LIMIT %s OFFSET %s',
            (limit, offset),
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.commit()
    return rows


def insert_table_row(table_name: str, data: dict[str, Any]) -> str:
    """Insert a row into a table (admin function)."""
    if not data:
        raise ValueError("No data provided for insert")

    table = _sanitize_table_name(table_name)
    valid_columns = {col["name"] for col in get_table_schema(table)}
    columns = [col for col in data if col in valid_columns]

    if not columns:
        raise ValueError("No valid columns provided")

    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join([f'"{col}"' for col in columns])
    values = [data[col] for col in columns]

    # Add ID if not provided
    if "id" not in data:
        new_id = str(uuid.uuid4())
        columns.insert(0, "id")
        values.insert(0, new_id)
        column_sql = '"id", ' + column_sql
        placeholders = "%s, " + placeholders
    else:
        new_id = data["id"]

    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute(
            f'INSERT INTO "{table}" ({column_sql}) VALUES ({placeholders})',
            values,
        )
        conn.commit()

    return new_id


def update_table_row(table_name: str, row_id: str, data: dict[str, Any]) -> None:
    """Update a row in a table (admin function)."""
    if not data:
        raise ValueError("No data provided for update")

    table = _sanitize_table_name(table_name)
    valid_columns = {col["name"] for col in get_table_schema(table)}
    set_clauses = []
    values = []

    for column, value in data.items():
        if column not in valid_columns or column == "id":
            continue
        set_clauses.append(f'"{column}" = %s')
        values.append(value)

    if not set_clauses:
        raise ValueError("No valid columns provided for update")

    values.append(row_id)

    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute(
            f'UPDATE "{table}" SET {", ".join(set_clauses)} WHERE id = %s',
            values,
        )
        conn.commit()


def delete_table_row(table_name: str, row_id: str) -> None:
    """Delete a row from a table (admin function)."""
    table = _sanitize_table_name(table_name)
    with get_connection_no_rls() as conn:
        cur = conn.cursor()
        cur.execute(f'DELETE FROM "{table}" WHERE id = %s', (row_id,))
        conn.commit()


# Backward compatibility aliases
list_sqlite_tables = list_tables
