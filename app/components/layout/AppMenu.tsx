"use client"

import { Hammer, FlaskConical, Brain, ExternalLink } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"

interface AppMenuProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

const apps = [
  {
    name: "Forge AI",
    description: "Visual agent configuration tool",
    icon: Hammer,
    href: "/forge",
    available: true,
  },
  {
    name: "Playground",
    description: "Test agents in dev before deployment",
    icon: FlaskConical,
    href: "/chat",
    available: true,
  },
  {
    name: "Domain Intelligence",
    description: "AI-powered domain analysis",
    icon: Brain,
    href: "/dis",
    available: false,
    badge: "Coming Soon",
  },
]

export function AppMenu({ open, onOpenChange }: AppMenuProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Agent Foundry Apps</DialogTitle>
          <DialogDescription>
            Choose an application to get started
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 gap-3 py-4">
          {apps.map((app) => {
            const Icon = app.icon
            const content = (
              <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:border-blue-600/50 hover:bg-bg-2 transition-colors">
                <div className="w-12 h-12 rounded-lg bg-blue-600/10 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-6 h-6 text-blue-500" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-fg-0">{app.name}</h3>
                    {app.badge && (
                      <Badge variant="secondary" className="text-xs">
                        {app.badge}
                      </Badge>
                    )}
                    {app.available && (
                      <ExternalLink className="w-4 h-4 text-fg-2 ml-auto" />
                    )}
                  </div>
                  <p className="text-sm text-fg-2">{app.description}</p>
                </div>
              </div>
            )

            if (app.available) {
              return (
                <Link
                  key={app.name}
                  href={app.href}
                  onClick={() => onOpenChange(false)}
                >
                  {content}
                </Link>
              )
            }

            return (
              <div
                key={app.name}
                className="opacity-60 cursor-not-allowed"
              >
                {content}
              </div>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
