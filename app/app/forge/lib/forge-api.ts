/**
 * Forge API Client
 * Communicates with Backend API for graph/agent CRUD operations
 * Uses the unified /api/graphs endpoints
 */

import { Node, Edge } from 'reactflow';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface GraphMetadata {
  id: string;
  name: string;
  display_name?: string;
  environment: string;
  description?: string;
  created_at: string;
  updated_at: string;
  status: string;
  graph_type?: string;
  version?: string;
  organization_id?: string;
  domain_id?: string;
  yaml_content?: string;
}

// Alias for backward compatibility
export type AgentMetadata = GraphMetadata;

export interface DeploymentRecord {
  id: string;
  graph_id: string;
  graph_name: string;
  environment: string;
  status: string;
  deployed_by: string;
  deployed_at: string;
  git_commit_sha?: string;
  error_message?: string;
}

export interface CreateGraphRequest {
  name: string;
  display_name?: string;
  description?: string;
  yaml_content: string;
  organization_id?: string;
  domain_id?: string;
  environment?: string;
  graph_type?: string;
  status?: string;
  version?: string;
  tags?: string;
}

export interface UpdateGraphRequest {
  name?: string;
  display_name?: string;
  description?: string;
  yaml_content?: string;
  status?: string;
  version?: string;
  tags?: string;
}

// Alias for backward compatibility
export type CreateAgentRequest = CreateGraphRequest;
export type UpdateAgentRequest = UpdateGraphRequest;

export interface DeployGraphRequest {
  environment: string;
  git_commit?: boolean;
}

// Alias for backward compatibility
export type DeployAgentRequest = DeployGraphRequest;

class ForgeAPIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      console.error(`Forge API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // ==================== Health Check ====================

  async healthCheck() {
    return this.request<{ status: string; service: string; version: string }>('/health');
  }

  // ==================== Graph CRUD ====================

  async createGraph(request: CreateGraphRequest): Promise<GraphMetadata> {
    return this.request<GraphMetadata>('/api/graphs', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async listGraphs(params?: {
    environment?: string;
    graph_type?: string;
  }): Promise<{ graphs: GraphMetadata[] }> {
    const searchParams = new URLSearchParams();
    if (params?.environment) searchParams.set('environment', params.environment);
    if (params?.graph_type) searchParams.set('graph_type', params.graph_type);
    const queryString = searchParams.toString();
    const endpoint = queryString ? `/api/graphs?${queryString}` : '/api/graphs';
    return this.request<{ graphs: GraphMetadata[] }>(endpoint);
  }

  async getGraph(graphId: string): Promise<GraphMetadata> {
    return this.request<GraphMetadata>(`/api/graphs/${graphId}`);
  }

  async updateGraph(graphId: string, request: UpdateGraphRequest): Promise<GraphMetadata> {
    return this.request<GraphMetadata>(`/api/graphs/${graphId}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  async deleteGraph(graphId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/graphs/${graphId}`, {
      method: 'DELETE',
    });
  }

  // ==================== Deployment ====================

  async deployGraph(graphId: string, request: DeployGraphRequest): Promise<DeploymentRecord> {
    return this.request<DeploymentRecord>(`/api/graphs/${graphId}/deploy`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ==================== Backward Compatibility Aliases ====================
  // These methods maintain compatibility with code using the old "agent" naming

  async createAgent(request: CreateAgentRequest): Promise<AgentMetadata> {
    return this.createGraph(request);
  }

  async listAgents(): Promise<AgentMetadata[]> {
    const result = await this.listGraphs({ graph_type: 'user' });
    return result.graphs || [];
  }

  async getAgent(agentNameOrId: string): Promise<any> {
    return this.getGraph(agentNameOrId);
  }

  async updateAgent(
    agentNameOrId: string,
    request: UpdateAgentRequest
  ): Promise<{ message: string }> {
    await this.updateGraph(agentNameOrId, request);
    return { message: 'Agent updated successfully' };
  }

  async deleteAgent(agentNameOrId: string): Promise<{ message: string }> {
    return this.deleteGraph(agentNameOrId);
  }

  async deployAgent(agentNameOrId: string, request: DeployAgentRequest): Promise<DeploymentRecord> {
    return this.deployGraph(agentNameOrId, request);
  }
}

// Export singleton instance
export const forgeAPI = new ForgeAPIClient();
