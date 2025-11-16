/**
 * Agent Foundry - Mock Deployment Data
 * Sample deployment history and pipeline data
 */

import { Deployment, PipelineStatus, DeploymentStatus, TestResult } from '@/types';

export const mockDeployments: Deployment[] = [
  {
    id: 'dep-001',
    agent_id: 'agt-001',
    agent_name: 'customer-support-agent',
    version: '2.1.0',
    environment: 'prod',
    status: 'success',
    created_at: '2025-01-15T14:22:00Z',
    started_at: '2025-01-15T14:22:05Z',
    completed_at: '2025-01-15T14:24:18Z',
    duration_ms: 133000,
    deployed_by: 'nwalker85',
    git_commit_sha: 'a7f3b2c',
    changelog: 'Improved response accuracy for order status queries',
    tests_passed: 47,
    tests_failed: 0,
    latency_delta_ms: -120,
    cost_delta: -0.0003,
    error_rate_delta: -0.012,
    can_rollback: true,
  },
  {
    id: 'dep-002',
    agent_id: 'agt-002',
    agent_name: 'sales-qualifying-agent',
    version: '1.8.3',
    environment: 'prod',
    status: 'success',
    created_at: '2025-01-14T16:45:00Z',
    started_at: '2025-01-14T16:45:12Z',
    completed_at: '2025-01-14T16:47:34Z',
    duration_ms: 142000,
    deployed_by: 'sarah.chen',
    git_commit_sha: 'f9e2d1a',
    changelog: 'Added lead scoring logic and CRM sync improvements',
    tests_passed: 38,
    tests_failed: 2,
    latency_delta_ms: 45,
    cost_delta: 0.0008,
    error_rate_delta: -0.008,
    can_rollback: true,
    test_results: [
      { id: 'test-001', name: 'Lead qualification flow', status: 'passed', duration_ms: 2300 },
      { id: 'test-002', name: 'CRM integration', status: 'failed', duration_ms: 4100, error_message: 'Salesforce API timeout' },
    ],
  },
  {
    id: 'dep-003',
    agent_id: 'agt-007',
    agent_name: 'invoice-processor-agent',
    version: '2.0.4',
    environment: 'prod',
    status: 'failed',
    created_at: '2025-01-16T08:15:00Z',
    started_at: '2025-01-16T08:15:08Z',
    completed_at: '2025-01-16T08:16:22Z',
    duration_ms: 74000,
    deployed_by: 'alex.kim',
    git_commit_sha: 'c4b8f7e',
    changelog: 'Updated OCR model for better invoice parsing',
    tests_passed: 12,
    tests_failed: 8,
    can_rollback: true,
    error_message: 'Test suite failed: OCR accuracy below 95% threshold',
  },
  {
    id: 'dep-004',
    agent_id: 'agt-003',
    agent_name: 'data-analyst-agent',
    version: '3.0.1',
    environment: 'staging',
    status: 'running',
    created_at: '2025-01-16T11:30:00Z',
    started_at: '2025-01-16T11:30:15Z',
    deployed_by: 'mike.rodriguez',
    git_commit_sha: 'd2a9c5f',
    changelog: 'Added support for PostgreSQL databases',
    tests_passed: 15,
    tests_failed: 0,
    can_rollback: false,
  },
  {
    id: 'dep-005',
    agent_id: 'agt-004',
    agent_name: 'hr-onboarding-agent',
    version: '1.4.2',
    environment: 'prod',
    status: 'success',
    created_at: '2025-01-13T15:30:00Z',
    started_at: '2025-01-13T15:30:20Z',
    completed_at: '2025-01-13T15:32:10Z',
    duration_ms: 110000,
    deployed_by: 'jessica.lee',
    git_commit_sha: 'e8f1a3b',
    tests_passed: 28,
    tests_failed: 0,
    latency_delta_ms: -200,
    cost_delta: -0.0012,
    can_rollback: true,
  },
];

export const mockPipelineStatus: Record<string, PipelineStatus> = {
  'dep-004': {
    deployment_id: 'dep-004',
    current_stage: 'deploy',
    stages: {
      design: { status: 'complete', started_at: '2025-01-16T11:30:15Z', completed_at: '2025-01-16T11:30:18Z' },
      validate: { status: 'complete', started_at: '2025-01-16T11:30:18Z', completed_at: '2025-01-16T11:30:25Z' },
      test: { status: 'complete', started_at: '2025-01-16T11:30:25Z', completed_at: '2025-01-16T11:31:45Z' },
      package: { status: 'complete', started_at: '2025-01-16T11:31:45Z', completed_at: '2025-01-16T11:31:52Z' },
      deploy: { status: 'running', started_at: '2025-01-16T11:31:52Z' },
      observe: { status: 'pending' },
      promote: { status: 'pending' },
    },
  },
};

export function getDeploymentsByAgent(agentId: string): Deployment[] {
  return mockDeployments.filter(dep => dep.agent_id === agentId);
}

export function getDeploymentsByStatus(status: DeploymentStatus): Deployment[] {
  return mockDeployments.filter(dep => dep.status === status);
}

export function getRecentDeployments(limit: number = 10): Deployment[] {
  return [...mockDeployments]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, limit);
}
