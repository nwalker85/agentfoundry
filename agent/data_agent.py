"""
Data Agent - LangGraph-based agent for persistent data access.

Responsibilities:
- Provide a natural-language interface for querying control-plane data
  (organizations, domains, instances, deployments)
- Translate NL queries into safe, parameterized SQL
- Execute SQL against PostgreSQL and return structured results

NOTE: For safety, the first version focuses on read-only SELECT queries.
"""

from __future__ import annotations

import os
from typing import TypedDict, Annotated, Any, List

import psycopg
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END

from backend.db import DB_URL


class DataAgentState(TypedDict, total=False):
    """State for the DataAgent LangGraph."""

    question: str
    sql: str
    rows: List[dict]
    error: str


SCHEMA_DOC = """
You are a SQL generation assistant for Agent Foundry.

Database schema (PostgreSQL):

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
);

Rules:
- Generate ONLY a single SQL SELECT statement.
- Never modify data (no INSERT/UPDATE/DELETE).
- Always include a LIMIT 100 clause.
- Prefer explicit column lists over SELECT * where reasonable.
"""


class DataAgent:
    """LangGraph agent that answers NL questions via SQL over the control-plane DB."""

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

    async def query(self, question: str) -> DataAgentState:
        """High-level entrypoint: answer a question using NL → SQL → rows."""
        state: DataAgentState = {"question": question}
        return await self.graph.ainvoke(state)

    # LangGraph nodes ---------------------------------------------------------

    async def _generate_sql(self, state: DataAgentState) -> DataAgentState:
        """Use LLM to generate a safe SELECT SQL query."""
        try:
            prompt = (
                SCHEMA_DOC
                + "\n\nUser question:\n"
                + state["question"]
                + "\n\nReturn ONLY the SQL query, nothing else."
            )
            resp = await self.llm.ainvoke(prompt)
            sql = resp.content.strip()

            # Basic safety checks
            lowered = sql.lower()
            if any(keyword in lowered for keyword in ["insert ", "update ", "delete ", "drop ", "alter ", "truncate "]):
                raise ValueError(f"Unsafe SQL generated: {sql}")
            if "select" not in lowered:
                raise ValueError(f"No SELECT found in SQL: {sql}")

            state["sql"] = sql
        except Exception as e:
            state["error"] = f"SQL generation failed: {e}"
        return state

    def _execute_sql(self, state: DataAgentState) -> DataAgentState:
        """Execute SELECT SQL and return rows as dicts."""
        if state.get("error"):
            return state
        try:
            with psycopg.connect(DB_URL, row_factory=psycopg.rows.dict_row) as conn:
                with conn.cursor() as cur:
                    cur.execute(state["sql"])
                    rows = cur.fetchall()
            state["rows"] = rows
        except Exception as e:
            state["error"] = f"SQL execution failed: {e}"
        return state


