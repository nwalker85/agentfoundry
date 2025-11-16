/**
 * Agent Foundry - Monitoring Type Definitions
 * Types for traces, metrics, logs, and observability
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';
export type SpanStatus = 'success' | 'error' | 'running';

export interface Trace {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_version: string;
  environment: string;

  // Timing
  started_at: string;
  completed_at?: string;
  duration_ms?: number;

  // Status
  status: SpanStatus;
  error_message?: string;

  // Input/Output
  input: any;
  output?: any;

  // Spans (nested execution tree)
  spans: Span[];

  // Metadata
  user_id?: string;
  session_id?: string;
  channel?: string;

  // Cost
  total_tokens: number;
  total_cost: number;
}

export interface Span {
  id: string;
  trace_id: string;
  parent_span_id?: string;
  name: string;
  type: 'llm' | 'tool' | 'process' | 'decision' | 'human';

  // Timing
  started_at: string;
  completed_at?: string;
  duration_ms?: number;

  // Status
  status: SpanStatus;
  error_message?: string;

  // Input/Output
  input: any;
  output?: any;

  // LLM specific
  model?: string;
  tokens_used?: number;
  cost?: number;

  // Tool specific
  tool_name?: string;
  tool_parameters?: any;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;

  // Context
  agent_id?: string;
  trace_id?: string;
  span_id?: string;

  // Additional data
  metadata?: Record<string, any>;
  error?: {
    message: string;
    stack?: string;
    code?: string;
  };
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
}

export interface Metric {
  name: string;
  description: string;
  unit: string;
  data_points: MetricDataPoint[];
  aggregation: 'avg' | 'sum' | 'count' | 'min' | 'max' | 'p95' | 'p99';
}

export interface CostBreakdown {
  total_cost: number;
  by_agent: Record<string, number>;
  by_model: Record<string, number>;
  by_tool: Record<string, number>;
  by_environment: Record<string, number>;
}

export interface Alert {
  id: string;
  name: string;
  severity: 'info' | 'warning' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  message: string;
  agent_id?: string;
  trace_id?: string;
  threshold_value: number;
  current_value: number;
}
