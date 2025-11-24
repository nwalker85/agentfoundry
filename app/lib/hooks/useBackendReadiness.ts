/**
 * Hook: useBackendReadiness
 * Polls the backend readiness endpoint to ensure all systems are up
 * before allowing chat/voice interactions.
 */

import { useState, useEffect, useCallback } from 'react';

export interface BackendReadiness {
  ready: boolean;
  marshal_initialized: boolean;
  agents_loaded: number;
  database_connected: boolean;
  message: string;
}

interface UseBackendReadinessOptions {
  /** Polling interval in ms when not ready (default: 2000) */
  pollingInterval?: number;
  /** Stop polling once ready (default: true) */
  stopOnReady?: boolean;
}

export function useBackendReadiness(options: UseBackendReadinessOptions = {}) {
  const { pollingInterval = 2000, stopOnReady = true } = options;

  const [readiness, setReadiness] = useState<BackendReadiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkReadiness = useCallback(async () => {
    try {
      const { buildServiceUrl } = await import('@/lib/config/services');
      const url = buildServiceUrl('backend', '/api/system/ready');
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Backend readiness check failed: ${response.status}`);
      }

      const data: BackendReadiness = await response.json();
      setReadiness(data);
      setError(null);
      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to check backend readiness';
      setError(errorMsg);
      console.error('Backend readiness check error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial check
    checkReadiness();

    // Set up polling
    const interval = setInterval(async () => {
      const result = await checkReadiness();
      // Stop polling if ready and stopOnReady is true
      if (stopOnReady && result?.ready) {
        clearInterval(interval);
      }
    }, pollingInterval);

    return () => clearInterval(interval);
  }, [checkReadiness, pollingInterval, stopOnReady]);

  return {
    readiness,
    loading,
    error,
    isReady: readiness?.ready ?? false,
    refresh: checkReadiness,
  };
}
