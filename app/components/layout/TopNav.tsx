"use client"

import {
  ChevronDown,
  User,
  Settings,
  LogOut,
  Circle,
  LayoutDashboard,
  Layers,
  Wrench,
  MessageSquare,
  Globe,
  Radio,
  Rocket,
  Activity,
  Database,
  Store,
  Shield,
  Server,
  FolderKanban,
  FileText,
} from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useState, useEffect } from "react"
import { AgentFoundryLogo } from "../logo/AgentFoundryLogo"
import { cn } from "@/lib/utils"
import type { LucideIcon } from "lucide-react"

// Page configuration with names and icons
interface PageConfig {
  name: string
  icon: LucideIcon
}

const PAGE_CONFIG: Record<string, PageConfig> = {
  '/': { name: 'Dashboard', icon: LayoutDashboard },
  '/agents': { name: 'Agents', icon: Layers },
  '/forge': { name: 'Forge', icon: Wrench },
  '/chat': { name: 'Playground', icon: MessageSquare },
  '/domains': { name: 'Domains', icon: Globe },
  '/tools': { name: 'Tools', icon: Wrench },
  '/channels': { name: 'Channels', icon: Radio },
  '/deployments': { name: 'Deployments', icon: Rocket },
  '/monitoring': { name: 'Monitoring', icon: Activity },
  '/datasets': { name: 'Datasets', icon: Database },
  '/marketplace': { name: 'Marketplace', icon: Store },
  '/admin': { name: 'Admin', icon: Shield },
  '/profile': { name: 'Profile', icon: User },
  '/instances': { name: 'Instances', icon: Server },
  '/projects': { name: 'Projects', icon: FolderKanban },
  '/artifacts': { name: 'Artifacts', icon: FileText },
}

type Instance = 'dev' | 'staging' | 'prod'

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
}

interface UserProfile {
  name: string
  email: string
  initials: string
  avatar?: string
}

// Mock data for organizations and domains
interface Organization {
  id: string
  name: string
  domains: Domain[]
}

interface Domain {
  id: string
  name: string
  organizationId: string
}

const MOCK_ORGANIZATIONS: Organization[] = [
  {
    id: 'org-1',
    name: 'Ravenhelm AI',
    domains: [
      { id: 'dom-1', name: 'Retail Banking', organizationId: 'org-1' },
      { id: 'dom-2', name: 'Investment Banking', organizationId: 'org-1' },
      { id: 'dom-3', name: 'Customer Service', organizationId: 'org-1' },
    ]
  },
  {
    id: 'org-2',
    name: 'Acme Corp',
    domains: [
      { id: 'dom-4', name: 'Sales', organizationId: 'org-2' },
      { id: 'dom-5', name: 'Marketing', organizationId: 'org-2' },
    ]
  },
  {
    id: 'org-3',
    name: 'Tech Solutions Inc',
    domains: [
      { id: 'dom-6', name: 'Engineering', organizationId: 'org-3' },
      { id: 'dom-7', name: 'Product', organizationId: 'org-3' },
      { id: 'dom-8', name: 'DevOps', organizationId: 'org-3' },
    ]
  }
]

export function TopNav() {
  const pathname = usePathname()
  const [instance, setInstance] = useState<Instance>('dev')
  const [selectedOrgId, setSelectedOrgId] = useState('org-1')
  const [selectedDomainId, setSelectedDomainId] = useState('dom-1')
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: 'User Name',
    email: 'user@ravenhelm.ai',
    initials: 'UN',
  })

  // Get current organization and domain
  const currentOrg = MOCK_ORGANIZATIONS.find(org => org.id === selectedOrgId) || MOCK_ORGANIZATIONS[0]
  const currentDomain = currentOrg.domains.find(dom => dom.id === selectedDomainId) || currentOrg.domains[0]

  // Get current page configuration
  const getCurrentPageConfig = (): PageConfig => {
    // Try exact match first
    if (PAGE_CONFIG[pathname]) {
      return PAGE_CONFIG[pathname]
    }
    // Try to match dynamic routes like /agents/123
    const basePath = '/' + pathname.split('/')[1]
    return PAGE_CONFIG[basePath] || { name: 'Agent Foundry', icon: LayoutDashboard }
  }

  const currentPageConfig = getCurrentPageConfig()
  const CurrentPageIcon = currentPageConfig.icon

  // Load state from localStorage on mount
  useEffect(() => {
    const savedInstance = localStorage.getItem('selectedInstance') as Instance
    if (savedInstance && ['dev', 'staging', 'prod'].includes(savedInstance)) {
      setInstance(savedInstance)
    }

    const savedOrgId = localStorage.getItem('selectedOrgId')
    if (savedOrgId) setSelectedOrgId(savedOrgId)

    const savedDomainId = localStorage.getItem('selectedDomainId')
    if (savedDomainId) setSelectedDomainId(savedDomainId)

    const savedProfile = localStorage.getItem('userProfile')
    if (savedProfile) {
      try {
        setUserProfile(JSON.parse(savedProfile))
      } catch (e) {
        console.error('Failed to parse user profile:', e)
      }
    }
  }, [])

  const handleInstanceChange = (inst: Instance) => {
    setInstance(inst)
    localStorage.setItem('selectedInstance', inst)
  }

  const handleOrganizationChange = (orgId: string) => {
    setSelectedOrgId(orgId)
    localStorage.setItem('selectedOrgId', orgId)

    // When changing org, default to first domain of that org
    const newOrg = MOCK_ORGANIZATIONS.find(org => org.id === orgId)
    if (newOrg && newOrg.domains.length > 0) {
      setSelectedDomainId(newOrg.domains[0].id)
      localStorage.setItem('selectedDomainId', newOrg.domains[0].id)
    }
  }

  const handleDomainChange = (domainId: string) => {
    setSelectedDomainId(domainId)
    localStorage.setItem('selectedDomainId', domainId)
  }

  const handleLogout = () => {
    // TODO: Implement logout logic
    console.log('Logging out...')
  }

  const currentInstanceConfig = instanceConfig[instance]

  return (
    <nav className="h-14 bg-bg-1 border-b border-white/10 flex items-center px-6 gap-6">
      {/* Left: Logo + Agent Foundry */}
      <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity flex-shrink-0">
        <AgentFoundryLogo className="h-7 w-7" />
        <span className="text-fg-0 font-semibold text-lg">Agent Foundry</span>
      </Link>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Center: Current Page with Icon */}
      <div className="absolute left-1/2 transform -translate-x-1/2">
        <div className="flex items-center gap-3">
          <CurrentPageIcon className="w-8 h-8 text-blue-500" />
          <h1 className="text-3xl font-bold text-fg-0 tracking-tight">
            {currentPageConfig.name}
          </h1>
        </div>
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
              className={cn(
                "gap-1.5 text-sm hover:bg-bg-2 px-3 h-9",
                currentInstanceConfig.color
              )}
            >
              <Circle className={cn("w-2 h-2", currentInstanceConfig.dotColor)} />
              <span className="hidden md:inline">{currentInstanceConfig.shortLabel}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="text-xs text-fg-2">
              Switch Instance
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {(Object.keys(instanceConfig) as Instance[]).map((inst) => {
              const config = instanceConfig[inst]
              const isActive = instance === inst

              return (
                <DropdownMenuItem
                  key={inst}
                  onClick={() => handleInstanceChange(inst)}
                  className="gap-2"
                >
                  <Circle className={cn("w-2 h-2", config.dotColor)} />
                  <span className={cn(isActive && config.color)}>
                    {config.label}
                  </span>
                  {isActive && (
                    <span className="ml-auto text-xs text-fg-2">Active</span>
                  )}
                </DropdownMenuItem>
              )
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* Organization Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="gap-1.5 text-sm hover:bg-bg-2 px-3 h-9 text-fg-1"
            >
              <span className="hidden lg:inline text-fg-2">Org:</span>
              <span className="font-medium">{currentOrg.name}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-fg-2">
              Select Organization
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {MOCK_ORGANIZATIONS.map((org) => {
              const isActive = selectedOrgId === org.id
              return (
                <DropdownMenuItem
                  key={org.id}
                  onClick={() => handleOrganizationChange(org.id)}
                  className="gap-2"
                >
                  <span className={cn(isActive && "text-blue-500 font-medium")}>
                    {org.name}
                  </span>
                  {isActive && (
                    <span className="ml-auto text-xs text-fg-2">Active</span>
                  )}
                </DropdownMenuItem>
              )
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* Domain Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="gap-1.5 text-sm hover:bg-bg-2 px-3 h-9 text-fg-1"
            >
              <span className="hidden lg:inline text-fg-2">Domain:</span>
              <span className="font-medium">{currentDomain.name}</span>
              <ChevronDown className="w-3.5 h-3.5 opacity-50" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-fg-2">
              Select Domain in {currentOrg.name}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {currentOrg.domains.map((domain) => {
              const isActive = selectedDomainId === domain.id
              return (
                <DropdownMenuItem
                  key={domain.id}
                  onClick={() => handleDomainChange(domain.id)}
                  className="gap-2"
                >
                  <span className={cn(isActive && "text-blue-500 font-medium")}>
                    {domain.name}
                  </span>
                  {isActive && (
                    <span className="ml-auto text-xs text-fg-2">Active</span>
                  )}
                </DropdownMenuItem>
              )
            })}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Divider */}
        <div className="h-4 w-px bg-white/20" />

        {/* User Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2 hover:bg-bg-2 h-9 px-2">
              <Avatar className="w-7 h-7">
                {userProfile.avatar && <AvatarImage src={userProfile.avatar} alt={userProfile.name} />}
                <AvatarFallback className="bg-blue-600 text-white text-xs font-semibold">
                  {userProfile.initials}
                </AvatarFallback>
              </Avatar>
              <ChevronDown className="w-3.5 h-3.5 opacity-50 hidden sm:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>
              <div className="flex flex-col">
                <span className="text-sm font-semibold text-fg-0">{userProfile.name}</span>
                <span className="text-xs font-normal text-fg-2">{userProfile.email}</span>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/profile" className="cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/profile?tab=preferences" className="cursor-pointer">
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
  )
}
