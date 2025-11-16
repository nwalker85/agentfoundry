"""
DIS Compiler - Agent YAML Generator
Transforms DIS 1.6.0 Dossiers into LangGraph Agent YAML manifests
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class CompilerResult(BaseModel):
    """Result of DIS → Agent YAML compilation"""
    agent_yaml: str
    agent_id: str
    warnings: List[str] = []
    errors: List[str] = []
    success: bool = True


class DISCompiler:
    """
    Compiles DIS 1.6.0 Dossiers into Agent YAML manifests.
    
    Input: DIS JSON Dossier (23 construct types)
    Output: LangGraph Agent YAML (pm-agent.agent.yaml format)
    """
    
    def __init__(self, schema_url: str = "https://schemas.domainintelligenceschema.org/dis/1.6.0"):
        self.schema_url = schema_url
        self.warnings = []
        self.errors = []
    
    def compile_dossier(self, dossier_json: Dict[str, Any]) -> CompilerResult:
        """
        Main compilation entry point.
        
        Args:
            dossier_json: Parsed DIS dossier JSON
            
        Returns:
            CompilerResult with generated YAML and any warnings/errors
        """
        try:
            # Extract dossier components
            header = dossier_json.get("header", {})
            definitions = dossier_json.get("dossierSpecificDefinitions", {})
            
            # Build agent manifest
            agent_manifest = self._build_agent_manifest(header, definitions)
            
            # Convert to YAML
            agent_yaml = yaml.dump(agent_manifest, sort_keys=False, default_flow_style=False)
            
            return CompilerResult(
                agent_yaml=agent_yaml,
                agent_id=self._sanitize_id(header.get("dossierId", "unknown")),
                warnings=self.warnings,
                errors=self.errors,
                success=len(self.errors) == 0
            )
            
        except Exception as e:
            self.errors.append(f"Compilation failed: {str(e)}")
            return CompilerResult(
                agent_yaml="",
                agent_id="failed",
                warnings=self.warnings,
                errors=self.errors,
                success=False
            )
    
    def _build_agent_manifest(self, header: Dict, definitions: Dict) -> Dict[str, Any]:
        """Build the agent YAML structure from DIS components"""
        
        # Extract key components
        agent_id = self._sanitize_id(header.get("dossierId", "unknown-agent"))
        triplets = definitions.get("agenticTriplets", [])
        functions = definitions.get("functionCatalogEntries", [])
        triplet_bindings = definitions.get("tripletFunctionMatrixEntries", [])
        entities = definitions.get("entities", [])
        applications = definitions.get("applications", [])
        telemetry = definitions.get("telemetryConfiguration", {})
        
        # Build manifest
        manifest = {
            "apiVersion": "engineering-dept/v1",
            "kind": "Agent",
            "metadata": {
                "id": agent_id,
                "name": header.get("domainName", "Unknown Agent"),
                "version": header.get("version", "1.0.0"),
                "description": header.get("description", "Generated from DIS dossier"),
                "tags": header.get("tags", []) + ["dis-compiled", "langgraph"],
                "created": header.get("versionDate", datetime.utcnow().isoformat()),
                "updated": datetime.utcnow().isoformat()
            },
            "spec": {
                "capabilities": self._extract_capabilities(triplets, entities),
                "parameters": self._extract_parameters(definitions),
                "workflow": self._build_workflow(triplets, functions, triplet_bindings),
                "integrations": self._build_integrations(applications),
                "resource_limits": {
                    "max_concurrent_tasks": 3,
                    "timeout_seconds": 300,
                    "memory_mb": 512,
                    "max_tokens_per_request": 4000
                },
                "observability": self._build_observability(telemetry),
                "health_check": {
                    "enabled": True,
                    "interval_seconds": 60,
                    "timeout_seconds": 5,
                    "unhealthy_threshold": 3
                }
            },
            "status": {
                "phase": "draft",
                "state": "inactive",
                "last_heartbeat": None,
                "uptime_seconds": 0,
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0
            }
        }
        
        return manifest
    
    def _extract_capabilities(self, triplets: List[Dict], entities: List[Dict]) -> List[str]:
        """Extract capability list from triplets and entities"""
        capabilities = set()
        
        # Extract from triplets (mode of interaction)
        for triplet in triplets:
            mode = triplet.get("modeId", "").lower()
            if mode:
                capabilities.add(f"{mode}_operations")
        
        # Extract from entity types
        for entity in entities:
            entity_type = entity.get("entityType", "")
            if entity_type == "agent":
                capabilities.add("agent_operations")
        
        return sorted(list(capabilities))
    
    def _extract_parameters(self, definitions: Dict) -> List[Dict[str, Any]]:
        """Extract agent parameters (currently using defaults)"""
        return [
            {
                "name": "max_iterations",
                "type": "integer",
                "default": 10,
                "min": 1,
                "max": 50,
                "description": "Maximum workflow iterations"
            },
            {
                "name": "llm_model",
                "type": "string",
                "default": "gpt-4",
                "description": "LLM model for agent reasoning"
            },
            {
                "name": "llm_temperature",
                "type": "float",
                "default": 0.3,
                "min": 0.0,
                "max": 2.0,
                "description": "LLM temperature"
            }
        ]
    
    def _build_workflow(
        self, 
        triplets: List[Dict], 
        functions: List[Dict],
        triplet_bindings: List[Dict]
    ) -> Dict[str, Any]:
        """Build LangGraph workflow from triplets and function bindings"""
        
        # Build node map from triplets
        nodes = []
        
        # Start with standard nodes
        nodes.append({
            "id": "understand",
            "handler": "agent.understand_task",
            "description": "Parse and understand input",
            "next": ["execute", "error"],
            "timeout_seconds": 30
        })
        
        # Add nodes for each unique triplet
        for triplet in triplets[:10]:  # Limit to first 10 for MVP
            triplet_id = triplet.get("tripletId", "")
            node_id = self._sanitize_id(triplet_id.replace("tri-", ""))
            
            nodes.append({
                "id": node_id,
                "handler": f"agent.{node_id}",
                "description": triplet.get("narrative", "Triplet operation"),
                "next": ["complete", "error"],
                "timeout_seconds": 60
            })
        
        # Standard terminal nodes
        nodes.append({
            "id": "complete",
            "handler": "agent.complete_task",
            "description": "Finalize operation",
            "next": ["END"],
            "timeout_seconds": 10
        })
        
        nodes.append({
            "id": "error",
            "handler": "agent.handle_error",
            "description": "Handle errors gracefully",
            "next": ["END"],
            "timeout_seconds": 5
        })
        
        return {
            "type": "langgraph.StateGraph",
            "entry_point": "understand",
            "recursion_limit": 100,
            "nodes": nodes
        }
    
    def _build_integrations(self, applications: List[Dict]) -> List[Dict[str, Any]]:
        """Build integration specs from DIS applications"""
        integrations = []
        
        for app in applications:
            app_id = app.get("applicationId", "")
            
            # Map common applications to integration types
            if "notion" in app_id.lower():
                integrations.append({
                    "type": "notion",
                    "required": True,
                    "operations": ["create_page", "read_database", "update_page"]
                })
            elif "github" in app_id.lower():
                integrations.append({
                    "type": "github",
                    "required": False,
                    "operations": ["create_issue", "update_issue"]
                })
        
        # Always include OpenAI
        integrations.append({
            "type": "openai",
            "model": "gpt-4",
            "required": True,
            "operations": ["chat_completion"]
        })
        
        return integrations
    
    def _build_observability(self, telemetry: Dict) -> Dict[str, Any]:
        """Build observability config from DIS telemetry"""
        return {
            "trace_level": "info",
            "metrics_enabled": True,
            "metrics_interval_seconds": 30,
            "log_retention_days": 30,
            "structured_logging": True
        }
    
    def _sanitize_id(self, raw_id: str) -> str:
        """Sanitize ID for YAML (lowercase, hyphens)"""
        return raw_id.lower().replace(" ", "-").replace("_", "-")


# Convenience function
def compile_dis_to_yaml(dossier_path: Path) -> CompilerResult:
    """
    Compile a DIS dossier JSON file to Agent YAML.
    
    Args:
        dossier_path: Path to DIS JSON file
        
    Returns:
        CompilerResult with generated YAML
    """
    with open(dossier_path) as f:
        dossier = json.load(f)
    
    compiler = DISCompiler()
    return compiler.compile_dossier(dossier)
