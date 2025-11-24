/**
 * Storage API Client
 * Frontend client for invoking the Storage Agent via API.
 * Replaces direct API calls with agent-based storage operations.
 */

import { getServiceUrl } from '@/lib/config/services';

export interface GraphData {
  nodes: any[];
  edges: any[];
  metadata?: any;
}

export interface StorageResponse<T = any> {
  success: boolean;
  result: T;
  error?: string;
}

export interface VersionHistoryItem {
  id: number;
  version: number;
  commit_message: string;
  commit_hash: string;
  user_id?: string;
  created_at: string;
}

export interface DraftInfo {
  agent_id: string;
  user_id: string;
  graph_data: GraphData;
  last_saved: string;
}

export interface RestoredVersion {
  graph_data: GraphData;
  version: number;
  commit_hash: string;
  restored_from: string;
}

/**
 * Storage Agent Client
 */
export class StorageClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // Use service discovery for backend URL
    this.baseUrl = baseUrl || getServiceUrl('backend');
  }

  /**
   * Autosave agent draft to Redis (every 3 seconds)
   */
  async autosave(
    agentId: string,
    userId: string,
    graphData: GraphData
  ): Promise<StorageResponse<string>> {
    const response = await fetch(`${this.baseUrl}/api/storage/autosave`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: agentId,
        user_id: userId,
        graph_data: graphData,
      }),
    });

    if (!response.ok) {
      throw new Error(`Autosave failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Commit agent version with message (git-like commit)
   */
  async commit(
    agentId: string,
    graphData: GraphData,
    commitMessage: string,
    userId?: string
  ): Promise<StorageResponse<string>> {
    const response = await fetch(`${this.baseUrl}/api/storage/commit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: agentId,
        graph_data: graphData,
        commit_message: commitMessage,
        user_id: userId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Commit failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get version history for an agent (git log)
   */
  async getHistory(
    agentId: string,
    limit: number = 50
  ): Promise<StorageResponse<VersionHistoryItem[]>> {
    const response = await fetch(`${this.baseUrl}/api/storage/history/${agentId}?limit=${limit}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Get history failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Restore agent to specific version (git checkout)
   */
  async restore(agentId: string, version: number): Promise<StorageResponse<RestoredVersion>> {
    const response = await fetch(`${this.baseUrl}/api/storage/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: agentId,
        version: version,
      }),
    });

    if (!response.ok) {
      throw new Error(`Restore failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get latest draft for an agent from Redis
   */
  async getDraft(agentId: string): Promise<StorageResponse<DraftInfo | null>> {
    const response = await fetch(`${this.baseUrl}/api/storage/draft/${agentId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`Get draft failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Import Python LangGraph code → ReactFlow graph
   */
  async importPython(pythonCode: string): Promise<StorageResponse<GraphData>> {
    const response = await fetch(`${this.baseUrl}/api/storage/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        python_code: pythonCode,
      }),
    });

    if (!response.ok) {
      throw new Error(`Import failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Export ReactFlow graph → Python LangGraph code
   */
  async exportPython(
    graphData: GraphData,
    agentName: string = 'agent'
  ): Promise<StorageResponse<string>> {
    const response = await fetch(`${this.baseUrl}/api/storage/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        graph_data: graphData,
        agent_name: agentName,
      }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List all active drafts for a user
   */
  async listDrafts(userId: string): Promise<StorageResponse<DraftInfo[]>> {
    const response = await fetch(`${this.baseUrl}/api/storage/drafts?user_id=${userId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`List drafts failed: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export singleton instance
export const storageClient = new StorageClient();

// Export helper functions
export const storageApi = {
  /**
   * Autosave current graph (called every 3s)
   */
  autosave: (agentId: string, userId: string, graphData: GraphData) =>
    storageClient.autosave(agentId, userId, graphData),

  /**
   * Commit version with message
   */
  commit: (agentId: string, graphData: GraphData, message: string, userId?: string) =>
    storageClient.commit(agentId, graphData, message, userId),

  /**
   * Get version history
   */
  getHistory: (agentId: string, limit?: number) => storageClient.getHistory(agentId, limit),

  /**
   * Restore to version
   */
  restore: (agentId: string, version: number) => storageClient.restore(agentId, version),

  /**
   * Get latest draft
   */
  getDraft: (agentId: string) => storageClient.getDraft(agentId),

  /**
   * Import Python code
   */
  importPython: (pythonCode: string) => storageClient.importPython(pythonCode),

  /**
   * Export to Python
   */
  exportPython: (graphData: GraphData, agentName?: string) =>
    storageClient.exportPython(graphData, agentName),

  /**
   * List user's drafts
   */
  listDrafts: (userId: string) => storageClient.listDrafts(userId),
};
