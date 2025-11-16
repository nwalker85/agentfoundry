"use client"

import { useState, useMemo } from "react"
import { Plus, Search, Filter, TrendingUp, TrendingDown, Download, RefreshCw } from "lucide-react"
import Link from "next/link"
import {
  PageHeader,
  EmptyState,
  LoadingState,
  SearchBar,
  StatusBadge,
  MetricCard,
  FilterPanel,
  ActiveFilters,
} from "@/components/shared"
import type { FilterGroup } from "@/components/shared"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Toolbar, type ToolbarAction } from "@/components/layout/Toolbar"
import { mockAgents } from "@/lib/mocks/agents.mock"
import type { Agent } from "@/types"
import { cn } from "@/lib/utils"

export default function AgentsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const [isRefreshing, setIsRefreshing] = useState(false)

  // Filter configuration
  const filterGroups: FilterGroup[] = [
    {
      id: "status",
      label: "Status",
      options: [
        { id: "active", label: "Active", count: mockAgents.filter(a => a.status === "active").length },
        { id: "inactive", label: "Inactive", count: mockAgents.filter(a => a.status === "inactive").length },
        { id: "draft", label: "Draft", count: mockAgents.filter(a => a.status === "draft").length },
        { id: "error", label: "Error", count: mockAgents.filter(a => a.status === "error").length },
      ],
    },
    {
      id: "environment",
      label: "Environment",
      options: [
        { id: "prod", label: "Production", count: mockAgents.filter(a => a.environment === "prod").length },
        { id: "staging", label: "Staging", count: mockAgents.filter(a => a.environment === "staging").length },
        { id: "dev", label: "Development", count: mockAgents.filter(a => a.environment === "dev").length },
      ],
    },
    {
      id: "tags",
      label: "Tags",
      options: [
        { id: "customer-service", label: "Customer Service", count: mockAgents.filter(a => a.tags.includes("customer-service")).length },
        { id: "sales", label: "Sales", count: mockAgents.filter(a => a.tags.includes("sales")).length },
        { id: "analytics", label: "Analytics", count: mockAgents.filter(a => a.tags.includes("analytics")).length },
        { id: "automation", label: "Automation", count: mockAgents.filter(a => a.tags.includes("automation")).length },
        { id: "development", label: "Development", count: mockAgents.filter(a => a.tags.includes("development")).length },
      ],
    },
  ]

  // Filter agents based on search and filters
  const filteredAgents = useMemo(() => {
    let result = mockAgents

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        agent =>
          agent.name.toLowerCase().includes(query) ||
          agent.display_name.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query) ||
          agent.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // Apply status filter
    if (selectedFilters.status?.length > 0) {
      result = result.filter(agent => selectedFilters.status.includes(agent.status))
    }

    // Apply environment filter
    if (selectedFilters.environment?.length > 0) {
      result = result.filter(agent => selectedFilters.environment.includes(agent.environment))
    }

    // Apply tags filter
    if (selectedFilters.tags?.length > 0) {
      result = result.filter(agent =>
        selectedFilters.tags.some(tag => agent.tags.includes(tag))
      )
    }

    return result
  }, [searchQuery, selectedFilters])

  const handleFilterChange = (groupId: string, optionId: string, checked: boolean) => {
    setSelectedFilters(prev => {
      const newFilters = { ...prev }
      if (!newFilters[groupId]) {
        newFilters[groupId] = []
      }
      if (checked) {
        newFilters[groupId] = [...newFilters[groupId], optionId]
      } else {
        newFilters[groupId] = newFilters[groupId].filter(id => id !== optionId)
      }
      return newFilters
    })
  }

  const handleRemoveFilter = (groupId: string, optionId: string) => {
    handleFilterChange(groupId, optionId, false)
  }

  const handleClearAllFilters = () => {
    setSelectedFilters({})
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    // Simulate refresh
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsRefreshing(false)
  }

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting agents...')
  }

  const handleCreateAgent = () => {
    // TODO: Navigate to create agent page
    console.log('Creating new agent...')
  }

  // Define toolbar actions
  const toolbarActions: ToolbarAction[] = useMemo(() => [
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
    {
      icon: Plus,
      label: 'Create Agent',
      onClick: handleCreateAgent,
      variant: 'default',
      tooltip: 'Create a new agent',
    },
  ], [isRefreshing])

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const active = mockAgents.filter(a => a.status === "active").length
    const totalExecutions = mockAgents.reduce((sum, a) => sum + a.metrics.executions_24h, 0)
    const avgSuccessRate = mockAgents.reduce((sum, a) => sum + a.metrics.success_rate, 0) / mockAgents.length
    const totalCost = mockAgents.reduce((sum, a) => sum + a.total_cost_24h, 0)

    return { active, totalExecutions, avgSuccessRate, totalCost }
  }, [])

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <Toolbar actions={toolbarActions} />
        <LoadingState message="Loading agents..." />
      </div>
    )
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
              value={summaryMetrics.active}
              subtitle={`${mockAgents.length - summaryMetrics.active} inactive`}
              icon={TrendingUp}
              trend={{ value: 12, direction: "up", label: "vs last week" }}
            />
            <MetricCard
              title="Total Executions (24h)"
              value={summaryMetrics.totalExecutions.toLocaleString()}
              icon={TrendingUp}
              trend={{ value: 8, direction: "up", label: "vs yesterday" }}
            />
            <MetricCard
              title="Avg Success Rate"
              value={`${(summaryMetrics.avgSuccessRate * 100).toFixed(1)}%`}
              icon={TrendingUp}
              trend={{ value: 2.3, direction: "up", label: "vs last week" }}
            />
            <MetricCard
              title="Total Cost (24h)"
              value={`$${summaryMetrics.totalCost.toFixed(2)}`}
              subtitle="Across all agents"
              icon={TrendingDown}
              trend={{ value: 5, direction: "down", label: "vs yesterday" }}
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
              {Object.keys(selectedFilters).some(key => selectedFilters[key]?.length > 0) && (
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
                  {filteredAgents.length === mockAgents.length
                    ? `Showing all ${filteredAgents.length} agents`
                    : `Found ${filteredAgents.length} of ${mockAgents.length} agents`}
                </p>
              </div>

              {/* Agent Grid */}
              {filteredAgents.length === 0 ? (
                <EmptyState
                  icon={Search}
                  title="No agents found"
                  description="Try adjusting your search or filters to find what you're looking for."
                  action={{
                    label: "Clear Filters",
                    onClick: () => {
                      setSearchQuery("")
                      handleClearAllFilters()
                    },
                  }}
                />
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredAgents.map(agent => (
                    <AgentCard key={agent.id} agent={agent} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function AgentCard({ agent }: { agent: Agent }) {
  const successRate = (agent.metrics.success_rate * 100).toFixed(1)
  const errorRate = ((1 - agent.metrics.success_rate) * 100).toFixed(1)

  return (
    <Link href={`/agents/${agent.id}`}>
      <Card className="p-6 hover:border-blue-600/50 transition-colors cursor-pointer h-full">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-fg-0 mb-1 truncate">
              {agent.display_name}
            </h3>
            <p className="text-xs text-fg-2 font-mono">{agent.name}</p>
          </div>
          <StatusBadge status={agent.status} />
        </div>

        {/* Description */}
        <p className="text-sm text-fg-2 mb-4 line-clamp-2">
          {agent.description}
        </p>

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
            <div className="text-lg font-semibold text-green-500 tabular-nums">
              {successRate}%
            </div>
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
            {agent.tags.slice(0, 2).map(tag => (
              <div
                key={tag}
                className="px-2 py-0.5 bg-bg-2 rounded text-xs text-fg-2"
              >
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
  )
}
