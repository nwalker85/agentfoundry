"use client"

import { useState, useMemo } from "react"
import { Plus, Download, Check, AlertCircle } from "lucide-react"
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
import {
  mockTools,
  getInstalledTools,
  getToolsByStatus,
  getToolStats,
} from "@/lib/mocks/tools.mock"
import type { Tool, ToolStatus } from "@/types"
import { cn } from "@/lib/utils"

export default function ToolsPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [isLoading, setIsLoading] = useState(false)

  // Get tool statistics
  const stats = useMemo(() => getToolStats(), [])

  // Filter configuration
  const filterGroups: FilterGroup[] = [
    {
      id: "status",
      label: "Status",
      options: [
        { id: "installed", label: "Installed", count: mockTools.filter(t => t.installed).length },
        { id: "available", label: "Available", count: mockTools.filter(t => !t.installed).length },
        { id: "update_available", label: "Updates", count: mockTools.filter(t => t.update_available).length },
      ],
    },
    {
      id: "category",
      label: "Category",
      options: [
        { id: "communication", label: "Communication", count: mockTools.filter(t => t.category === "communication").length },
        { id: "data", label: "Data", count: mockTools.filter(t => t.category === "data").length },
        { id: "integration", label: "Integration", count: mockTools.filter(t => t.category === "integration").length },
        { id: "ml_ai", label: "ML/AI", count: mockTools.filter(t => t.category === "ml_ai").length },
        { id: "search", label: "Search", count: mockTools.filter(t => t.category === "search").length },
        { id: "analytics", label: "Analytics", count: mockTools.filter(t => t.category === "analytics").length },
      ],
    },
    {
      id: "verification",
      label: "Verification",
      options: [
        { id: "verified", label: "Verified", count: mockTools.filter(t => t.verified).length },
        { id: "unverified", label: "Unverified", count: mockTools.filter(t => !t.verified).length },
      ],
    },
  ]

  // Filter tools based on search and filters
  const filteredTools = useMemo(() => {
    let result = mockTools

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        tool =>
          tool.name.toLowerCase().includes(query) ||
          tool.display_name.toLowerCase().includes(query) ||
          tool.description.toLowerCase().includes(query) ||
          tool.tags.some(tag => tag.toLowerCase().includes(query))
      )
    }

    // Apply status filter
    if (selectedFilters.status?.length > 0) {
      result = result.filter(tool => {
        if (selectedFilters.status.includes("installed") && tool.installed) return true
        if (selectedFilters.status.includes("available") && !tool.installed) return true
        if (selectedFilters.status.includes("update_available") && tool.update_available) return true
        return false
      })
    }

    // Apply category filter
    if (selectedFilters.category?.length > 0) {
      result = result.filter(tool => selectedFilters.category.includes(tool.category))
    }

    // Apply verification filter
    if (selectedFilters.verification?.length > 0) {
      result = result.filter(tool => {
        if (selectedFilters.verification.includes("verified") && tool.verified) return true
        if (selectedFilters.verification.includes("unverified") && !tool.verified) return true
        return false
      })
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

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Tools"
          description="Manage tools and integrations for your agents"
        />
        <LoadingState message="Loading tools..." />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <PageHeader
        title="Tools"
        description="Manage tools and integrations for your agents"
        badge={{ label: `${mockTools.length} Total` }}
        actions={
          <Button>
            <Plus className="w-4 h-4 mr-2" />
            Add Custom Tool
          </Button>
        }
      />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          {/* Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Installed Tools"
              value={stats.installed}
              subtitle={`${stats.available} available`}
              icon={Download}
            />
            <MetricCard
              title="Updates Available"
              value={stats.updates_available}
              icon={AlertCircle}
            />
            <MetricCard
              title="Total Invocations (24h)"
              value={stats.total_invocations_24h.toLocaleString()}
              icon={Check}
            />
            <MetricCard
              title="Avg Success Rate"
              value={`${(stats.avg_success_rate * 100).toFixed(1)}%`}
              icon={Check}
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
                  placeholder="Search tools by name, description, or tags..."
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
                  {filteredTools.length === mockTools.length
                    ? `Showing all ${filteredTools.length} tools`
                    : `Found ${filteredTools.length} of ${mockTools.length} tools`}
                </p>
              </div>

              {/* Tool Grid */}
              {filteredTools.length === 0 ? (
                <EmptyState
                  title="No tools found"
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
                  {filteredTools.map(tool => (
                    <ToolCard key={tool.id} tool={tool} />
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

function ToolCard({ tool }: { tool: Tool }) {
  const [isInstalling, setIsInstalling] = useState(false)

  const handleInstall = async () => {
    setIsInstalling(true)
    // Simulate install
    await new Promise(resolve => setTimeout(resolve, 1000))
    setIsInstalling(false)
  }

  return (
    <Card className="p-6 hover:border-blue-600/50 transition-colors h-full flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-lg font-semibold text-fg-0 truncate">
              {tool.display_name}
            </h3>
            {tool.verified && (
              <Badge variant="secondary" className="text-xs">
                <Check className="w-3 h-3 mr-1" />
                Verified
              </Badge>
            )}
          </div>
          <p className="text-xs text-fg-2">{tool.vendor}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-fg-2 mb-4 line-clamp-2 flex-1">
        {tool.description}
      </p>

      {/* Stats */}
      {tool.installed && (
        <div className="grid grid-cols-2 gap-3 mb-4 pb-4 border-b border-white/10">
          <div>
            <div className="text-xs text-fg-2 mb-1">Invocations (24h)</div>
            <div className="text-base font-semibold text-fg-0">
              {tool.total_invocations_24h.toLocaleString()}
            </div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Success Rate</div>
            <div className="text-base font-semibold text-green-500">
              {(tool.success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Avg Latency</div>
            <div className="text-base font-semibold text-fg-0">
              {tool.avg_latency_ms}ms
            </div>
          </div>
          <div>
            <div className="text-xs text-fg-2 mb-1">Used By</div>
            <div className="text-base font-semibold text-fg-0">
              {tool.used_by_agents.length} agents
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto">
        <div className="flex items-center gap-2">
          <Badge
            variant={tool.category === "integration" ? "default" : "secondary"}
            className="text-xs"
          >
            {tool.category}
          </Badge>
          <Badge variant="outline" className="text-xs">
            v{tool.version}
          </Badge>
          {tool.update_available && (
            <Badge variant="outline" className="text-xs text-yellow-500">
              Update: v{tool.latest_version}
            </Badge>
          )}
        </div>
      </div>

      {/* Install Button */}
      <div className="mt-4">
        {tool.installed ? (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="flex-1">
              Configure
            </Button>
            <Button variant="ghost" size="sm" className="flex-1">
              Uninstall
            </Button>
          </div>
        ) : (
          <Button
            onClick={handleInstall}
            disabled={isInstalling}
            className="w-full"
            size="sm"
          >
            {isInstalling ? "Installing..." : "Install"}
          </Button>
        )}
      </div>
    </Card>
  )
}
