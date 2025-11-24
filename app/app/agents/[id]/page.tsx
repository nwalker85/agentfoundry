'use client';

import { useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Play,
  Pause,
  Settings,
  Copy,
  Download,
  Trash2,
  MoreVertical,
  Activity,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import {
  PageHeader,
  EmptyState,
  LoadingState,
  StatusBadge,
  MetricCard,
  CompactMetricCard,
} from '@/components/shared';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { mockAgents, getAgentById } from '@/lib/mocks/agents.mock';
import { mockDeployments, getDeploymentsByAgent } from '@/lib/mocks/deployments.mock';
import { mockTraces, getTracesByAgent } from '@/lib/mocks/monitoring.mock';
import type { Agent } from '@/types';
import { cn } from '@/lib/utils';

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Get agent data
  const agent = useMemo(() => getAgentById(agentId), [agentId]);
  const deployments = useMemo(() => getDeploymentsByAgent(agentId), [agentId]);
  const traces = useMemo(() => getTracesByAgent(agentId), [agentId]);

  if (isLoading) {
    return <LoadingState message="Loading agent details..." />;
  }

  if (!agent) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader title="Agent Not Found" />
        <EmptyState
          title="Agent not found"
          description="The agent you're looking for doesn't exist or has been deleted."
          action={{
            label: 'Back to Agents',
            onClick: () => router.push('/app/agents'),
          }}
        />
      </div>
    );
  }

  const latestDeployment = deployments[0];
  const successRate = (agent.metrics.success_rate * 100).toFixed(1);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader
        title={agent.display_name}
        description={agent.description}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm">
              <Play className="w-4 h-4 mr-2" />
              Test Agent
            </Button>
            <Button variant="outline" size="sm">
              <Copy className="w-4 h-4 mr-2" />
              Duplicate
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Download className="w-4 h-4 mr-2" />
                  Export YAML
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-500">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Agent
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        }
      />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Back Button */}
          <Link
            href="/app/agents"
            className="inline-flex items-center text-sm text-fg-2 hover:text-fg-0 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Agents
          </Link>

          {/* Agent Meta */}
          <div className="flex items-start gap-6 mb-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <StatusBadge status={agent.status} />
                <Badge variant="secondary">{agent.environment}</Badge>
                <Badge variant="outline">v{agent.version}</Badge>
              </div>
              <p className="text-xs text-fg-2 font-mono mb-2">{agent.name}</p>
              <div className="flex items-center gap-4 text-sm text-fg-2">
                <span>Created {new Date(agent.created_at).toLocaleDateString()}</span>
                <span>•</span>
                <span>Updated {new Date(agent.updated_at).toLocaleDateString()}</span>
                <span>•</span>
                <span>By {agent.created_by}</span>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Executions (24h)"
              value={agent.metrics.executions_24h.toLocaleString()}
              icon={Activity}
              trend={{ value: 8, direction: 'up', label: 'vs yesterday' }}
            />
            <MetricCard
              title="Success Rate"
              value={`${successRate}%`}
              icon={CheckCircle}
              trend={{ value: 2, direction: 'up', label: 'vs last week' }}
            />
            <MetricCard
              title="Avg Latency"
              value={`${agent.metrics.avg_latency_ms}ms`}
              subtitle={`P95: ${agent.metrics.p95_latency_ms}ms`}
              icon={Clock}
            />
            <MetricCard
              title="Cost (24h)"
              value={`$${agent.total_cost_24h.toFixed(2)}`}
              subtitle={`P95: $${agent.cost_p95.toFixed(4)}`}
              icon={DollarSign}
            />
          </div>

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="metrics">Metrics & Logs</TabsTrigger>
              <TabsTrigger value="deployments">Deployments</TabsTrigger>
              <TabsTrigger value="configuration">Configuration</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Tools & Models */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-fg-0 mb-4">
                    Tools ({agent.tools_used.length})
                  </h3>
                  <div className="space-y-2">
                    {agent.tools_used.map((tool) => (
                      <div
                        key={tool}
                        className="flex items-center justify-between p-2 bg-bg-2 rounded"
                      >
                        <span className="text-sm text-fg-1">{tool}</span>
                        <Badge variant="outline" className="text-xs">
                          installed
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="p-6">
                  <h3 className="text-sm font-semibold text-fg-0 mb-4">
                    Models ({agent.models_used.length})
                  </h3>
                  <div className="space-y-2">
                    {agent.models_used.map((model) => (
                      <div
                        key={model}
                        className="flex items-center justify-between p-2 bg-bg-2 rounded"
                      >
                        <span className="text-sm text-fg-1">{model}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Channels */}
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-fg-0 mb-4">
                  Channels ({agent.channels.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {agent.channels.map((channel) => (
                    <Badge key={channel} variant="secondary">
                      {channel}
                    </Badge>
                  ))}
                </div>
              </Card>

              {/* Tags */}
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-fg-0 mb-4">Tags ({agent.tags.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {agent.tags.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </Card>
            </TabsContent>

            {/* Metrics Tab */}
            <TabsContent value="metrics" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  Detailed Metrics (Last 24 Hours)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  <CompactMetricCard
                    label="Total Executions"
                    value={agent.metrics.executions_24h.toLocaleString()}
                  />
                  <CompactMetricCard
                    label="Success Count"
                    value={(agent.metrics.executions_24h * agent.metrics.success_rate).toFixed(0)}
                  />
                  <CompactMetricCard label="Error Count" value={agent.metrics.error_count} />
                  <CompactMetricCard label="Success Rate" value={`${successRate}%`} />
                  <CompactMetricCard
                    label="Avg Latency"
                    value={`${agent.metrics.avg_latency_ms}ms`}
                  />
                  <CompactMetricCard
                    label="P95 Latency"
                    value={`${agent.metrics.p95_latency_ms}ms`}
                  />
                  <CompactMetricCard
                    label="P99 Latency"
                    value={`${agent.metrics.p99_latency_ms}ms`}
                  />
                  <CompactMetricCard
                    label="Total Cost"
                    value={`$${agent.total_cost_24h.toFixed(2)}`}
                  />
                </div>
              </Card>

              {/* Recent Traces */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  Recent Traces ({traces.length})
                </h3>
                {traces.length === 0 ? (
                  <EmptyState
                    title="No traces yet"
                    description="Traces will appear here once the agent starts executing."
                  />
                ) : (
                  <div className="space-y-3">
                    {traces.map((trace) => (
                      <Link
                        key={trace.id}
                        href={`/monitoring/traces/${trace.id}`}
                        className="block p-4 bg-bg-2 rounded hover:bg-bg-2/80 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-fg-0 mb-1">{trace.id}</p>
                            <p className="text-xs text-fg-2">
                              {new Date(trace.started_at).toLocaleString()}
                            </p>
                          </div>
                          <StatusBadge status={trace.status} />
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-xs">
                          <div>
                            <span className="text-fg-2">Duration:</span>{' '}
                            <span className="text-fg-1">{trace.duration_ms}ms</span>
                          </div>
                          <div>
                            <span className="text-fg-2">Tokens:</span>{' '}
                            <span className="text-fg-1">{trace.total_tokens}</span>
                          </div>
                          <div>
                            <span className="text-fg-2">Cost:</span>{' '}
                            <span className="text-fg-1">${trace.total_cost.toFixed(4)}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </Card>
            </TabsContent>

            {/* Deployments Tab */}
            <TabsContent value="deployments" className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-fg-0">
                  Deployment History ({deployments.length})
                </h3>
                <Button>
                  <Play className="w-4 h-4 mr-2" />
                  New Deployment
                </Button>
              </div>

              {deployments.length === 0 ? (
                <EmptyState
                  title="No deployments yet"
                  description="Deploy this agent to start tracking deployment history."
                  action={{
                    label: 'Deploy Agent',
                    onClick: () => console.log('Deploy'),
                  }}
                />
              ) : (
                <div className="space-y-4">
                  {deployments.map((deployment) => (
                    <Card key={deployment.id} className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="text-base font-semibold text-fg-0">
                              v{deployment.version}
                            </h4>
                            <StatusBadge status={deployment.status} />
                            <Badge variant="secondary">{deployment.environment}</Badge>
                          </div>
                          <p className="text-sm text-fg-2">{deployment.changelog}</p>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <CompactMetricCard
                          label="Duration"
                          value={`${(deployment.duration_ms! / 1000).toFixed(1)}s`}
                        />
                        <CompactMetricCard
                          label="Tests"
                          value={`${deployment.tests_passed}/${deployment.tests_passed + deployment.tests_failed}`}
                        />
                        {deployment.latency_delta_ms !== undefined && (
                          <CompactMetricCard
                            label="Latency Δ"
                            value={`${deployment.latency_delta_ms > 0 ? '+' : ''}${deployment.latency_delta_ms}ms`}
                          />
                        )}
                        {deployment.cost_delta !== undefined && (
                          <CompactMetricCard
                            label="Cost Δ"
                            value={`${deployment.cost_delta > 0 ? '+' : ''}$${deployment.cost_delta.toFixed(4)}`}
                          />
                        )}
                      </div>

                      <div className="flex items-center justify-between text-xs text-fg-2">
                        <span>Deployed {new Date(deployment.created_at).toLocaleString()}</span>
                        <span>By {deployment.deployed_by}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Configuration Tab */}
            <TabsContent value="configuration" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">Agent Configuration</h3>
                <div className="bg-bg-2 rounded p-4 font-mono text-sm text-fg-1 overflow-x-auto">
                  <pre>{agent.graph_yaml}</pre>
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
