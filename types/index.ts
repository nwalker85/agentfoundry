/**
 * Agent Foundry - Type Definitions Index
 * Central export for all TypeScript types
 */

// Agent types
export * from './agent';
export * from './agent-manifest';

// Deployment types
export * from './deployment';

// Monitoring types
export * from './monitoring';

// Tool types
export * from './tool';

// Channel types
export * from './channel';

// Domain types
export * from './domain';

// Dataset types
export * from './dataset';

// Forge / Designer types
export * from './forge';

// Common utility types
export type Status = 'idle' | 'loading' | 'success' | 'error';

export interface PaginationParams {
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
}

export interface FilterParams {
  search?: string;
  tags?: string[];
  status?: string;
  environment?: string;
  created_after?: string;
  created_before?: string;
}

export interface SortParams {
  field: string;
  direction: 'asc' | 'desc';
}

export interface ApiResponse<T> {
  data: T;
  status: Status;
  error?: string;
  pagination?: PaginationParams;
}

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: 'admin' | 'user' | 'viewer';
  organization_id: string;
}

export interface Organization {
  id: string;
  name: string;
  tier: 'free' | 'standard' | 'enterprise';
  created_at: string;
  user_count: number;
  agent_count: number;
}
