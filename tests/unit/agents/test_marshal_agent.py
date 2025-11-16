"""
Unit tests for Marshal Agent (orchestrator).

Tests:
- Marshal startup/shutdown
- Agent loading from YAML files
- Hot-reload on file changes
- Health monitoring integration
- Validation error tracking
- Status summary reporting
- Error recovery and resilience
"""

import pytest
import asyncio
import yaml
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from agents.marshal_agent import MarshalAgent
from agents.yaml_validator import AgentYAML, ValidationResult


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def agents_dir(tmp_path):
    """Create temporary agents directory"""
    agents_path = tmp_path / "agents"
    agents_path.mkdir()
    return agents_path


@pytest.fixture
def valid_agent_yaml() -> dict:
    """Valid agent YAML structure"""
    return {
        "apiVersion": "engineering-dept/v1",
        "kind": "Agent",
        "metadata": {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "description": "Test agent for unit testing",
            "tags": ["test"],
            "created": "2025-11-15T00:00:00Z",
            "updated": "2025-11-15T00:00:00Z"
        },
        "spec": {
            "capabilities": ["chat"],
            "workflow": {
                "type": "langgraph.StateGraph",
                "entry_point": "start",
                "nodes": [
                    {
                        "id": "start",
                        "handler": "unittest.mock.Mock.return_value",
                        "description": "Start node for testing",
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "handler": "unittest.mock.Mock.assert_called",
                        "description": "End node for testing",
                        "next": ["END"]
                    }
                ]
            }
        }
    }


@pytest.fixture
def create_yaml_file(agents_dir, valid_agent_yaml):
    """Helper to create YAML files"""
    def _create(agent_id: str, yaml_data: dict = None):
        if yaml_data is None:
            yaml_data = valid_agent_yaml.copy()
            yaml_data["metadata"]["id"] = agent_id
        
        yaml_file = agents_dir / f"{agent_id}.agent.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(yaml_data, f)
        return yaml_file
    
    return _create


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_marshal_initialization(agents_dir):
    """Test Marshal Agent initialization"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True
    )
    
    assert marshal.agents_dir == agents_dir
    assert marshal.enable_file_watcher is True
    assert marshal.enable_health_monitor is True
    assert marshal._running is False
    assert marshal.registry is not None
    assert marshal.loader is not None
    assert marshal.health_monitor is not None


def test_marshal_initialization_with_options(agents_dir):
    """Test Marshal initialization with different options"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False,
        health_check_interval=30
    )
    
    assert marshal.enable_file_watcher is False
    assert marshal.enable_health_monitor is False
    # Verify health monitor was initialized with custom interval
    assert marshal.health_monitor.check_interval_seconds == 30


def test_marshal_initialization_creates_components(agents_dir):
    """Test that Marshal creates all required components"""
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    # Verify all components are created
    assert hasattr(marshal, 'registry')
    assert hasattr(marshal, 'loader')
    assert hasattr(marshal, 'health_monitor')
    assert hasattr(marshal, 'file_watcher')  # Not initialized yet
    assert marshal.file_watcher is None  # Only initialized on start


# ============================================================================
# STARTUP TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_marshal_start_empty_directory(agents_dir):
    """Test starting Marshal with empty agents directory"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    assert marshal._running is True
    assert marshal.is_running is True
    assert await marshal.registry.count() == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_marshal_start_with_existing_agents(agents_dir, create_yaml_file):
    """Test starting Marshal with existing agent files"""
    # Create agent files
    create_yaml_file("agent-1")
    create_yaml_file("agent-2")
    create_yaml_file("agent-3")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Should load all agents
    assert await marshal.registry.count() == 3
    assert await marshal.registry.exists("agent-1")
    assert await marshal.registry.exists("agent-2")
    assert await marshal.registry.exists("agent-3")
    
    # Verify agents have correct metadata
    agent1 = await marshal.registry.get("agent-1")
    assert agent1.metadata.id == "agent-1"
    assert agent1.metadata.version == "1.0.0"
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_marshal_start_with_invalid_yaml(agents_dir, valid_agent_yaml):
    """Test starting Marshal with invalid YAML files"""
    # Create invalid YAML file (missing required field)
    invalid_yaml = valid_agent_yaml.copy()
    del invalid_yaml["metadata"]["id"]
    
    yaml_file = agents_dir / "invalid-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Should not load invalid agent
    assert await marshal.registry.count() == 0
    
    # Should track validation error
    errors = marshal.get_validation_errors()
    assert len(errors) > 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_marshal_start_with_malformed_yaml(agents_dir):
    """Test starting Marshal with malformed YAML syntax"""
    # Create syntactically invalid YAML
    yaml_file = agents_dir / "bad-syntax.agent.yaml"
    with open(yaml_file, 'w') as f:
        f.write("apiVersion: test\n  invalid: : : syntax\n")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    # Should not crash, should handle gracefully
    await marshal.start()
    
    assert await marshal.registry.count() == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_marshal_start_initializes_components(agents_dir, create_yaml_file):
    """Test that start() properly initializes all components"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True
    )
    
    await marshal.start()
    
    # File watcher should be initialized
    assert marshal.file_watcher is not None
    
    # Background tasks should be created
    assert len(marshal._tasks) > 0
    
    # Health monitor should be running
    assert marshal.health_monitor._running is True
    
    await marshal.stop()


# ============================================================================
# SHUTDOWN TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_marshal_stop(agents_dir):
    """Test Marshal shutdown"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    assert marshal._running is True
    assert marshal.is_running is True
    
    await marshal.stop()
    assert marshal._running is False
    assert marshal.is_running is False


@pytest.mark.asyncio
async def test_marshal_stop_before_start(agents_dir):
    """Test stopping Marshal that was never started"""
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    # Should handle gracefully
    await marshal.stop()
    assert marshal._running is False


@pytest.mark.asyncio
async def test_marshal_stop_cancels_tasks(agents_dir):
    """Test that stop() cancels all background tasks"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True
    )
    
    await marshal.start()
    
    initial_task_count = len(marshal._tasks)
    assert initial_task_count > 0
    
    await marshal.stop()
    
    # All tasks should be cancelled
    for task in marshal._tasks:
        assert task.cancelled() or task.done()


@pytest.mark.asyncio
async def test_marshal_stop_graceful_shutdown(agents_dir, create_yaml_file):
    """Test graceful shutdown with active agents"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True
    )
    
    await marshal.start()
    
    # Verify running
    assert await marshal.registry.count() == 1
    
    # Stop should complete without errors
    await marshal.stop()
    
    assert marshal._running is False
    # Registry should still contain agents (not cleared)
    assert await marshal.registry.count() == 1


# ============================================================================
# FILE WATCHER INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_hot_reload_on_file_add(agents_dir, create_yaml_file):
    """Test hot-reload when new file is added"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Wait for watcher to initialize
    await asyncio.sleep(1.5)
    
    assert await marshal.registry.count() == 0
    
    # Add new agent file
    create_yaml_file("new-agent")
    
    # Wait for detection and loading
    await asyncio.sleep(2.5)
    
    # Should have loaded new agent
    assert await marshal.registry.exists("new-agent")
    assert await marshal.registry.count() == 1
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_hot_reload_on_file_modify(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test hot-reload when file is modified"""
    # Create initial file
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(1.5)
    
    # Get initial version
    agent = await marshal.registry.get("test-agent")
    initial_version = agent.metadata.version
    assert initial_version == "1.0.0"
    
    # Modify file with new version
    modified_yaml = valid_agent_yaml.copy()
    modified_yaml["metadata"]["id"] = "test-agent"
    modified_yaml["metadata"]["version"] = "2.0.0"
    
    with open(yaml_file, 'w') as f:
        yaml.dump(modified_yaml, f)
    
    # Wait for detection and reload
    await asyncio.sleep(2.5)
    
    # Should have reloaded with new version
    agent = await marshal.registry.get("test-agent")
    assert agent.metadata.version == "2.0.0"
    assert agent.metadata.version != initial_version
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_hot_reload_on_file_delete(agents_dir, create_yaml_file):
    """Test agent removal when file is deleted"""
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(1.5)
    
    assert await marshal.registry.exists("test-agent")
    assert await marshal.registry.count() == 1
    
    # Delete file
    yaml_file.unlink()
    
    # Wait for detection
    await asyncio.sleep(2.5)
    
    # Agent should be unregistered
    assert not await marshal.registry.exists("test-agent")
    assert await marshal.registry.count() == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_hot_reload_preserves_other_agents(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test that hot-reload doesn't affect other agents"""
    # Create multiple agents
    create_yaml_file("agent-1")
    yaml_file_2 = create_yaml_file("agent-2")
    create_yaml_file("agent-3")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(1.5)
    
    assert await marshal.registry.count() == 3
    
    # Modify only agent-2
    modified_yaml = valid_agent_yaml.copy()
    modified_yaml["metadata"]["id"] = "agent-2"
    modified_yaml["metadata"]["version"] = "2.0.0"
    
    with open(yaml_file_2, 'w') as f:
        yaml.dump(modified_yaml, f)
    
    await asyncio.sleep(2.5)
    
    # Agent-2 should be updated
    agent2 = await marshal.registry.get("agent-2")
    assert agent2.metadata.version == "2.0.0"
    
    # Other agents should be unchanged
    agent1 = await marshal.registry.get("agent-1")
    agent3 = await marshal.registry.get("agent-3")
    assert agent1.metadata.version == "1.0.0"
    assert agent3.metadata.version == "1.0.0"
    
    assert await marshal.registry.count() == 3
    
    await marshal.stop()


# ============================================================================
# HEALTH MONITORING INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_health_monitoring_enabled(agents_dir, create_yaml_file):
    """Test that health monitoring runs when enabled"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=True,
        health_check_interval=1  # Short interval for testing
    )
    
    await marshal.start()
    
    # Wait for health checks to run
    await asyncio.sleep(2.5)
    
    # Should have health metrics
    metrics = marshal.health_monitor.get_metrics("test-agent")
    assert metrics is not None
    assert metrics.total_checks > 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_health_monitoring_disabled(agents_dir, create_yaml_file):
    """Test that health monitoring doesn't run when disabled"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(2.0)
    
    # Should not have health metrics
    metrics = marshal.health_monitor.get_metrics("test-agent")
    assert metrics is None or metrics.total_checks == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_health_monitoring_multiple_agents(agents_dir, create_yaml_file):
    """Test health monitoring tracks multiple agents"""
    create_yaml_file("agent-1")
    create_yaml_file("agent-2")
    create_yaml_file("agent-3")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=True,
        health_check_interval=1
    )
    
    await marshal.start()
    await asyncio.sleep(2.5)
    
    # Should have metrics for all agents
    metrics1 = marshal.health_monitor.get_metrics("agent-1")
    metrics2 = marshal.health_monitor.get_metrics("agent-2")
    metrics3 = marshal.health_monitor.get_metrics("agent-3")
    
    assert metrics1 is not None and metrics1.total_checks > 0
    assert metrics2 is not None and metrics2.total_checks > 0
    assert metrics3 is not None and metrics3.total_checks > 0
    
    await marshal.stop()


# ============================================================================
# MANUAL RELOAD TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_manual_reload_success(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test manually reloading an agent"""
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Get initial state
    agent = await marshal.registry.get("test-agent")
    assert agent.metadata.version == "1.0.0"
    
    # Modify file
    modified_yaml = valid_agent_yaml.copy()
    modified_yaml["metadata"]["id"] = "test-agent"
    modified_yaml["metadata"]["version"] = "2.0.0"
    
    with open(yaml_file, 'w') as f:
        yaml.dump(modified_yaml, f)
    
    # Manual reload
    success = await marshal.reload_agent("test-agent")
    
    assert success is True
    
    # Verify reload
    agent = await marshal.registry.get("test-agent")
    assert agent.metadata.version == "2.0.0"
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_manual_reload_nonexistent(agents_dir):
    """Test manually reloading non-existent agent"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    success = await marshal.reload_agent("nonexistent")
    
    assert success is False
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_manual_reload_invalid_yaml(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test manual reload with invalid YAML"""
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Make YAML invalid
    invalid_yaml = valid_agent_yaml.copy()
    invalid_yaml["spec"]["workflow"]["entry_point"] = "nonexistent_node"
    
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    # Manual reload should fail
    success = await marshal.reload_agent("test-agent")
    
    # Depending on implementation, this might return False or True
    # but validation errors should be tracked
    errors = marshal.get_validation_errors()
    assert "test-agent" in errors or success is False
    
    await marshal.stop()


# ============================================================================
# VALIDATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_validate_agent_success(agents_dir, create_yaml_file):
    """Test validating a valid agent"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    result = await marshal.validate_agent("test-agent")
    
    assert isinstance(result, ValidationResult)
    assert result.valid is True
    assert len(result.errors) == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_validate_agent_with_errors(agents_dir, valid_agent_yaml):
    """Test validating an invalid agent"""
    # Create invalid YAML (entry point doesn't exist)
    invalid_yaml = valid_agent_yaml.copy()
    invalid_yaml["spec"]["workflow"]["entry_point"] = "nonexistent"
    
    yaml_file = agents_dir / "invalid-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    result = await marshal.validate_agent("invalid-agent")
    
    assert isinstance(result, ValidationResult)
    assert result.valid is False
    assert len(result.errors) > 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_validate_nonexistent_agent(agents_dir):
    """Test validating non-existent agent"""
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    await marshal.start()
    
    result = await marshal.validate_agent("nonexistent")
    
    assert isinstance(result, ValidationResult)
    assert result.valid is False
    assert len(result.errors) > 0
    assert any("not found" in err.lower() for err in result.errors)
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_validation_result_structure(agents_dir, create_yaml_file):
    """Test ValidationResult has correct structure"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    await marshal.start()
    
    result = await marshal.validate_agent("test-agent")
    
    # Check all expected fields
    assert hasattr(result, 'valid')
    assert hasattr(result, 'agent_id')
    assert hasattr(result, 'errors')
    assert hasattr(result, 'warnings')
    
    assert isinstance(result.valid, bool)
    assert isinstance(result.errors, list)
    assert isinstance(result.warnings, list)
    
    await marshal.stop()


# ============================================================================
# STATUS SUMMARY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_status_summary_empty(agents_dir):
    """Test status summary with no agents"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    summary = await marshal.get_status_summary()
    
    # Verify structure
    assert "marshal" in summary
    assert "agents" in summary
    assert "health" in summary
    assert "validation_errors" in summary
    
    # Verify marshal section
    assert summary["marshal"]["running"] is True
    assert summary["marshal"]["file_watcher_enabled"] is False
    assert summary["marshal"]["health_monitor_enabled"] is False
    
    # Verify agents section
    assert summary["agents"]["total"] == 0
    assert summary["agents"]["healthy"] == 0
    assert summary["agents"]["unhealthy"] == 0
    assert len(summary["agents"]["list"]) == 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_status_summary_with_agents(agents_dir, create_yaml_file):
    """Test status summary with loaded agents"""
    create_yaml_file("agent-1")
    create_yaml_file("agent-2")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=True
    )
    
    await marshal.start()
    
    summary = await marshal.get_status_summary()
    
    # Verify marshal status
    assert summary["marshal"]["running"] is True
    assert summary["marshal"]["file_watcher_enabled"] is True
    assert summary["marshal"]["health_monitor_enabled"] is True
    assert Path(summary["marshal"]["agents_dir"]) == agents_dir
    
    # Verify agents counts
    assert summary["agents"]["total"] == 2
    assert len(summary["agents"]["list"]) == 2
    
    # Verify agent list structure
    agent_list = summary["agents"]["list"]
    for agent in agent_list:
        assert "id" in agent
        assert "name" in agent
        assert "version" in agent
        assert "state" in agent
        assert "phase" in agent
        assert "uptime_seconds" in agent
        assert "total_executions" in agent
        assert "success_rate" in agent
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_status_summary_agent_details(agents_dir, create_yaml_file):
    """Test that status summary includes correct agent details"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    await marshal.start()
    
    summary = await marshal.get_status_summary()
    
    agent_list = summary["agents"]["list"]
    assert len(agent_list) == 1
    
    agent = agent_list[0]
    assert agent["id"] == "test-agent"
    assert agent["name"] == "Test Agent"
    assert agent["version"] == "1.0.0"
    assert agent["state"] in ["active", "inactive", "paused", "error"]
    assert agent["phase"] in ["alpha", "beta", "production", "deprecated"]
    
    await marshal.stop()


# ============================================================================
# VALIDATION ERROR TRACKING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_validation_errors_tracking(agents_dir, valid_agent_yaml):
    """Test that validation errors are tracked"""
    # Create invalid YAML
    invalid_yaml = valid_agent_yaml.copy()
    del invalid_yaml["metadata"]["id"]
    
    yaml_file = agents_dir / "invalid-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    errors = marshal.get_validation_errors()
    
    # Should track validation error
    assert len(errors) > 0
    assert isinstance(errors, dict)
    
    # Each error should be a ValidationResult
    for agent_id, result in errors.items():
        assert isinstance(result, ValidationResult)
        assert result.valid is False
        assert len(result.errors) > 0
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_validation_errors_cleared_on_fix(agents_dir, valid_agent_yaml):
    """Test that validation errors are cleared when file is fixed"""
    # Create invalid YAML
    invalid_yaml = valid_agent_yaml.copy()
    invalid_yaml["spec"]["workflow"]["entry_point"] = "nonexistent"
    
    yaml_file = agents_dir / "test-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(1.5)
    
    # Should have validation error
    errors = marshal.get_validation_errors()
    assert len(errors) > 0
    
    # Fix the YAML
    fixed_yaml = valid_agent_yaml.copy()
    fixed_yaml["metadata"]["id"] = "test-agent"
    
    with open(yaml_file, 'w') as f:
        yaml.dump(fixed_yaml, f)
    
    # Wait for reload
    await asyncio.sleep(2.5)
    
    # Error should be cleared
    errors = marshal.get_validation_errors()
    assert "test-agent" not in errors
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_validation_errors_multiple_agents(agents_dir, valid_agent_yaml):
    """Test tracking validation errors for multiple agents"""
    # Create multiple invalid agents
    for i in range(1, 4):
        invalid_yaml = valid_agent_yaml.copy()
        invalid_yaml["spec"]["workflow"]["entry_point"] = "nonexistent"
        
        yaml_file = agents_dir / f"invalid-agent-{i}.agent.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    errors = marshal.get_validation_errors()
    
    # Should track all errors
    assert len(errors) >= 3
    
    await marshal.stop()


# ============================================================================
# EDGE CASES AND ERROR RECOVERY
# ============================================================================

@pytest.mark.asyncio
async def test_nonexistent_agents_directory():
    """Test Marshal with non-existent directory"""
    nonexistent = Path("/nonexistent/agents")
    
    marshal = MarshalAgent(
        agents_dir=nonexistent,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    # Should handle gracefully during start
    await marshal.start()
    
    assert await marshal.registry.count() == 0
    assert marshal._running is True
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_concurrent_operations(agents_dir, create_yaml_file):
    """Test concurrent Marshal operations"""
    create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    # Perform multiple operations concurrently
    tasks = [
        marshal.reload_agent("test-agent"),
        marshal.validate_agent("test-agent"),
        marshal.get_status_summary(),
        marshal.reload_agent("test-agent"),  # Duplicate reload
        marshal.get_status_summary(),  # Duplicate summary
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All should complete without exceptions
    assert len(results) == 5
    for result in results:
        assert not isinstance(result, Exception)
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_is_running_property(agents_dir):
    """Test is_running property"""
    marshal = MarshalAgent(agents_dir=agents_dir)
    
    assert marshal.is_running is False
    assert marshal._running is False
    
    await marshal.start()
    assert marshal.is_running is True
    assert marshal._running is True
    
    await marshal.stop()
    assert marshal.is_running is False
    assert marshal._running is False


@pytest.mark.asyncio
async def test_double_start(agents_dir):
    """Test calling start() twice"""
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    assert marshal.is_running is True
    
    # Second start - implementation should handle gracefully
    # Either ignore or raise appropriate error
    try:
        await marshal.start()
        # If it succeeds, verify state is still correct
        assert marshal.is_running is True
    except RuntimeError:
        # If it raises, that's also acceptable behavior
        pass
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_rapid_file_changes(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test handling rapid successive file changes"""
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=True,
        enable_health_monitor=False
    )
    
    await marshal.start()
    await asyncio.sleep(1.5)
    
    # Make rapid changes
    for version in range(2, 6):
        modified_yaml = valid_agent_yaml.copy()
        modified_yaml["metadata"]["id"] = "test-agent"
        modified_yaml["metadata"]["version"] = f"{version}.0.0"
        
        with open(yaml_file, 'w') as f:
            yaml.dump(modified_yaml, f)
        
        await asyncio.sleep(0.1)  # Very short delay
    
    # Wait for all changes to process
    await asyncio.sleep(3.0)
    
    # Agent should still be loaded and have final version
    assert await marshal.registry.exists("test-agent")
    agent = await marshal.registry.get("test-agent")
    # Should have some version (exact version depends on race conditions)
    assert agent.metadata.version in ["2.0.0", "3.0.0", "4.0.0", "5.0.0"]
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_get_validation_errors_returns_copy(agents_dir, valid_agent_yaml):
    """Test that get_validation_errors returns a copy, not reference"""
    # Create invalid agent
    invalid_yaml = valid_agent_yaml.copy()
    invalid_yaml["spec"]["workflow"]["entry_point"] = "nonexistent"
    
    yaml_file = agents_dir / "invalid-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(invalid_yaml, f)
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    errors1 = marshal.get_validation_errors()
    errors2 = marshal.get_validation_errors()
    
    # Should be separate objects
    assert errors1 is not errors2
    
    # But have same content
    assert errors1.keys() == errors2.keys()
    
    await marshal.stop()


@pytest.mark.asyncio
async def test_file_watcher_disabled_no_auto_reload(agents_dir, create_yaml_file, valid_agent_yaml):
    """Test that disabling file watcher prevents auto-reload"""
    yaml_file = create_yaml_file("test-agent")
    
    marshal = MarshalAgent(
        agents_dir=agents_dir,
        enable_file_watcher=False,  # Disabled
        enable_health_monitor=False
    )
    
    await marshal.start()
    
    agent = await marshal.registry.get("test-agent")
    assert agent.metadata.version == "1.0.0"
    
    # Modify file
    modified_yaml = valid_agent_yaml.copy()
    modified_yaml["metadata"]["id"] = "test-agent"
    modified_yaml["metadata"]["version"] = "2.0.0"
    
    with open(yaml_file, 'w') as f:
        yaml.dump(modified_yaml, f)
    
    # Wait - should NOT reload automatically
    await asyncio.sleep(2.0)
    
    agent = await marshal.registry.get("test-agent")
    # Should still be old version
    assert agent.metadata.version == "1.0.0"
    
    await marshal.stop()
