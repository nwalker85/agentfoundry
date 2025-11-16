"""
Observability Agent - Runtime monitoring and tracing

Responsibilities:
- Collect execution traces for all agent runs
- Track performance metrics (latency, throughput)
- Create state snapshots at each node
- Monitor resource usage (tokens, API calls, cost)
- Detect anomalies in agent behavior
- Enable execution playback for debugging
- Send traces to external systems (LangSmith, DataDog, etc.)

Platform agent (Tier 1 - Production Required).
"""

import asyncio
import logging
import time
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExecutionTrace:
    """Single execution trace record"""
    trace_id: str
    agent_id: str
    node_id: str
    timestamp: str
    duration_ms: float
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentMetrics:
    """Aggregated metrics for an agent"""
    agent_id: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_latency_ms: float
    total_tokens: int
    total_cost_usd: float
    timestamp: str


class ObservabilityAgent:
    """
    Platform agent for runtime monitoring and observability.
    Collects traces, metrics, and enables debugging.
    """
    
    def __init__(self, langsmith_enabled: bool = False):
        """
        Initialize Observability Agent.
        
        Args:
            langsmith_enabled: Whether to send traces to LangSmith
        """
        self.langsmith_enabled = langsmith_enabled
        
        # In-memory trace storage (production would use persistent store)
        self._traces: List[ExecutionTrace] = []
        self._active_traces: Dict[str, Dict[str, Any]] = {}
        
        # Metrics storage
        self._metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Anomaly detection thresholds
        self._anomaly_thresholds = {
            'max_latency_ms': 30000,  # 30 seconds
            'max_tokens': 100000,
            'max_cost_usd': 10.0,
            'error_rate_threshold': 0.5  # 50%
        }
        
        logger.info("ObservabilityAgent initialized")
    
    async def start_trace(
        self,
        agent_id: str,
        execution_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new execution trace.
        
        Args:
            agent_id: Agent being executed
            execution_id: Unique execution identifier
            metadata: Additional context
        
        Returns:
            Trace ID
        """
        trace_id = f"{agent_id}:{execution_id}:{int(time.time() * 1000)}"
        
        self._active_traces[trace_id] = {
            'agent_id': agent_id,
            'execution_id': execution_id,
            'start_time': time.time(),
            'nodes': [],
            'metadata': metadata or {},
            'state_snapshots': []
        }
        
        logger.info(f"Started trace: {trace_id}")
        return trace_id
    
    async def log_node_execution(
        self,
        trace_id: str,
        node_id: str,
        input_state: Dict[str, Any],
        output_state: Dict[str, Any],
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost_usd: Optional[float] = None
    ):
        """
        Log execution of a single node.
        
        Args:
            trace_id: Trace identifier
            node_id: Node that was executed
            input_state: State before node execution
            output_state: State after node execution
            duration_ms: Execution time in milliseconds
            success: Whether execution succeeded
            error: Error message if failed
            tokens_used: Tokens consumed (for LLM nodes)
            cost_usd: Estimated cost in USD
        """
        if trace_id not in self._active_traces:
            logger.warning(f"Unknown trace ID: {trace_id}")
            return
        
        trace_record = ExecutionTrace(
            trace_id=trace_id,
            agent_id=self._active_traces[trace_id]['agent_id'],
            node_id=node_id,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            input_state=self._sanitize_state(input_state),
            output_state=self._sanitize_state(output_state),
            success=success,
            error=error,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            metadata=self._active_traces[trace_id]['metadata']
        )
        
        # Add to active trace
        self._active_traces[trace_id]['nodes'].append(asdict(trace_record))
        
        # Store in permanent traces
        self._traces.append(trace_record)
        
        # Limit trace storage (keep last 10000)
        if len(self._traces) > 10000:
            self._traces.pop(0)
        
        logger.debug(f"Logged node execution: {node_id} ({duration_ms:.2f}ms)")
        
        # Check for anomalies
        await self._check_anomalies(trace_record)
    
    async def create_state_snapshot(
        self,
        trace_id: str,
        node_id: str,
        state: Dict[str, Any]
    ):
        """
        Create a snapshot of state at a specific node (for debugging).
        
        Args:
            trace_id: Trace identifier
            node_id: Node where snapshot was taken
            state: Current state
        """
        if trace_id not in self._active_traces:
            return
        
        snapshot = {
            'node_id': node_id,
            'timestamp': datetime.now().isoformat(),
            'state': self._sanitize_state(state)
        }
        
        self._active_traces[trace_id]['state_snapshots'].append(snapshot)
        logger.debug(f"Created state snapshot at {node_id}")
    
    async def end_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        End an execution trace and compute summary.
        
        Args:
            trace_id: Trace identifier
        
        Returns:
            Trace summary with metrics
        """
        if trace_id not in self._active_traces:
            logger.warning(f"Unknown trace ID: {trace_id}")
            return {}
        
        trace_data = self._active_traces[trace_id]
        end_time = time.time()
        total_duration_ms = (end_time - trace_data['start_time']) * 1000
        
        # Compute summary
        nodes_executed = len(trace_data['nodes'])
        successful_nodes = sum(1 for n in trace_data['nodes'] if n['success'])
        failed_nodes = nodes_executed - successful_nodes
        total_tokens = sum(n.get('tokens_used', 0) or 0 for n in trace_data['nodes'])
        total_cost = sum(n.get('cost_usd', 0) or 0 for n in trace_data['nodes'])
        
        summary = {
            'trace_id': trace_id,
            'agent_id': trace_data['agent_id'],
            'execution_id': trace_data['execution_id'],
            'total_duration_ms': total_duration_ms,
            'nodes_executed': nodes_executed,
            'successful_nodes': successful_nodes,
            'failed_nodes': failed_nodes,
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'state_snapshots_count': len(trace_data['state_snapshots']),
            'metadata': trace_data['metadata']
        }
        
        # Store metrics
        await self._store_metrics(trace_data['agent_id'], summary)
        
        # Send to LangSmith if enabled
        if self.langsmith_enabled:
            await self._send_to_langsmith(trace_id, trace_data, summary)
        
        # Clean up active trace
        del self._active_traces[trace_id]
        
        logger.info(f"Ended trace: {trace_id} ({total_duration_ms:.2f}ms, {nodes_executed} nodes)")
        return summary
    
    def _sanitize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize state for storage (remove sensitive data, limit size).
        
        Args:
            state: Raw state
        
        Returns:
            Sanitized state
        """
        # Deep copy to avoid modifying original
        sanitized = {}
        
        for key, value in state.items():
            # Skip very large values
            if isinstance(value, (list, dict)):
                try:
                    serialized = json.dumps(value)
                    if len(serialized) > 10000:  # 10KB limit
                        sanitized[key] = f"<large_value: {len(serialized)} bytes>"
                        continue
                except (TypeError, ValueError):
                    sanitized[key] = "<non_serializable>"
                    continue
            
            # Redact sensitive keys
            sensitive_keys = ['password', 'api_key', 'secret', 'token', 'credential']
            if any(sens in key.lower() for sens in sensitive_keys):
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _check_anomalies(self, trace_record: ExecutionTrace):
        """
        Check for anomalies in execution and log warnings.
        
        Args:
            trace_record: Execution trace to check
        """
        anomalies = []
        
        # Check latency
        if trace_record.duration_ms > self._anomaly_thresholds['max_latency_ms']:
            anomalies.append(f"High latency: {trace_record.duration_ms:.2f}ms")
        
        # Check tokens
        if trace_record.tokens_used and trace_record.tokens_used > self._anomaly_thresholds['max_tokens']:
            anomalies.append(f"High token usage: {trace_record.tokens_used}")
        
        # Check cost
        if trace_record.cost_usd and trace_record.cost_usd > self._anomaly_thresholds['max_cost_usd']:
            anomalies.append(f"High cost: ${trace_record.cost_usd:.2f}")
        
        # Check errors
        if not trace_record.success:
            anomalies.append(f"Execution failed: {trace_record.error}")
        
        if anomalies:
            logger.warning(f"Anomalies detected in {trace_record.node_id}: {', '.join(anomalies)}")
    
    async def _store_metrics(self, agent_id: str, summary: Dict[str, Any]):
        """
        Store aggregated metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            summary: Execution summary
        """
        metric = {
            'timestamp': datetime.now().isoformat(),
            'total_duration_ms': summary['total_duration_ms'],
            'nodes_executed': summary['nodes_executed'],
            'successful': summary['failed_nodes'] == 0,
            'tokens': summary['total_tokens'],
            'cost': summary['total_cost_usd']
        }
        
        self._metrics[agent_id].append(metric)
        
        # Limit metrics storage (keep last 1000 per agent)
        if len(self._metrics[agent_id]) > 1000:
            self._metrics[agent_id].pop(0)
    
    async def _send_to_langsmith(
        self,
        trace_id: str,
        trace_data: Dict[str, Any],
        summary: Dict[str, Any]
    ):
        """
        Send trace to LangSmith for visualization.
        
        Args:
            trace_id: Trace identifier
            trace_data: Full trace data
            summary: Execution summary
        """
        # TODO: Implement actual LangSmith integration
        logger.info(f"Would send trace {trace_id} to LangSmith (not yet implemented)")
        
        # LangSmith integration would use:
        # from langsmith import Client
        # client = Client()
        # client.create_run(...)
    
    async def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full trace data by ID.
        
        Args:
            trace_id: Trace identifier
        
        Returns:
            Trace data or None if not found
        """
        # Check active traces
        if trace_id in self._active_traces:
            return self._active_traces[trace_id]
        
        # Check stored traces
        matching_traces = [t for t in self._traces if t.trace_id == trace_id]
        if matching_traces:
            return {
                'trace_id': trace_id,
                'nodes': [asdict(t) for t in matching_traces],
                'status': 'completed'
            }
        
        return None
    
    async def get_agent_traces(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent traces for a specific agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of traces to return
        
        Returns:
            List of trace summaries
        """
        # Group traces by execution
        trace_groups = defaultdict(list)
        for trace in reversed(self._traces[-limit * 10:]):  # Search more traces
            if trace.agent_id == agent_id:
                trace_groups[trace.trace_id].append(trace)
        
        # Build summaries
        summaries = []
        for trace_id, traces in list(trace_groups.items())[:limit]:
            summaries.append({
                'trace_id': trace_id,
                'agent_id': agent_id,
                'nodes_count': len(traces),
                'success': all(t.success for t in traces),
                'total_duration_ms': sum(t.duration_ms for t in traces),
                'total_tokens': sum(t.tokens_used or 0 for t in traces),
                'total_cost': sum(t.cost_usd or 0 for t in traces),
                'timestamp': traces[0].timestamp
            })
        
        return summaries
    
    async def get_metrics(
        self,
        agent_id: str,
        time_window_hours: int = 24
    ) -> AgentMetrics:
        """
        Get aggregated metrics for an agent.
        
        Args:
            agent_id: Agent identifier
            time_window_hours: Time window in hours
        
        Returns:
            Aggregated metrics
        """
        if agent_id not in self._metrics:
            return AgentMetrics(
                agent_id=agent_id,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                avg_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        metrics = self._metrics[agent_id]
        
        # Filter by time window
        cutoff = datetime.now().timestamp() - (time_window_hours * 3600)
        recent_metrics = [
            m for m in metrics
            if datetime.fromisoformat(m['timestamp']).timestamp() > cutoff
        ]
        
        if not recent_metrics:
            return AgentMetrics(
                agent_id=agent_id,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                avg_latency_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                timestamp=datetime.now().isoformat()
            )
        
        total = len(recent_metrics)
        successful = sum(1 for m in recent_metrics if m['successful'])
        failed = total - successful
        avg_latency = sum(m['total_duration_ms'] for m in recent_metrics) / total
        total_tokens = sum(m['tokens'] for m in recent_metrics)
        total_cost = sum(m['cost'] for m in recent_metrics)
        
        return AgentMetrics(
            agent_id=agent_id,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            avg_latency_ms=avg_latency,
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            timestamp=datetime.now().isoformat()
        )
    
    async def get_execution_playback(self, trace_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get execution playback data for debugging (step-by-step state changes).
        
        Args:
            trace_id: Trace identifier
        
        Returns:
            List of execution steps with state transitions
        """
        trace_data = await self.get_trace(trace_id)
        if not trace_data:
            return None
        
        playback = []
        for node_data in trace_data.get('nodes', []):
            step = {
                'node_id': node_data['node_id'],
                'timestamp': node_data['timestamp'],
                'duration_ms': node_data['duration_ms'],
                'input_state': node_data['input_state'],
                'output_state': node_data['output_state'],
                'success': node_data['success'],
                'error': node_data.get('error'),
                'tokens_used': node_data.get('tokens_used'),
                'cost_usd': node_data.get('cost_usd')
            }
            playback.append(step)
        
        return playback
    
    async def detect_performance_degradation(
        self,
        agent_id: str,
        threshold_increase: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect if agent performance has degraded recently.
        
        Args:
            agent_id: Agent to check
            threshold_increase: Threshold for degradation (e.g., 1.5 = 50% slower)
        
        Returns:
            Degradation analysis
        """
        if agent_id not in self._metrics or len(self._metrics[agent_id]) < 10:
            return {'degraded': False, 'reason': 'Insufficient data'}
        
        metrics = self._metrics[agent_id]
        
        # Compare recent performance to baseline
        baseline = metrics[-100:-50] if len(metrics) > 100 else metrics[:len(metrics)//2]
        recent = metrics[-50:]
        
        if not baseline or not recent:
            return {'degraded': False, 'reason': 'Insufficient data'}
        
        baseline_latency = sum(m['total_duration_ms'] for m in baseline) / len(baseline)
        recent_latency = sum(m['total_duration_ms'] for m in recent) / len(recent)
        
        if recent_latency > baseline_latency * threshold_increase:
            return {
                'degraded': True,
                'baseline_latency_ms': baseline_latency,
                'recent_latency_ms': recent_latency,
                'increase_percentage': ((recent_latency / baseline_latency) - 1) * 100,
                'recommendation': 'Investigate recent code changes or infrastructure issues'
            }
        
        return {'degraded': False, 'recent_latency_ms': recent_latency}
    
    async def export_traces(
        self,
        agent_id: Optional[str] = None,
        format: str = 'json'
    ) -> str:
        """
        Export traces for external analysis.
        
        Args:
            agent_id: Optional agent filter
            format: Export format ('json', 'csv')
        
        Returns:
            Exported data as string
        """
        # Filter traces
        traces_to_export = self._traces
        if agent_id:
            traces_to_export = [t for t in self._traces if t.agent_id == agent_id]
        
        if format == 'json':
            return json.dumps([asdict(t) for t in traces_to_export], indent=2)
        elif format == 'csv':
            # Simple CSV export
            lines = ['trace_id,agent_id,node_id,timestamp,duration_ms,success,tokens_used,cost_usd']
            for t in traces_to_export:
                lines.append(
                    f"{t.trace_id},{t.agent_id},{t.node_id},{t.timestamp},"
                    f"{t.duration_ms},{t.success},{t.tokens_used or 0},{t.cost_usd or 0}"
                )
            return '\n'.join(lines)
        
        return ''

