"""
Forge Service - Agent Configuration API
FastAPI service for managing agent graphs, YAML files, and deployments
Port: 8003
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import yaml
import os
import shutil
from pathlib import Path

# Initialize FastAPI
app = FastAPI(
    title="Forge Service",
    description="Agent Configuration and Management API",
    version="0.9.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
AGENTS_DIR = Path("../agents")  # Agent YAML files
FORGE_DATA_DIR = Path("../data/forge")  # Forge-specific data
FORGE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ==================== Models ====================

class GraphNode(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any]

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    label: Optional[str] = None
    animated: bool = True

class AgentGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class CreateAgentRequest(BaseModel):
    name: str = Field(..., description="Agent name (must be unique)")
    graph: AgentGraph
    environment: str = Field(default="dev", description="Environment: dev, staging, prod")
    description: Optional[str] = None

class UpdateAgentRequest(BaseModel):
    graph: Optional[AgentGraph] = None
    description: Optional[str] = None

class DeployAgentRequest(BaseModel):
    environment: str = Field(..., description="Target environment: dev, staging, prod")
    git_commit: bool = Field(default=False, description="Commit to Git after deploy")

class AgentMetadata(BaseModel):
    id: str
    name: str
    environment: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    node_count: int
    edge_count: int
    status: str = "draft"  # draft, deployed, error

class DeploymentRecord(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    environment: str
    status: str  # pending, running, success, failed
    deployed_by: str = "system"
    deployed_at: datetime
    git_commit_sha: Optional[str] = None
    error_message: Optional[str] = None

# ==================== Helper Functions ====================

def graph_to_yaml_dict(graph: AgentGraph, agent_name: str) -> Dict[str, Any]:
    """Convert graph to YAML-compatible dict"""
    return {
        "apiVersion": "foundry.ai/v1",
        "kind": "Agent",
        "metadata": {
            "name": agent_name,
            "labels": {
                "app": "agent-foundry",
                "tier": "worker",
            }
        },
        "spec": {
            "graph": {
                "nodes": [
                    {
                        "id": node.id,
                        "type": node.type,
                        **node.data
                    }
                    for node in graph.nodes
                ],
                "edges": [
                    {
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "sourceHandle": edge.sourceHandle,
                        "targetHandle": edge.targetHandle,
                        "label": edge.label,
                    }
                    for edge in graph.edges
                ]
            },
            "state_schema": {
                "messages": "list",
                "context": "dict",
                "current_node": "string",
            }
        }
    }

def save_agent_yaml(agent_name: str, yaml_dict: Dict[str, Any], environment: str) -> str:
    """Save agent YAML to file"""
    # Determine filename
    if environment == "prod":
        filename = f"{agent_name}.agent.yaml"
    else:
        filename = f"{agent_name}.{environment}.agent.yaml"

    filepath = AGENTS_DIR / filename

    # Write YAML
    with open(filepath, 'w') as f:
        yaml.dump(yaml_dict, f, default_flow_style=False, sort_keys=False)

    return str(filepath)

def load_agent_metadata() -> Dict[str, AgentMetadata]:
    """Load metadata for all agents from filesystem"""
    metadata = {}

    if not AGENTS_DIR.exists():
        return metadata

    for yaml_file in AGENTS_DIR.glob("*.agent.yaml"):
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            agent_name = data.get("metadata", {}).get("name", yaml_file.stem)

            # Determine environment from filename
            if ".dev." in yaml_file.name:
                environment = "dev"
            elif ".staging." in yaml_file.name:
                environment = "staging"
            else:
                environment = "prod"

            # Get file stats
            stats = yaml_file.stat()

            metadata[agent_name] = AgentMetadata(
                id=agent_name,
                name=agent_name,
                environment=environment,
                description=data.get("metadata", {}).get("description"),
                created_at=datetime.fromtimestamp(stats.st_ctime),
                updated_at=datetime.fromtimestamp(stats.st_mtime),
                node_count=len(data.get("spec", {}).get("graph", {}).get("nodes", [])),
                edge_count=len(data.get("spec", {}).get("graph", {}).get("edges", [])),
                status="deployed" if environment == "prod" else "draft",
            )
        except Exception as e:
            print(f"Error loading {yaml_file}: {e}")
            continue

    return metadata

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "forge-service",
        "version": "0.9.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

# ==================== Agent CRUD Endpoints ====================

@app.post("/api/forge/agents", response_model=AgentMetadata)
async def create_agent(request: CreateAgentRequest):
    """Create a new agent from graph"""
    try:
        # Check if agent already exists
        metadata = load_agent_metadata()
        if request.name in metadata:
            raise HTTPException(status_code=409, detail=f"Agent '{request.name}' already exists")

        # Convert graph to YAML
        yaml_dict = graph_to_yaml_dict(request.graph, request.name)
        if request.description:
            yaml_dict["metadata"]["description"] = request.description

        # Save to file
        filepath = save_agent_yaml(request.name, yaml_dict, request.environment)

        # Return metadata
        return AgentMetadata(
            id=request.name,
            name=request.name,
            environment=request.environment,
            description=request.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            node_count=len(request.graph.nodes),
            edge_count=len(request.graph.edges),
            status="draft",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.get("/api/forge/agents", response_model=List[AgentMetadata])
async def list_agents():
    """List all agents"""
    try:
        metadata = load_agent_metadata()
        return list(metadata.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.get("/api/forge/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get agent details including graph"""
    try:
        # Find agent file
        yaml_files = list(AGENTS_DIR.glob(f"{agent_name}*.agent.yaml"))
        if not yaml_files:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # Load YAML
        with open(yaml_files[0], 'r') as f:
            data = yaml.safe_load(f)

        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@app.put("/api/forge/agents/{agent_name}")
async def update_agent(agent_name: str, request: UpdateAgentRequest):
    """Update existing agent"""
    try:
        # Find agent file
        yaml_files = list(AGENTS_DIR.glob(f"{agent_name}*.agent.yaml"))
        if not yaml_files:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # Load existing YAML
        with open(yaml_files[0], 'r') as f:
            data = yaml.safe_load(f)

        # Update graph if provided
        if request.graph:
            data["spec"]["graph"] = {
                "nodes": [{"id": n.id, "type": n.type, **n.data} for n in request.graph.nodes],
                "edges": [
                    {
                        "id": e.id,
                        "source": e.source,
                        "target": e.target,
                        "sourceHandle": e.sourceHandle,
                        "targetHandle": e.targetHandle,
                        "label": e.label,
                    }
                    for e in request.graph.edges
                ]
            }

        # Update description if provided
        if request.description:
            data["metadata"]["description"] = request.description

        # Save updated YAML
        with open(yaml_files[0], 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return {"message": f"Agent '{agent_name}' updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update agent: {str(e)}")

@app.delete("/api/forge/agents/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent"""
    try:
        # Find and delete agent files
        yaml_files = list(AGENTS_DIR.glob(f"{agent_name}*.agent.yaml"))
        if not yaml_files:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        for filepath in yaml_files:
            filepath.unlink()

        return {"message": f"Agent '{agent_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

# ==================== Deployment Endpoints ====================

@app.post("/api/forge/agents/{agent_name}/deploy", response_model=DeploymentRecord)
async def deploy_agent(agent_name: str, request: DeployAgentRequest):
    """Deploy agent to environment"""
    try:
        # Find agent file
        yaml_files = list(AGENTS_DIR.glob(f"{agent_name}*.agent.yaml"))
        if not yaml_files:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")

        # Load YAML
        with open(yaml_files[0], 'r') as f:
            data = yaml.safe_load(f)

        # Create deployment-specific YAML
        target_filename = f"{agent_name}.{request.environment}.agent.yaml"
        target_path = AGENTS_DIR / target_filename

        with open(target_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        # TODO: Trigger actual deployment (notify Marshal agent, hot-reload, etc.)

        # Create deployment record
        deployment_id = str(uuid.uuid4())
        deployment = DeploymentRecord(
            id=deployment_id,
            agent_id=agent_name,
            agent_name=agent_name,
            environment=request.environment,
            status="success",
            deployed_by="system",
            deployed_at=datetime.utcnow(),
            git_commit_sha=None if not request.git_commit else "pending",
        )

        # TODO: If git_commit is True, commit to Git via MCP

        return deployment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy agent: {str(e)}")

# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
