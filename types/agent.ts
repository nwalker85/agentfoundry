/**
 * Agent Foundry - Agent Type Definitions
 * Core types for AI agents, versions, and execution
 */

export type AgentStatus = 'active' | 'inactive' | 'draft' | 'archived' | 'error';
export type Environment = 'dev' | 'staging' | 'prod';
export type AgentVersion = string; // Semver format: "1.2.3"

export interface Agent {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: AgentVersion;
  status: AgentStatus;
  environment: Environment;

  // Organization & Domain binding
  organization_id: string;
  organization_name?: string;
  domain_id: string;
  domain_name?: string;

  // Metadata
  created_at: string;
  updated_at: string;
  created_by: string;
  tags: string[];

  // Configuration
  graph_yaml: string;
  graph_json: any; // Parsed graph structure

  // Tools & Dependencies
  tools_used: string[];
  models_used: string[];
  channels: string[];

  // Metrics (last 24h)
  metrics: AgentMetrics;

  // Cost tracking
  cost_p95: number; // P95 cost per execution
  total_cost_24h: number;
}

export interface AgentMetrics {
  executions_24h: number;
  success_rate: number;
  error_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
}

export interface AgentVersionHistory {
  id: string;
  agent_id: string;
  version: string;
  created_at: string;
  created_by: string;
  changelog: string;
  graph_yaml: string;
  is_current: boolean;
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  tags: string[];
  verified: boolean;
  downloads: number;
  rating: number;
  author: string;
  graph_yaml: string;
  preview_image?: string;
}
