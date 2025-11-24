"""
Storage API Routes - Agent Design Persistence
Invokes the Storage Agent for all storage operations.
"""

import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.storage_agent import invoke_storage_agent

router = APIRouter(prefix="/api/storage", tags=["storage"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class SaveDraftRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    user_id: str = Field(..., description="User ID who owns this draft")
    graph_data: dict = Field(..., description="ReactFlow graph structure")


class CommitVersionRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    graph_data: dict = Field(..., description="ReactFlow graph structure")
    commit_message: str = Field(..., description="Commit message describing changes")
    user_id: str | None = Field(None, description="User ID who created this commit")


class RestoreVersionRequest(BaseModel):
    agent_id: str = Field(..., description="Unique identifier for the agent")
    version: int = Field(..., description="Version number to restore")


class ImportPythonRequest(BaseModel):
    python_code: str = Field(..., description="Python LangGraph code to import")


class ExportPythonRequest(BaseModel):
    graph_data: dict = Field(..., description="ReactFlow graph to export")
    agent_name: str = Field("agent", description="Name for the generated agent")


class StorageResponse(BaseModel):
    success: bool
    result: Any
    error: str | None = None


# ============================================================================
# ROUTES
# ============================================================================


@router.post("/autosave", response_model=StorageResponse)
async def autosave_draft(request: SaveDraftRequest):
    """
    Autosave agent design draft to Redis.
    Called automatically every 3 seconds from the frontend.
    """
    try:
        result = await invoke_storage_agent(
            action="save_draft", agent_id=request.agent_id, user_id=request.user_id, graph_data=request.graph_data
        )

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commit", response_model=StorageResponse)
async def commit_version(request: CommitVersionRequest):
    """
    Commit agent version to SQLite with commit message (git-like).
    Creates an immutable version snapshot.
    """
    try:
        result = await invoke_storage_agent(
            action="commit_version",
            agent_id=request.agent_id,
            graph_data=request.graph_data,
            commit_message=request.commit_message,
            user_id=request.user_id,
        )

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{agent_id}", response_model=StorageResponse)
async def get_history(agent_id: str, limit: int = 50):
    """
    Get version history for an agent (git log style).
    Returns list of commits with metadata.
    """
    try:
        result = await invoke_storage_agent(action="get_history", agent_id=agent_id)

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore", response_model=StorageResponse)
async def restore_version(request: RestoreVersionRequest):
    """
    Restore agent to a specific version (git checkout).
    Returns the graph_data from that version.
    """
    try:
        result = await invoke_storage_agent(
            action="restore_version", agent_id=request.agent_id, version=request.version
        )

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/draft/{agent_id}", response_model=StorageResponse)
async def get_draft(agent_id: str):
    """
    Get the latest draft for an agent from Redis.
    Returns None if no draft exists.
    """
    try:
        result = await invoke_storage_agent(action="get_draft", agent_id=agent_id)

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", response_model=StorageResponse)
async def import_python(request: ImportPythonRequest):
    """
    Import Python LangGraph code and convert to ReactFlow graph.
    Parses the AST and extracts nodes/edges.
    """
    try:
        result = await invoke_storage_agent(action="import_python", python_code=request.python_code)

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=StorageResponse)
async def export_python(request: ExportPythonRequest):
    """
    Export ReactFlow graph to Python LangGraph code.
    Generates executable Python code.
    """
    try:
        result = await invoke_storage_agent(
            action="export_python", graph_data=request.graph_data, agent_name=request.agent_name
        )

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drafts", response_model=StorageResponse)
async def list_drafts(user_id: str):
    """
    List all active drafts for a user.
    """
    try:
        result = await invoke_storage_agent(action="list_drafts", user_id=user_id)

        return StorageResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
