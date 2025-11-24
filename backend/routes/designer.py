"""
Agent Designer API Routes
Endpoints for the visual agent designer (Forge)
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.converters.react_flow_to_python import reactflow_to_python, validate_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/designer", tags=["designer"])


# ============================================
# Request/Response Models
# ============================================


class NodeData(BaseModel):
    """ReactFlow node data"""

    label: str
    description: str = ""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    maxTokens: int = 1000
    tool: str = ""
    conditions: list[dict[str, Any]] = []


class GraphNode(BaseModel):
    """ReactFlow node"""

    id: str
    type: str
    data: dict[str, Any]
    position: dict[str, float]


class GraphEdge(BaseModel):
    """ReactFlow edge"""

    id: str
    source: str
    target: str
    animated: bool = True


class GeneratePythonRequest(BaseModel):
    """Request to generate Python code from graph"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    agentName: str = Field(default="untitled_agent", description="Name of the agent")


class GeneratePythonResponse(BaseModel):
    """Response with generated Python code"""

    code: str
    validation: dict[str, Any]
    agent_name: str
    node_count: int
    edge_count: int


class ValidateGraphRequest(BaseModel):
    """Request to validate graph structure"""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ValidateGraphResponse(BaseModel):
    """Graph validation result"""

    valid: bool
    errors: list[str]
    warnings: list[str] = []


# ============================================
# API Endpoints
# ============================================


@router.post("/generate-python", response_model=GeneratePythonResponse)
async def generate_python_code(request: GeneratePythonRequest):
    """
    Generate Python LangGraph code from ReactFlow graph.

    This endpoint converts the visual agent designer graph into
    executable Python code using LangGraph.

    Args:
        request: Graph data with nodes, edges, and agent name

    Returns:
        Generated Python code with validation results
    """
    try:
        # Convert to dict for converter
        graph_data = {
            "nodes": [node.dict() for node in request.nodes],
            "edges": [edge.dict() for edge in request.edges],
            "agentName": request.agentName,
        }

        # Validate graph structure
        validation = validate_graph(graph_data["nodes"], graph_data["edges"])

        # Generate Python code
        python_code = reactflow_to_python(graph_data)

        return GeneratePythonResponse(
            code=python_code,
            validation=validation,
            agent_name=request.agentName,
            node_count=len(request.nodes),
            edge_count=len(request.edges),
        )

    except Exception as e:
        logger.error(f"Failed to generate Python code: {e}")
        raise HTTPException(status_code=500, detail=f"Code generation failed: {e!s}")


@router.post("/validate-graph", response_model=ValidateGraphResponse)
async def validate_graph_structure(request: ValidateGraphRequest):
    """
    Validate graph structure before code generation.

    Checks for:
    - Entry point existence
    - Disconnected nodes
    - Invalid edges
    - Circular dependencies (if applicable)

    Args:
        request: Graph data with nodes and edges

    Returns:
        Validation result with errors and warnings
    """
    try:
        graph_data = {
            "nodes": [node.dict() for node in request.nodes],
            "edges": [edge.dict() for edge in request.edges],
        }

        result = validate_graph(graph_data["nodes"], graph_data["edges"])

        # Add warnings
        warnings = []

        # Check for end nodes
        end_nodes = [n for n in request.nodes if n.type == "end"]
        if not end_nodes:
            warnings.append("No end node found - workflow may not terminate properly")

        # Check for isolated nodes
        node_ids = {n.id for n in request.nodes}
        connected_as_source = {e.source for e in request.edges}
        connected_as_target = {e.target for e in request.edges}
        connected = connected_as_source | connected_as_target

        isolated = node_ids - connected
        if isolated:
            warnings.append(f"Isolated nodes (not connected): {', '.join(isolated)}")

        return ValidateGraphResponse(valid=result["valid"], errors=result["errors"], warnings=warnings)

    except Exception as e:
        logger.error(f"Failed to validate graph: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e!s}")


@router.get("/health")
async def designer_health():
    """Health check endpoint for designer service"""
    return {"status": "healthy", "service": "designer", "converters": ["reactflow_to_python"], "version": "1.0.0"}
