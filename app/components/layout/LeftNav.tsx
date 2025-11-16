"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Layers,
  Globe,
  Wrench,
  Radio,
  Rocket,
  Activity,
  Database,
  Store,
  Shield,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Settings,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { QuantLogo } from "../logo/QuantLogo"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface NavItem {
  icon: React.ElementType
  label: string
  href: string
}

const navItems: NavItem[] = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: Layers, label: "Agents", href: "/agents" },
  { icon: Settings, label: "System Agents", href: "/system-agents" },
  { icon: Wrench, label: "Forge", href: "/forge" },
  { icon: MessageSquare, label: "Playground", href: "/chat" },
  { icon: Globe, label: "Domains", href: "/domains" },
  { icon: Wrench, label: "Tools", href: "/tools" },
  { icon: Radio, label: "Channels", href: "/channels" },
  { icon: Rocket, label: "Deployments", href: "/deployments" },
  { icon: Activity, label: "Monitoring", href: "/monitoring" },
  { icon: Database, label: "Datasets", href: "/datasets" },
  { icon: Store, label: "Marketplace", href: "/marketplace" },
  { icon: Shield, label: "Admin", href: "/admin" },
]

export function LeftNav() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('leftNavCollapsed')
    if (saved !== null) {
      setIsCollapsed(saved === 'true')
    }
  }, [])

  // Save collapsed state to localStorage when it changes
  const toggleCollapsed = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    localStorage.setItem('leftNavCollapsed', String(newState))
  }

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        aria-label="Primary navigation"
        className={cn(
          "hidden md:flex bg-bg-1 border-r border-white/10 p-4 flex-col transition-all duration-300",
          isCollapsed ? "w-[72px]" : "w-64"
        )}
      >
        {/* Header with Quant Logo */}
        <div className={cn(
          "mb-6 flex items-center",
          isCollapsed ? "flex-col gap-3" : "justify-between"
        )}>
          {!isCollapsed ? (
            <div className="flex items-center gap-2 px-2">
              <QuantLogo className="h-6 w-auto" />
            </div>
          ) : (
            <div className="mx-auto">
              <QuantLogo className="h-6 w-6" />
            </div>
          )}
          <button
            onClick={toggleCollapsed}
            className={cn(
              "p-1.5 rounded-lg hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors flex-shrink-0",
              isCollapsed && "mx-auto"
            )}
            aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Primary Navigation */}
        <nav aria-label="Main menu" className="space-y-1 flex-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/")

            const linkContent = (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-blue-600/10 text-blue-500 hover:bg-blue-600/20"
                    : "text-fg-1 hover:text-fg-0 hover:bg-bg-2",
                  isCollapsed && "justify-center"
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            )

            if (isCollapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right" className="bg-bg-2 border-white/10">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              )
            }

            return linkContent
          })}
        </nav>

        {/* Footer */}
        <div className="mt-4 pt-4 border-t border-white/10">
          {!isCollapsed ? (
            <div className="text-xs text-fg-2 px-3">
              <p className="font-semibold">Agent Foundry</p>
              <p className="text-fg-2/60 mt-1">v0.9.0-dev</p>
            </div>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="text-xs text-fg-2 text-center cursor-default">
                  <p className="font-semibold">AF</p>
                </div>
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-bg-2 border-white/10">
                Agent Foundry v0.9.0-dev
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </aside>
    </TooltipProvider>
  )
}
