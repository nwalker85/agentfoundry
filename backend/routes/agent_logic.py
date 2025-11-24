"""
Agent Logic Extraction API Routes
Provides endpoints to extract and serve implementation logic from Python agent files
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.converters.python_logic_extractor import LangGraphLogicExtractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agent-logic"])

# In-memory cache for extracted metadata (30min TTL)
_logic_cache: dict[str, dict[str, Any]] = {}
_cache_timestamps: dict[str, datetime] = {}
CACHE_TTL_MINUTES = 30


def _get_agent_python_path(agent_id: str) -> str | None:
    """
    Find the Python file for an agent

    Args:
        agent_id: Agent ID (e.g., "cibc-card-activation")

    Returns:
        Path to Python file or None if not found
    """
    # Convert agent-id to python_file_name
    # cibc-card-activation → cibc_card_activation.py
    python_filename = agent_id.replace("-", "_") + ".py"

    # Check common locations
    possible_paths = [
        f"/app/agents/{python_filename}",
        f"agents/{python_filename}",
        f"/app/agent/{python_filename}",  # Legacy location
        f"agent/{python_filename}",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found Python file for {agent_id}: {path}")
            return path

    logger.warning(f"Python file not found for agent {agent_id}, tried: {possible_paths}")
    return None


def _is_cache_valid(agent_id: str) -> bool:
    """Check if cached data is still valid"""
    if agent_id not in _cache_timestamps:
        return False

    age = datetime.now() - _cache_timestamps[agent_id]
    return age < timedelta(minutes=CACHE_TTL_MINUTES)


def _cache_result(agent_id: str, result: dict[str, Any]):
    """Cache extraction result"""
    _logic_cache[agent_id] = result
    _cache_timestamps[agent_id] = datetime.now()
    logger.info(f"Cached logic metadata for {agent_id}")


def _get_cached_result(agent_id: str) -> dict[str, Any] | None:
    """Get cached result if valid"""
    if _is_cache_valid(agent_id):
        logger.info(f"Using cached logic metadata for {agent_id}")
        return _logic_cache[agent_id]
    return None


@router.get("/{agent_id}/logic")
async def get_agent_logic(agent_id: str, force_refresh: bool = False):
    """
    Extract implementation logic from Python agent file

    Args:
        agent_id: Agent ID (e.g., "cibc-card-activation")
        force_refresh: Skip cache and re-extract

    Returns:
        {
            "agent_id": "cibc-card-activation",
            "python_path": "agents/cibc_card_activation.py",
            "class_info": {...},
            "nodes": {...},
            "business_methods": {...},
            "total_nodes": 16,
            "total_business_methods": 3,
            "extracted_at": "2025-11-19T12:00:00Z",
            "cached": false
        }
    """
    try:
        # Check cache first
        if not force_refresh:
            cached = _get_cached_result(agent_id)
            if cached:
                return {**cached, "cached": True}

        # Find Python file
        python_path = _get_agent_python_path(agent_id)

        if not python_path:
            # Not found - might be a YAML-only agent (not Python-based)
            return {
                "agent_id": agent_id,
                "python_path": None,
                "error": "No Python implementation found",
                "message": "This agent may be declarative (YAML-only) or Python file not found",
                "nodes": {},
                "business_methods": {},
                "total_nodes": 0,
                "total_business_methods": 0,
                "extracted_at": datetime.utcnow().isoformat(),
                "cached": False,
            }

        # Extract logic using AST parser
        extractor = LangGraphLogicExtractor()
        result = extractor.extract_from_file(python_path)

        # Check for extraction errors
        if "error" in result:
            logger.error(f"Failed to extract logic from {python_path}: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Failed to parse Python file: {result['error']}")

        # Add metadata
        response = {
            "agent_id": agent_id,
            "python_path": python_path,
            **result,
            "extracted_at": datetime.utcnow().isoformat(),
            "cached": False,
        }

        # Cache the result
        _cache_result(agent_id, response)

        logger.info(
            f"Extracted logic for {agent_id}: "
            f"{result['total_nodes']} nodes, "
            f"{result['total_business_methods']} business methods"
        )

        return response

    except FileNotFoundError as e:
        logger.error(f"File not found for {agent_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Agent Python file not found: {e}")
    except Exception as e:
        logger.error(f"Failed to extract logic for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract agent logic: {e!s}")


@router.get("/{agent_id}/logic/node/{node_id}")
async def get_node_logic(agent_id: str, node_id: str):
    """
    Get implementation details for a specific node

    Args:
        agent_id: Agent ID
        node_id: Node ID (e.g., "process_step_1")

    Returns:
        Node metadata with prompts, conditions, state mutations, etc.
    """
    try:
        # Get full agent logic (from cache if available)
        agent_logic = await get_agent_logic(agent_id)

        # Find the specific node
        if "nodes" not in agent_logic or node_id not in agent_logic["nodes"]:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found in agent '{agent_id}'")

        node_data = agent_logic["nodes"][node_id]

        return {
            "agent_id": agent_id,
            "node_id": node_id,
            **node_data,
            "extracted_at": agent_logic.get("extracted_at"),
            "cached": agent_logic.get("cached", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node {node_id} for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get node logic: {e!s}")


@router.get("/{agent_id}/logic/business/{method_name}")
async def get_business_method(agent_id: str, method_name: str):
    """
    Get implementation details for a business logic method

    Args:
        agent_id: Agent ID
        method_name: Method name (e.g., "evaluate_verification")

    Returns:
        Business method metadata with source code, docstring, etc.
    """
    try:
        # Get full agent logic
        agent_logic = await get_agent_logic(agent_id)

        # Find the specific method
        if "business_methods" not in agent_logic or method_name not in agent_logic["business_methods"]:
            raise HTTPException(
                status_code=404, detail=f"Business method '{method_name}' not found in agent '{agent_id}'"
            )

        method_data = agent_logic["business_methods"][method_name]

        return {
            "agent_id": agent_id,
            "method_name": method_name,
            **method_data,
            "extracted_at": agent_logic.get("extracted_at"),
            "cached": agent_logic.get("cached", False),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get business method {method_name} for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get business method: {e!s}")


@router.post("/{agent_id}/logic/refresh")
async def refresh_agent_logic(agent_id: str):
    """
    Force refresh the cached logic metadata for an agent

    Useful after modifying the Python file
    """
    try:
        # Clear cache
        _logic_cache.pop(agent_id, None)
        _cache_timestamps.pop(agent_id, None)

        # Re-extract
        result = await get_agent_logic(agent_id, force_refresh=True)

        return {
            "status": "refreshed",
            "agent_id": agent_id,
            "total_nodes": result.get("total_nodes", 0),
            "total_business_methods": result.get("total_business_methods", 0),
            "extracted_at": result.get("extracted_at"),
        }

    except Exception as e:
        logger.error(f"Failed to refresh logic for {agent_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refresh agent logic: {e!s}")


@router.get("/logic/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    return {
        "cached_agents": list(_logic_cache.keys()),
        "cache_size": len(_logic_cache),
        "cache_ttl_minutes": CACHE_TTL_MINUTES,
        "timestamps": {agent_id: timestamp.isoformat() for agent_id, timestamp in _cache_timestamps.items()},
    }
