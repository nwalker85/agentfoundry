/**
 * Unified Header Component
 * Consistent header structure across all pages with Quant + Agent Foundry branding
 */

'use client';

import { useState, useEffect } from 'react';
import { Building, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { QuantLogo } from '../logo/QuantLogo';
import { AgentFoundryLogo } from '../logo/AgentFoundryLogo';
import { AgentSelector } from './AgentSelector';
import { EnvironmentSelector, type Environment } from './EnvironmentSelector';
import { ActionButtons, type HeaderAction } from './ActionButtons';
import { OrgSwitcher } from '../layout/OrgSwitcher';
import type { Agent } from '@/types';
import { cn } from '@/lib/utils';

export interface UnifiedHeaderProps {
  currentPage?: string;
  agents?: Agent[];
  selectedAgent?: Agent | null;
  showAgentSelector?: boolean;
  actions?: HeaderAction[];
  onAgentSelect?: (agent: Agent) => void;
  onCreateAgent?: () => void;
}

export function UnifiedHeader({
  currentPage,
  agents = [],
  selectedAgent,
  showAgentSelector = false,
  actions = [],
  onAgentSelect,
  onCreateAgent,
}: UnifiedHeaderProps) {
  const [environment, setEnvironment] = useState<Environment>('dev');
  const [orgSwitcherOpen, setOrgSwitcherOpen] = useState(false);

  // Load environment from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('selectedEnvironment') as Environment;
    if (saved && ['dev', 'staging', 'prod'].includes(saved)) {
      setEnvironment(saved);
    }
  }, []);

  // Save environment to localStorage when it changes
  const handleEnvironmentChange = (env: Environment) => {
    setEnvironment(env);
    localStorage.setItem('selectedEnvironment', env);
  };

  return (
    <>
      <header className="h-14 bg-gray-950 border-b border-gray-800 fixed top-0 w-full z-50">
        <div className="h-full flex items-center px-4">
          {/* Left Section - Logos & Branding */}
          <div className="flex items-center gap-6 min-w-[320px]">
            {/* Quant Logo */}
            <div className="flex items-center gap-2">
              <QuantLogo className="h-6 w-auto" />
              <span className="text-gray-500 text-xs font-medium">PLATFORM</span>
            </div>

            {/* Divider */}
            <div className="h-6 w-px bg-gray-800" />

            {/* Agent Foundry Logo */}
            <div className="flex items-center gap-2">
              <AgentFoundryLogo className="h-6 w-6" />
              <span className="text-white font-medium">Agent Foundry</span>
            </div>
          </div>

          {/* Center Section - Context Bar */}
          <div className="flex-1 flex items-center justify-center">
            <div className="flex items-center bg-gray-900 rounded-lg px-1 py-1 gap-1">
              {/* Agent Selector (when applicable) */}
              {showAgentSelector && agents.length > 0 && onAgentSelect && (
                <>
                  <AgentSelector
                    agents={agents}
                    selectedAgent={selectedAgent}
                    onSelect={onAgentSelect}
                    onCreateNew={onCreateAgent}
                  />
                  <div className="w-px h-6 bg-gray-700" />
                </>
              )}

              {/* Environment Selector */}
              <EnvironmentSelector current={environment} onChange={handleEnvironmentChange} />

              {/* Page-specific Actions */}
              {actions.length > 0 && (
                <>
                  <div className="w-px h-6 bg-gray-700" />
                  <ActionButtons actions={actions} />
                </>
              )}
            </div>
          </div>

          {/* Right Section - Org & User */}
          <div className="flex items-center gap-3 min-w-[200px] justify-end">
            {/* Organization Switcher */}
            <Button
              variant="ghost"
              onClick={() => setOrgSwitcherOpen(true)}
              className="gap-2 text-sm text-fg-1 hover:text-fg-0 hover:bg-bg-2 px-3 py-1.5 h-auto"
            >
              <Building className="w-4 h-4" />
              <span className="hidden sm:inline">Acme Corp</span>
            </Button>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 rounded-full hover:bg-bg-2">
                  <Avatar className="h-8 w-8 bg-blue-600">
                    <AvatarFallback className="bg-blue-600 text-white text-sm">JD</AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">John Doe</p>
                    <p className="text-xs leading-none text-muted-foreground">john@example.com</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600">Log out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Spacer to prevent content from going under fixed header */}
      <div className="h-14" />

      {/* Organization Switcher Modal */}
      <OrgSwitcher open={orgSwitcherOpen} onOpenChange={setOrgSwitcherOpen} />
    </>
  );
}
