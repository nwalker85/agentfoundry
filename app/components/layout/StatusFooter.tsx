'use client';

import { useEffect, useState } from 'react';
import { Activity, Wifi, Zap, Bot, Rocket, Database, Clock } from 'lucide-react';
import { useEventSubscription } from '@/lib/hooks/useEventSubscription';

interface SystemMetrics {
  backendStatus: 'healthy' | 'warning' | 'error' | 'disconnected';
  wsStatus: 'connected' | 'disconnected' | 'reconnecting';
  wsClients: number;
  eventCount: number;
  agentCount: number;
  activeDeployments: number;
  dbLatency: number;
}

export function StatusFooter({ onOpenPanel }: { onOpenPanel?: (tab: string) => void }) {
  const { isConnected } = useEventSubscription();
  const [metrics, setMetrics] = useState<SystemMetrics>({
    backendStatus: 'healthy',
    wsStatus: 'disconnected',
    wsClients: 0,
    eventCount: 0,
    agentCount: 0,
    activeDeployments: 0,
    dbLatency: 0,
  });
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update WebSocket status based on connection
  useEffect(() => {
    setMetrics((prev) => ({
      ...prev,
      wsStatus: isConnected ? 'connected' : 'disconnected',
    }));
  }, [isConnected]);

  // Poll backend health
  useEffect(() => {
    const pollHealth = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/system/metrics`);
        if (res.ok) {
          const data = await res.json();
          setMetrics((prev) => ({
            ...prev,
            backendStatus: 'healthy',
            agentCount: data.agentCount || prev.agentCount,
            activeDeployments: data.activeDeployments || prev.activeDeployments,
            dbLatency: data.dbLatency || prev.dbLatency,
          }));
        } else {
          setMetrics((prev) => ({ ...prev, backendStatus: 'error' }));
        }
      } catch (e) {
        setMetrics((prev) => ({ ...prev, backendStatus: 'disconnected' }));
      }
    };

    pollHealth();
    const interval = setInterval(pollHealth, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  // Update clock every second
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return 'text-green-400';
      case 'warning':
      case 'reconnecting':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      case 'disconnected':
      default:
        return 'text-fg-3';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return '🟢';
      case 'warning':
      case 'reconnecting':
        return '🟡';
      case 'error':
        return '🔴';
      case 'disconnected':
      default:
        return '⚫';
    }
  };

  return (
    <footer className="h-6 border-t border-white/10 bg-bg-1/95 backdrop-blur-sm px-3 flex items-center justify-between text-xs text-fg-2">
      <div className="flex items-center gap-4">
        {/* Backend Status */}
        <button
          onClick={() => onOpenPanel?.('system')}
          className="flex items-center gap-1.5 hover:text-fg-0 transition-colors"
          title="Click to view system details"
        >
          <span>{getStatusIcon(metrics.backendStatus)}</span>
          <Activity className="h-3 w-3" />
          <span className={getStatusColor(metrics.backendStatus)}>
            Backend: {metrics.backendStatus === 'healthy' ? 'Healthy' : 'Error'}
          </span>
        </button>

        {/* WebSocket Status */}
        <button
          onClick={() => onOpenPanel?.('system')}
          className="flex items-center gap-1.5 hover:text-fg-0 transition-colors"
          title="Click to view WebSocket details"
        >
          <span>{getStatusIcon(metrics.wsStatus)}</span>
          <Wifi className="h-3 w-3" />
          <span className={getStatusColor(metrics.wsStatus)}>
            WS: {metrics.wsStatus === 'connected' ? 'Connected' : 'Disconnected'}
          </span>
          {metrics.wsClients > 0 && <span className="text-fg-3">({metrics.wsClients})</span>}
        </button>

        {/* Events */}
        <button
          onClick={() => onOpenPanel?.('events')}
          className="flex items-center gap-1.5 hover:text-fg-0 transition-colors"
          title="Click to view live events"
        >
          <Zap className="h-3 w-3" />
          <span>{metrics.eventCount} events</span>
        </button>

        {/* Agents */}
        <button
          onClick={() => onOpenPanel?.('system')}
          className="flex items-center gap-1.5 hover:text-fg-0 transition-colors"
          title="Click to view agents"
        >
          <Bot className="h-3 w-3" />
          <span>{metrics.agentCount} agents</span>
        </button>

        {/* Deployments */}
        {metrics.activeDeployments > 0 && (
          <button
            onClick={() => onOpenPanel?.('events')}
            className="flex items-center gap-1.5 hover:text-fg-0 transition-colors"
            title="Click to view deployments"
          >
            <Rocket className="h-3 w-3" />
            <span>{metrics.activeDeployments} active</span>
          </button>
        )}

        {/* Database Latency */}
        {metrics.dbLatency > 0 && (
          <div className="flex items-center gap-1.5" title="Database latency">
            <Database className="h-3 w-3" />
            <span>{metrics.dbLatency}ms</span>
          </div>
        )}
      </div>

      {/* Clock */}
      <div className="flex items-center gap-1.5 text-fg-3">
        <Clock className="h-3 w-3" />
        <span>{currentTime.toLocaleTimeString()}</span>
      </div>
    </footer>
  );
}
