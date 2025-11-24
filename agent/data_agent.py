"""
Data Agent - LangGraph-based agent for persistent data access (PostgreSQL + RLS).

Responsibilities:
- Provide a natural-language interface for querying control-plane data
  (organizations, domains, instances, deployments)
- Translate NL queries into safe, parameterized SQL
- Execute SQL with Row-Level Security (RLS) for tenant isolation

SECURITY: RLS ensures queries only return data for the current tenant,
even if the AI generates queries without tenant filters.

NOTE: For safety, the first version focuses on read-only SELECT queries.
"""

from __future__ import annotations

from typing import TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import END, START, StateGraph

from backend.context import get_tenant_id
from backend.db_postgres import DictCursor, get_connection


class DataAgentState(TypedDict, total=False):
    """State for the DataAgent LangGraph."""

    question: str
    tenant_id: str | None  # Tenant context for RLS
    sql: str
    rows: list[dict]
    error: str


SCHEMA_DOC = """
You are a SQL generation assistant for Agent Foundry.

Database schema (PostgreSQL with Row-Level Security):

organizations(id TEXT PRIMARY KEY, name TEXT, tier TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ)

domains(
  id TEXT PRIMARY KEY,
  organization_id TEXT REFERENCES organizations(id),
  name TEXT,
  display_name TEXT,
  version TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

instances(
  id TEXT PRIMARY KEY,
  organization_id TEXT REFERENCES organizations(id),
  domain_id TEXT REFERENCES domains(id),
  environment TEXT,
  instance_id TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

users(
  id TEXT PRIMARY KEY,
  organization_id TEXT REFERENCES organizations(id),
  email TEXT UNIQUE,
  name TEXT,
  role TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

agents(
  id TEXT PRIMARY KEY,
  organization_id TEXT REFERENCES organizations(id),
  domain_id TEXT REFERENCES domains(id),
  name TEXT,
  display_name TEXT,
  description TEXT,
  version TEXT,
  status TEXT,
  environment TEXT,
  yaml_path TEXT,
  is_system_agent BOOLEAN,
  system_tier INTEGER,
  created_by TEXT,
  tags JSONB,
  graph_type TEXT,
  channel TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
)

deployments(
  id TEXT PRIMARY KEY,
  instance_id TEXT REFERENCES instances(id),
  agent_id TEXT,
  version TEXT,
  status TEXT,
  created_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  deployed_by TEXT,
  git_commit_sha TEXT,
  error_message TEXT
)

sessions(
  id TEXT PRIMARY KEY,
  organization_id TEXT REFERENCES organizations(id),
  user_id TEXT REFERENCES users(id),
  agent_id TEXT REFERENCES agents(id),
  session_type TEXT,
  status TEXT,
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ
)

IMPORTANT SECURITY NOTE:
- Row-Level Security (RLS) is enabled on all tenant-scoped tables.
- Queries automatically filter by the current tenant context.
- You do NOT need to add organization_id filters - RLS handles this.
- System agents (is_system_agent = TRUE) are visible to all tenants.

Rules:
- Generate ONLY a single SQL SELECT statement.
- Never modify data (no INSERT/UPDATE/DELETE).
- Always include a LIMIT 100 clause.
- Prefer explicit column lists over SELECT * where reasonable.
- Use PostgreSQL syntax (not SQLite).
- Timestamps are TIMESTAMPTZ fields.
- Booleans are BOOLEAN (not INTEGER).
- JSONB fields can be queried with ->> operator.
"""


class DataAgent:
    """LangGraph agent that answers NL questions via SQL over the control-plane DB.

    Uses PostgreSQL with Row-Level Security (RLS) for automatic tenant isolation.
    """

    def __init__(self) -> None:
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            temperature=0,
            max_tokens=512,
        )

        builder = StateGraph(DataAgentState)
        builder.add_node("generate_sql", self._generate_sql)
        builder.add_node("execute_sql", self._execute_sql)

        builder.add_edge(START, "generate_sql")
        builder.add_edge("generate_sql", "execute_sql")
        builder.add_edge("execute_sql", END)

        self.graph = builder.compile()

    async def query(self, question: str, tenant_id: str | None = None) -> DataAgentState:
        """High-level entrypoint: answer a question using NL -> SQL -> rows.

        Args:
            question: Natural language question about the data
            tenant_id: Optional tenant context override. If not provided,
                       uses the current request context.

        Returns:
            DataAgentState with question, sql, rows (or error)
        """
        # Get tenant context - from parameter or from request context
        effective_tenant = tenant_id or get_tenant_id()

        state: DataAgentState = {
            "question": question,
            "tenant_id": effective_tenant,
        }
        return await self.graph.ainvoke(state)

    # LangGraph nodes ---------------------------------------------------------

    async def _generate_sql(self, state: DataAgentState) -> DataAgentState:
        """Use LLM to generate a safe SELECT SQL query."""
        try:
            prompt = (
                SCHEMA_DOC + "\n\nUser question:\n" + state["question"] + "\n\nReturn ONLY the SQL query, nothing else."
            )
            resp = await self.llm.ainvoke(prompt)
            sql = resp.content.strip()

            # Remove markdown code blocks if present
            if sql.startswith("```"):
                lines = sql.split("\n")
                sql = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                sql = sql.strip()

            # Basic safety checks
            lowered = sql.lower()
            dangerous_keywords = [
                "insert ",
                "update ",
                "delete ",
                "drop ",
                "alter ",
                "truncate ",
                "create ",
                "grant ",
                "revoke ",
                "set ",
            ]
            if any(keyword in lowered for keyword in dangerous_keywords):
                raise ValueError(f"Unsafe SQL generated: {sql}")
            if "select" not in lowered:
                raise ValueError(f"No SELECT found in SQL: {sql}")

            state["sql"] = sql
        except Exception as e:
            state["error"] = f"SQL generation failed: {e}"
        return state

    def _execute_sql(self, state: DataAgentState) -> DataAgentState:
        """Execute SELECT SQL with RLS context and return rows as dicts.

        RLS automatically filters results to the current tenant.
        Even if the AI-generated query doesn't include tenant filters,
        PostgreSQL RLS policies ensure data isolation.
        """
        if state.get("error"):
            return state

        try:
            # Get tenant from state (set during query() call)
            tenant_id = state.get("tenant_id")

            # Use RLS-aware connection with tenant context
            with get_connection(tenant_id) as conn:
                cur = conn.cursor(cursor_factory=DictCursor)
                cur.execute(state["sql"])
                rows = [dict(row) for row in cur.fetchall()]
                conn.commit()

            state["rows"] = rows

        except Exception as e:
            state["error"] = f"SQL execution failed: {e}"

        return state


# Convenience function for direct queries
async def query_data(question: str, tenant_id: str | None = None) -> DataAgentState:
    """Query the control-plane database using natural language.

    Args:
        question: Natural language question
        tenant_id: Optional tenant context for RLS

    Returns:
        DataAgentState with rows or error
    """
    agent = DataAgent()
    return await agent.query(question, tenant_id)
