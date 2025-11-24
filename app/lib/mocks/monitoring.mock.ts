/**
 * Agent Foundry - Mock Monitoring Data
 * Sample traces, logs, metrics, and alerts
 */

import { Trace, Span, LogEntry, Metric, CostBreakdown, Alert } from '@/types';

export const mockTraces: Trace[] = [
  {
    id: 'trace-001',
    agent_id: 'agt-001',
    agent_name: 'customer-support-agent',
    agent_version: '2.1.0',
    environment: 'prod',
    started_at: '2025-01-16T10:15:23Z',
    completed_at: '2025-01-16T10:15:27Z',
    duration_ms: 4200,
    status: 'success',
    input: { query: 'What is the status of my order #12345?' },
    output: {
      response: 'Your order #12345 is currently in transit and expected to arrive tomorrow.',
    },
    spans: [
      {
        id: 'span-001',
        trace_id: 'trace-001',
        name: 'understand_query',
        type: 'llm',
        started_at: '2025-01-16T10:15:23Z',
        completed_at: '2025-01-16T10:15:24Z',
        duration_ms: 1200,
        status: 'success',
        input: { query: 'What is the status of my order #12345?' },
        output: { intent: 'order_status', order_id: '12345' },
        model: 'gpt-4o-mini',
        tokens_used: 145,
        cost: 0.00021,
      },
      {
        id: 'span-002',
        trace_id: 'trace-001',
        parent_span_id: 'span-001',
        name: 'fetch_order_status',
        type: 'tool',
        started_at: '2025-01-16T10:15:24Z',
        completed_at: '2025-01-16T10:15:26Z',
        duration_ms: 2100,
        status: 'success',
        input: { order_id: '12345' },
        tool_name: 'order_api',
        tool_parameters: { order_id: '12345' },
        output: { status: 'in_transit', eta: '2025-01-17' },
      },
      {
        id: 'span-003',
        trace_id: 'trace-001',
        parent_span_id: 'span-002',
        name: 'generate_response',
        type: 'llm',
        started_at: '2025-01-16T10:15:26Z',
        completed_at: '2025-01-16T10:15:27Z',
        duration_ms: 900,
        status: 'success',
        input: { order_status: 'in_transit', eta: '2025-01-17' },
        model: 'gpt-4o-mini',
        tokens_used: 98,
        cost: 0.00014,
      },
    ],
    user_id: 'user-7234',
    session_id: 'sess-982',
    channel: 'slack',
    total_tokens: 243,
    total_cost: 0.00035,
  },
  {
    id: 'trace-002',
    agent_id: 'agt-007',
    agent_name: 'invoice-processor-agent',
    agent_version: '2.0.4',
    environment: 'prod',
    started_at: '2025-01-16T09:42:15Z',
    completed_at: '2025-01-16T09:42:19Z',
    duration_ms: 3800,
    status: 'error',
    error_message: 'OCR parsing failed: Unable to extract invoice total',
    input: { invoice_pdf: 'invoice-2025-001.pdf' },
    spans: [
      {
        id: 'span-004',
        trace_id: 'trace-002',
        name: 'ocr_extraction',
        type: 'tool',
        started_at: '2025-01-16T09:42:15Z',
        completed_at: '2025-01-16T09:42:18Z',
        duration_ms: 3200,
        status: 'error',
        input: { invoice_pdf: 'invoice-2025-001.pdf' },
        error_message: 'Low confidence score: 0.62 (threshold: 0.85)',
        tool_name: 'ocr_engine',
      },
    ],
    total_tokens: 0,
    total_cost: 0.0008,
  },
];

export const mockLogs: LogEntry[] = [
  {
    id: 'log-001',
    timestamp: '2025-01-16T10:15:23.234Z',
    level: 'info',
    message: 'Agent execution started',
    agent_id: 'agt-001',
    trace_id: 'trace-001',
    metadata: { user_id: 'user-7234', channel: 'slack' },
  },
  {
    id: 'log-002',
    timestamp: '2025-01-16T10:15:24.456Z',
    level: 'debug',
    message: 'LLM call completed',
    agent_id: 'agt-001',
    trace_id: 'trace-001',
    span_id: 'span-001',
    metadata: { model: 'gpt-4o-mini', tokens: 145, latency_ms: 1200 },
  },
  {
    id: 'log-003',
    timestamp: '2025-01-16T10:15:26.789Z',
    level: 'info',
    message: 'Tool invocation successful',
    agent_id: 'agt-001',
    trace_id: 'trace-001',
    span_id: 'span-002',
    metadata: { tool: 'order_api', duration_ms: 2100 },
  },
  {
    id: 'log-004',
    timestamp: '2025-01-16T09:42:18.123Z',
    level: 'error',
    message: 'OCR parsing failed',
    agent_id: 'agt-007',
    trace_id: 'trace-002',
    span_id: 'span-004',
    error: {
      message: 'Low confidence score: 0.62 (threshold: 0.85)',
      code: 'OCR_LOW_CONFIDENCE',
    },
  },
  {
    id: 'log-005',
    timestamp: '2025-01-16T08:30:15.567Z',
    level: 'warn',
    message: 'High latency detected',
    agent_id: 'agt-003',
    metadata: { latency_ms: 8934, threshold_ms: 5000 },
  },
];

export const mockMetrics: Metric[] = [
  {
    name: 'agent_executions_total',
    description: 'Total number of agent executions',
    unit: 'count',
    aggregation: 'sum',
    data_points: [
      { timestamp: '2025-01-16T09:00:00Z', value: 234 },
      { timestamp: '2025-01-16T10:00:00Z', value: 312 },
      { timestamp: '2025-01-16T11:00:00Z', value: 289 },
    ],
  },
  {
    name: 'agent_latency_p95',
    description: 'P95 latency of agent executions',
    unit: 'ms',
    aggregation: 'p95',
    data_points: [
      { timestamp: '2025-01-16T09:00:00Z', value: 3200 },
      { timestamp: '2025-01-16T10:00:00Z', value: 2800 },
      { timestamp: '2025-01-16T11:00:00Z', value: 3100 },
    ],
  },
  {
    name: 'agent_error_rate',
    description: 'Error rate as percentage',
    unit: 'percent',
    aggregation: 'avg',
    data_points: [
      { timestamp: '2025-01-16T09:00:00Z', value: 2.3 },
      { timestamp: '2025-01-16T10:00:00Z', value: 1.8 },
      { timestamp: '2025-01-16T11:00:00Z', value: 2.1 },
    ],
  },
];

export const mockCostBreakdown: CostBreakdown = {
  total_cost: 28.47,
  by_agent: {
    'customer-support-agent': 12.34,
    'sales-qualifying-agent': 8.21,
    'data-analyst-agent': 5.67,
    'it-helpdesk-agent': 2.25,
  },
  by_model: {
    'gpt-4o': 18.92,
    'gpt-4o-mini': 7.34,
    'claude-3-opus': 2.21,
  },
  by_tool: {
    web_search: 3.45,
    notion: 1.23,
    salesforce: 0.89,
  },
  by_environment: {
    prod: 24.12,
    staging: 3.21,
    dev: 1.14,
  },
};

export const mockAlerts: Alert[] = [
  {
    id: 'alert-001',
    name: 'High Error Rate',
    severity: 'critical',
    status: 'active',
    created_at: '2025-01-16T09:42:00Z',
    message: 'Error rate for invoice-processor-agent exceeded 15% threshold',
    agent_id: 'agt-007',
    threshold_value: 15,
    current_value: 18.8,
  },
  {
    id: 'alert-002',
    name: 'Latency Spike',
    severity: 'warning',
    status: 'acknowledged',
    created_at: '2025-01-16T08:15:00Z',
    acknowledged_at: '2025-01-16T08:22:00Z',
    message: 'P95 latency for data-analyst-agent exceeded 8s threshold',
    agent_id: 'agt-003',
    threshold_value: 8000,
    current_value: 8934,
  },
];

export function getTracesByAgent(agentId: string): Trace[] {
  return mockTraces.filter((trace) => trace.agent_id === agentId);
}

export function getLogsByTraceId(traceId: string): LogEntry[] {
  return mockLogs.filter((log) => log.trace_id === traceId);
}

export function getActiveAlerts(): Alert[] {
  return mockAlerts.filter((alert) => alert.status === 'active');
}
