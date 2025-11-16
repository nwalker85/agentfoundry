"use client"

import { useState, useMemo } from "react"
import { Search, Clock, CheckCircle2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { StatusBadge } from "@/components/shared"
import type { Agent } from "@/types"
import { cn } from "@/lib/utils"

interface AgentOpenDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  agents: Agent[]
  onSelectAgent: (agent: Agent) => void
  currentAgentId?: string
}

export function AgentOpenDialog({
  open,
  onOpenChange,
  agents,
  onSelectAgent,
  currentAgentId,
}: AgentOpenDialogProps) {
  const [searchQuery, setSearchQuery] = useState("")

  // Filter agents based on search
  const filteredAgents = useMemo(() => {
    if (!searchQuery) return agents

    const query = searchQuery.toLowerCase()
    return agents.filter(
      agent =>
        agent.name.toLowerCase().includes(query) ||
        agent.display_name.toLowerCase().includes(query) ||
        agent.description.toLowerCase().includes(query)
    )
  }, [agents, searchQuery])

  // Sort agents: current first, then by recent updates
  const sortedAgents = useMemo(() => {
    return [...filteredAgents].sort((a, b) => {
      if (a.id === currentAgentId) return -1
      if (b.id === currentAgentId) return 1
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  }, [filteredAgents, currentAgentId])

  const handleSelectAgent = (agent: Agent) => {
    onSelectAgent(agent)
    onOpenChange(false)
    setSearchQuery("")
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Open Agent</DialogTitle>
          <DialogDescription>
            Select an agent to open in Forge
          </DialogDescription>
        </DialogHeader>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-2" />
          <Input
            placeholder="Search agents by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Agent List */}
        <ScrollArea className="h-[400px] -mx-6 px-6">
          {sortedAgents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="w-12 h-12 text-fg-2 mb-4" />
              <h3 className="text-lg font-semibold text-fg-0 mb-2">No agents found</h3>
              <p className="text-sm text-fg-2">
                {searchQuery
                  ? "Try adjusting your search query"
                  : "No agents available in this domain"}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {sortedAgents.map((agent) => {
                const isCurrent = agent.id === currentAgentId
                const updatedDate = new Date(agent.updated_at).toLocaleDateString()

                return (
                  <button
                    key={agent.id}
                    onClick={() => handleSelectAgent(agent)}
                    className={cn(
                      "w-full text-left p-4 rounded-lg border transition-all",
                      "hover:border-blue-600/50 hover:bg-bg-2",
                      isCurrent
                        ? "border-blue-600 bg-blue-600/10"
                        : "border-border bg-bg-1"
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      {/* Left: Agent Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-fg-0 truncate">
                            {agent.display_name}
                          </h3>
                          {isCurrent && (
                            <Badge variant="secondary" className="gap-1 text-xs">
                              <CheckCircle2 className="w-3 h-3" />
                              Current
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-fg-2 font-mono mb-2">{agent.name}</p>
                        <p className="text-sm text-fg-2 line-clamp-2">
                          {agent.description}
                        </p>
                      </div>

                      {/* Right: Badges */}
                      <div className="flex flex-col items-end gap-2 flex-shrink-0">
                        <StatusBadge status={agent.status} />
                        <div className="flex items-center gap-1.5 text-xs text-fg-2">
                          <Clock className="w-3 h-3" />
                          {updatedDate}
                        </div>
                      </div>
                    </div>

                    {/* Bottom: Tags and Environment */}
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/10">
                      <div className="flex items-center gap-1.5">
                        {agent.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                        {agent.tags.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{agent.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {agent.environment}
                      </Badge>
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <div className="text-xs text-fg-2 text-center pt-2 border-t border-white/10">
          Showing {sortedAgents.length} of {agents.length} agents
        </div>
      </DialogContent>
    </Dialog>
  )
}
