"""
Object Admin Agent - LangGraph-based control-plane admin for core objects (PostgreSQL Version).

Objects:
- organizations
- domains
- instances
- users

This agent provides typed list/get operations (and is easy to extend to create/update).
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.db_postgres import DictCursor, get_connection_no_rls

ObjectType = Literal["organization", "domain", "instance", "user"]
OperationType = Literal["list", "get"]


class ObjectAdminState(TypedDict, total=False):
    # Inputs
    object_type: ObjectType
    operation: OperationType
    id: str | None
    organization_id: str | None
    domain_id: str | None
    environment: str | None

    # Outputs
    result: Any
    error: str | None


class ObjectAdminAgent:
    """LangGraph admin agent for orgs/domains/instances/users."""

    def __init__(self) -> None:
        builder = StateGraph(ObjectAdminState)
        builder.add_node("dispatch", self._dispatch)
        builder.add_edge(START, "dispatch")
        builder.add_edge("dispatch", END)
        self.graph = builder.compile()

    async def run(self, state: ObjectAdminState) -> ObjectAdminState:
        return await self.graph.ainvoke(state)

    # Node --------------------------------------------------------------------

    def _dispatch(self, state: ObjectAdminState) -> ObjectAdminState:
        try:
            op = state["operation"]
            obj = state["object_type"]
            if op == "list":
                state["result"] = self._list_objects(state)
            elif op == "get":
                if not state.get("id"):
                    raise ValueError("id is required for get")
                state["result"] = self._get_object(state)
            else:
                raise ValueError(f"Unsupported operation: {op}")
        except Exception as e:
            state["error"] = str(e)
        return state

    # Helpers -----------------------------------------------------------------

    def _list_objects(self, state: ObjectAdminState) -> list[dict]:
        """List objects by type and optional filters."""
        obj = state["object_type"]

        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            if obj == "organization":
                cur.execute(
                    """
                    SELECT id, name, tier, created_at, updated_at
                    FROM organizations
                    ORDER BY created_at DESC
                    LIMIT 200
                    """
                )
            elif obj == "domain":
                if state.get("organization_id"):
                    cur.execute(
                        """
                        SELECT id, organization_id, name, display_name, version, created_at, updated_at
                        FROM domains
                        WHERE organization_id = %s
                        ORDER BY created_at DESC
                        LIMIT 200
                        """,
                        (state["organization_id"],),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, organization_id, name, display_name, version, created_at, updated_at
                        FROM domains
                        ORDER BY created_at DESC
                        LIMIT 200
                        """
                    )
            elif obj == "instance":
                params = []
                where = []
                if state.get("organization_id"):
                    where.append("organization_id = %s")
                    params.append(state["organization_id"])
                if state.get("domain_id"):
                    where.append("domain_id = %s")
                    params.append(state["domain_id"])
                if state.get("environment"):
                    where.append("environment = %s")
                    params.append(state["environment"])

                where_clause = "WHERE " + " AND ".join(where) if where else ""
                query = f"""
                    SELECT id, organization_id, domain_id, environment, instance_id, created_at, updated_at
                    FROM instances
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 200
                """

                if params:
                    cur.execute(query, tuple(params))
                else:
                    cur.execute(query)

            elif obj == "user":
                if state.get("organization_id"):
                    cur.execute(
                        """
                        SELECT id, organization_id, email, name, role, created_at, updated_at
                        FROM users
                        WHERE organization_id = %s
                        ORDER BY created_at DESC
                        LIMIT 200
                        """,
                        (state["organization_id"],),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, organization_id, email, name, role, created_at, updated_at
                        FROM users
                        ORDER BY created_at DESC
                        LIMIT 200
                        """
                    )
            else:
                raise ValueError(f"Unsupported object_type: {obj}")

            rows = [dict(row) for row in cur.fetchall()]
            conn.commit()

        return rows

    def _get_object(self, state: ObjectAdminState) -> dict | None:
        """Get a single object by id."""
        obj = state["object_type"]

        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            if obj == "organization":
                cur.execute(
                    """
                    SELECT id, name, tier, created_at, updated_at
                    FROM organizations
                    WHERE id = %s
                    """,
                    (state["id"],),
                )
            elif obj == "domain":
                cur.execute(
                    """
                    SELECT id, organization_id, name, display_name, version, created_at, updated_at
                    FROM domains
                    WHERE id = %s
                    """,
                    (state["id"],),
                )
            elif obj == "instance":
                cur.execute(
                    """
                    SELECT id, organization_id, domain_id, environment, instance_id, created_at, updated_at
                    FROM instances
                    WHERE id = %s
                    """,
                    (state["id"],),
                )
            elif obj == "user":
                cur.execute(
                    """
                    SELECT id, organization_id, email, name, role, created_at, updated_at
                    FROM users
                    WHERE id = %s
                    """,
                    (state["id"],),
                )
            else:
                raise ValueError(f"Unsupported object_type: {obj}")

            row = cur.fetchone()
            conn.commit()

        return dict(row) if row else None
