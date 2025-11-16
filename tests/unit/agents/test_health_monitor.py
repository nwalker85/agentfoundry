"""
Unit tests for health monitor.

Tests:
- Health check execution
- Metrics collection
- Health status tracking
- Failure detection
- Recovery detection
- Alert generation
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from agents.health_monitor import (
    HealthMonitor,
    HealthCheck,
    AgentHealthMetrics
)
from agents.agent_registry import AgentRegistry, AgentInstance, AgentStatus
from agents.yaml_validator import AgentMetadata


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def registry():
    """Create AgentRegistry"""
    return AgentRegistry()


@pytest.fixture
def health_monitor(registry):
    """Create HealthMonitor with short check interval for testing"""
    return HealthMonitor(
        registry=registry,
        check_interval_seconds=1  # Short interval for tests
    )


@pytest.fixture
async def mock_healthy_agent(registry):
    """Create and register a healthy mock agent"""
    metadata = AgentMetadata(
        id="healthy-agent",
        name="Healthy Agent",
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
    instance.status.state = "healthy"
    instance.status.phase = "ready"
    
    await registry.register("healthy-agent", instance)
    return instance


@pytest.fixture
async def mock_unhealthy_agent(registry):
    """Create and register an unhealthy mock agent"""
    metadata = AgentMetadata(
        id="unhealthy-agent",
        name="Unhealthy Agent",
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
    instance.status.state = "unhealthy"
    instance.status.phase = "error"
    
    await registry.register("unhealthy-agent", instance)
    return instance


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_health_check_healthy_agent(health_monitor, mock_healthy_agent):
    """Test health check on healthy agent"""
    result = await health_monitor.check_agent_health("healthy-agent")
    
    assert result is not None
    assert result.healthy is True
    assert result.agent_id == "healthy-agent"
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_health_check_unhealthy_agent(health_monitor, mock_unhealthy_agent):
    """Test health check on unhealthy agent"""
    result = await health_monitor.check_agent_health("unhealthy-agent")
    
    assert result is not None
    assert result.healthy is False
    assert result.agent_id == "unhealthy-agent"


@pytest.mark.asyncio
async def test_health_check_nonexistent_agent(health_monitor):
    """Test health check on non-existent agent"""
    result = await health_monitor.check_agent_health("nonexistent")
    
    assert result is not None
    assert result.healthy is False
    assert result.error_message is not None


# ============================================================================
# MONITORING LIFECYCLE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_start_health_monitor(health_monitor, mock_healthy_agent):
    """Test starting health monitor"""
    task = asyncio.create_task(health_monitor.start())
    
    # Let it run for a bit
    await asyncio.sleep(2.5)
    
    # Stop monitor
    await health_monitor.stop()
    await task
    
    # Should have performed checks
    metrics = health_monitor.get_metrics("healthy-agent")
    assert metrics is not None
    assert metrics.total_checks > 0


@pytest.mark.asyncio
async def test_stop_before_start(health_monitor):
    """Test stopping monitor that was never started"""
    await health_monitor.stop()
    # Should handle gracefully


@pytest.mark.asyncio
async def test_multiple_check_cycles(health_monitor, mock_healthy_agent):
    """Test that monitor performs multiple check cycles"""
    task = asyncio.create_task(health_monitor.start())
    
    # Let it run for multiple cycles
    await asyncio.sleep(3.5)
    
    await health_monitor.stop()
    await task
    
    # Should have performed multiple checks
    metrics = health_monitor.get_metrics("healthy-agent")
    assert metrics.total_checks >= 2


# ============================================================================
# METRICS COLLECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_initialization(health_monitor, mock_healthy_agent):
    """Test that metrics are initialized on first check"""
    await health_monitor.check_agent_health("healthy-agent")
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    assert metrics is not None
    assert metrics.agent_id == "healthy-agent"
    assert metrics.total_checks == 1
    assert metrics.successful_checks == 1


@pytest.mark.asyncio
async def test_metrics_accumulation(health_monitor, mock_healthy_agent):
    """Test that metrics accumulate over multiple checks"""
    # Perform multiple checks
    for _ in range(5):
        await health_monitor.check_agent_health("healthy-agent")
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    assert metrics.total_checks == 5
    assert metrics.successful_checks == 5


@pytest.mark.asyncio
async def test_metrics_failed_checks(health_monitor, mock_unhealthy_agent):
    """Test metrics for failed checks"""
    # Perform checks on unhealthy agent
    for _ in range(3):
        await health_monitor.check_agent_health("unhealthy-agent")
    
    metrics = health_monitor.get_metrics("unhealthy-agent")
    
    assert metrics.total_checks == 3
    assert metrics.failed_checks == 3
    assert metrics.successful_checks == 0


@pytest.mark.asyncio
async def test_health_rate_calculation(health_monitor, registry):
    """Test health rate calculation"""
    # Create agent and perform mixed checks
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
    
    # Perform some successful checks
    instance.status.state = "healthy"
    for _ in range(7):
        await health_monitor.check_agent_health("test-agent")
    
    # Then some failed checks
    instance.status.state = "unhealthy"
    for _ in range(3):
        await health_monitor.check_agent_health("test-agent")
    
    metrics = health_monitor.get_metrics("test-agent")
    
    assert metrics.total_checks == 10
    assert metrics.successful_checks == 7
    assert metrics.failed_checks == 3
    assert metrics.health_rate == 0.7


# ============================================================================
# LATENCY TRACKING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_latency_measurement(health_monitor, mock_healthy_agent):
    """Test that latency is measured for checks"""
    await health_monitor.check_agent_health("healthy-agent")
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    assert metrics.avg_latency_ms >= 0
    assert metrics.avg_latency_ms < 1000  # Should be fast


@pytest.mark.asyncio
async def test_average_latency_calculation(health_monitor, mock_healthy_agent):
    """Test average latency calculation over multiple checks"""
    # Perform multiple checks
    for _ in range(10):
        await health_monitor.check_agent_health("healthy-agent")
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    # Average should be reasonable
    assert metrics.avg_latency_ms >= 0
    assert metrics.avg_latency_ms < 100


# ============================================================================
# FAILURE DETECTION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_consecutive_failures_tracking(health_monitor, mock_unhealthy_agent):
    """Test tracking consecutive failures"""
    # Perform multiple failed checks
    for _ in range(5):
        await health_monitor.check_agent_health("unhealthy-agent")
    
    metrics = health_monitor.get_metrics("unhealthy-agent")
    
    assert metrics.consecutive_failures == 5


@pytest.mark.asyncio
async def test_consecutive_failures_reset_on_success(health_monitor, registry):
    """Test that consecutive failures reset on successful check"""
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
    
    # Some failures
    instance.status.state = "unhealthy"
    for _ in range(3):
        await health_monitor.check_agent_health("test-agent")
    
    # Then success
    instance.status.state = "healthy"
    await health_monitor.check_agent_health("test-agent")
    
    metrics = health_monitor.get_metrics("test-agent")
    
    # Consecutive failures should reset
    assert metrics.consecutive_failures == 0


# ============================================================================
# RECENT CHECKS HISTORY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_recent_checks_storage(health_monitor, mock_healthy_agent):
    """Test that recent checks are stored"""
    # Perform some checks
    for _ in range(5):
        await health_monitor.check_agent_health("healthy-agent")
    
    recent = health_monitor.get_recent_checks("healthy-agent", limit=10)
    
    assert len(recent) == 5


@pytest.mark.asyncio
async def test_recent_checks_limit(health_monitor, mock_healthy_agent):
    """Test that recent checks respects limit"""
    # Perform many checks
    for _ in range(20):
        await health_monitor.check_agent_health("healthy-agent")
    
    # Request limited number
    recent = health_monitor.get_recent_checks("healthy-agent", limit=5)
    
    assert len(recent) == 5


@pytest.mark.asyncio
async def test_recent_checks_ordering(health_monitor, mock_healthy_agent):
    """Test that recent checks are in reverse chronological order"""
    # Perform checks
    for _ in range(5):
        await health_monitor.check_agent_health("healthy-agent")
        await asyncio.sleep(0.1)
    
    recent = health_monitor.get_recent_checks("healthy-agent", limit=10)
    
    # Should be newest first
    for i in range(len(recent) - 1):
        assert recent[i].timestamp >= recent[i + 1].timestamp


# ============================================================================
# HEALTH SUMMARY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_health_summary_empty_registry(health_monitor):
    """Test health summary with no agents"""
    summary = health_monitor.get_health_summary()
    
    assert summary["total_agents"] == 0
    assert summary["healthy_agents"] == 0
    assert summary["unhealthy_agents"] == 0


@pytest.mark.asyncio
async def test_health_summary_mixed_agents(
    health_monitor,
    mock_healthy_agent,
    mock_unhealthy_agent
):
    """Test health summary with mixed healthy/unhealthy agents"""
    # Perform checks
    await health_monitor.check_agent_health("healthy-agent")
    await health_monitor.check_agent_health("unhealthy-agent")
    
    summary = health_monitor.get_health_summary()
    
    assert summary["total_agents"] == 2
    assert summary["healthy_agents"] == 1
    assert summary["unhealthy_agents"] == 1


@pytest.mark.asyncio
async def test_overall_health_rate(health_monitor, registry):
    """Test overall health rate calculation"""
    # Create multiple agents with different health states
    for i in range(5):
        metadata = AgentMetadata(
            id=f"agent-{i}",
            name=f"Agent {i}",
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
        
        # 3 healthy, 2 unhealthy
        instance.status.state = "healthy" if i < 3 else "unhealthy"
        
        await registry.register(f"agent-{i}", instance)
        await health_monitor.check_agent_health(f"agent-{i}")
    
    summary = health_monitor.get_health_summary()
    
    assert summary["total_agents"] == 5
    assert summary["healthy_agents"] == 3
    assert summary["overall_health_rate"] == 0.6


# ============================================================================
# METRICS RETRIEVAL TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_metrics_nonexistent_agent(health_monitor):
    """Test getting metrics for non-existent agent"""
    metrics = health_monitor.get_metrics("nonexistent")
    
    assert metrics is None


@pytest.mark.asyncio
async def test_get_metrics_before_check(health_monitor, mock_healthy_agent):
    """Test getting metrics before any checks performed"""
    metrics = health_monitor.get_metrics("healthy-agent")
    
    # Should be None or empty metrics
    assert metrics is None or metrics.total_checks == 0


# ============================================================================
# UPTIME TRACKING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_uptime_calculation(health_monitor, mock_healthy_agent):
    """Test uptime calculation"""
    # First check
    await health_monitor.check_agent_health("healthy-agent")
    
    # Wait a bit
    await asyncio.sleep(1.0)
    
    # Second check
    await health_monitor.check_agent_health("healthy-agent")
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    # Uptime should be >= 1 second
    assert metrics.uptime_seconds >= 1


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_checks(health_monitor, mock_healthy_agent):
    """Test concurrent health checks"""
    # Perform multiple checks concurrently
    tasks = [
        health_monitor.check_agent_health("healthy-agent")
        for _ in range(10)
    ]
    
    await asyncio.gather(*tasks)
    
    metrics = health_monitor.get_metrics("healthy-agent")
    
    # Should have recorded all checks
    assert metrics.total_checks == 10


@pytest.mark.asyncio
async def test_agent_removal_during_monitoring(health_monitor, registry, mock_healthy_agent):
    """Test handling agent removal during monitoring"""
    task = asyncio.create_task(health_monitor.start())
    await asyncio.sleep(1.5)
    
    # Remove agent
    await registry.unregister("healthy-agent")
    
    await asyncio.sleep(1.5)
    
    await health_monitor.stop()
    await task
    
    # Should handle gracefully
