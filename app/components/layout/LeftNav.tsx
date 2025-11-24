'use client';

import { useState, useEffect, useTransition, useRef } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Layers,
  Globe,
  Wrench,
  Rocket,
  Activity,
  Database,
  Store,
  Shield,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  FileCode,
  Plus,
  FolderKanban,
  Users,
  Workflow,
  GitBranch,
  Key,
  Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { QuantLogo } from '../logo/QuantLogo';
import { AgentFoundryLogo } from '../logo/AgentFoundryLogo';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
  section?: string; // Section header (CREATE, MANAGE, LAUNCH, CONFIGURE)
  isSeparator?: boolean;
}

const APP_BASE = '/app';

// New navigation structure with sections
const navItems: NavItem[] = [
  // Dashboard (standalone)
  { icon: LayoutDashboard, label: 'Dashboard', href: `${APP_BASE}` },

  // Separator
  { icon: LayoutDashboard, label: '', href: '', isSeparator: true },

  // CREATE section
  { icon: FileCode, label: 'CREATE', href: '', section: 'CREATE' },
  { icon: FileCode, label: 'From DIS', href: `${APP_BASE}/compiler` },
  { icon: GitBranch, label: 'Agent Graphs', href: `${APP_BASE}/graphs` },

  // MANAGE section
  { icon: Layers, label: 'MANAGE', href: '', section: 'MANAGE' },
  { icon: Layers, label: 'Agents', href: `${APP_BASE}/agents` },
  { icon: Database, label: 'Datasets', href: `${APP_BASE}/datasets` },
  { icon: Wrench, label: 'Tools', href: `${APP_BASE}/tools` },

  // LAUNCH section
  { icon: Rocket, label: 'LAUNCH', href: '', section: 'LAUNCH' },
  { icon: MessageSquare, label: 'Test', href: `${APP_BASE}/chat` },
  { icon: Rocket, label: 'Deploy', href: `${APP_BASE}/deployments` },
  { icon: Activity, label: 'Monitor', href: `${APP_BASE}/monitoring` },

  // CONFIGURE section
  { icon: FolderKanban, label: 'CONFIGURE', href: '', section: 'CONFIGURE' },
  { icon: FolderKanban, label: 'Projects', href: `${APP_BASE}/projects` },
  { icon: Globe, label: 'Domains', href: `${APP_BASE}/domains` },
  { icon: Users, label: 'Teams', href: `${APP_BASE}/teams` },
  { icon: Key, label: 'Secrets', href: `${APP_BASE}/settings/secrets` },

  // Bottom items (no section)
  { icon: LayoutDashboard, label: '', href: '', isSeparator: true },
  { icon: Store, label: 'Marketplace', href: `${APP_BASE}/marketplace` },
  { icon: Shield, label: 'Admin', href: `${APP_BASE}/admin` },
  { icon: Database, label: 'Manage DBs', href: `${APP_BASE}/admin/manage-dbs` },
];

export function LeftNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [pendingHref, setPendingHref] = useState<string | null>(null);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Unsaved changes dialog state
  const [unsavedDialogOpen, setUnsavedDialogOpen] = useState(false);
  const pendingNavigationRef = useRef<string | null>(null);

  // Clear pending state when navigation completes
  useEffect(() => {
    setPendingHref(null);
  }, [pathname]);

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('leftNavCollapsed');
    if (saved !== null) {
      setIsCollapsed(saved === 'true');
    }
  }, []);

  // Save collapsed state to localStorage when it changes
  const toggleCollapsed = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('leftNavCollapsed', String(newState));
  };

  return (
    <TooltipProvider delayDuration={0}>
      <aside
        aria-label="Primary navigation"
        className={cn(
          'hidden md:flex bg-bg-1 border-r border-white/10 p-4 flex-col transition-all duration-300',
          isCollapsed ? 'w-[72px]' : 'w-64'
        )}
      >
        {/* Header with Agent Foundry Logo */}
        <div
          className={cn(
            'mb-6 flex items-center',
            isCollapsed ? 'flex-col gap-3' : 'justify-between'
          )}
        >
          {!isCollapsed ? (
            <div className="flex items-center gap-2 px-2">
              <AgentFoundryLogo className="h-7 w-7 flex-shrink-0" />
              <span className="text-fg-0 font-semibold text-base">Agent Foundry</span>
            </div>
          ) : (
            <div className="mx-auto">
              <AgentFoundryLogo className="h-7 w-7" />
            </div>
          )}
          <button
            onClick={toggleCollapsed}
            className={cn(
              'p-1.5 rounded-lg hover:bg-bg-2 text-fg-2 hover:text-fg-0 transition-colors flex-shrink-0',
              isCollapsed && 'mx-auto'
            )}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Primary Navigation */}
        <nav aria-label="Main menu" className="flex-1 overflow-y-auto">
          {navItems.map((item, index) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');

            // Render separator
            if (item.isSeparator) {
              return (
                <div
                  key={`separator-${index}`}
                  className="my-3 border-t border-white/10"
                  aria-hidden="true"
                />
              );
            }

            // Render section header
            if (item.section) {
              if (isCollapsed) {
                // Don't show section headers when collapsed
                return null;
              }
              return (
                <div
                  key={`section-${item.section}`}
                  className="px-3 pt-4 pb-2 text-xs font-semibold uppercase text-fg-3 tracking-wider"
                  aria-label={`${item.section} section`}
                >
                  {item.section}
                </div>
              );
            }

            // Render navigation link
            const isLoading = pendingHref === item.href && isPending;
            const linkContent = (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
                onClick={(e) => {
                  // Skip if already on this page
                  if (pathname === item.href) return;

                  // Check for unsaved changes when navigating away from graphs section
                  const isLeavingGraphs =
                    pathname?.startsWith('/app/graphs') && !item.href.startsWith('/app/graphs');
                  if (isLeavingGraphs) {
                    const hasUnsavedChanges =
                      sessionStorage.getItem('graphsHasUnsavedChanges') === 'true';
                    if (hasUnsavedChanges) {
                      e.preventDefault();
                      pendingNavigationRef.current = item.href;
                      setUnsavedDialogOpen(true);
                      return;
                    }
                  }

                  e.preventDefault();
                  setPendingHref(item.href);
                  startTransition(() => {
                    router.push(item.href);
                  });
                }}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors mb-1',
                  isActive
                    ? 'bg-blue-600/10 text-blue-500 hover:bg-blue-600/20'
                    : 'text-fg-1 hover:text-fg-0 hover:bg-bg-2',
                  isLoading && 'bg-blue-600/5 text-blue-400',
                  isCollapsed ? 'justify-center' : 'ml-2' // Indent 8px when expanded
                )}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 flex-shrink-0 animate-spin" aria-hidden="true" />
                ) : (
                  <Icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                )}
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            );

            if (isCollapsed) {
              return (
                <Tooltip key={item.href}>
                  <TooltipTrigger asChild>{linkContent}</TooltipTrigger>
                  <TooltipContent side="right" className="bg-bg-2 border-white/10">
                    {item.label}
                  </TooltipContent>
                </Tooltip>
              );
            }

            return linkContent;
          })}
        </nav>

        {/* Footer - Quant Logo */}
        <div className="mt-4 pt-4 border-t border-white/10">
          {!isCollapsed ? (
            <div className="flex items-center justify-center px-3">
              <QuantLogo className="h-6 w-auto" />
            </div>
          ) : (
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center justify-center">
                  <QuantLogo className="h-6 w-6" />
                </div>
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-bg-2 border-white/10">
                Quant
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </aside>

      {/* Unsaved Changes Confirmation Dialog */}
      <ConfirmDialog
        open={unsavedDialogOpen}
        onOpenChange={setUnsavedDialogOpen}
        title="Unsaved Changes"
        description="You have unsaved changes in your agent graphs. Are you sure you want to leave? Your changes will be lost."
        confirmLabel="Leave"
        cancelLabel="Stay"
        variant="destructive"
        onConfirm={() => {
          const href = pendingNavigationRef.current;
          if (href) {
            setPendingHref(href);
            startTransition(() => {
              router.push(href);
            });
            pendingNavigationRef.current = null;
          }
        }}
        onCancel={() => {
          pendingNavigationRef.current = null;
        }}
      />
    </TooltipProvider>
  );
}
