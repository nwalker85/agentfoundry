'use client';

import { useState, useMemo, useEffect } from 'react';
import { Plus, Search, Filter, TrendingUp, TrendingDown, Download, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import {
  PageHeader,
  EmptyState,
  LoadingState,
  SearchBar,
  StatusBadge,
  MetricCard,
  FilterPanel,
  ActiveFilters,
} from '@/components/shared';
import type { FilterGroup } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import { mockAgents } from '@/lib/mocks/agents.mock';
import type { Agent } from '@/types';
import { cn } from '@/lib/utils';
import { useEventSubscription, type Event } from '@/lib/hooks/useEventSubscription';
import { useAllAgentsMetrics, type AgentMetrics } from '@/lib/hooks/useActivityHistory';

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isLoadingAgents, setIsLoadingAgents] = useState(true);
  const { subscribe, isConnected } = useEventSubscription();

  // Fetch real metrics from observability database
  const {
    agents: agentMetrics,
    summary: metricsSummary,
    isLoading: isLoadingMetrics,
    refresh: refreshMetrics,
  } = useAllAgentsMetrics(24, false); // 24h window, no auto-refresh

  // Create a map of agent_id -> metrics for quick lookup
  const metricsMap = useMemo(() => {
    const map = new Map<string, AgentMetrics>();
    agentMetrics.forEach((m) => map.set(m.agent_id, m));
    return map;
  }, [agentMetrics]);

  // Load selected org/domain from localStorage
  useEffect(() => {
    const orgId = localStorage.getItem('selectedOrgId');
    const domainId = localStorage.getItem('selectedDomainId');
    setSelectedOrgId(orgId);
    setSelectedDomainId(domainId);
  }, []);

  // Subscribe to agent events for selected org/domain
  useEffect(() => {
    if (!selectedOrgId || !selectedDomainId) return;

    const unsubscribe = subscribe(
      {
        type: 'agent.*', // All agent events
        organization_id: selectedOrgId,
        domain_id: selectedDomainId,
      },
      (event: Event) => {
        console.log('📨 Received agent event:', event.type, event.data);

        if (event.type === 'agent.created') {
          // Add new agent to list
          const newAgent = {
            ...event.data,
            metrics: {
              executions_24h: 0,
              success_rate: 0.0,
              error_count: 0,
              avg_latency_ms: 0,
              p95_latency_ms: 0,
              p99_latency_ms: 0,
            },
            cost_p95: 0,
            total_cost_24h: 0,
            tools_used: [],
            models_used: [],
            channels: [],
            graph_yaml: '',
            graph_json: {},
          } as Agent;
          setAgents((prev) => [newAgent, ...prev]);
        } else if (event.type === 'agent.updated') {
          // Update existing agent
          setAgents((prev) =>
            prev.map((agent) => (agent.id === event.data.id ? { ...agent, ...event.data } : agent))
          );
        } else if (event.type === 'agent.deleted') {
          // Remove agent from list
          setAgents((prev) => prev.filter((agent) => agent.id !== event.data.id));
        }
      }
    );

    return unsubscribe;
  }, [selectedOrgId, selectedDomainId, subscribe]);

  // Fetch agents from API when org/domain changes
  useEffect(() => {
    const fetchAgents = async () => {
      if (!selectedOrgId || !selectedDomainId) {
        setAgents([]);
        setIsLoadingAgents(false);
        return;
      }

      setIsLoadingAgents(true);
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const url = `${apiBase}/api/control/agents?organization_id=${selectedOrgId}&domain_id=${selectedDomainId}`;
        const res = await fetch(url);

        if (!res.ok) {
          console.error('Failed to fetch agents:', res.statusText);
          setAgents([]);
          return;
        }

        const data = await res.json();
        // Map database agents to UI Agent type
        const mappedAgents: Agent[] = (data.agents || []).map((agent: any) => {
          // Look up real metrics from observability data
          const realMetrics = metricsMap.get(agent.id) || metricsMap.get(agent.name);
          return {
            ...agent,
            // Use real metrics if available, otherwise defaults
            metrics: {
              executions_24h: realMetrics?.executions ?? 0,
              success_rate: realMetrics?.success_rate ?? 0.0,
              error_count: realMetrics?.errors ?? 0,
              avg_latency_ms: realMetrics?.avg_latency_ms ?? 0,
              p95_latency_ms: realMetrics?.p95_latency_ms ?? 0,
              p99_latency_ms: realMetrics?.p99_latency_ms ?? 0,
            },
            cost_p95: 0, // TODO: Add cost tracking
            total_cost_24h: 0, // TODO: Add cost tracking
            tools_used: [],
            models_used: [],
            channels: [],
            graph_yaml: '',
            graph_json: {},
          };
        });
        setAgents(mappedAgents);
      } catch (error) {
        console.error('Error fetching agents:', error);
        setAgents([]);
      } finally {
        setIsLoadingAgents(false);
      }
    };

    fetchAgents();
  }, [selectedOrgId, selectedDomainId, metricsMap]);

  // Filter configuration (based on fetched agents)
  const filterGroups: FilterGroup[] = [
    {
      id: 'status',
      label: 'Status',
      options: [
        {
          id: 'active',
          label: 'Active',
          count: agents.filter((a) => a.status === 'active').length,
        },
        {
          id: 'inactive',
          label: 'Inactive',
          count: agents.filter((a) => a.status === 'inactive').length,
        },
        { id: 'draft', label: 'Draft', count: agents.filter((a) => a.status === 'draft').length },
        { id: 'error', label: 'Error', count: agents.filter((a) => a.status === 'error').length },
      ],
    },
    {
      id: 'environment',
      label: 'Environment',
      options: [
        {
          id: 'prod',
          label: 'Production',
          count: agents.filter((a) => a.environment === 'prod').length,
        },
        {
          id: 'staging',
          label: 'Staging',
          count: agents.filter((a) => a.environment === 'staging').length,
        },
        {
          id: 'dev',
          label: 'Development',
          count: agents.filter((a) => a.environment === 'dev').length,
        },
      ],
    },
    {
      id: 'tags',
      label: 'Tags',
      options: [
        {
          id: 'customer-service',
          label: 'Customer Service',
          count: agents.filter((a) => a.tags?.includes('customer-service')).length,
        },
        {
          id: 'sales',
          label: 'Sales',
          count: agents.filter((a) => a.tags?.includes('sales')).length,
        },
        {
          id: 'analytics',
          label: 'Analytics',
          count: agents.filter((a) => a.tags?.includes('analytics')).length,
        },
        {
          id: 'automation',
          label: 'Automation',
          count: agents.filter((a) => a.tags?.includes('automation')).length,
        },
        {
          id: 'development',
          label: 'Development',
          count: agents.filter((a) => a.tags?.includes('development')).length,
        },
      ],
    },
  ];

  // Filter agents based on search and filters
  const filteredAgents = useMemo(() => {
    let result = agents;

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (agent) =>
          agent.name.toLowerCase().includes(query) ||
          agent.display_name.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query) ||
          agent.tags?.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    // Apply status filter
    if (selectedFilters.status?.length > 0) {
      result = result.filter((agent) => selectedFilters.status.includes(agent.status));
    }

    // Apply environment filter
    if (selectedFilters.environment?.length > 0) {
      result = result.filter((agent) => selectedFilters.environment.includes(agent.environment));
    }

    // Apply tags filter
    if (selectedFilters.tags?.length > 0) {
      result = result.filter((agent) =>
        agent.tags?.some((tag) => selectedFilters.tags.includes(tag))
      );
    }

    return result;
  }, [searchQuery, selectedFilters, agents]);

  const handleFilterChange = (groupId: string, optionId: string, checked: boolean) => {
    setSelectedFilters((prev) => {
      const newFilters = { ...prev };
      if (!newFilters[groupId]) {
        newFilters[groupId] = [];
      }
      if (checked) {
        newFilters[groupId] = [...newFilters[groupId], optionId];
      } else {
        newFilters[groupId] = newFilters[groupId].filter((id) => id !== optionId);
      }
      return newFilters;
    });
  };

  const handleRemoveFilter = (groupId: string, optionId: string) => {
    handleFilterChange(groupId, optionId, false);
  };

  const handleClearAllFilters = () => {
    setSelectedFilters({});
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      // Refresh both agents and metrics in parallel
      const refreshPromises: Promise<void>[] = [refreshMetrics()];

      if (selectedOrgId && selectedDomainId) {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const url = `${apiBase}/api/control/agents?organization_id=${selectedOrgId}&domain_id=${selectedDomainId}`;

        refreshPromises.push(
          fetch(url).then(async (res) => {
            if (res.ok) {
              const data = await res.json();
              const mappedAgents: Agent[] = (data.agents || []).map((agent: any) => {
                const realMetrics = metricsMap.get(agent.id) || metricsMap.get(agent.name);
                return {
                  ...agent,
                  metrics: {
                    executions_24h: realMetrics?.executions ?? 0,
                    success_rate: realMetrics?.success_rate ?? 0.0,
                    error_count: realMetrics?.errors ?? 0,
                    avg_latency_ms: realMetrics?.avg_latency_ms ?? 0,
                    p95_latency_ms: realMetrics?.p95_latency_ms ?? 0,
                    p99_latency_ms: realMetrics?.p99_latency_ms ?? 0,
                  },
                  cost_p95: 0,
                  total_cost_24h: 0,
                  tools_used: [],
                  models_used: [],
                  channels: [],
                  graph_yaml: '',
                  graph_json: {},
                };
              });
              setAgents(mappedAgents);
            }
          })
        );
      }

      await Promise.all(refreshPromises);
    } catch (error) {
      console.error('Error refreshing agents:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting agents...');
  };

  const handleCreateAgent = () => {
    // TODO: Navigate to create agent page
    console.log('Creating new agent...');
  };

  // Define toolbar actions
  const toolbarActions: ToolbarAction[] = useMemo(
    () => [
      {
        icon: RefreshCw,
        label: 'Refresh',
        onClick: handleRefresh,
        disabled: isRefreshing,
        variant: 'ghost',
        tooltip: 'Refresh agent list',
      },
      {
        icon: Download,
        label: 'Export',
        onClick: handleExport,
        variant: 'ghost',
        tooltip: 'Export agent data',
      },
    ],
    [isRefreshing]
  );

  // Calculate summary metrics - prefer real metrics from observability, fall back to computed
  const summaryMetrics = useMemo(() => {
    const active = agents.filter((a) => a.status === 'active').length;

    // Use real metrics summary if available
    if (metricsSummary) {
      return {
        active,
        activeAgents: metricsSummary.active_agents,
        totalExecutions: metricsSummary.total_executions,
        avgSuccessRate: metricsSummary.overall_success_rate,
        avgLatency: metricsSummary.avg_latency_ms,
        totalErrors: metricsSummary.total_errors,
        totalCost: agents.reduce((sum, a) => sum + a.total_cost_24h, 0), // Cost not in observability yet
      };
    }

    // Fall back to computing from agent data
    const totalExecutions = agents.reduce((sum, a) => sum + a.metrics.executions_24h, 0);
    const avgSuccessRate =
      agents.length > 0
        ? agents.reduce((sum, a) => sum + a.metrics.success_rate, 0) / agents.length
        : 0;
    const avgLatency =
      agents.length > 0
        ? agents.reduce((sum, a) => sum + a.metrics.avg_latency_ms, 0) / agents.length
        : 0;
    const totalErrors = agents.reduce((sum, a) => sum + a.metrics.error_count, 0);
    const totalCost = agents.reduce((sum, a) => sum + a.total_cost_24h, 0);

    return {
      active,
      activeAgents: active,
      totalExecutions,
      avgSuccessRate,
      avgLatency,
      totalErrors,
      totalCost,
    };
  }, [agents, metricsSummary]);

  if (isLoadingAgents && agents.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <Toolbar actions={toolbarActions} />
        <LoadingState message="Loading agents..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <Toolbar actions={toolbarActions} />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Active Agents"
              value={summaryMetrics.activeAgents || summaryMetrics.active}
              subtitle={`${agents.length - summaryMetrics.active} inactive`}
              icon={TrendingUp}
            />
            <MetricCard
              title="Total Executions (24h)"
              value={summaryMetrics.totalExecutions.toLocaleString()}
              subtitle={isLoadingMetrics ? 'Loading...' : 'From observability data'}
              icon={TrendingUp}
            />
            <MetricCard
              title="Avg Success Rate"
              value={`${(summaryMetrics.avgSuccessRate * 100).toFixed(1)}%`}
              subtitle={
                summaryMetrics.totalErrors > 0
                  ? `${summaryMetrics.totalErrors} errors`
                  : 'No errors'
              }
              icon={summaryMetrics.avgSuccessRate >= 0.95 ? TrendingUp : TrendingDown}
            />
            <MetricCard
              title="Avg Latency"
              value={
                summaryMetrics.avgLatency ? `${Math.round(summaryMetrics.avgLatency)}ms` : 'N/A'
              }
              subtitle="Response time"
              icon={TrendingUp}
            />
          </div>

          {/* Search and Filters */}
          <div className="flex flex-col lg:flex-row gap-6">
            {/* Left Sidebar - Filters */}
            <div className="lg:w-64 flex-shrink-0">
              <Card className="p-4">
                <FilterPanel
                  groups={filterGroups}
                  selectedFilters={selectedFilters}
                  onFilterChange={handleFilterChange}
                  onClearAll={handleClearAllFilters}
                />
              </Card>
            </div>

            {/* Main Content */}
            <div className="flex-1 min-w-0">
              {/* Search Bar */}
              <div className="mb-4">
                <SearchBar
                  placeholder="Search agents by name, description, or tags..."
                  value={searchQuery}
                  onChange={setSearchQuery}
                  className="max-w-xl"
                />
              </div>

              {/* Active Filters */}
              {Object.keys(selectedFilters).some((key) => selectedFilters[key]?.length > 0) && (
                <div className="mb-4">
                  <ActiveFilters
                    selectedFilters={selectedFilters}
                    groups={filterGroups}
                    onRemove={handleRemoveFilter}
                  />
                </div>
              )}

              {/* Results Count */}
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-fg-2">
                  {filteredAgents.length === agents.length
                    ? `Showing all ${filteredAgents.length} agents`
                    : `Found ${filteredAgents.length} of ${agents.length} agents`}
                </p>
              </div>

              {/* Agent Grid */}
              {filteredAgents.length === 0 ? (
                <EmptyState
                  icon={Search}
                  title="No agents found"
                  description="Try adjusting your search or filters to find what you're looking for."
                  action={{
                    label: 'Clear Filters',
                    onClick: () => {
                      setSearchQuery('');
                      handleClearAllFilters();
                    },
                  }}
                />
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredAgents.map((agent) => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  const successRate = (agent.metrics.success_rate * 100).toFixed(1);
  const errorRate = ((1 - agent.metrics.success_rate) * 100).toFixed(1);

  return (
    <Link href={`/app/agents/${agent.id}`}>
      <Card className="p-6 hover:border-blue-600/50 transition-colors cursor-pointer h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-fg-0 mb-1 truncate">{agent.display_name}</h3>
            <p className="text-xs text-fg-2 font-mono">{agent.name}</p>
          </div>
          <StatusBadge status={agent.status} />
        </div>

        {/* Description */}
        <p className="text-sm text-fg-2 mb-4 line-clamp-2">{agent.description}</p>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 mb-4 pb-4 border-b border-white/10">
          <div>
            <div className="text-xs text-fg-2 mb-1">Executions (24h)</div>
            <div className="text-lg font-semibold text-fg-0 tabular-nums">
              {agent.metrics.executions_24h.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Success Rate</div>
            <div className="text-lg font-semibold text-green-500 tabular-nums">{successRate}%</div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Avg Latency</div>
            <div className="text-lg font-semibold text-fg-0 tabular-nums">
              {agent.metrics.avg_latency_ms}ms
            </div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Cost (24h)</div>
            <div className="text-lg font-semibold text-fg-0 tabular-nums">
              ${agent.total_cost_24h.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {agent.environment}
            </Badge>
            <Badge variant="outline" className="text-xs">
              v{agent.version}
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            {agent.tags.slice(0, 2).map((tag) => (
              <div key={tag} className="px-2 py-0.5 bg-bg-2 rounded text-xs text-fg-2">
                {tag}
              </div>
            ))}
            {agent.tags.length > 2 && (
              <div className="px-2 py-0.5 bg-bg-2 rounded text-xs text-fg-2">
                +{agent.tags.length - 2}
              </div>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
