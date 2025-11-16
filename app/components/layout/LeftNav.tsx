"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  Building,
  FolderKanban,
  Server,
  Package,
  BarChart3,
  Shield,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface NavItem {
  icon: React.ElementType
  label: string
  href: string
  collapsible?: boolean
}

const navItems: NavItem[] = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/" },
  { icon: Building, label: "Organizations", href: "/organizations", collapsible: true },
  { icon: FolderKanban, label: "Projects", href: "/projects" },
  { icon: Server, label: "Instances", href: "/instances" },
  { icon: Package, label: "Artifacts", href: "/artifacts" },
  { icon: BarChart3, label: "Reporting", href: "/reporting" },
  { icon: Shield, label: "Administration", href: "/admin", collapsible: true },
]

export function LeftNav() {
  const pathname = usePathname()

  return (
    <aside className="hidden md:flex w-64 bg-bg-1 border-r border-white/10 p-4 flex-col">
      <div className="mb-6">
        <h2 className="text-xs font-semibold text-fg-2 uppercase tracking-wide mb-3 px-3">
          Navigation
        </h2>
      </div>

      <nav className="space-y-1 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/")

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-600/10 text-blue-500 hover:bg-blue-600/20"
                  : "text-fg-1 hover:text-fg-0 hover:bg-bg-2"
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="mt-auto pt-4 border-t border-white/10">
        <div className="text-xs text-fg-2 px-3">
          <p className="font-semibold">Agent Foundry</p>
          <p className="text-fg-2/60 mt-1">v0.8.1-dev</p>
        </div>
      </div>
    </aside>
  )
}
