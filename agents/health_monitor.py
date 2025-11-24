"""
Health Monitor - Periodic health checks and metrics collection for agents

Responsibilities:
- Periodic health checks on all registered agents
- Metrics collection (uptime, success rate, latency)
- Alert generation for unhealthy agents
- Reporting to admin endpoints
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime

from .agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    agent_id: str
    timestamp: datetime
    healthy: bool
    latency_ms: float
    error_message: str | None = None


@dataclass
class AgentMetrics:
    """Aggregated metrics for an agent."""

    agent_id: str
    uptime_seconds: int
    total_checks: int
    successful_checks: int
    failed_checks: int
    avg_latency_ms: float
    last_check: datetime | None = None
    consecutive_failures: int = 0

    @property
    def health_rate(self) -> float:
        """Calculate health check success rate."""
        if self.total_checks == 0:
            return 0.0
        return self.successful_checks / self.total_checks


@dataclass
class HealthAlert:
    """Alert for unhealthy agent."""

    agent_id: str
    severity: str  # 'warning', 'critical'
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0


class HealthMonitor:
    """
    Monitors health of all registered agents.

    Features:
    - Periodic health checks (configurable interval)
    - Metrics aggregation
    - Alert generation for unhealthy agents
    - Historical health data retention
    """

    def __init__(self, registry: AgentRegistry, check_interval_seconds: int = 60, unhealthy_threshold: int = 3):
        """Initialize health monitor.

        Args:
            registry: AgentRegistry to monitor
            check_interval_seconds: Seconds between health checks
            unhealthy_threshold: Failed checks before alerting
        """
        self.registry = registry
        self.check_interval_seconds = check_interval_seconds
        self.unhealthy_threshold = unhealthy_threshold

        self._running = False
        self._metrics: dict[str, AgentMetrics] = {}
        self._recent_checks: list[HealthCheckResult] = []
        self._alerts: list[HealthAlert] = []
        self._max_recent_checks = 1000  # Keep last 1000 checks

        logger.info(f"HealthMonitor initialized (interval={check_interval_seconds}s, threshold={unhealthy_threshold})")

    async def start(self):
        """Start health monitoring loop.

        This is a long-running task that should be run in the background.
        """
        logger.info("Starting health monitor...")
        self._running = True

        try:
            while self._running:
                await self._run_health_checks()
                await asyncio.sleep(self.check_interval_seconds)
        except Exception as e:
            logger.error(f"Health monitor error: {e}", exc_info=True)
            raise
        finally:
            logger.info("Health monitor stopped")

    async def stop(self):
        """Stop health monitoring."""
        logger.info("Stopping health monitor...")
        self._running = False

    async def _run_health_checks(self):
        """Run health checks on all registered agents."""
        agent_ids = await self.registry.list_ids()

        if not agent_ids:
            logger.debug("No agents to check")
            return

        logger.info(f"Running health checks on {len(agent_ids)} agents")

        # Run checks concurrently
        tasks = [self._check_agent_health(agent_id) for agent_id in agent_ids]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
            elif result:
                self._process_health_check(result)

    async def _check_agent_health(self, agent_id: str) -> HealthCheckResult | None:
        """Check health of a single agent.

        Args:
            agent_id: Agent to check

        Returns:
            HealthCheckResult if agent exists, None otherwise
        """
        instance = await self.registry.get(agent_id)
        if not instance:
            logger.warning(f"Agent {agent_id} not found in registry")
            return None

        # Measure health check latency
        start_time = datetime.now()

        try:
            # Run agent's health check
            is_healthy = await instance.health_check()

            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = HealthCheckResult(
                agent_id=agent_id, timestamp=start_time, healthy=is_healthy, latency_ms=latency_ms
            )

            logger.debug(f"Health check for {agent_id}: {'✓' if is_healthy else 'X'} ({latency_ms:.2f}ms)")

            return result

        except Exception as e:
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.error(f"Health check exception for {agent_id}: {e}")

            return HealthCheckResult(
                agent_id=agent_id, timestamp=start_time, healthy=False, latency_ms=latency_ms, error_message=str(e)
            )

    def _process_health_check(self, result: HealthCheckResult):
        """Process health check result and update metrics.

        Args:
            result: Health check result to process
        """
        agent_id = result.agent_id

        # Initialize metrics if needed
        if agent_id not in self._metrics:
            self._metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                uptime_seconds=0,
                total_checks=0,
                successful_checks=0,
                failed_checks=0,
                avg_latency_ms=0.0,
            )

        metrics = self._metrics[agent_id]

        # Update metrics
        metrics.total_checks += 1
        metrics.last_check = result.timestamp

        if result.healthy:
            metrics.successful_checks += 1
            metrics.consecutive_failures = 0
        else:
            metrics.failed_checks += 1
            metrics.consecutive_failures += 1

        # Update rolling average latency
        total_latency = metrics.avg_latency_ms * (metrics.total_checks - 1)
        metrics.avg_latency_ms = (total_latency + result.latency_ms) / metrics.total_checks

        # Check for alert conditions
        if metrics.consecutive_failures >= self.unhealthy_threshold:
            self._generate_alert(agent_id, metrics)

        # Store recent check
        self._recent_checks.append(result)

        # Trim old checks
        if len(self._recent_checks) > self._max_recent_checks:
            self._recent_checks = self._recent_checks[-self._max_recent_checks :]

    def _generate_alert(self, agent_id: str, metrics: AgentMetrics):
        """Generate alert for unhealthy agent.

        Args:
            agent_id: Agent ID
            metrics: Current metrics
        """
        # Determine severity
        severity = "critical" if metrics.consecutive_failures >= 10 else "warning"

        # Create alert
        alert = HealthAlert(
            agent_id=agent_id,
            severity=severity,
            message=(f"Agent {agent_id} failed {metrics.consecutive_failures} consecutive health checks"),
            consecutive_failures=metrics.consecutive_failures,
        )

        self._alerts.append(alert)

        logger.warning(f"🚨 {severity.upper()}: {alert.message} (health_rate={metrics.health_rate:.1%})")

    def get_metrics(self, agent_id: str) -> AgentMetrics | None:
        """Get metrics for specific agent.

        Args:
            agent_id: Agent ID

        Returns:
            AgentMetrics if available, None otherwise
        """
        return self._metrics.get(agent_id)

    def get_all_metrics(self) -> dict[str, AgentMetrics]:
        """Get metrics for all agents.

        Returns:
            Dictionary of agent_id -> AgentMetrics
        """
        return self._metrics.copy()

    def get_recent_checks(self, agent_id: str | None = None, limit: int = 100) -> list[HealthCheckResult]:
        """Get recent health check results.

        Args:
            agent_id: Optional filter by agent ID
            limit: Maximum number of results

        Returns:
            List of recent health checks
        """
        checks = self._recent_checks

        if agent_id:
            checks = [c for c in checks if c.agent_id == agent_id]

        return checks[-limit:]

    def get_active_alerts(self, severity: str | None = None) -> list[HealthAlert]:
        """Get active alerts.

        Args:
            severity: Optional filter by severity ('warning' or 'critical')

        Returns:
            List of active alerts
        """
        alerts = self._alerts

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def clear_alerts(self, agent_id: str | None = None):
        """Clear alerts.

        Args:
            agent_id: Optional filter - clear only alerts for this agent
        """
        if agent_id:
            self._alerts = [a for a in self._alerts if a.agent_id != agent_id]
            logger.info(f"Cleared alerts for {agent_id}")
        else:
            self._alerts.clear()
            logger.info("Cleared all alerts")

    def get_health_summary(self) -> dict:
        """Get overall health summary.

        Returns:
            Dictionary with aggregate health metrics
        """
        total_agents = len(self._metrics)
        healthy_agents = sum(1 for m in self._metrics.values() if m.consecutive_failures == 0)

        total_checks = sum(m.total_checks for m in self._metrics.values())
        total_successful = sum(m.successful_checks for m in self._metrics.values())

        overall_health_rate = total_successful / total_checks if total_checks > 0 else 0.0

        critical_alerts = len([a for a in self._alerts if a.severity == "critical"])
        warning_alerts = len([a for a in self._alerts if a.severity == "warning"])

        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "unhealthy_agents": total_agents - healthy_agents,
            "overall_health_rate": overall_health_rate,
            "total_checks": total_checks,
            "critical_alerts": critical_alerts,
            "warning_alerts": warning_alerts,
            "monitoring_interval_seconds": self.check_interval_seconds,
        }

    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running
