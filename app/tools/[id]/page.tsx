"use client"

import { useState, useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
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
} from "lucide-react"
import Link from "next/link"
import {
  PageHeader,
  EmptyState,
  LoadingState,
  StatusBadge,
  MetricCard,
  CompactMetricCard,
} from "@/components/shared"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { mockTools, getToolById, mockToolInvocations } from "@/lib/mocks/tools.mock"
import { mockAgents } from "@/lib/mocks/agents.mock"
import type { Tool } from "@/types"
import { cn } from "@/lib/utils"

export default function ToolDetailPage() {
  const params = useParams()
  const router = useRouter()
  const toolId = params.id as string

  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState("overview")
  const [isInstalling, setIsInstalling] = useState(false)
  const [isUninstalling, setIsUninstalling] = useState(false)

  // Get tool data
  const tool = useMemo(() => getToolById(toolId), [toolId])

  // Get agents using this tool
  const agentsUsingTool = useMemo(() => {
    if (!tool) return []
    return mockAgents.filter(agent =>
      agent.tools_used.includes(tool.name)
    )
  }, [tool])

  // Get recent invocations for this tool
  const recentInvocations = useMemo(() => {
    if (!tool) return []
    return mockToolInvocations.filter(inv => inv.tool_id === tool.id)
  }, [tool])

  const handleInstall = async () => {
    setIsInstalling(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsInstalling(false)
  }

  const handleUninstall = async () => {
    setIsUninstalling(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsUninstalling(false)
  }

  if (isLoading) {
    return <LoadingState message="Loading tool details..." />
  }

  if (!tool) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader title="Tool Not Found" />
        <EmptyState
          title="Tool not found"
          description="The tool you're looking for doesn't exist or has been removed."
          action={{
            label: "Back to Tools",
            onClick: () => router.push("/tools"),
          }}
        />
      </div>
    )
  }

  const successRate = (tool.success_rate * 100).toFixed(1)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader
        title={tool.display_name}
        description={tool.description}
        actions={
          <div className="flex items-center gap-2">
            {tool.installed ? (
              <>
                <Button variant="outline" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Configure
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUninstall}
                  disabled={isUninstalling}
                >
                  {isUninstalling ? "Uninstalling..." : "Uninstall"}
                </Button>
              </>
            ) : (
              <Button onClick={handleInstall} disabled={isInstalling}>
                <Download className="w-4 h-4 mr-2" />
                {isInstalling ? "Installing..." : "Install Tool"}
              </Button>
            )}
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
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-500">
                  <Trash2 className="w-4 h-4 mr-2" />
                  Remove Tool
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
            href="/tools"
            className="inline-flex items-center text-sm text-fg-2 hover:text-fg-0 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tools
          </Link>

          {/* Tool Meta */}
          <div className="flex items-start gap-6 mb-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                {tool.installed ? (
                  <Badge variant="default" className="bg-green-600">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Installed
                  </Badge>
                ) : (
                  <Badge variant="secondary">Available</Badge>
                )}
                {tool.verified && (
                  <Badge variant="outline">
                    <Shield className="w-3 h-3 mr-1" />
                    Verified
                  </Badge>
                )}
                {tool.update_available && (
                  <Badge variant="outline" className="text-yellow-500">
                    Update Available: v{tool.latest_version}
                  </Badge>
                )}
                <Badge variant="secondary">{tool.category}</Badge>
                <Badge variant="outline">v{tool.version}</Badge>
              </div>
              <p className="text-xs text-fg-2 mb-2">
                by {tool.vendor} • {tool.author}
              </p>
              <div className="flex items-center gap-4 text-sm text-fg-2">
                {tool.rating && (
                  <>
                    <span>⭐ {tool.rating.toFixed(1)}</span>
                    <span>•</span>
                  </>
                )}
                {tool.downloads && (
                  <>
                    <span>{tool.downloads.toLocaleString()} downloads</span>
                    <span>•</span>
                  </>
                )}
                <span>{agentsUsingTool.length} agents using</span>
              </div>
            </div>
          </div>

          {/* Key Metrics - Only show if installed */}
          {tool.installed && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Invocations (24h)"
                value={tool.total_invocations_24h.toLocaleString()}
                icon={Activity}
                trend={{ value: 12, direction: "up", label: "vs yesterday" }}
              />
              <MetricCard
                title="Success Rate"
                value={`${successRate}%`}
                icon={CheckCircle}
                trend={{ value: 1.5, direction: "up", label: "vs last week" }}
              />
              <MetricCard
                title="Avg Latency"
                value={`${tool.avg_latency_ms}ms`}
                icon={Clock}
              />
              <MetricCard
                title="Agents Using"
                value={agentsUsingTool.length}
                subtitle="Across environments"
                icon={TrendingUp}
              />
            </div>
          )}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="usage">Usage & Metrics</TabsTrigger>
              <TabsTrigger value="agents">Agents</TabsTrigger>
              <TabsTrigger value="permissions">Permissions</TabsTrigger>
              <TabsTrigger value="documentation">Documentation</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              {/* Description */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  About {tool.display_name}
                </h3>
                <p className="text-fg-1 mb-4">{tool.description}</p>
                {tool.documentation_url && (
                  <a
                    href={tool.documentation_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-sm text-blue-500 hover:text-blue-400"
                  >
                    View full documentation
                    <ExternalLink className="w-4 h-4 ml-1" />
                  </a>
                )}
              </Card>

              {/* Tags */}
              <Card className="p-6">
                <h3 className="text-sm font-semibold text-fg-0 mb-4">
                  Tags ({tool.tags.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {tool.tags.map(tag => (
                    <Badge key={tag} variant="outline">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </Card>

              {/* JSON Schema Preview */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  Parameter Schema
                </h3>
                <div className="bg-bg-2 rounded p-4 font-mono text-sm text-fg-1 overflow-x-auto">
                  <pre>{JSON.stringify(tool.json_schema, null, 2)}</pre>
                </div>
              </Card>
            </TabsContent>

            {/* Usage Tab */}
            <TabsContent value="usage" className="space-y-6">
              {!tool.installed ? (
                <EmptyState
                  title="Tool not installed"
                  description="Install this tool to view usage metrics and invocation history."
                  action={{
                    label: "Install Tool",
                    onClick: handleInstall,
                  }}
                />
              ) : (
                <>
                  {/* Detailed Metrics */}
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold text-fg-0 mb-4">
                      Usage Metrics (Last 24 Hours)
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                      <CompactMetricCard
                        label="Total Invocations"
                        value={tool.total_invocations_24h.toLocaleString()}
                      />
                      <CompactMetricCard
                        label="Successful"
                        value={(tool.total_invocations_24h * tool.success_rate).toFixed(0)}
                      />
                      <CompactMetricCard
                        label="Failed"
                        value={(tool.total_invocations_24h * (1 - tool.success_rate)).toFixed(0)}
                      />
                      <CompactMetricCard
                        label="Success Rate"
                        value={`${successRate}%`}
                      />
                      <CompactMetricCard
                        label="Avg Latency"
                        value={`${tool.avg_latency_ms}ms`}
                      />
                      <CompactMetricCard
                        label="Agents Using"
                        value={agentsUsingTool.length}
                      />
                    </div>
                  </Card>

                  {/* Recent Invocations */}
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold text-fg-0 mb-4">
                      Recent Invocations ({recentInvocations.length})
                    </h3>
                    {recentInvocations.length === 0 ? (
                      <EmptyState
                        title="No recent invocations"
                        description="This tool hasn't been called recently."
                      />
                    ) : (
                      <div className="space-y-3">
                        {recentInvocations.map(invocation => (
                          <div
                            key={invocation.id}
                            className="p-4 bg-bg-2 rounded"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex-1">
                                <p className="text-sm font-medium text-fg-0 mb-1">
                                  {invocation.id}
                                </p>
                                <p className="text-xs text-fg-2">
                                  {new Date(invocation.invoked_at).toLocaleString()}
                                </p>
                              </div>
                              <StatusBadge status={invocation.status} />
                            </div>
                            <div className="grid grid-cols-3 gap-4 text-xs mb-2">
                              <div>
                                <span className="text-fg-2">Agent:</span>{" "}
                                <Link
                                  href={`/agents/${invocation.agent_id}`}
                                  className="text-blue-500 hover:text-blue-400"
                                >
                                  {invocation.agent_id}
                                </Link>
                              </div>
                              {invocation.duration_ms && (
                                <div>
                                  <span className="text-fg-2">Duration:</span>{" "}
                                  <span className="text-fg-1">{invocation.duration_ms}ms</span>
                                </div>
                              )}
                              {invocation.cost && (
                                <div>
                                  <span className="text-fg-2">Cost:</span>{" "}
                                  <span className="text-fg-1">${invocation.cost.toFixed(4)}</span>
                                </div>
                              )}
                            </div>
                            {invocation.error_message && (
                              <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded">
                                <p className="text-xs text-red-400">{invocation.error_message}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                </>
              )}
            </TabsContent>

            {/* Agents Tab */}
            <TabsContent value="agents" className="space-y-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-fg-0">
                  Agents Using This Tool ({agentsUsingTool.length})
                </h3>
              </div>

              {agentsUsingTool.length === 0 ? (
                <EmptyState
                  title="No agents using this tool"
                  description="This tool is not currently being used by any agents."
                />
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {agentsUsingTool.map(agent => (
                    <Link key={agent.id} href={`/agents/${agent.id}`}>
                      <Card className="p-4 hover:border-blue-600/50 transition-colors cursor-pointer">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <h4 className="text-base font-semibold text-fg-0 mb-1">
                              {agent.display_name}
                            </h4>
                            <p className="text-xs text-fg-2">{agent.name}</p>
                          </div>
                          <StatusBadge status={agent.status} />
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-3">
                          <CompactMetricCard
                            label="Executions"
                            value={agent.metrics.executions_24h.toLocaleString()}
                          />
                          <CompactMetricCard
                            label="Success Rate"
                            value={`${(agent.metrics.success_rate * 100).toFixed(1)}%`}
                          />
                        </div>
                      </Card>
                    </Link>
                  ))}
                </div>
              )}
            </TabsContent>

            {/* Permissions Tab */}
            <TabsContent value="permissions" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  Required Permissions ({tool.permissions.length})
                </h3>
                {tool.permissions.length === 0 ? (
                  <p className="text-sm text-fg-2">
                    This tool does not require any special permissions.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {tool.permissions.map((permission, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-bg-2 rounded"
                      >
                        <div>
                          <p className="text-sm font-medium text-fg-0">
                            {permission.resource}
                          </p>
                          <p className="text-xs text-fg-2">
                            Scope: {permission.scope}
                          </p>
                        </div>
                        <Badge variant="outline">{permission.action}</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </TabsContent>

            {/* Documentation Tab */}
            <TabsContent value="documentation" className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-fg-0 mb-4">
                  Documentation
                </h3>
                <div className="prose prose-invert max-w-none">
                  <p className="text-fg-1">
                    Detailed documentation for {tool.display_name} is available in the official documentation.
                  </p>
                  {tool.documentation_url && (
                    <a
                      href={tool.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-500 hover:text-blue-400 mt-4"
                    >
                      View full documentation
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </a>
                  )}
                </div>
              </Card>

              {/* Handler Code for Custom Tools */}
              {tool.handler_code && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-fg-0 mb-4">
                    Handler Code
                  </h3>
                  <div className="bg-bg-2 rounded p-4 font-mono text-sm text-fg-1 overflow-x-auto">
                    <pre>{tool.handler_code}</pre>
                  </div>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
