"""
Manifest Agent - LangGraph-based agent for managing agent manifests.

Responsibilities (control plane):
- Create/update agent YAML specs on disk
- Create/update manifest entries binding agents to org/domain/environment/instance
- Perform basic validation and health checks on manifests

This agent is intended to run in the Foundry backend (MCP server) and can be
exposed via MCP tools or HTTP endpoints.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, TypedDict

import yaml
from langgraph.graph import END, START, StateGraph

AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
MANIFEST_DIR = os.path.join(AGENTS_DIR, "manifests")


class ManifestState(TypedDict, total=False):
    """
    State for the ManifestAgent LangGraph.

    This is intentionally simple: we treat all fields as "replace" semantics.
    """

    # Input parameters
    operation: str  # "create_or_update_agent_binding"
    agent_id: str
    agent_yaml: str
    yaml_path: str
    organization_id: str
    organization_name: str
    domain_id: str
    domain_name: str
    environment: str  # "dev" | "staging" | "prod"
    instance_id: str
    author: str
    last_editor: str
    tags: list[str]
    is_system_agent: bool
    system_tier: int | None

    # Internal fields
    manifest_path: str
    manifest: dict[str, Any]

    # Outputs
    result: dict[str, Any]
    error: str | None


@dataclass
class ManifestAgent:
    """
    LangGraph-based agent for manifest management.
    """

    agents_dir: str = AGENTS_DIR
    manifest_dir: str = MANIFEST_DIR

    def __post_init__(self) -> None:
        builder = StateGraph(ManifestState)

        builder.add_node("prepare_paths", self._prepare_paths)
        builder.add_node("load_manifest", self._load_manifest)
        builder.add_node("write_agent_yaml", self._write_agent_yaml)
        builder.add_node("update_manifest", self._update_manifest)

        builder.add_edge(START, "prepare_paths")
        builder.add_edge("prepare_paths", "load_manifest")
        builder.add_edge("load_manifest", "write_agent_yaml")
        builder.add_edge("write_agent_yaml", "update_manifest")
        builder.add_edge("update_manifest", END)

        self.graph = builder.compile()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def create_or_update_agent_binding(
        self,
        *,
        agent_id: str,
        agent_yaml: str,
        yaml_path: str | None,
        organization_id: str,
        organization_name: str,
        domain_id: str,
        domain_name: str,
        environment: str,
        instance_id: str,
        author: str,
        last_editor: str | None = None,
        tags: list[str] | None = None,
        is_system_agent: bool = False,
        system_tier: int | None = None,
    ) -> dict[str, Any]:
        """
        High-level entrypoint: create or update an agent YAML + manifest entry.

        This is what Forge (or an MCP tool) would call.
        """
        last_editor = last_editor or author

        state: ManifestState = {
            "operation": "create_or_update_agent_binding",
            "agent_id": agent_id,
            "agent_yaml": agent_yaml,
            "yaml_path": yaml_path or f"{environment}_{agent_id}.yaml",
            "organization_id": organization_id,
            "organization_name": organization_name,
            "domain_id": domain_id,
            "domain_name": domain_name,
            "environment": environment,
            "instance_id": instance_id,
            "author": author,
            "last_editor": last_editor,
            "tags": tags or [],
            "is_system_agent": is_system_agent,
            "system_tier": system_tier,
        }

        result_state = await self.graph.ainvoke(state)
        if result_state.get("error"):
            raise RuntimeError(result_state["error"])
        return result_state.get("result", {})

    # -------------------------------------------------------------------------
    # LangGraph node implementations
    # -------------------------------------------------------------------------

    def _prepare_paths(self, state: ManifestState) -> ManifestState:
        """Resolve manifest path and ensure directories exist."""
        env = state["environment"]
        manifest_path = os.path.join(self.manifest_dir, f"manifest.{env}.yaml")
        os.makedirs(self.manifest_dir, exist_ok=True)
        os.makedirs(self.agents_dir, exist_ok=True)
        state["manifest_path"] = manifest_path
        return state

    def _load_manifest(self, state: ManifestState) -> ManifestState:
        """Load the environment manifest, or initialize an empty one."""
        manifest_path = state["manifest_path"]
        if os.path.exists(manifest_path):
            with open(manifest_path, encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
        else:
            manifest = {
                "apiVersion": "agent-foundry/v1",
                "kind": "AgentManifest",
                "metadata": {
                    "description": f"Environment manifest for {state['environment']}",
                    "generated_at": "",
                    "version": "0.1.0",
                },
                "spec": {"entries": []},
            }
        if "spec" not in manifest:
            manifest["spec"] = {"entries": []}
        if "entries" not in manifest["spec"]:
            manifest["spec"]["entries"] = []
        state["manifest"] = manifest
        return state

    def _write_agent_yaml(self, state: ManifestState) -> ManifestState:
        """Write the agent YAML spec to disk."""
        yaml_path = state["yaml_path"]
        full_path = os.path.join(self.agents_dir, yaml_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        try:
            # Validate YAML parses
            parsed = yaml.safe_load(state["agent_yaml"]) or {}
            # Ensure metadata.id matches agent_id
            metadata = parsed.setdefault("metadata", {})
            metadata.setdefault("id", state["agent_id"])
            metadata.setdefault("name", state["agent_id"])

            with open(full_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(parsed, f, sort_keys=False)
        except Exception as e:
            state["error"] = f"Failed to write agent YAML: {e}"
        return state

    def _update_manifest(self, state: ManifestState) -> ManifestState:
        """Upsert an entry in the manifest for this agent/org/domain/instance."""
        if state.get("error"):
            return state

        manifest = state["manifest"]
        entries: list[dict[str, Any]] = manifest["spec"]["entries"]

        # Upsert by (agent_id, org, domain, instance, env)
        updated = False
        for entry in entries:
            if (
                entry.get("agent_id") == state["agent_id"]
                and entry.get("organization_id") == state["organization_id"]
                and entry.get("domain_id") == state["domain_id"]
                and entry.get("environment") == state["environment"]
                and entry.get("instance_id") == state["instance_id"]
            ):
                entry.update(
                    {
                        "yaml_path": state["yaml_path"],
                        "organization_name": state["organization_name"],
                        "domain_name": state["domain_name"],
                        "is_system_agent": state["is_system_agent"],
                        "system_tier": state["system_tier"],
                        "version": entry.get("version") or "0.1.0",
                        "author": state["author"],
                        "last_editor": state["last_editor"],
                        "tags": state["tags"],
                    }
                )
                updated = True
                break

        if not updated:
            entries.append(
                {
                    "agent_id": state["agent_id"],
                    "yaml_path": state["yaml_path"],
                    "organization_id": state["organization_id"],
                    "organization_name": state["organization_name"],
                    "domain_id": state["domain_id"],
                    "domain_name": state["domain_name"],
                    "environment": state["environment"],
                    "instance_id": state["instance_id"],
                    "is_system_agent": state["is_system_agent"],
                    "system_tier": state["system_tier"],
                    "version": "0.1.0",
                    "author": state["author"],
                    "last_editor": state["last_editor"],
                    "tags": state["tags"],
                }
            )

        # Persist manifest
        try:
            with open(state["manifest_path"], "w", encoding="utf-8") as f:
                yaml.safe_dump(manifest, f, sort_keys=False)
        except Exception as e:
            state["error"] = f"Failed to write manifest: {e}"
            return state

        state["result"] = {
            "agent_id": state["agent_id"],
            "yaml_path": state["yaml_path"],
            "manifest_path": state["manifest_path"],
            "organization_id": state["organization_id"],
            "domain_id": state["domain_id"],
            "environment": state["environment"],
            "instance_id": state["instance_id"],
        }
        return state
