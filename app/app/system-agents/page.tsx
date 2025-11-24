'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import {
  Settings,
  Activity,
  Database,
  Zap,
  Network,
  Save,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Info,
  Clock,
  MemoryStick,
  Gauge,
  FolderOpen,
} from 'lucide-react';

interface AgentConfig {
  metadata: {
    id: string;
    name: string;
    version: string;
    description: string;
    tags: string[];
  };
  spec: {
    capabilities: string[];
    workflow: {
      type: string;
      entry_point: string;
      recursion_limit: number;
    };
    integrations: Array<{
      type: string;
      required: boolean;
      operations: string[];
    }>;
    resource_limits: {
      max_concurrent_tasks: number;
      timeout_seconds: number;
      memory_mb: number;
      max_tokens_per_request: number;
    };
    observability: {
      trace_level: 'debug' | 'info' | 'warning' | 'error';
      metrics_enabled: boolean;
      metrics_interval_seconds: number;
      log_retention_days: number;
      structured_logging: boolean;
    };
    health_check: {
      enabled: boolean;
      interval_seconds: number;
      timeout_seconds: number;
      unhealthy_threshold: number;
    };
  };
  status: {
    phase: 'development' | 'staging' | 'production';
    state: 'active' | 'inactive' | 'error';
    last_health_check?: string;
    health_status?: 'healthy' | 'unhealthy' | 'unknown';
  };
}

const SYSTEM_AGENTS = [
  'io-agent',
  'supervisor-agent',
  'context-agent',
  'coherence-agent',
  'exception-agent',
  'observability-agent',
  'governance-agent',
];

export default function SystemAgentsPage() {
  const [agents, setAgents] = useState<Record<string, AgentConfig>>({});
  const [selectedAgent, setSelectedAgent] = useState<string>('io-agent');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load agent configurations
  useEffect(() => {
    loadAgentConfigs();
  }, []);

  const loadAgentConfigs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/system-agents');
      if (!response.ok) {
        throw new Error('Failed to load agents');
      }
      const data = await response.json();
      console.log('Loaded agents:', Object.keys(data));
      console.log('Agent data:', data);
      setAgents(data);
    } catch (error) {
      console.error('Error loading agent configs:', error);
      setMessage({ type: 'error', text: 'Failed to load agent configurations' });
    } finally {
      setLoading(false);
    }
  };

  const saveAgentConfig = async (agentId: string) => {
    setSaving(true);
    try {
      const response = await fetch(`/api/system-agents?id=${agentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(agents[agentId]),
      });

      if (!response.ok) {
        throw new Error('Failed to save configuration');
      }

      setMessage({
        type: 'success',
        text: `${agents[agentId].metadata.name} configuration saved successfully`,
      });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      console.error('Error saving agent config:', error);
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  };

  const updateAgentConfig = (agentId: string, updates: Partial<AgentConfig>) => {
    setAgents((prev) => ({
      ...prev,
      [agentId]: {
        ...prev[agentId],
        ...updates,
        spec: {
          ...prev[agentId].spec,
          ...updates.spec,
        },
      },
    }));
  };

  const currentAgent = agents[selectedAgent];

  // Define toolbar actions similar to Forge
  const toolbarActions: ToolbarAction[] = useMemo(
    () => [
      {
        icon: FolderOpen,
        label: 'Load Config',
        onClick: loadAgentConfigs,
        variant: 'ghost',
        tooltip: 'Reload agent configurations',
      },
      {
        icon: Save,
        label: 'Save',
        onClick: () => currentAgent && saveAgentConfig(selectedAgent),
        disabled: saving || !currentAgent,
        variant: 'ghost',
        tooltip: saving ? 'Saving...' : 'Save current agent configuration',
      },
      {
        icon: RefreshCw,
        label: 'Refresh',
        onClick: loadAgentConfigs,
        disabled: loading,
        variant: 'ghost',
        tooltip: 'Refresh agent list',
      },
    ],
    [saving, loading, currentAgent, selectedAgent]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-bg-0">
      {/* Toolbar */}
      <Toolbar actions={toolbarActions} />

      {/* Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Status Messages */}
        {message && (
          <Alert
            className={`absolute top-16 left-1/2 transform -translate-x-1/2 z-10 w-auto ${message.type === 'success' ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="w-4 h-4 text-green-500" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-500" />
            )}
            <AlertDescription
              className={message.type === 'success' ? 'text-green-400' : 'text-red-400'}
            >
              {message.text}
            </AlertDescription>
          </Alert>
        )}
        {/* Agent List Sidebar */}
        <div className="w-64 border-r border-white/10 bg-bg-1 overflow-y-auto">
          <div className="p-4">
            <h2 className="text-sm font-semibold text-fg-2 mb-2">TIER 0: FOUNDATION</h2>
            <p className="text-xs text-fg-3 mb-3">Core platform agents</p>
            <div className="space-y-2">
              {SYSTEM_AGENTS.slice(0, 4).map((agentId) => {
                const agent = agents[agentId];
                if (!agent) return null;

                return (
                  <button
                    key={agentId}
                    onClick={() => setSelectedAgent(agentId)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedAgent === agentId
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20 hover:bg-bg-2'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="font-medium text-fg-0 text-sm">{agent.metadata.name}</span>
                      {agent.status.health_status === 'healthy' ? (
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-fg-2 line-clamp-2">{agent.metadata.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          agent.status.state === 'active'
                            ? 'border-green-500/30 text-green-400'
                            : 'border-red-500/30 text-red-400'
                        }`}
                      >
                        {agent.status.state}
                      </Badge>
                      <span className="text-xs text-fg-3">v{agent.metadata.version}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            <h2 className="text-sm font-semibold text-fg-2 mt-6 mb-2">TIER 1: PRODUCTION</h2>
            <p className="text-xs text-fg-3 mb-3">Essential for production</p>

            <div className="space-y-2">
              {SYSTEM_AGENTS.slice(4).map((agentId) => {
                const agent = agents[agentId];
                if (!agent) return null;

                return (
                  <button
                    key={agentId}
                    onClick={() => setSelectedAgent(agentId)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedAgent === agentId
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20 hover:bg-bg-2'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-1">
                      <span className="font-medium text-fg-0 text-sm">{agent.metadata.name}</span>
                      {agent.status.health_status === 'healthy' ? (
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-fg-2 line-clamp-2">{agent.metadata.description}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          agent.status.state === 'active'
                            ? 'border-green-500/30 text-green-400'
                            : 'border-red-500/30 text-red-400'
                        }`}
                      >
                        {agent.status.state}
                      </Badge>
                      <span className="text-xs text-fg-3">v{agent.metadata.version}</span>
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
              <Info className="w-4 h-4 text-blue-400 mb-2" />
              <p className="text-xs text-blue-300">
                Tier 0 agents ARE the platform. Tier 1 agents are essential for production readiness
                (error handling, monitoring, security).
              </p>
            </div>
          </div>
        </div>

        {/* Agent Configuration Panel */}
        {currentAgent && (
          <div className="flex-1 overflow-y-auto">
            <div className="p-6">
              {/* Agent Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-2xl font-bold text-fg-0">{currentAgent.metadata.name}</h2>
                  <Button onClick={() => saveAgentConfig(selectedAgent)} disabled={saving}>
                    <Save className="w-4 h-4 mr-2" />
                    {saving ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
                <p className="text-fg-2">{currentAgent.metadata.description}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {currentAgent.metadata.tags.map((tag) => (
                    <Badge key={tag} variant="outline" className="border-white/20 text-fg-2">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Configuration Tabs */}
              <Tabs defaultValue="general" className="space-y-4">
                <TabsList className="bg-bg-1 border border-white/10">
                  <TabsTrigger value="general">General</TabsTrigger>
                  <TabsTrigger value="resources">Resources</TabsTrigger>
                  <TabsTrigger value="integrations">Integrations</TabsTrigger>
                  <TabsTrigger value="observability">Observability</TabsTrigger>
                  <TabsTrigger value="health">Health Check</TabsTrigger>
                </TabsList>

                {/* General Tab */}
                <TabsContent value="general" className="space-y-4">
                  <Card className="p-6 bg-bg-1 border-white/10">
                    <h3 className="font-semibold text-fg-0 mb-4 flex items-center">
                      <Settings className="w-4 h-4 mr-2 text-blue-500" />
                      General Configuration
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Version
                        </label>
                        <Input
                          value={currentAgent.metadata.version}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              metadata: { ...currentAgent.metadata, version: e.target.value },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">Status</label>
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Switch
                              checked={currentAgent.status.state === 'active'}
                              onCheckedChange={(checked) =>
                                updateAgentConfig(selectedAgent, {
                                  status: {
                                    ...currentAgent.status,
                                    state: checked ? 'active' : 'inactive',
                                  },
                                })
                              }
                            />
                            <span className="text-sm text-fg-1">
                              {currentAgent.status.state === 'active' ? 'Active' : 'Inactive'}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Deployment Phase
                        </label>
                        <select
                          value={currentAgent.status.phase}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              status: { ...currentAgent.status, phase: e.target.value as any },
                            })
                          }
                          className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm"
                        >
                          <option value="development">Development</option>
                          <option value="staging">Staging</option>
                          <option value="production">Production</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Capabilities
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {currentAgent.spec.capabilities.map((cap) => (
                            <Badge
                              key={cap}
                              className="bg-blue-500/20 text-blue-300 border-blue-500/30"
                            >
                              {cap.replace(/_/g, ' ')}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Workflow Entry Point
                        </label>
                        <Input
                          value={currentAgent.spec.workflow.entry_point}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                workflow: {
                                  ...currentAgent.spec.workflow,
                                  entry_point: e.target.value,
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Recursion Limit
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.workflow.recursion_limit}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                workflow: {
                                  ...currentAgent.spec.workflow,
                                  recursion_limit: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                {/* Resources Tab */}
                <TabsContent value="resources" className="space-y-4">
                  <Card className="p-6 bg-bg-1 border-white/10">
                    <h3 className="font-semibold text-fg-0 mb-4 flex items-center">
                      <Gauge className="w-4 h-4 mr-2 text-purple-500" />
                      Resource Limits
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          <Zap className="w-4 h-4 inline mr-1" />
                          Max Concurrent Tasks
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.resource_limits.max_concurrent_tasks}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                resource_limits: {
                                  ...currentAgent.spec.resource_limits,
                                  max_concurrent_tasks: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Maximum number of tasks this agent can handle simultaneously
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          <Clock className="w-4 h-4 inline mr-1" />
                          Timeout (seconds)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.resource_limits.timeout_seconds}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                resource_limits: {
                                  ...currentAgent.spec.resource_limits,
                                  timeout_seconds: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Maximum execution time before task is cancelled
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          <MemoryStick className="w-4 h-4 inline mr-1" />
                          Memory Limit (MB)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.resource_limits.memory_mb}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                resource_limits: {
                                  ...currentAgent.spec.resource_limits,
                                  memory_mb: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Maximum memory allocation for this agent
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Max Tokens Per Request
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.resource_limits.max_tokens_per_request}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                resource_limits: {
                                  ...currentAgent.spec.resource_limits,
                                  max_tokens_per_request: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Maximum LLM tokens allowed per request
                        </p>
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                {/* Integrations Tab */}
                <TabsContent value="integrations" className="space-y-4">
                  <Card className="p-6 bg-bg-1 border-white/10">
                    <h3 className="font-semibold text-fg-0 mb-4 flex items-center">
                      <Network className="w-4 h-4 mr-2 text-green-500" />
                      Service Integrations
                    </h3>

                    <div className="space-y-4">
                      {currentAgent.spec.integrations.map((integration, index) => (
                        <Card key={index} className="p-4 bg-bg-2 border-white/10">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <Database className="w-4 h-4 text-fg-2" />
                              <span className="font-medium text-fg-0">{integration.type}</span>
                            </div>
                            <Badge
                              variant="outline"
                              className={
                                integration.required
                                  ? 'border-red-500/30 text-red-400'
                                  : 'border-yellow-500/30 text-yellow-400'
                              }
                            >
                              {integration.required ? 'Required' : 'Optional'}
                            </Badge>
                          </div>
                          <div className="space-y-1">
                            <p className="text-xs text-fg-2 font-medium">Operations:</p>
                            <div className="flex flex-wrap gap-1">
                              {integration.operations.map((op) => (
                                <Badge
                                  key={op}
                                  variant="outline"
                                  className="text-xs border-white/10 text-fg-2"
                                >
                                  {op}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </Card>
                </TabsContent>

                {/* Observability Tab */}
                <TabsContent value="observability" className="space-y-4">
                  <Card className="p-6 bg-bg-1 border-white/10">
                    <h3 className="font-semibold text-fg-0 mb-4 flex items-center">
                      <Activity className="w-4 h-4 mr-2 text-orange-500" />
                      Observability Settings
                    </h3>

                    <div className="space-y-4">
                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Trace Level
                        </label>
                        <select
                          value={currentAgent.spec.observability.trace_level}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                observability: {
                                  ...currentAgent.spec.observability,
                                  trace_level: e.target.value as any,
                                },
                              },
                            })
                          }
                          className="w-full bg-bg-2 border border-white/10 rounded-lg px-3 py-2 text-fg-0 text-sm"
                        >
                          <option value="debug">Debug</option>
                          <option value="info">Info</option>
                          <option value="warning">Warning</option>
                          <option value="error">Error</option>
                        </select>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <label className="text-sm font-medium text-fg-1 block">
                            Metrics Enabled
                          </label>
                          <p className="text-xs text-fg-3 mt-1">
                            Collect performance and usage metrics
                          </p>
                        </div>
                        <Switch
                          checked={currentAgent.spec.observability.metrics_enabled}
                          onCheckedChange={(checked) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                observability: {
                                  ...currentAgent.spec.observability,
                                  metrics_enabled: checked,
                                },
                              },
                            })
                          }
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Metrics Interval (seconds)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.observability.metrics_interval_seconds}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                observability: {
                                  ...currentAgent.spec.observability,
                                  metrics_interval_seconds: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Log Retention (days)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.observability.log_retention_days}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                observability: {
                                  ...currentAgent.spec.observability,
                                  log_retention_days: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                        />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <label className="text-sm font-medium text-fg-1 block">
                            Structured Logging
                          </label>
                          <p className="text-xs text-fg-3 mt-1">Use JSON format for logs</p>
                        </div>
                        <Switch
                          checked={currentAgent.spec.observability.structured_logging}
                          onCheckedChange={(checked) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                observability: {
                                  ...currentAgent.spec.observability,
                                  structured_logging: checked,
                                },
                              },
                            })
                          }
                        />
                      </div>
                    </div>
                  </Card>
                </TabsContent>

                {/* Health Check Tab */}
                <TabsContent value="health" className="space-y-4">
                  <Card className="p-6 bg-bg-1 border-white/10">
                    <h3 className="font-semibold text-fg-0 mb-4 flex items-center">
                      <Activity className="w-4 h-4 mr-2 text-green-500" />
                      Health Check Configuration
                    </h3>

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <label className="text-sm font-medium text-fg-1 block">
                            Health Checks Enabled
                          </label>
                          <p className="text-xs text-fg-3 mt-1">
                            Automatically monitor agent health
                          </p>
                        </div>
                        <Switch
                          checked={currentAgent.spec.health_check.enabled}
                          onCheckedChange={(checked) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                health_check: {
                                  ...currentAgent.spec.health_check,
                                  enabled: checked,
                                },
                              },
                            })
                          }
                        />
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Check Interval (seconds)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.health_check.interval_seconds}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                health_check: {
                                  ...currentAgent.spec.health_check,
                                  interval_seconds: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                          disabled={!currentAgent.spec.health_check.enabled}
                        />
                        <p className="text-xs text-fg-3 mt-1">How often to check agent health</p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Check Timeout (seconds)
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.health_check.timeout_seconds}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                health_check: {
                                  ...currentAgent.spec.health_check,
                                  timeout_seconds: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                          disabled={!currentAgent.spec.health_check.enabled}
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Maximum time to wait for health check response
                        </p>
                      </div>

                      <div>
                        <label className="text-sm font-medium text-fg-1 mb-1.5 block">
                          Unhealthy Threshold
                        </label>
                        <Input
                          type="number"
                          value={currentAgent.spec.health_check.unhealthy_threshold}
                          onChange={(e) =>
                            updateAgentConfig(selectedAgent, {
                              spec: {
                                ...currentAgent.spec,
                                health_check: {
                                  ...currentAgent.spec.health_check,
                                  unhealthy_threshold: parseInt(e.target.value),
                                },
                              },
                            })
                          }
                          className="bg-bg-2 border-white/10"
                          disabled={!currentAgent.spec.health_check.enabled}
                        />
                        <p className="text-xs text-fg-3 mt-1">
                          Failed checks before marking agent as unhealthy
                        </p>
                      </div>

                      {/* Current Health Status */}
                      <Card className="p-4 bg-bg-2 border-white/10 mt-6">
                        <h4 className="text-sm font-medium text-fg-1 mb-3">
                          Current Health Status
                        </h4>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-fg-2">Status:</span>
                            <Badge
                              variant="outline"
                              className={
                                currentAgent.status.health_status === 'healthy'
                                  ? 'border-green-500/30 text-green-400'
                                  : currentAgent.status.health_status === 'unhealthy'
                                    ? 'border-red-500/30 text-red-400'
                                    : 'border-yellow-500/30 text-yellow-400'
                              }
                            >
                              {currentAgent.status.health_status || 'unknown'}
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm text-fg-2">Last Check:</span>
                            <span className="text-sm text-fg-1">
                              {currentAgent.status.last_health_check
                                ? new Date(currentAgent.status.last_health_check).toLocaleString()
                                : 'Never'}
                            </span>
                          </div>
                        </div>
                      </Card>
                    </div>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
