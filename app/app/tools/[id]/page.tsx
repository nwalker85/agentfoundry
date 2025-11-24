'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Download,
  Trash2,
  Settings,
  MoreVertical,
  Activity,
  Clock,
  CheckCircle,
  TrendingUp,
  ExternalLink,
  Code,
  Shield,
  FileInput,
  FileOutput,
  Play,
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
import type { IntegrationToolCatalogItem } from '@/types';
import { cn } from '@/lib/utils';
import { ConfigurationDrawer } from './ConfigurationDrawer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ToolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.id as string;

  const [tool, setTool] = useState<IntegrationToolCatalogItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isInstalling, setIsInstalling] = useState(false);
  const [isUninstalling, setIsUninstalling] = useState(false);
  const [showConfigDrawer, setShowConfigDrawer] = useState(false);

  // Fetch tool data
  useEffect(() => {
    const fetchTool = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API_BASE_URL}/api/integrations/tools/${toolId}`);
        if (!res.ok) {
          if (res.status === 404) {
            setError('Tool not found');
          } else {
            throw new Error(res.statusText);
          }
          setTool(null);
          return;
        }
        const data = await res.json();
        setTool(data);
      } catch (err) {
        console.error('Failed to load tool:', err);
        setError('Failed to load tool. Ensure the MCP integration server is running.');
        setTool(null);
      } finally {
        setIsLoading(false);
      }
    };

    void fetchTool();
  }, [toolId]);

  // TODO: Fetch agents using this tool from API
  const agentsUsingTool: any[] = [];

  // TODO: Fetch recent invocations from API
  const recentInvocations: any[] = [];

  const handleInstall = async () => {
    setIsInstalling(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsInstalling(false);
  };

  const handleUninstall = async () => {
    setIsUninstalling(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsUninstalling(false);
  };

  if (isLoading) {
    return <LoadingState message="Loading tool details..." />;
  }

  if (error || !tool) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader title="Tool Not Found" />
        <EmptyState
          title={error || 'Tool not found'}
          description="The tool you're looking for doesn't exist or the MCP integration server may not be running."
          action={{
            label: 'Back to Tools',
            onClick: () => router.push('/app/tools'),
          }}
        />
      </div>
    );
  }

  const healthStatus = tool.health
    ? tool.health.failure && tool.health.failure > 0
      ? 'degraded'
      : 'healthy'
    : 'unknown';

  const totalInvocations = (tool.health?.success || 0) + (tool.health?.failure || 0);
  const successRate =
    totalInvocations > 0
      ? (((tool.health?.success || 0) / totalInvocations) * 100).toFixed(1)
      : '0';

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader
        title={tool.displayName}
        description={tool.description}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setShowConfigDrawer(true)}>
              <Settings className="w-4 h-4 mr-2" />
              Configure
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Documentation
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Code className="w-4 h-4 mr-2" />
                  View Schema
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        }
      />

      {/* Configuration Drawer */}
      <ConfigurationDrawer
        toolName={tool.toolName}
        toolDisplayName={tool.displayName}
        open={showConfigDrawer}
        onOpenChange={setShowConfigDrawer}
        onSaved={() => {
          // Optionally refresh tool data or show success message
          console.log('Configuration saved successfully');
        }}
      />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Back Button */}
          <Link
            href="/app/tools"
            className="inline-flex items-center text-sm text-fg-2 hover:text-fg-0 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tools
          </Link>

          {/* Tool Meta */}
          <div className="flex items-start gap-6 mb-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Badge
                  variant={healthStatus === 'healthy' ? 'default' : 'secondary'}
                  className={
                    healthStatus === 'healthy'
                      ? 'bg-green-600'
                      : healthStatus === 'degraded'
                        ? 'bg-yellow-600'
                        : ''
                  }
                >
                  {healthStatus === 'healthy' ? (
                    <>
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Healthy
                    </>
                  ) : healthStatus === 'degraded' ? (
                    'Degraded'
                  ) : (
                    'Unknown'
                  )}
                </Badge>
                <Badge variant="secondary">{tool.category}</Badge>
              </div>
              <div className="flex items-center gap-4 text-sm text-fg-2">
                <span>{tool.tags.length} tags</span>
                {tool.health && (
                  <>
                    <span>•</span>
                    <span>{totalInvocations} total invocations</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          {tool.health && totalInvocations > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Total Invocations"
                value={totalInvocations.toLocaleString()}
                icon={Activity}
              />
              <MetricCard title="Success Rate" value={`${successRate}%`} icon={CheckCircle} />
              <MetricCard
                title="Successful"
                value={(tool.health.success || 0).toString()}
                icon={CheckCircle}
              />
              <MetricCard
                title="Failed"
                value={(tool.health.failure || 0).toString()}
                icon={Activity}
              />
            </div>
          )}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="schema">Schema</TabsTrigger>
              <TabsTrigger value="usage">Usage & Metrics</TabsTrigger>
              <TabsTrigger value="agents">Agents</TabsTrigger>
              <TabsTrigger value="permissions">Permissions</TabsTrigger>
              <TabsTrigger value="documentation">Documentation</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Description */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">About {tool.displayName}</h3>
                <p className="text-fg-1 mb-4">{tool.description}</p>
              </Card>

              {/* Tags */}
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-fg-0 mb-4">Tags ({tool.tags.length})</h3>
                <div className="flex flex-wrap gap-2">
                  {tool.tags.map((tag) => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </Card>

              {/* Metadata */}
              {tool.metadata && Object.keys(tool.metadata).length > 0 && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-fg-0 mb-4">Metadata</h3>
                  <div className="bg-bg-2 rounded p-4 font-mono text-sm text-fg-1 overflow-x-auto">
                    <pre>{JSON.stringify(tool.metadata, null, 2)}</pre>
                  </div>
                </Card>
              )}

              {/* Health Status */}
              {tool.health && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-fg-0 mb-4">Health Status</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-fg-2">Successful Invocations</span>
                      <span className="text-fg-0 font-medium">{tool.health.success || 0}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-fg-2">Failed Invocations</span>
                      <span className="text-fg-0 font-medium">{tool.health.failure || 0}</span>
                    </div>
                    {tool.health.last_error && (
                      <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded">
                        <p className="text-xs font-semibold text-red-400 mb-1">Last Error</p>
                        <p className="text-xs text-red-300">{tool.health.last_error}</p>
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </TabsContent>

            {/* Schema Tab */}
            <TabsContent value="schema" className="space-y-6">
              {/* Input Schema */}
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileInput className="w-5 h-5 text-blue-400" />
                  <h3 className="text-lg font-semibold text-fg-0">Input Parameters</h3>
                </div>
                {tool.inputSchema?.properties &&
                Object.keys(tool.inputSchema.properties).length > 0 ? (
                  <div className="space-y-4">
                    {/* Parameters Table */}
                    <div className="border border-white/10 rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-bg-2">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-fg-2 uppercase tracking-wide">
                              Parameter
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-fg-2 uppercase tracking-wide">
                              Type
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-fg-2 uppercase tracking-wide">
                              Required
                            </th>
                            <th className="px-4 py-3 text-left text-xs font-semibold text-fg-2 uppercase tracking-wide">
                              Description
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {Object.entries(tool.inputSchema.properties).map(
                            ([name, prop]: [string, any]) => (
                              <tr key={name} className="hover:bg-bg-1/50">
                                <td className="px-4 py-3">
                                  <code className="text-sm font-mono text-blue-300">{name}</code>
                                </td>
                                <td className="px-4 py-3">
                                  <Badge variant="outline" className="text-xs font-mono">
                                    {prop.type}
                                    {prop.enum && ` (${prop.enum.join(' | ')})`}
                                  </Badge>
                                </td>
                                <td className="px-4 py-3">
                                  {tool.inputSchema?.required?.includes(name) ? (
                                    <Badge className="bg-red-500/20 text-red-300 text-xs">
                                      Required
                                    </Badge>
                                  ) : (
                                    <span className="text-fg-3 text-xs">Optional</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm text-fg-1">
                                  {prop.description || '-'}
                                  {prop.default !== undefined && (
                                    <span className="ml-2 text-fg-3">
                                      (default: <code className="font-mono">{String(prop.default)}</code>)
                                    </span>
                                  )}
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <p className="text-fg-2 text-sm">No input parameters defined.</p>
                )}
              </Card>

              {/* Output Schema */}
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <FileOutput className="w-5 h-5 text-green-400" />
                  <h3 className="text-lg font-semibold text-fg-0">Output Schema</h3>
                </div>
                {tool.outputSchema ? (
                  <div className="bg-bg-2 rounded-lg p-4 font-mono text-sm text-fg-1 overflow-x-auto">
                    <pre>{JSON.stringify(tool.outputSchema, null, 2)}</pre>
                  </div>
                ) : (
                  <p className="text-fg-2 text-sm">No output schema defined.</p>
                )}
              </Card>

              {/* Examples */}
              {tool.examples && tool.examples.length > 0 && (
                <Card className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Play className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-semibold text-fg-0">Examples</h3>
                  </div>
                  <div className="space-y-6">
                    {tool.examples.map((example, idx) => (
                      <div
                        key={idx}
                        className="border border-white/10 rounded-lg overflow-hidden"
                      >
                        <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/10">
                          {/* Input */}
                          <div className="p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <FileInput className="w-4 h-4 text-blue-400" />
                              <span className="text-xs font-semibold text-fg-2 uppercase tracking-wide">
                                Input
                              </span>
                            </div>
                            <div className="bg-bg-2 rounded p-3 font-mono text-sm text-fg-1 overflow-x-auto">
                              <pre>{JSON.stringify(example.input, null, 2)}</pre>
                            </div>
                          </div>
                          {/* Output */}
                          <div className="p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <FileOutput className="w-4 h-4 text-green-400" />
                              <span className="text-xs font-semibold text-fg-2 uppercase tracking-wide">
                                Output
                              </span>
                            </div>
                            <div className="bg-bg-2 rounded p-3 font-mono text-sm text-fg-1 overflow-x-auto">
                              <pre>{JSON.stringify(example.output, null, 2)}</pre>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Raw JSON Schema */}
              <Card className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Code className="w-5 h-5 text-fg-2" />
                  <h3 className="text-lg font-semibold text-fg-0">Raw JSON Schema</h3>
                </div>
                <div className="bg-bg-2 rounded-lg p-4 font-mono text-xs text-fg-1 overflow-x-auto max-h-96">
                  <pre>
                    {JSON.stringify(
                      {
                        inputSchema: tool.inputSchema,
                        outputSchema: tool.outputSchema,
                      },
                      null,
                      2
                    )}
                  </pre>
                </div>
              </Card>
            </TabsContent>

            {/* Usage Tab */}
            <TabsContent value="usage" className="space-y-6">
              {totalInvocations === 0 ? (
                <EmptyState
                  title="No usage data yet"
                  description="This tool hasn't been invoked yet. Usage metrics will appear here after the first invocation."
                />
              ) : (
                <>
                  {/* Detailed Metrics */}
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold text-fg-0 mb-4">Usage Metrics</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <CompactMetricCard
                        label="Total Invocations"
                        value={totalInvocations.toLocaleString()}
                      />
                      <CompactMetricCard
                        label="Successful"
                        value={(tool.health?.success || 0).toString()}
                      />
                      <CompactMetricCard
                        label="Failed"
                        value={(tool.health?.failure || 0).toString()}
                      />
                      <CompactMetricCard label="Success Rate" value={`${successRate}%`} />
                    </div>
                  </Card>

                  {/* Recent Invocations Placeholder */}
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold text-fg-0 mb-4">Recent Invocations</h3>
                    <EmptyState
                      title="Invocation history coming soon"
                      description="Detailed invocation logs will be available in a future update."
                    />
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Agents Tab */}
            <TabsContent value="agents" className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-fg-0">Agents Using This Tool</h3>
              </div>

              <EmptyState
                title="Agent binding coming soon"
                description="Agent-tool binding will be available in a future update. You'll be able to see which agents are using this tool."
              />
            </TabsContent>

            {/* Permissions Tab */}
            <TabsContent value="permissions" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">Required Permissions</h3>
                <p className="text-sm text-fg-2">
                  Permission management for tools will be available in a future update.
                </p>
              </Card>
            </TabsContent>

            {/* Documentation Tab */}
            <TabsContent value="documentation" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">Documentation</h3>
                <div className="prose prose-invert max-w-none">
                  <p className="text-fg-1">
                    Documentation for {tool.displayName} will be available from the n8n integration.
                  </p>
                  <p className="text-fg-2 text-sm mt-4">
                    This tool is powered by n8n workflows. For detailed documentation about the
                    underlying integration, visit the n8n UI or check the integration's metadata.
                  </p>
                </div>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
