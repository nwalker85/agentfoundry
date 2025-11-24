/**
 * Agent Status Panel
 * Displays deployed agents with real-time status
 */

import React from 'react';
import { Agent } from '@/lib/hooks/useDeployedAgents';
import { Activity } from 'lucide-react';

interface AgentStatusPanelProps {
  systemAgents: Agent[];
  domainAgents: Agent[];
  activeAgent?: string | null;
}

export function AgentStatusPanel({
  systemAgents,
  domainAgents,
  activeAgent,
}: AgentStatusPanelProps) {
  return (
    <div className="agent-status-panel space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity className="w-5 h-5 text-blue-500" />
        <h3 className="text-lg font-semibold text-fg-0">Deployed Agents</h3>
      </div>

      {/* System Agents */}
      <div>
        <h4 className="text-sm font-medium text-fg-2 mb-3 uppercase tracking-wide">
          System Agents ({systemAgents.length})
        </h4>
        <div className="space-y-2">
          {systemAgents.map((agent) => (
            <AgentStatusCard key={agent.id} agent={agent} isActive={activeAgent === agent.id} />
          ))}
        </div>
      </div>

      {/* Domain Agents */}
      {domainAgents.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-fg-2 mb-3 uppercase tracking-wide">
            Domain Agents ({domainAgents.length})
          </h4>
          <div className="space-y-2">
            {domainAgents.map((agent) => (
              <AgentStatusCard key={agent.id} agent={agent} isActive={activeAgent === agent.id} />
            ))}
          </div>
        </div>
      )}

      {domainAgents.length === 0 && (
        <div className="text-center py-8 text-fg-3 text-sm">
          <p>No domain agents deployed</p>
          <p className="text-xs mt-1">Deploy agents to see them here</p>
        </div>
      )}
    </div>
  );
}

interface AgentStatusCardProps {
  agent: Agent;
  isActive: boolean;
}

function AgentStatusCard({ agent, isActive }: AgentStatusCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div
      className={`
        agent-status-card
        p-3 rounded-lg border transition-all duration-200
        ${
          isActive
            ? 'border-blue-500 bg-blue-500/10 shadow-sm'
            : 'border-white/10 bg-bg-1 hover:bg-bg-2 hover:border-white/20'
        }
      `}
    >
      <div className="flex items-start gap-3">
        {/* Status Indicator */}
        <div className="flex-shrink-0 mt-1">
          <div
            className={`
              w-3 h-3 rounded-full
              ${getStatusColor(agent.status)}
              ${isActive ? 'animate-pulse' : ''}
            `}
            title={getStatusLabel(agent.status)}
          />
        </div>

        {/* Agent Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <div className="font-medium text-sm text-fg-0 truncate">{agent.name}</div>
            {agent.version && (
              <span className="text-xs text-fg-3 flex-shrink-0">v{agent.version}</span>
            )}
          </div>

          <div className="text-xs text-fg-2 mt-0.5 truncate">{agent.description}</div>

          {/* Capabilities */}
          {agent.capabilities && agent.capabilities.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {agent.capabilities.slice(0, 3).map((cap, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-0.5 rounded bg-bg-2 text-fg-2 border border-white/10"
                >
                  {cap}
                </span>
              ))}
              {agent.capabilities.length > 3 && (
                <span className="text-xs px-2 py-0.5 text-fg-3">
                  +{agent.capabilities.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Error Message */}
          {agent.error && <div className="text-xs text-red-400 mt-1">Error: {agent.error}</div>}
        </div>

        {/* Active Indicator */}
        {isActive && (
          <div className="flex-shrink-0">
            <span className="text-blue-500 text-xs font-semibold uppercase tracking-wide">
              Active
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
