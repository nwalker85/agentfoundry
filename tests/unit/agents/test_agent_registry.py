"""
Unit tests for agent registry.

Tests:
- Register/unregister agents
- Get agent by ID
- List all agents
- Health status tracking
- Hot reload
- Concurrent access
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from agents.agent_registry import AgentRegistry, AgentInstance, AgentStatus
from agents.yaml_validator import AgentYAML, AgentMetadata


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def registry():
    """Create fresh AgentRegistry"""
    return AgentRegistry()


@pytest.fixture
def mock_agent_instance():
    """Create mock AgentInstance"""
    metadata = AgentMetadata(
        id="test-agent",
        name="Test Agent",
        version="1.0.0",
        description="Test",
        tags=["test"]
    )
    
    config = Mock(spec=AgentYAML)
    config.metadata = metadata
    config.spec = Mock()
    config.spec.capabilities = ["chat"]
    config.spec.workflow = Mock()
    config.spec.workflow.nodes = [{"id": "start"}]
    
    instance = AgentInstance(
        metadata=metadata,
        config=config,
        graph=Mock(),
        status=AgentStatus()
    )
    
    return instance


@pytest.fixture
def multiple_mock_instances():
    """Create multiple mock instances"""
    instances = []
    for i in range(3):
        metadata = AgentMetadata(
            id=f"agent-{i}",
            name=f"Agent {i}",
            version="1.0.0",
            description=f"Test agent {i}",
            tags=["test"]
        )
        
        config = Mock(spec=AgentYAML)
        config.metadata = metadata
        config.spec = Mock()
        config.spec.capabilities = ["chat"]
        config.spec.workflow = Mock()
        config.spec.workflow.nodes = [{"id": "start"}]
        
        instance = AgentInstance(
            metadata=metadata,
            config=config,
            graph=Mock(),
            status=AgentStatus()
        )
        instances.append(instance)
    
    return instances


# ============================================================================
# REGISTRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_register_agent(registry, mock_agent_instance):
    """Test registering a new agent"""
    await registry.register("test-agent", mock_agent_instance)
    
    assert await registry.count() == 1
    assert await registry.exists("test-agent") is True


@pytest.mark.asyncio
async def test_register_multiple_agents(registry, multiple_mock_instances):
    """Test registering multiple agents"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    assert await registry.count() == 3


@pytest.mark.asyncio
async def test_register_duplicate_id(registry, mock_agent_instance):
    """Test registering agent with duplicate ID (should replace)"""
    await registry.register("test-agent", mock_agent_instance)
    
    # Create new instance
    new_instance = AgentInstance(
        metadata=mock_agent_instance.metadata,
        config=mock_agent_instance.config,
        graph=Mock(),
        status=AgentStatus()
    )
    
    await registry.register("test-agent", new_instance)
    
    # Should still have 1 agent (replaced)
    assert await registry.count() == 1
    
    # Get agent and verify it's the new instance
    retrieved = await registry.get("test-agent")
    assert retrieved is new_instance


# ============================================================================
# RETRIEVAL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_existing_agent(registry, mock_agent_instance):
    """Test retrieving existing agent"""
    await registry.register("test-agent", mock_agent_instance)
    
    retrieved = await registry.get("test-agent")
    
    assert retrieved is not None
    assert retrieved.metadata.id == "test-agent"


@pytest.mark.asyncio
async def test_get_nonexistent_agent(registry):
    """Test retrieving non-existent agent"""
    retrieved = await registry.get("nonexistent")
    
    assert retrieved is None


@pytest.mark.asyncio
async def test_list_all_empty(registry):
    """Test listing agents when registry is empty"""
    agents = await registry.list_all()
    
    assert agents == {}


@pytest.mark.asyncio
async def test_list_all_multiple(registry, multiple_mock_instances):
    """Test listing all agents"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    agents = await registry.list_all()
    
    assert len(agents) == 3
    assert "agent-0" in agents
    assert "agent-1" in agents
    assert "agent-2" in agents


@pytest.mark.asyncio
async def test_exists(registry, mock_agent_instance):
    """Test checking if agent exists"""
    assert await registry.exists("test-agent") is False
    
    await registry.register("test-agent", mock_agent_instance)
    
    assert await registry.exists("test-agent") is True


# ============================================================================
# UNREGISTRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_unregister_existing_agent(registry, mock_agent_instance):
    """Test unregistering existing agent"""
    await registry.register("test-agent", mock_agent_instance)
    
    success = await registry.unregister("test-agent")
    
    assert success is True
    assert await registry.count() == 0
    assert await registry.exists("test-agent") is False


@pytest.mark.asyncio
async def test_unregister_nonexistent_agent(registry):
    """Test unregistering non-existent agent"""
    success = await registry.unregister("nonexistent")
    
    assert success is False


@pytest.mark.asyncio
async def test_unregister_multiple(registry, multiple_mock_instances):
    """Test unregistering multiple agents"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    await registry.unregister("agent-0")
    await registry.unregister("agent-2")
    
    assert await registry.count() == 1
    assert await registry.exists("agent-1") is True


# ============================================================================
# HOT RELOAD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_reload_existing_agent(registry, mock_agent_instance):
    """Test hot-reloading an existing agent"""
    await registry.register("test-agent", mock_agent_instance)
    
    # Create new instance (simulating reload)
    new_metadata = AgentMetadata(
        id="test-agent",
        name="Test Agent Updated",
        version="2.0.0",
        description="Updated",
        tags=["test", "updated"]
    )
    
    new_instance = AgentInstance(
        metadata=new_metadata,
        config=Mock(),
        graph=Mock(),
        status=AgentStatus()
    )
    
    success = await registry.reload("test-agent", new_instance)
    
    assert success is True
    
    # Verify new instance is registered
    retrieved = await registry.get("test-agent")
    assert retrieved.metadata.version == "2.0.0"
    assert retrieved.metadata.name == "Test Agent Updated"


@pytest.mark.asyncio
async def test_reload_nonexistent_agent(registry, mock_agent_instance):
    """Test reloading non-existent agent (should fail)"""
    success = await registry.reload("nonexistent", mock_agent_instance)
    
    assert success is False


# ============================================================================
# HEALTH STATUS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_healthy_count_all_healthy(registry, multiple_mock_instances):
    """Test counting healthy agents when all are healthy"""
    for i, instance in enumerate(multiple_mock_instances):
        instance.status.state = "healthy"
        await registry.register(f"agent-{i}", instance)
    
    count = await registry.get_healthy_count()
    
    assert count == 3


@pytest.mark.asyncio
async def test_get_healthy_count_mixed(registry, multiple_mock_instances):
    """Test counting healthy agents when some are unhealthy"""
    multiple_mock_instances[0].status.state = "healthy"
    multiple_mock_instances[1].status.state = "unhealthy"
    multiple_mock_instances[2].status.state = "healthy"
    
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    count = await registry.get_healthy_count()
    
    assert count == 2


@pytest.mark.asyncio
async def test_get_healthy_count_empty_registry(registry):
    """Test counting healthy agents in empty registry"""
    count = await registry.get_healthy_count()
    
    assert count == 0


# ============================================================================
# COUNT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_count_empty(registry):
    """Test count on empty registry"""
    count = await registry.count()
    
    assert count == 0


@pytest.mark.asyncio
async def test_count_multiple(registry, multiple_mock_instances):
    """Test count with multiple agents"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    count = await registry.count()
    
    assert count == 3


# ============================================================================
# CONCURRENT ACCESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_registration(registry):
    """Test concurrent agent registration"""
    async def register_agent(agent_id: str):
        metadata = AgentMetadata(
            id=agent_id,
            name=f"Agent {agent_id}",
            version="1.0.0",
            description="Test",
            tags=["test"]
        )
        
        instance = AgentInstance(
            metadata=metadata,
            config=Mock(),
            graph=Mock(),
            status=AgentStatus()
        )
        
        await registry.register(agent_id, instance)
    
    # Register 10 agents concurrently
    tasks = [register_agent(f"agent-{i}") for i in range(10)]
    await asyncio.gather(*tasks)
    
    assert await registry.count() == 10


@pytest.mark.asyncio
async def test_concurrent_get(registry, mock_agent_instance):
    """Test concurrent agent retrieval"""
    await registry.register("test-agent", mock_agent_instance)
    
    async def get_agent():
        return await registry.get("test-agent")
    
    # Get agent 10 times concurrently
    tasks = [get_agent() for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    # All should return the same instance
    assert all(r is mock_agent_instance for r in results)


@pytest.mark.asyncio
async def test_concurrent_unregister(registry, multiple_mock_instances):
    """Test concurrent agent unregistration"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    async def unregister_agent(agent_id: str):
        return await registry.unregister(agent_id)
    
    # Unregister all concurrently
    tasks = [unregister_agent(f"agent-{i}") for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(results)
    assert await registry.count() == 0


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_register_with_special_characters_in_id(registry, mock_agent_instance):
    """Test registering agent with special characters in ID"""
    special_id = "test-agent_v1.0-alpha"
    
    await registry.register(special_id, mock_agent_instance)
    
    assert await registry.exists(special_id) is True


@pytest.mark.asyncio
async def test_clear_registry(registry, multiple_mock_instances):
    """Test clearing entire registry"""
    for i, instance in enumerate(multiple_mock_instances):
        await registry.register(f"agent-{i}", instance)
    
    # Unregister all
    for i in range(3):
        await registry.unregister(f"agent-{i}")
    
    assert await registry.count() == 0


@pytest.mark.asyncio
async def test_registry_isolation(registry):
    """Test that registry instances are isolated"""
    registry2 = AgentRegistry()
    
    metadata = AgentMetadata(
        id="test-agent",
        name="Test",
        version="1.0.0",
        description="Test",
        tags=[]
    )
    
    instance = AgentInstance(
        metadata=metadata,
        config=Mock(),
        graph=Mock(),
        status=AgentStatus()
    )
    
    await registry.register("test-agent", instance)
    
    # Second registry should be empty
    assert await registry2.count() == 0
