/**
 * Agent Foundry - Deployment Type Definitions
 * Types for deployment pipeline, history, and status
 */

import { Environment, AgentVersion } from './agent';

export type DeploymentStatus =
  | 'pending'
  | 'running'
  | 'success'
  | 'failed'
  | 'rolled_back'
  | 'cancelled';

export type PipelineStage =
  | 'design'
  | 'validate'
  | 'test'
  | 'package'
  | 'deploy'
  | 'observe'
  | 'promote';

export interface Deployment {
  id: string;
  agent_id: string;
  agent_name: string;
  version: AgentVersion;
  environment: Environment;
  status: DeploymentStatus;

  // Timing
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;

  // Metadata
  deployed_by: string;
  git_commit_sha?: string;
  changelog?: string;

  // Results
  tests_passed: number;
  tests_failed: number;
  test_results?: TestResult[];

  // Delta metrics (vs previous version)
  latency_delta_ms?: number;
  cost_delta?: number;
  error_rate_delta?: number;

  // Rollback info
  can_rollback: boolean;
  rollback_from?: string; // deployment ID

  // Error info
  error_message?: string;
  error_stack?: string;
}

export interface TestResult {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration_ms: number;
  error_message?: string;
}

export interface PipelineStatus {
  deployment_id: string;
  stages: {
    [key in PipelineStage]: {
      status: 'pending' | 'running' | 'complete' | 'failed' | 'skipped';
      started_at?: string;
      completed_at?: string;
      error?: string;
    };
  };
  current_stage: PipelineStage;
}
