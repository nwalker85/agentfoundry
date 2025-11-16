"""
Unit tests for agent loader.

Tests:
- Dynamic module loading
- Agent instantiation
- Validation integration
- Error handling
- Handler import resolution
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from agents.agent_loader import AgentLoader
from agents.yaml_validator import AgentYAML, ValidationResult
from agents.agent_registry import AgentInstance


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def agent_loader():
    """Create AgentLoader instance"""
    return AgentLoader()


@pytest.fixture
def valid_agent_config() -> dict:
    """Valid agent YAML config"""
    return {
        "version": "1.0.0",
        "metadata": {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "description": "Test agent",
            "tags": ["test"]
        },
        "spec": {
            "capabilities": ["chat"],
            "workflow": {
                "type": "graph",
                "entry_point": "start",
                "nodes": [
                    {
                        "id": "start",
                        "type": "handler",
                        "handler": "agents.workers.test_agent.start_handler",
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": "terminal"
                    }
                ]
            }
        }
    }


@pytest.fixture
def mock_handler_module():
    """Mock handler module"""
    module = Mock()
    module.start_handler = AsyncMock()
    return module


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_validate_valid_yaml(agent_loader, valid_agent_config):
    """Test validation of valid YAML config"""
    agent_config = AgentYAML(**valid_agent_config)
    
    result = await agent_loader.validate_yaml(agent_config)
    
    assert result.valid is True
    assert result.agent_id == "test-agent"
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_validate_missing_entry_point(agent_loader, valid_agent_config):
    """Test validation catches missing entry point node"""
    valid_agent_config["spec"]["workflow"]["entry_point"] = "nonexistent"
    agent_config = AgentYAML(**valid_agent_config)
    
    result = await agent_loader.validate_yaml(agent_config)
    
    assert result.valid is False
    assert any("entry_point" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_validate_unreachable_nodes(agent_loader, valid_agent_config):
    """Test validation detects unreachable nodes"""
    valid_agent_config["spec"]["workflow"]["nodes"].append({
        "id": "orphan",
        "type": "handler",
        "handler": "test.orphan",
        "next": ["end"]
    })
    agent_config = AgentYAML(**valid_agent_config)
    
    result = await agent_loader.validate_yaml(agent_config)
    
    # Should have warning about unreachable node
    assert len(result.warnings) > 0
    assert any("unreachable" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_validate_broken_next_references(agent_loader, valid_agent_config):
    """Test validation catches broken next references"""
    valid_agent_config["spec"]["workflow"]["nodes"][0]["next"] = ["nonexistent"]
    agent_config = AgentYAML(**valid_agent_config)
    
    result = await agent_loader.validate_yaml(agent_config)
    
    assert result.valid is False
    assert any("nonexistent" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_validate_circular_reference(agent_loader, valid_agent_config):
    """Test validation detects circular references"""
    valid_agent_config["spec"]["workflow"]["nodes"] = [
        {"id": "a", "type": "handler", "handler": "test.a", "next": ["b"]},
        {"id": "b", "type": "handler", "handler": "test.b", "next": ["a"]},
    ]
    agent_config = AgentYAML(**valid_agent_config)
    
    result = await agent_loader.validate_yaml(agent_config)
    
    # Should have warning or error about circular dependency
    assert len(result.warnings) > 0 or not result.valid


# ============================================================================
# HANDLER LOADING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_load_handler_success(agent_loader):
    """Test successful handler loading"""
    # Use a real Python built-in function for testing
    handler = await agent_loader._load_handler("builtins.print")
    
    assert handler is not None
    assert callable(handler)


@pytest.mark.asyncio
async def test_load_handler_missing_module(agent_loader):
    """Test loading handler from non-existent module"""
    with pytest.raises(ImportError):
        await agent_loader._load_handler("nonexistent.module.handler")


@pytest.mark.asyncio
async def test_load_handler_missing_function(agent_loader):
    """Test loading non-existent function from module"""
    with pytest.raises(AttributeError):
        await agent_loader._load_handler("builtins.nonexistent_function")


@pytest.mark.asyncio
async def test_load_handler_invalid_format(agent_loader):
    """Test loading handler with invalid format"""
    with pytest.raises(ValueError):
        await agent_loader._load_handler("invalid_format")


# ============================================================================
# AGENT LOADING TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_load_agent_success(mock_load_handler, agent_loader, valid_agent_config):
    """Test successful agent loading"""
    # Mock handler loading
    mock_load_handler.return_value = AsyncMock()
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    assert instance is not None
    assert isinstance(instance, AgentInstance)
    assert instance.metadata.id == "test-agent"
    assert instance.config == agent_config
    assert instance.graph is not None


@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_load_agent_with_multiple_handlers(
    mock_load_handler,
    agent_loader,
    valid_agent_config
):
    """Test loading agent with multiple handler nodes"""
    valid_agent_config["spec"]["workflow"]["nodes"] = [
        {"id": "start", "type": "handler", "handler": "test.start", "next": ["middle"]},
        {"id": "middle", "type": "handler", "handler": "test.middle", "next": ["end"]},
        {"id": "end", "type": "terminal"}
    ]
    
    mock_load_handler.return_value = AsyncMock()
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    assert instance is not None
    assert len(agent_config.spec.workflow.nodes) == 3


@pytest.mark.asyncio
async def test_load_agent_with_invalid_handler(agent_loader, valid_agent_config):
    """Test loading agent with invalid handler"""
    valid_agent_config["spec"]["workflow"]["nodes"][0]["handler"] = "nonexistent.handler"
    agent_config = AgentYAML(**valid_agent_config)
    
    with pytest.raises(ImportError):
        await agent_loader.load_agent(agent_config)


# ============================================================================
# GRAPH CONSTRUCTION TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_build_graph_simple(mock_load_handler, agent_loader, valid_agent_config):
    """Test building simple graph"""
    mock_load_handler.return_value = AsyncMock()
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    # Graph should have nodes matching YAML
    assert instance.graph is not None


@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_build_graph_conditional(mock_load_handler, agent_loader, valid_agent_config):
    """Test building graph with conditional node"""
    valid_agent_config["spec"]["workflow"]["nodes"] = [
        {"id": "start", "type": "handler", "handler": "test.start", "next": ["decide"]},
        {
            "id": "decide",
            "type": "conditional",
            "handler": "test.decide",
            "next": ["path_a", "path_b"]
        },
        {"id": "path_a", "type": "handler", "handler": "test.a", "next": ["end"]},
        {"id": "path_b", "type": "handler", "handler": "test.b", "next": ["end"]},
        {"id": "end", "type": "terminal"}
    ]
    
    mock_load_handler.return_value = AsyncMock()
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    assert instance.graph is not None


@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_build_graph_terminal_nodes(mock_load_handler, agent_loader, valid_agent_config):
    """Test that terminal nodes are properly handled"""
    mock_load_handler.return_value = AsyncMock()
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    # Terminal node should not have outgoing edges
    assert instance.graph is not None


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_load_agent_empty_workflow(agent_loader, valid_agent_config):
    """Test loading agent with empty workflow"""
    valid_agent_config["spec"]["workflow"]["nodes"] = []
    
    with pytest.raises(ValueError):
        agent_config = AgentYAML(**valid_agent_config)


@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_load_agent_handler_import_error(mock_load_handler, agent_loader, valid_agent_config):
    """Test handling of handler import errors"""
    mock_load_handler.side_effect = ImportError("Module not found")
    
    agent_config = AgentYAML(**valid_agent_config)
    
    with pytest.raises(ImportError):
        await agent_loader.load_agent(agent_config)


# ============================================================================
# CACHING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_handler_caching(agent_loader):
    """Test that handlers are cached after first load"""
    # Load same handler twice
    handler1 = await agent_loader._load_handler("builtins.print")
    handler2 = await agent_loader._load_handler("builtins.print")
    
    # Should return same object (cached)
    assert handler1 is handler2


# ============================================================================
# METADATA PRESERVATION TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_metadata_preserved(mock_load_handler, agent_loader, valid_agent_config):
    """Test that metadata is preserved in loaded instance"""
    mock_load_handler.return_value = AsyncMock()
    
    valid_agent_config["metadata"]["author"] = "Test Author"
    valid_agent_config["metadata"]["tags"] = ["tag1", "tag2"]
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    assert instance.metadata.author == "Test Author"
    assert "tag1" in instance.metadata.tags
    assert "tag2" in instance.metadata.tags


@pytest.mark.asyncio
@patch('agents.agent_loader.AgentLoader._load_handler')
async def test_capabilities_preserved(mock_load_handler, agent_loader, valid_agent_config):
    """Test that capabilities are preserved"""
    mock_load_handler.return_value = AsyncMock()
    
    valid_agent_config["spec"]["capabilities"] = ["chat", "voice", "tools"]
    
    agent_config = AgentYAML(**valid_agent_config)
    instance = await agent_loader.load_agent(agent_config)
    
    assert "chat" in instance.config.spec.capabilities
    assert "voice" in instance.config.spec.capabilities
    assert "tools" in instance.config.spec.capabilities
