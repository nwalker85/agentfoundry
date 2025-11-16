/**
 * Agent Foundry - Dataset Type Definitions
 * Types for datasets, evaluations, and testing
 */

export type DatasetType = 'training' | 'validation' | 'test' | 'evaluation' | 'custom';
export type DatasetFormat = 'json' | 'jsonl' | 'csv' | 'parquet';

export interface Dataset {
  id: string;
  name: string;
  description: string;
  type: DatasetType;
  format: DatasetFormat;

  // File info
  file_url: string;
  file_size_bytes: number;
  row_count: number;

  // Schema
  schema: DatasetSchema[];

  // Versions
  version: string;
  versions: DatasetVersion[];

  // Usage
  used_by_agents: string[];
  last_evaluation_run?: string;
  last_evaluation_id?: string;

  // Stats
  evaluation_stats?: EvaluationStats;

  // Metadata
  created_at: string;
  updated_at: string;
  created_by: string;
  tags: string[];
}

export interface DatasetSchema {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  description?: string;
  required: boolean;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version: string;
  created_at: string;
  created_by: string;
  changelog: string;
  file_url: string;
  row_count: number;
  is_current: boolean;
}

export interface DatasetRow {
  id: string;
  index: number;
  data: Record<string, any>;
}

export interface Evaluation {
  id: string;
  dataset_id: string;
  dataset_name: string;
  agent_id: string;
  agent_name: string;
  agent_version: string;

  // Timing
  started_at: string;
  completed_at?: string;
  duration_ms?: number;

  // Status
  status: 'pending' | 'running' | 'complete' | 'failed';

  // Results
  total_tests: number;
  tests_passed: number;
  tests_failed: number;
  pass_rate: number;

  // Detailed results
  test_results: EvaluationResult[];

  // Metrics
  avg_latency_ms: number;
  total_cost: number;
  avg_cost_per_test: number;

  // Comparison
  baseline_evaluation_id?: string;
  delta_pass_rate?: number;
  delta_latency_ms?: number;
  delta_cost?: number;
}

export interface EvaluationResult {
  id: string;
  evaluation_id: string;
  test_index: number;
  test_name?: string;

  // Input/Output
  input: any;
  expected_output: any;
  actual_output: any;

  // Status
  status: 'passed' | 'failed';
  error_message?: string;

  // Metrics
  latency_ms: number;
  tokens_used: number;
  cost: number;

  // Scoring
  score?: number; // 0-1
  scoring_criteria?: Record<string, number>;
}

export interface EvaluationStats {
  total_evaluations: number;
  last_run_at?: string;
  best_pass_rate: number;
  worst_pass_rate: number;
  avg_pass_rate: number;
  avg_latency_ms: number;
  trend: 'improving' | 'stable' | 'declining';
}
