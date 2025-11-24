'use client';

import { useEffect, useState } from 'react';
import { Activity, Database, Zap, Server, Wifi, HardDrive, Cpu } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  latency?: number;
  memory?: string;
  uptime?: string;
}

interface SystemMetrics {
  services: ServiceStatus[];
  agentCount: number;
  activeDeployments: number;
  eventRate: number;
  successRate: number;
  cpuUsage?: number;
  memoryUsage?: number;
  diskUsage?: number;
}

export function SystemStatusTab() {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    services: [
      { name: 'FastAPI Server', status: 'unknown', latency: 0, memory: '0 MB' },
      { name: 'PostgreSQL', status: 'unknown', latency: 0, memory: '0 MB' },
      { name: 'Redis', status: 'unknown', latency: 0, memory: '0 MB' },
      { name: 'LiveKit Server', status: 'unknown', latency: 0, memory: '0 MB' },
    ],
    agentCount: 0,
    activeDeployments: 0,
    eventRate: 0,
    successRate: 100,
    cpuUsage: 0,
    memoryUsage: 0,
    diskUsage: 0,
  });
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Poll system metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/system/metrics`);
        if (res.ok) {
          const data = await res.json();
          setMetrics({
            services: data.services || metrics.services,
            agentCount: data.agentCount || 0,
            activeDeployments: data.activeDeployments || 0,
            eventRate: data.eventRate || 0,
            successRate: data.successRate || 100,
            cpuUsage: data.cpuUsage || 0,
            memoryUsage: data.memoryUsage || 0,
            diskUsage: data.diskUsage || 0,
          });
          setLastUpdate(new Date());
        }
      } catch (e) {
        console.error('Failed to fetch system metrics:', e);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'error':
        return '❌';
      default:
        return '⚫';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-fg-3';
    }
  };

  return (
    <div className="h-full flex flex-col">
      <ScrollArea className="flex-1 px-3 py-3">
        <div className="space-y-4">
          {/* Backend Services */}
          <div>
            <h3 className="text-xs font-semibold text-fg-1 mb-2 flex items-center gap-2">
              <Server className="h-3.5 w-3.5" />
              Backend Services
            </h3>
            <div className="space-y-2">
              {metrics.services.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10"
                >
                  <div className="flex items-center gap-2">
                    <span>{getStatusIcon(service.status)}</span>
                    <span className="text-xs font-medium text-fg-0">{service.name}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-fg-2">
                    {service.latency !== undefined && service.latency > 0 && (
                      <span className={service.latency > 100 ? 'text-yellow-400' : ''}>
                        {service.latency}ms
                      </span>
                    )}
                    {service.memory && <span className="text-fg-3">{service.memory}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Agent Platform */}
          <div>
            <h3 className="text-xs font-semibold text-fg-1 mb-2 flex items-center gap-2">
              <Zap className="h-3.5 w-3.5" />
              Agent Platform
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                <div className="text-[10px] text-fg-2 uppercase tracking-wide mb-1">
                  Active Agents
                </div>
                <div className="text-lg font-semibold text-fg-0">{metrics.agentCount}</div>
              </div>
              <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                <div className="text-[10px] text-fg-2 uppercase tracking-wide mb-1">
                  Deployments
                </div>
                <div className="text-lg font-semibold text-fg-0">{metrics.activeDeployments}</div>
              </div>
              <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                <div className="text-[10px] text-fg-2 uppercase tracking-wide mb-1">Event Rate</div>
                <div className="text-lg font-semibold text-fg-0">{metrics.eventRate}/min</div>
              </div>
              <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                <div className="text-[10px] text-fg-2 uppercase tracking-wide mb-1">
                  Success Rate
                </div>
                <div className="text-lg font-semibold text-green-400">{metrics.successRate}%</div>
              </div>
            </div>
          </div>

          {/* Resource Usage */}
          {(metrics.cpuUsage ?? 0) > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-fg-1 mb-2 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5" />
                Resource Usage
              </h3>
              <div className="space-y-3">
                <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-xs text-fg-1">
                      <Cpu className="h-3.5 w-3.5" />
                      <span>CPU Usage</span>
                    </div>
                    <span className="text-xs font-medium text-fg-0">{metrics.cpuUsage}%</span>
                  </div>
                  <Progress value={metrics.cpuUsage} className="h-1.5" />
                </div>

                <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2 text-xs text-fg-1">
                      <HardDrive className="h-3.5 w-3.5" />
                      <span>Memory Usage</span>
                    </div>
                    <span className="text-xs font-medium text-fg-0">{metrics.memoryUsage}%</span>
                  </div>
                  <Progress value={metrics.memoryUsage} className="h-1.5" />
                </div>

                {(metrics.diskUsage ?? 0) > 0 && (
                  <div className="bg-bg-2/60 rounded-lg px-3 py-2 border border-white/10">
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2 text-xs text-fg-1">
                        <Database className="h-3.5 w-3.5" />
                        <span>Disk Usage</span>
                      </div>
                      <span className="text-xs font-medium text-fg-0">{metrics.diskUsage}%</span>
                    </div>
                    <Progress value={metrics.diskUsage} className="h-1.5" />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t border-white/10 px-3 py-1.5 bg-bg-1/50">
        <div className="text-[10px] text-fg-3">Last updated: {lastUpdate.toLocaleTimeString()}</div>
      </div>
    </div>
  );
}
