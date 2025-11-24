/**
 * Hook: useDeployedAgents
 * Fetches and monitors deployed agents for a domain
 */

import { useState, useEffect } from 'react';

export interface Agent {
  id: string;
  name: string;
  type: 'system' | 'domain';
  status: 'healthy' | 'degraded' | 'error' | 'unknown';
  description: string;
  version?: string;
  capabilities?: string[];
  error?: string;
}

export interface DeployedAgentsResponse {
  domain_id: string;
  timestamp: string;
  system_agents: Agent[];
  domain_agents: Agent[];
  total_agents: number;
}

export function useDeployedAgents(domainId: string | undefined) {
  const [data, setData] = useState<DeployedAgentsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!domainId) {
      setLoading(false);
      return;
    }

    const fetchAgents = async () => {
      try {
        setLoading(true);
        const { buildServiceUrl } = await import('@/lib/config/services');
        const url = buildServiceUrl('backend', `/api/monitoring/domains/${domainId}/agents/status`);
        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch agents: ${response.status}`);
        }

        const responseData = await response.json();
        setData(responseData);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch agents');
        console.error('Error fetching deployed agents:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();

    // Refresh every 30 seconds
    const interval = setInterval(fetchAgents, 30000);

    return () => clearInterval(interval);
  }, [domainId]);

  return { data, loading, error };
}
