'use client';

import { useCallback, useEffect, useMemo, useState, type ComponentType } from 'react';
import { useRouter } from 'next/navigation';
import {
  RefreshCw,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Star,
  Settings,
} from 'lucide-react';
import {
  PageHeader,
  EmptyState,
  LoadingState,
  SearchBar,
  FilterPanel,
  ActiveFilters,
} from '@/components/shared';
import type { FilterGroup } from '@/components/shared';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import type { IntegrationToolCatalogItem, IntegrationConfig } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CURRENT_USER_ID = 'nate'; // TODO: Get from auth session

type HealthState = 'healthy' | 'degraded' | 'unknown';

const HEALTH_COPY: Record<HealthState, string> = {
  healthy: 'Ready',
  degraded: 'Needs attention',
  unknown: 'Unknown',
};

const HEALTH_BADGE_STYLES: Record<HealthState, string> = {
  healthy: 'border-green-500/40 bg-green-500/10 text-green-300',
  degraded: 'border-yellow-500/40 bg-yellow-500/10 text-yellow-300',
  unknown: 'border-white/15 bg-white/5 text-fg-2',
};

export default function ToolsPage() {
  const [tools, setTools] = useState<IntegrationToolCatalogItem[]>([]);
  const [favorites, setFavorites] = useState<string[]>([]); // tool names
  const [configurations, setConfigurations] = useState<IntegrationConfig[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('all');

  const fetchCatalog = useCallback(async (options?: { silent?: boolean }) => {
    const silent = options?.silent ?? false;
    if (silent) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/tools`);
      if (!res.ok) {
        throw new Error(res.statusText);
      }
      const data = await res.json();
      setTools(data.items ?? []);
      setError(null);
    } catch (err) {
      console.error('Failed to load integrations catalog:', err);
      setTools([]);
      setError('Failed to load integrations. Ensure the MCP integration server is running.');
    } finally {
      if (silent) {
        setIsRefreshing(false);
      } else {
        setIsLoading(false);
      }
    }
  }, []);

  const fetchFavorites = useCallback(async () => {
    try {
      console.log(
        '[Favorites] Fetching from:',
        `${API_BASE_URL}/api/users/${CURRENT_USER_ID}/favorites`
      );
      const res = await fetch(`${API_BASE_URL}/api/users/${CURRENT_USER_ID}/favorites`);
      console.log('[Favorites] Response status:', res.status);

      if (res.ok) {
        const data = await res.json();
        console.log('[Favorites] Loaded favorites:', data);
        const toolNames = data.map((fav: any) => fav.tool_name);
        console.log('[Favorites] Tool names:', toolNames);
        setFavorites(toolNames);
      } else {
        console.error('[Favorites] Failed to fetch:', res.status, res.statusText);
      }
    } catch (err) {
      console.error('[Favorites] Failed to load favorites:', err);
    }
  }, []);

  const fetchConfigurations = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/integrations/configs`);
      if (res.ok) {
        const data = await res.json();
        setConfigurations(data ?? []);
      }
    } catch (err) {
      console.error('Failed to load configurations:', err);
    }
  }, []);

  useEffect(() => {
    void fetchCatalog();
    void fetchFavorites();
    void fetchConfigurations();
  }, [fetchCatalog, fetchFavorites, fetchConfigurations]);

  const handleToggleFavorite = async (toolName: string) => {
    const isFavorited = favorites.includes(toolName);

    try {
      if (isFavorited) {
        // Remove favorite
        await fetch(`${API_BASE_URL}/api/users/${CURRENT_USER_ID}/favorites/${toolName}`, {
          method: 'DELETE',
        });
        setFavorites(favorites.filter((f) => f !== toolName));
      } else {
        // Add favorite
        await fetch(`${API_BASE_URL}/api/users/${CURRENT_USER_ID}/favorites`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tool_name: toolName }),
        });
        setFavorites([...favorites, toolName]);
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  };

  const healthCounts = useMemo(() => {
    return tools.reduce(
      (acc, tool) => {
        const status = getHealthStatus(tool);
        acc[status] += 1;
        return acc;
      },
      { healthy: 0, degraded: 0, unknown: 0 } as Record<HealthState, number>
    );
  }, [tools]);

  const summaryMetrics = useMemo(() => {
    const categories = new Set(tools.map((tool) => tool.category));
    const tags = new Set(tools.flatMap((tool) => tool.tags || []));

    return {
      total: tools.length,
      healthy: healthCounts.healthy,
      degraded: healthCounts.degraded,
      categories: categories.size,
      tags: tags.size,
      favorites: favorites.length,
      configurations: configurations.length,
    };
  }, [tools, healthCounts, favorites, configurations]);

  const filterGroups: FilterGroup[] = useMemo(() => {
    const categoryOptions = Array.from(new Set(tools.map((tool) => tool.category))).map(
      (category) => ({
        id: category,
        label: formatCategory(category),
        count: tools.filter((tool) => tool.category === category).length,
      })
    );

    const tagOptions = Array.from(new Set(tools.flatMap((tool) => tool.tags ?? []))).map((tag) => ({
      id: tag,
      label: tag,
      count: tools.filter((tool) => tool.tags?.includes(tag)).length,
    }));

    return [
      {
        id: 'health',
        label: 'Status',
        options: [
          { id: 'healthy', label: 'Healthy', count: healthCounts.healthy },
          { id: 'degraded', label: 'Needs attention', count: healthCounts.degraded },
          { id: 'unknown', label: 'Unknown', count: healthCounts.unknown },
        ],
      },
      {
        id: 'category',
        label: 'Category',
        options: categoryOptions,
      },
      {
        id: 'tags',
        label: 'Tags',
        options: tagOptions,
      },
    ];
  }, [tools, healthCounts]);

  const filteredTools = useMemo(() => {
    let result = tools;

    // Filter by tab
    if (activeTab === 'favorites') {
      result = result.filter((tool) => favorites.includes(tool.toolName));
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((tool) =>
        [tool.displayName, tool.toolName, tool.description, ...(tool.tags || [])]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(query))
      );
    }

    if (selectedFilters.health?.length) {
      result = result.filter((tool) => selectedFilters.health?.includes(getHealthStatus(tool)));
    }

    if (selectedFilters.category?.length) {
      result = result.filter((tool) => selectedFilters.category?.includes(tool.category));
    }

    if (selectedFilters.tags?.length) {
      result = result.filter((tool) =>
        tool.tags?.some((tag) => selectedFilters.tags?.includes(tag))
      );
    }

    return result;
  }, [tools, searchQuery, selectedFilters, activeTab, favorites]);

  const handleFilterChange = (groupId: string, optionId: string, checked: boolean) => {
    setSelectedFilters((prev) => {
      const next = { ...prev };
      if (!next[groupId]) {
        next[groupId] = [];
      }
      if (checked) {
        next[groupId] = [...next[groupId], optionId];
      } else {
        next[groupId] = next[groupId].filter((id) => id !== optionId);
      }
      return next;
    });
  };

  const handleRemoveFilter = (groupId: string, optionId: string) => {
    handleFilterChange(groupId, optionId, false);
  };

  const handleClearAllFilters = () => {
    setSelectedFilters({});
  };

  const handleRefresh = () => {
    void fetchCatalog({ silent: true });
    void fetchFavorites();
    void fetchConfigurations();
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <PageHeader
          title="Tool Catalog"
          description="Browse every MCP tool surfaced from the n8n integration gateway."
        />
        <LoadingState message="Loading MCP integrations..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Tool Catalog"
        description="Day-one integrations powered by n8n's connector library. Every entry here is callable via MCP without custom backend work."
        badge={{ label: `${tools.length} integrations` }}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={cn('w-4 h-4 mr-2', isRefreshing && 'animate-spin')} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a
                href="https://n8n.io/integrations"
                target="_blank"
                rel="noreferrer"
                className="flex items-center"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View n8n Gallery
              </a>
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-auto">
        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
            <MetricCard
              title="Available Integrations"
              value={summaryMetrics.total}
              subtitle="From n8n manifest"
              icon={Layers}
            />
            <MetricCard
              title="Healthy Connectors"
              value={summaryMetrics.healthy}
              subtitle="Ready to use"
              icon={CheckCircle2}
            />
            <MetricCard
              title="Needs Attention"
              value={summaryMetrics.degraded}
              subtitle="Check configuration"
              icon={AlertTriangle}
            />
            <MetricCard
              title="My Favorites"
              value={summaryMetrics.favorites}
              subtitle="Starred tools"
              icon={Star}
            />
            <MetricCard
              title="Configurations"
              value={summaryMetrics.configurations}
              subtitle="Active configs"
              icon={Settings}
            />
          </div>

          {error && (
            <Card className="mb-6 border border-red-500/40 bg-red-500/5 p-4 text-sm text-red-200">
              {error}
            </Card>
          )}

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="all">All Tools ({tools.length})</TabsTrigger>
              <TabsTrigger value="favorites">
                <Star className="w-4 h-4 mr-2" />
                My Tools ({favorites.length})
              </TabsTrigger>
              <TabsTrigger value="configurations">
                <Settings className="w-4 h-4 mr-2" />
                Configurations ({configurations.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-0">
              <ToolsGridView
                tools={filteredTools}
                allTools={tools}
                favorites={favorites}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                filterGroups={filterGroups}
                selectedFilters={selectedFilters}
                handleFilterChange={handleFilterChange}
                handleRemoveFilter={handleRemoveFilter}
                handleClearAllFilters={handleClearAllFilters}
                onToggleFavorite={handleToggleFavorite}
              />
            </TabsContent>

            <TabsContent value="favorites" className="mt-0">
              <ToolsGridView
                tools={filteredTools}
                allTools={tools}
                favorites={favorites}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                filterGroups={filterGroups}
                selectedFilters={selectedFilters}
                handleFilterChange={handleFilterChange}
                handleRemoveFilter={handleRemoveFilter}
                handleClearAllFilters={handleClearAllFilters}
                onToggleFavorite={handleToggleFavorite}
                emptyMessage="You haven't favorited any tools yet. Click the star icon on any tool card to add it to your favorites."
              />
            </TabsContent>

            <TabsContent value="configurations" className="mt-0">
              <ConfigurationsView configurations={configurations} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

// Tools grid view component (used by All Tools and My Tools tabs)
function ToolsGridView({
  tools,
  allTools,
  favorites,
  searchQuery,
  setSearchQuery,
  filterGroups,
  selectedFilters,
  handleFilterChange,
  handleRemoveFilter,
  handleClearAllFilters,
  onToggleFavorite,
  emptyMessage,
}: {
  tools: IntegrationToolCatalogItem[];
  allTools: IntegrationToolCatalogItem[];
  favorites: string[];
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  filterGroups: FilterGroup[];
  selectedFilters: Record<string, string[]>;
  handleFilterChange: (groupId: string, optionId: string, checked: boolean) => void;
  handleRemoveFilter: (groupId: string, optionId: string) => void;
  handleClearAllFilters: () => void;
  onToggleFavorite: (toolName: string) => void;
  emptyMessage?: string;
}) {
  return (
    <div className="flex flex-col lg:flex-row gap-6">
      <div className="lg:w-64 flex-shrink-0">
        <Card className="p-4">
          <FilterPanel
            groups={filterGroups}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearAllFilters}
          />
        </Card>
      </div>

      <div className="flex-1 min-w-0">
        <div className="mb-4">
          <SearchBar
            placeholder="Search by tool name, vendor, category, or tag..."
            value={searchQuery}
            onChange={setSearchQuery}
            className="max-w-xl"
          />
        </div>

        {Object.keys(selectedFilters).some((key) => selectedFilters[key]?.length) && (
          <div className="mb-4">
            <ActiveFilters
              selectedFilters={selectedFilters}
              groups={filterGroups}
              onRemove={handleRemoveFilter}
            />
          </div>
        )}

        <div className="flex items-center justify-between mb-4 text-sm text-fg-2">
          <span>
            {tools.length === allTools.length
              ? `Showing all ${tools.length} tools`
              : `Showing ${tools.length} of ${allTools.length} tools`}
          </span>
        </div>

        {tools.length === 0 ? (
          <EmptyState
            title={emptyMessage || 'No tools match your filters'}
            description={emptyMessage ? '' : 'Try clearing filters or refreshing the catalog.'}
            action={
              emptyMessage
                ? undefined
                : {
                    label: 'Reset filters',
                    onClick: () => {
                      setSearchQuery('');
                      handleClearAllFilters();
                    },
                  }
            }
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {tools.map((tool) => (
              <ToolCard
                key={tool.toolName}
                tool={tool}
                isFavorited={favorites.includes(tool.toolName)}
                onToggleFavorite={() => onToggleFavorite(tool.toolName)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Configurations view component
function ConfigurationsView({ configurations }: { configurations: IntegrationConfig[] }) {
  const router = useRouter();

  if (configurations.length === 0) {
    return (
      <EmptyState
        title="No configurations yet"
        description="Configure tools by clicking the Configure button on any tool detail page."
      />
    );
  }

  return (
    <div className="space-y-4">
      {configurations.map((config) => (
        <Card
          key={config.id}
          className="p-6 border-white/10 bg-gradient-to-b from-bg-1/90 to-bg-0/60 cursor-pointer hover:border-white/20"
          onClick={() => router.push(`/app/tools/${encodeURIComponent(config.tool_name)}`)}
        >
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-lg font-semibold text-fg-0">{config.instance_name}</h3>
              <p className="text-sm text-fg-2">{config.tool_name}</p>
            </div>
            <Badge variant="outline" className="text-xs capitalize">
              {config.environment}
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-fg-3 text-xs mb-1">Organization</p>
              <p className="text-fg-1">{config.organization_id}</p>
            </div>
            {config.project_id && (
              <div>
                <p className="text-fg-3 text-xs mb-1">Project</p>
                <p className="text-fg-1">{config.project_id}</p>
              </div>
            )}
            <div>
              <p className="text-fg-3 text-xs mb-1">Domain</p>
              <p className="text-fg-1">{config.domain_id}</p>
            </div>
            <div>
              <p className="text-fg-3 text-xs mb-1">Auth Method</p>
              <p className="text-fg-1 capitalize">{config.auth_method}</p>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-white/5">
            <p className="text-xs text-fg-3">Base URL: {config.base_url}</p>
          </div>
        </Card>
      ))}
    </div>
  );
}

type IconType = ComponentType<{ className?: string }>;

function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: IconType;
}) {
  return (
    <Card className="p-5 border-white/10 bg-bg-1/80">
      <div className="flex items-center gap-3 mb-3">
        <div className="rounded-full bg-bg-2 p-2 text-blue-300">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <p className="text-xs text-fg-2">{title}</p>
          <p className="text-2xl font-semibold text-fg-0">{value}</p>
        </div>
      </div>
      {subtitle && <p className="text-xs text-fg-2">{subtitle}</p>}
    </Card>
  );
}

function ToolCard({
  tool,
  isFavorited,
  onToggleFavorite,
}: {
  tool: IntegrationToolCatalogItem;
  isFavorited: boolean;
  onToggleFavorite: () => void;
}) {
  const router = useRouter();
  const healthStatus = getHealthStatus(tool);
  const docsValue = tool.metadata?.['docsUrl'];
  const authValue = tool.metadata?.['authType'];

  const docsUrl = typeof docsValue === 'string' ? docsValue : undefined;
  const authType = typeof authValue === 'string' ? authValue : undefined;

  const handleClick = () => {
    router.push(`/app/tools/${encodeURIComponent(tool.toolName)}`);
  };

  const handleStarClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onToggleFavorite();
  };

  return (
    <Card
      className="p-6 border-white/10 bg-gradient-to-b from-bg-1/90 to-bg-0/60 backdrop-blur-sm cursor-pointer transition-all hover:border-white/20 hover:bg-gradient-to-b hover:from-bg-1 hover:to-bg-0/70"
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-4 gap-3">
        <div className="flex items-center gap-3">
          <ToolLogo logo={tool.logo} name={tool.displayName} />
          <div>
            <p className="text-sm text-fg-2">{tool.toolName}</p>
            <h3 className="text-lg font-semibold text-fg-0">{tool.displayName}</h3>
          </div>
        </div>
        <button
          onClick={handleStarClick}
          className={cn(
            'p-1.5 rounded-md transition-colors',
            isFavorited
              ? 'text-yellow-400 hover:text-yellow-300'
              : 'text-fg-3 hover:text-yellow-400'
          )}
        >
          <Star className={cn('w-5 h-5', isFavorited && 'fill-current')} />
        </button>
      </div>

      <p className="text-sm text-fg-2 mb-4 line-clamp-3">{tool.description}</p>

      <div className="flex flex-wrap items-center gap-2 text-xs text-fg-2 mb-4">
        <Badge variant="outline" className="text-xs capitalize">
          {formatCategory(tool.category)}
        </Badge>
        {authType && (
          <Badge variant="outline" className="text-xs">
            Auth: {authType}
          </Badge>
        )}
      </div>

      {tool.tags?.length ? (
        <div className="flex flex-wrap gap-2 mb-4">
          {tool.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      ) : null}

      <div className="flex items-center justify-between text-xs text-fg-2">
        <div>
          <p className="uppercase tracking-wide text-[10px] text-fg-3">Backed by MCP</p>
          <p>n8n workflow manifest</p>
        </div>
        <div className="flex items-center gap-2">
          {docsUrl && (
            <a
              href={docsUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-xs"
              onClick={(e) => e.stopPropagation()}
            >
              Docs <ExternalLink className="h-3 w-3" />
            </a>
          )}
          <Badge className={cn('text-xs border', HEALTH_BADGE_STYLES[healthStatus])}>
            {HEALTH_COPY[healthStatus]}
          </Badge>
        </div>
      </div>
    </Card>
  );
}

function ToolLogo({ logo, name }: { logo: string; name: string }) {
  const [iconLoaded, setIconLoaded] = useState(false);
  const [iconError, setIconError] = useState(false);
  const initials = name.slice(0, 2).toUpperCase();
  const iconName = logo || name.toLowerCase();
  const iconUrl = `https://cdn.simpleicons.org/${iconName}`;

  return (
    <div className="h-12 w-12 rounded-2xl bg-bg-2 border border-white/10 flex items-center justify-center shadow-lg shadow-black/40 overflow-hidden">
      {!iconError ? (
        <>
          <img
            src={iconUrl}
            alt={`${name} icon`}
            className={cn(
              'h-7 w-7 object-contain transition-opacity',
              iconLoaded ? 'opacity-100' : 'opacity-0'
            )}
            onLoad={() => setIconLoaded(true)}
            onError={() => {
              setIconError(true);
              setIconLoaded(false);
            }}
          />
          {!iconLoaded && <div className="text-sm font-semibold text-fg-2">{initials}</div>}
        </>
      ) : (
        <div className="text-sm font-semibold text-fg-2">{initials}</div>
      )}
    </div>
  );
}

function getHealthStatus(tool: IntegrationToolCatalogItem): HealthState {
  const metrics = tool.health;
  if (!metrics) {
    return 'unknown';
  }

  if (metrics.last_error) {
    return 'degraded';
  }

  if ((metrics.failure ?? 0) > 0 && (metrics.success ?? 0) === 0) {
    return 'degraded';
  }

  return 'healthy';
}

function formatCategory(category: string) {
  return category.replace(/[_-]/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}
