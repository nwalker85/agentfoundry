/**
 * Hook: useActivityHistory
 * Fetches historical activity data from the backend and merges with real-time updates
 */

import { useState, useEffect, useCallback } from 'react';
import { AgentActivity } from './useAgentActivity';

interface SessionSummary {
  session_id: string;
  started_at: string;
  ended_at: string;
  duration_seconds: number;
  activity_count: number;
  agent_count: number;
  error_count: number;
  agents: string[];
}

interface SessionMetrics {
  session_id: string;
  duration_seconds: number;
  activity_count: number;
  event_counts: Record<string, number>;
  tool_calls: number;
  errors: number;
  agents_involved: string[];
  message_count: {
    user: number;
    agent: number;
  };
  first_activity: string;
  last_activity: string;
}

interface UseActivityHistoryOptions {
  limit?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

interface UseActivityHistoryResult {
  activities: AgentActivity[];
  isLoading: boolean;
  error: string | null;
  hasMore: boolean;
  total: number;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
}

import { getServiceUrl } from '@/lib/config/services';

const API_BASE = getServiceUrl('backend');

/**
 * Fetch historical activities for a session
 */
export function useActivityHistory(
  sessionId: string | null,
  options: UseActivityHistoryOptions = {}
): UseActivityHistoryResult {
  const { limit = 100, autoRefresh = false, refreshInterval = 30000 } = options;

  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);

  const fetchActivities = useCallback(
    async (reset = false) => {
      if (!sessionId) return;

      setIsLoading(true);
      setError(null);

      try {
        const currentOffset = reset ? 0 : offset;
        const response = await fetch(
          `${API_BASE}/api/monitoring/sessions/${sessionId}/activities?limit=${limit}&offset=${currentOffset}`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch activities: ${response.statusText}`);
        }

        const data = await response.json();

        const newActivities = data.activities.map((act: any) => ({
          agent_id: act.agent_id,
          agent_name: act.agent_name,
          event_type: act.event_type,
          timestamp: act.timestamp,
          message: act.message,
          metadata: act.metadata,
        }));

        if (reset) {
          setActivities(newActivities);
          setOffset(newActivities.length);
        } else {
          setActivities((prev) => [...prev, ...newActivities]);
          setOffset((prev) => prev + newActivities.length);
        }

        setTotal(data.total);
        setHasMore(data.has_more);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, limit, offset]
  );

  // Initial fetch
  useEffect(() => {
    if (sessionId) {
      fetchActivities(true);
    }
  }, [sessionId]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh || !sessionId) return;

    const interval = setInterval(() => {
      fetchActivities(true);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, sessionId]);

  const loadMore = useCallback(async () => {
    if (hasMore && !isLoading) {
      await fetchActivities(false);
    }
  }, [hasMore, isLoading, fetchActivities]);

  const refresh = useCallback(async () => {
    await fetchActivities(true);
  }, [fetchActivities]);

  return { activities, isLoading, error, hasMore, total, loadMore, refresh };
}

/**
 * Fetch recent sessions list
 */
export function useRecentSessions(limit: number = 20) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/monitoring/sessions/recent?limit=${limit}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.statusText}`);
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return { sessions, isLoading, error, refresh: fetchSessions };
}

/**
 * Fetch session metrics
 */
export function useSessionMetrics(sessionId: string | null) {
  const [metrics, setMetrics] = useState<SessionMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (!sessionId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/monitoring/sessions/${sessionId}/metrics`);

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.statusText}`);
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      fetchMetrics();
    }
  }, [sessionId, fetchMetrics]);

  return { metrics, isLoading, error, refresh: fetchMetrics };
}

/**
 * Search activities
 */
export function useActivitySearch() {
  const [results, setResults] = useState<AgentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (params: {
      query?: string;
      eventType?: string;
      agentId?: string;
      sessionId?: string;
      limit?: number;
    }) => {
      setIsLoading(true);
      setError(null);

      try {
        const queryParams = new URLSearchParams();
        if (params.query) queryParams.append('q', params.query);
        if (params.eventType) queryParams.append('event_type', params.eventType);
        if (params.agentId) queryParams.append('agent_id', params.agentId);
        if (params.sessionId) queryParams.append('session_id', params.sessionId);
        if (params.limit) queryParams.append('limit', params.limit.toString());

        const response = await fetch(`${API_BASE}/api/monitoring/activities/search?${queryParams}`);

        if (!response.ok) {
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const data = await response.json();
        setResults(data.activities || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return { results, isLoading, error, search };
}

/**
 * Natural language query
 */
export function useObservabilityQuery() {
  const [response, setResponse] = useState<string>('');
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useCallback(async (queryText: string, sessionId?: string, agentId?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/monitoring/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: queryText,
          session_id: sessionId,
          agent_id: agentId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
      }

      const result = await response.json();
      setResponse(result.response || '');
      setData(result.data);

      if (result.error) {
        setError(result.error);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { response, data, isLoading, error, query };
}

// ============================================================================
// Agent Metrics Hooks (Phase 1 - Agent Dashboard)
// ============================================================================

export interface AgentMetrics {
  agent_id: string;
  executions: number;
  success_rate: number;
  errors: number;
  tool_calls: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  sessions: number;
  last_active: string | null;
}

export interface AllAgentsMetrics {
  hours: number;
  agents: AgentMetrics[];
  summary: {
    active_agents: number;
    total_executions: number;
    overall_success_rate: number;
    total_errors: number;
    avg_latency_ms: number;
  };
}

/**
 * Fetch metrics for a single agent
 */
export function useAgentMetrics(agentId: string | null, hours: number = 24) {
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    if (!agentId) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/monitoring/agents/${encodeURIComponent(agentId)}/metrics?hours=${hours}`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch agent metrics: ${response.statusText}`);
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [agentId, hours]);

  useEffect(() => {
    if (agentId) {
      fetchMetrics();
    }
  }, [agentId, hours, fetchMetrics]);

  return { metrics, isLoading, error, refresh: fetchMetrics };
}

/**
 * Fetch metrics for all agents (for dashboard)
 */
export function useAllAgentsMetrics(
  hours: number = 24,
  autoRefresh: boolean = false,
  refreshInterval: number = 30000
) {
  const [data, setData] = useState<AllAgentsMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/monitoring/agents/metrics?hours=${hours}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch agents metrics: ${response.statusText}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [hours]);

  // Initial fetch
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchMetrics();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchMetrics]);

  return {
    agents: data?.agents || [],
    summary: data?.summary || null,
    hours: data?.hours || hours,
    isLoading,
    error,
    refresh: fetchMetrics,
  };
}
