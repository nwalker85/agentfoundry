"use client"

import { Search, Building, Check } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface OrgSwitcherProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const organizations = [
  {
    name: "APEX CoE",
    slug: "apex-coe",
    tier: "ENTERPRISE",
    isActive: false,
  },
  {
    name: "Program APEX",
    slug: "program-apex",
    tier: "STANDARD",
    isActive: false,
  },
  {
    name: "Default Organization",
    slug: "default-organization",
    tier: "FREE",
    isActive: true,
  },
]

export function OrgSwitcher({ open, onOpenChange }: OrgSwitcherProps) {
  const [search, setSearch] = useState("")

  const filteredOrgs = organizations.filter((org) =>
    org.name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Switch Organization</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-fg-2" />
            <Input
              placeholder="Search organizations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Org List */}
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {filteredOrgs.map((org) => (
              <button
                key={org.slug}
                className={cn(
                  "w-full p-4 rounded-lg border transition-colors text-left",
                  org.isActive
                    ? "border-blue-600 bg-blue-600/10"
                    : "border-border hover:border-blue-600/50 hover:bg-bg-2"
                )}
                onClick={() => {
                  // TODO: Implement org switching
                  console.log("Switch to:", org.slug)
                  onOpenChange(false)
                }}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-bg-2 flex items-center justify-center flex-shrink-0">
                    <Building className="w-5 h-5 text-fg-1" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-fg-0 truncate">
                        {org.name}
                      </h3>
                      {org.isActive && (
                        <Check className="w-4 h-4 text-blue-500 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-sm text-fg-2 truncate">{org.slug}</p>
                  </div>

                  <Badge
                    variant={org.tier === "ENTERPRISE" ? "default" : "secondary"}
                    className="flex-shrink-0"
                  >
                    {org.tier}
                  </Badge>
                </div>
              </button>
            ))}

            {filteredOrgs.length === 0 && (
              <div className="text-center py-8 text-fg-2">
                <Building className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No organizations found</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
