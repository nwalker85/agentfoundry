'use client';

import {
  ChevronDown,
  User,
  Users,
  Settings,
  LogOut,
  Circle,
  LayoutDashboard,
  Layers,
  Wrench,
  MessageSquare,
  Globe,
  Rocket,
  Activity,
  Database,
  Store,
  Shield,
  Server,
  FolderKanban,
  FileText,
  FileCode,
  Plus,
  Workflow,
  GitBranch,
} from 'lucide-react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';
import { useSession, signOut } from 'next-auth/react';

// Page configuration with names and icons
interface PageConfig {
  name: string;
  icon: LucideIcon;
}

const PAGE_CONFIG: Record<string, PageConfig> = {
  '/': { name: 'Dashboard', icon: LayoutDashboard },
  '/agents': { name: 'Agents', icon: Layers },
  '/system-agents': { name: 'System Agents', icon: Settings },
  '/compiler': { name: 'From DIS', icon: FileCode },
  '/graphs': { name: 'Agent Graphs', icon: GitBranch },
  '/chat': { name: 'Test', icon: MessageSquare },
  '/domains': { name: 'Domains', icon: Globe },
  '/tools': { name: 'Tools', icon: Wrench },
  '/deployments': { name: 'Deploy', icon: Rocket },
  '/monitoring': { name: 'Monitor', icon: Activity },
  '/datasets': { name: 'Datasets', icon: Database },
  '/marketplace': { name: 'Marketplace', icon: Store },
  '/admin': { name: 'Admin', icon: Shield },
  '/profile': { name: 'Profile', icon: User },
  '/instances': { name: 'Instances', icon: Server },
  '/projects': { name: 'Projects', icon: FolderKanban },
  '/teams': { name: 'Teams', icon: Users },
  '/artifacts': { name: 'Artifacts', icon: FileText },
  '/admin/manage-dbs': { name: 'Manage DBs', icon: Database },
};

const APP_BASE = '/app';

type Instance = 'dev' | 'staging' | 'prod';

const instanceConfig = {
  dev: {
    label: 'Development',
    shortLabel: 'Dev',
    color: 'text-blue-500',
    dotColor: 'fill-blue-500',
  },
  staging: {
    label: 'Staging',
    shortLabel: 'Staging',
    color: 'text-yellow-500',
    dotColor: 'fill-yellow-500',
  },
  prod: {
    label: 'Production',
    shortLabel: 'Prod',
    color: 'text-green-500',
    dotColor: 'fill-green-500',
  },
};

// Mock data for organizations and domains
interface Domain {
  id: string;
  name: string;
  organizationId: string;
}

interface Organization {
  id: string;
  name: string;
  domains: Domain[];
}

export function TopNav() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [instance, setInstance] = useState<Instance>('dev');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);

  const normalizePath = () => {
    if (!pathname) return '/';
    if (pathname === APP_BASE) return '/';
    if (pathname.startsWith(`${APP_BASE}/`)) {
      const normalized = pathname.slice(APP_BASE.length);
      return normalized.startsWith('/') ? normalized : `/${normalized}`;
    }
    return pathname;
  };

  const normalizedPathname = normalizePath();

  // Get current page configuration
  const getCurrentPageConfig = (): PageConfig => {
    // Try exact match first
    if (PAGE_CONFIG[normalizedPathname]) {
      return PAGE_CONFIG[normalizedPathname];
    }
    // Try to match dynamic routes like /agents/123
    const basePath = '/' + normalizedPathname.split('/')[1];
    return PAGE_CONFIG[basePath] || { name: 'Agent Foundry', icon: LayoutDashboard };
  };

  const currentPageConfig = getCurrentPageConfig();
  const CurrentPageIcon = currentPageConfig.icon;

  // Derive current org/domain from state
  const hasOrgData = organizations.length > 0;
  const currentOrg = hasOrgData
    ? organizations.find((org) => org.id === selectedOrgId) || organizations[0]
    : undefined;
  const currentDomain = currentOrg
    ? currentOrg.domains.find((dom) => dom.id === selectedDomainId) || currentOrg.domains[0]
    : undefined;
  const orgDisplayName = currentOrg?.name ?? 'Loading...';
  const domainDisplayName = currentDomain?.name ?? 'Loading...';

  // Load state from localStorage on mount
  useEffect(() => {
    // Load organizations from backend
    const loadOrganizations = async () => {
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/control/organizations`);
        if (!res.ok) {
          console.error('Failed to load organizations:', res.statusText);
          return;
        }
        const data = await res.json();
        const orgs: Organization[] = (data || []).map((o: any) => ({
          id: o.id,
          name: o.name,
          domains: (o.domains || []).map((d: any) => ({
            id: d.id,
            name: d.name,
            organizationId: d.organization_id,
          })),
        }));
        setOrganizations(orgs);

        // If we don't have a selected org yet, set defaults
        if (!selectedOrgId && orgs.length > 0) {
          const savedOrgId = localStorage.getItem('selectedOrgId');
          const orgId =
            savedOrgId && orgs.find((o) => o.id === savedOrgId) ? savedOrgId : orgs[0].id;
          setSelectedOrgId(orgId);
          localStorage.setItem('selectedOrgId', orgId);

          const savedDomainId = localStorage.getItem('selectedDomainId');
          const org = orgs.find((o) => o.id === orgId)!;
          const domId =
            savedDomainId && org.domains.find((d) => d.id === savedDomainId)
              ? savedDomainId
              : org.domains[0]?.id;
          if (domId) {
            setSelectedDomainId(domId);
            localStorage.setItem('selectedDomainId', domId);
          }
        }
      } catch (e) {
        console.error('Failed to load organizations from backend:', e);
      }
    };

    void loadOrganizations();

    const savedInstance = localStorage.getItem('selectedInstance') as Instance;
    if (savedInstance && ['dev', 'staging', 'prod'].includes(savedInstance)) {
      setInstance(savedInstance);
    }
  }, []);

  const handleInstanceChange = (inst: Instance) => {
    setInstance(inst);
    localStorage.setItem('selectedInstance', inst);
  };

  const handleOrganizationChange = (orgId: string) => {
    setSelectedOrgId(orgId);
    localStorage.setItem('selectedOrgId', orgId);

    // When changing org, default to first domain of that org
    const newOrg = organizations.find((org) => org.id === orgId);
    if (newOrg && newOrg.domains.length > 0) {
      setSelectedDomainId(newOrg.domains[0].id);
      localStorage.setItem('selectedDomainId', newOrg.domains[0].id);
    }
  };

  const handleDomainChange = (domainId: string) => {
    setSelectedDomainId(domainId);
    localStorage.setItem('selectedDomainId', domainId);
  };

  const handleLogout = async () => {
    await signOut({ callbackUrl: '/login' });
  };

  // Get user info from session
  const userName = session?.user?.name || 'User';
  const userEmail = session?.user?.email || 'user@example.com';
  const userInitials = userName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
  const userAvatar = session?.user?.image;

  const currentInstanceConfig = instanceConfig[instance];

  return (
    <nav className="h-14 bg-bg-1 border-b border-white/10 flex items-center px-6 gap-6">
      {/* Left: Current Page Title with Icon */}
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <CurrentPageIcon className="w-5 h-5 text-blue-500" />
        <h1 className="text-base font-semibold text-fg-0">{currentPageConfig.name}</h1>
      </div>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right: Instance | Domain | Organization | User */}
      <div className="flex items-center gap-1">
        {/* Instance */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className={cn('gap-1.5 text-sm hover:bg-bg-2 px-3 h-9', currentInstanceConfig.color)}
            >
              <Circle className={cn('w-2 h-2', currentInstanceConfig.dotColor)} />
              <span className="hidden md:inline">{currentInstanceConfig.shortLabel}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="text-xs text-fg-2">Switch Instance</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {(Object.keys(instanceConfig) as Instance[]).map((inst) => {
              const config = instanceConfig[inst];
              const isActive = instance === inst;

              return (
                <DropdownMenuItem
                  key={inst}
                  onClick={() => handleInstanceChange(inst)}
                  className="gap-2"
                >
                  <Circle className={cn('w-2 h-2', config.dotColor)} />
                  <span className={cn(isActive && config.color)}>{config.label}</span>
                  {isActive && <span className="ml-auto text-xs text-fg-2">Active</span>}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* Organization Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-1.5 text-sm hover:bg-bg-2 px-3 h-9 text-fg-1">
              <span className="hidden lg:inline text-fg-2">Org:</span>
              <span className="font-medium">{orgDisplayName}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-fg-2">Select Organization</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {organizations.map((org) => {
              const isActive = selectedOrgId === org.id;
              return (
                <DropdownMenuItem
                  key={org.id}
                  onClick={() => handleOrganizationChange(org.id)}
                  className="gap-2"
                >
                  <span className={cn(isActive && 'text-blue-500 font-medium')}>{org.name}</span>
                  {isActive && <span className="ml-auto text-xs text-fg-2">Active</span>}
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* Domain Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-1.5 text-sm hover:bg-bg-2 px-3 h-9 text-fg-1">
              <span className="hidden lg:inline text-fg-2">Domain:</span>
              <span className="font-medium">{domainDisplayName}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-fg-2">
              Select Domain{currentOrg ? ` in ${currentOrg.name}` : ''}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {currentOrg && currentOrg.domains.length > 0 ? (
              currentOrg.domains.map((domain) => {
                const isActive = selectedDomainId === domain.id;
                return (
                  <DropdownMenuItem
                    key={domain.id}
                    onClick={() => handleDomainChange(domain.id)}
                    className="gap-2"
                  >
                    <span className={cn(isActive && 'text-blue-500 font-medium')}>
                      {domain.name}
                    </span>
                    {isActive && <span className="ml-auto text-xs text-fg-2">Active</span>}
                  </DropdownMenuItem>
                );
              })
            ) : (
              <DropdownMenuItem disabled className="text-fg-2">
                No domains available
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* User Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2 hover:bg-bg-2 h-9 px-2">
              <Avatar className="w-7 h-7">
                {userAvatar && <AvatarImage src={userAvatar} alt={userName} />}
                <AvatarFallback className="bg-blue-600 text-white text-xs font-semibold">
                  {userInitials}
                </AvatarFallback>
              </Avatar>
              <ChevronDown className="w-3.5 h-3.5 opacity-50 hidden sm:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-fg-0">{userName}</span>
                <span className="text-xs font-normal text-fg-2">{userEmail}</span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href={`${APP_BASE}/profile`} className="cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={`${APP_BASE}/profile?tab=preferences`} className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                <span>Preferences</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-red-500 focus:text-red-500">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </nav>
  );
}
