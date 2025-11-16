"""
Object Admin Agent - LangGraph-based control-plane admin for core objects.

Objects:
- organizations
- domains
- instances
- users

This agent provides typed list/get operations (and is easy to extend to create/update).
"""

from __future__ import annotations

from typing import TypedDict, Literal, Any, List, Optional

import psycopg
from langgraph.graph import StateGraph, START, END

from backend.db import DB_URL


ObjectType = Literal["organization", "domain", "instance", "user"]
OperationType = Literal["list", "get"]


class ObjectAdminState(TypedDict, total=False):
    # Inputs
    object_type: ObjectType
    operation: OperationType
    id: Optional[str]
    organization_id: Optional[str]
    domain_id: Optional[str]
    environment: Optional[str]

    # Outputs
    result: Any
    error: Optional[str]


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

    def _list_objects(self, state: ObjectAdminState) -> List[dict]:
        """List objects by type and optional filters."""
        obj = state["object_type"]
        with psycopg.connect(DB_URL, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
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
                    cur.execute(
                        f"""
                        SELECT id, organization_id, domain_id, environment, instance_id, created_at, updated_at
                        FROM instances
                        {where_clause}
                        ORDER BY created_at DESC
                        LIMIT 200
                        """,
                        tuple(params) if params else None,
                    )
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

                rows = cur.fetchall()
                return rows

    def _get_object(self, state: ObjectAdminState) -> Optional[dict]:
        """Get a single object by id."""
        obj = state["object_type"]
        with psycopg.connect(DB_URL, row_factory=psycopg.rows.dict_row) as conn:
            with conn.cursor() as cur:
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
                return row


