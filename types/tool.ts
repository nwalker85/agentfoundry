/**
 * Agent Foundry - Tool Type Definitions
 * Types for tools, functions, and integrations
 */

export type ToolStatus = 'installed' | 'available' | 'update_available' | 'deprecated';
export type ToolCategory =
  | 'data'
  | 'communication'
  | 'ml_ai'
  | 'integration'
  | 'custom'
  | 'search'
  | 'analytics';

export interface Tool {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: ToolCategory;
  vendor: string;
  version: string;
  status: ToolStatus;

  // Installation
  installed: boolean;
  installed_at?: string;
  update_available?: boolean;
  latest_version?: string;

  // Usage
  used_by_agents: string[]; // agent IDs
  total_invocations_24h: number;
  success_rate: number;
  avg_latency_ms: number;

  // Schema & Config
  json_schema: any; // JSON Schema for tool parameters
  handler_code?: string; // For custom tools
  permissions: ToolPermission[];

  // Marketplace metadata
  verified: boolean;
  rating?: number;
  downloads?: number;
  author?: string;
  documentation_url?: string;
  icon_url?: string;
  tags: string[];
}

export interface ToolPermission {
  resource: string;
  action: 'read' | 'write' | 'execute' | 'delete';
  scope: string;
}

export interface ToolInvocation {
  id: string;
  tool_id: string;
  tool_name: string;
  agent_id: string;
  trace_id: string;
  span_id: string;

  // Timing
  invoked_at: string;
  completed_at?: string;
  duration_ms?: number;

  // Input/Output
  parameters: any;
  result?: any;

  // Status
  status: 'success' | 'error';
  error_message?: string;

  // Cost
  cost?: number;
}

export interface ToolTest {
  id: string;
  tool_id: string;
  name: string;
  description: string;
  test_parameters: any;
  expected_result: any;
  status: 'passed' | 'failed' | 'not_run';
  last_run_at?: string;
  error_message?: string;
}
