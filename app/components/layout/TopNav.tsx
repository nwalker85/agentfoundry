"use client"

import { Building, ChevronDown, Grid, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useState } from "react"
import { OrgSwitcher } from "./OrgSwitcher"
import { AppMenu } from "./AppMenu"

export function TopNav() {
  const [orgSwitcherOpen, setOrgSwitcherOpen] = useState(false)
  const [appMenuOpen, setAppMenuOpen] = useState(false)

  return (
    <>
      <nav className="h-14 bg-bg-1 border-b border-white/10 flex items-center px-4 gap-4">
        {/* Logo + App Name */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">AF</span>
          </div>
          <span className="text-fg-0 font-semibold text-base">Agent Foundry</span>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Org Switcher */}
        <Button
          variant="ghost"
          className="gap-2 text-fg-1 hover:text-fg-0 hover:bg-bg-2"
          onClick={() => setOrgSwitcherOpen(true)}
        >
          <Building className="w-4 h-4" />
          <span className="hidden sm:inline">Default Organization</span>
          <ChevronDown className="w-4 h-4" />
        </Button>

        {/* App Menu */}
        <Button
          variant="ghost"
          size="icon"
          className="text-fg-1 hover:text-fg-0 hover:bg-bg-2"
          onClick={() => setAppMenuOpen(true)}
        >
          <Grid className="w-5 h-5" />
        </Button>

        {/* User Menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="hover:bg-bg-2">
              <Avatar className="w-8 h-8">
                <AvatarFallback className="bg-blue-600 text-white text-sm">
                  U
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Log out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </nav>

      {/* Modals */}
      <OrgSwitcher open={orgSwitcherOpen} onOpenChange={setOrgSwitcherOpen} />
      <AppMenu open={appMenuOpen} onOpenChange={setAppMenuOpen} />
    </>
  )
}
