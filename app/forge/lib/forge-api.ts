/**
 * Forge API Client
 * Communicates with Forge Service (port 8003) for agent CRUD operations
 */

import { Node, Edge } from 'reactflow';

const FORGE_API_URL = process.env.NEXT_PUBLIC_FORGE_API_URL || 'http://localhost:8003';

export interface AgentMetadata {
  id: string;
  name: string;
  environment: string;
  description?: string;
  created_at: string;
  updated_at: string;
  node_count: number;
  edge_count: number;
  status: string;
}

export interface DeploymentRecord {
  id: string;
  agent_id: string;
  agent_name: string;
  environment: string;
  status: string;
  deployed_by: string;
  deployed_at: string;
  git_commit_sha?: string;
  error_message?: string;
}

export interface CreateAgentRequest {
  name: string;
  graph: {
    nodes: Node[];
    edges: Edge[];
  };
  environment: string;
  description?: string;
}

export interface UpdateAgentRequest {
  graph?: {
    nodes: Node[];
    edges: Edge[];
  };
  description?: string;
}

export interface DeployAgentRequest {
  environment: string;
  git_commit?: boolean;
}

class ForgeAPIClient {
  private baseURL: string;

  constructor(baseURL: string = FORGE_API_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
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

  // ==================== Agent CRUD ====================

  async createAgent(request: CreateAgentRequest): Promise<AgentMetadata> {
    return this.request<AgentMetadata>('/api/forge/agents', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async listAgents(): Promise<AgentMetadata[]> {
    return this.request<AgentMetadata[]>('/api/forge/agents');
  }

  async getAgent(agentName: string): Promise<any> {
    return this.request<any>(`/api/forge/agents/${agentName}`);
  }

  async updateAgent(agentName: string, request: UpdateAgentRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/forge/agents/${agentName}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  }

  async deleteAgent(agentName: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/forge/agents/${agentName}`, {
      method: 'DELETE',
    });
  }

  // ==================== Deployment ====================

  async deployAgent(agentName: string, request: DeployAgentRequest): Promise<DeploymentRecord> {
    return this.request<DeploymentRecord>(`/api/forge/agents/${agentName}/deploy`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }
}

// Export singleton instance
export const forgeAPI = new ForgeAPIClient();
