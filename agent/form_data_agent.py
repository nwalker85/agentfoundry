"""
Form Data Agent - LangGraph-based agent for populating UI fields
based on org/domain/environment/instance context.

This agent is intended to be used via WebSockets (or HTTP) to
provide dynamic options for dropdowns, defaults, etc.
"""

from __future__ import annotations

from typing import TypedDict, Optional, List, Any

from langgraph.graph import StateGraph, START, END

from .data_agent import DataAgent


class FormDataState(TypedDict, total=False):
    # Inputs
    org_id: str
    domain_id: str
    environment: str
    instance_id: str
    field_id: str  # e.g. "instances_for_org_domain"

    # Internal
    question: str
    sql: str

    # Outputs
    result: Any
    error: Optional[str]


class FormDataAgent:
    """Agent that uses DataAgent to populate UI field data."""

    def __init__(self) -> None:
        self.data_agent = DataAgent()

        builder = StateGraph(FormDataState)
        builder.add_node("prepare_question", self._prepare_question)
        builder.add_node("run_data_agent", self._run_data_agent)

        builder.add_edge(START, "prepare_question")
        builder.add_edge("prepare_question", "run_data_agent")
        builder.add_edge("run_data_agent", END)

        self.graph = builder.compile()

    async def populate_fields(
        self,
        *,
        org_id: str,
        domain_id: str,
        environment: str,
        instance_id: str,
        field_id: str,
    ) -> FormDataState:
        """Populate data for a specific field based on context."""
        state: FormDataState = {
            "org_id": org_id,
            "domain_id": domain_id,
            "environment": environment,
            "instance_id": instance_id,
            "field_id": field_id,
        }
        return await self.graph.ainvoke(state)

    # --------------------------------------------------------------------- #
    # Nodes
    # --------------------------------------------------------------------- #

    def _prepare_question(self, state: FormDataState) -> FormDataState:
        """Turn the field_id + context into a natural-language question."""
        field_id = state["field_id"]

        if field_id == "instances_for_org_domain":
            state["question"] = (
                "Return up to 100 rows from the instances table with columns "
                "id, organization_id, domain_id, environment, instance_id, created_at "
                f"where organization_id = '{state['org_id']}' "
                f"and domain_id = '{state['domain_id']}' "
                f"and environment = '{state['environment']}' "
                "ordered by created_at DESC."
            )
        elif field_id == "deployments_for_instance":
            state["question"] = (
                "Return up to 100 rows from the deployments table with columns "
                "id, instance_id, agent_id, version, status, created_at, completed_at "
                f"where instance_id = '{state['instance_id']}' "
                "ordered by created_at DESC."
            )
        else:
            state["error"] = f"Unknown field_id: {field_id}"

        return state

    async def _run_data_agent(self, state: FormDataState) -> FormDataState:
        """Delegate to DataAgent to generate SQL and fetch rows."""
        if state.get("error"):
            return state

        try:
            data_state = await self.data_agent.query(state["question"])
            if data_state.get("error"):
                state["error"] = data_state["error"]
                state["sql"] = data_state.get("sql", "")
            else:
                state["sql"] = data_state.get("sql", "")
                state["result"] = {
                    "field_id": state["field_id"],
                    "rows": data_state.get("rows", []),
                }
        except Exception as e:
            state["error"] = f"FormDataAgent failed: {e}"

        return state


