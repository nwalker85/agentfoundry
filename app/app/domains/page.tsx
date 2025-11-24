'use client';

import { useEffect, useState, useMemo } from 'react';
import { RefreshCw, Download, Plus, Globe, Building2, Calendar, User } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Toolbar, type ToolbarAction } from '@/components/layout/Toolbar';
import { LoadingState, EmptyState, UnderConstruction } from '@/components/shared';

interface Domain {
  id: string;
  name: string;
  display_name?: string;
  organization_id: string;
  organization_name?: string;
  version: string;
  created_at: string;
  updated_at: string;
  description?: string;
  status?: 'active' | 'inactive';
}

export default function DomainsPage() {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);

  // Load selected org from localStorage
  useEffect(() => {
    const orgId = localStorage.getItem('selectedOrgId');
    setSelectedOrgId(orgId);
  }, []);

  // Fetch domains from API
  useEffect(() => {
    const fetchDomains = async () => {
      if (!selectedOrgId) return;

      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiBase}/api/control/organizations`);
        if (!res.ok) {
          console.error('Failed to load organizations:', res.statusText);
          return;
        }
        const data = await res.json();

        // Find the selected org and get its domains
        const selectedOrg = data.find((org: any) => org.id === selectedOrgId);
        if (selectedOrg && selectedOrg.domains) {
          const mappedDomains: Domain[] = selectedOrg.domains.map((d: any) => ({
            id: d.id,
            name: d.name,
            display_name: d.display_name || d.name,
            organization_id: selectedOrg.id,
            organization_name: selectedOrg.name,
            version: d.version || '1.0.0',
            created_at: d.created_at || new Date().toISOString(),
            updated_at: d.updated_at || new Date().toISOString(),
            description: d.description,
            status: d.status || 'active',
          }));
          setDomains(mappedDomains);
        }
      } catch (e) {
        console.error('Failed to fetch domains:', e);
      } finally {
        setLoading(false);
      }
    };

    fetchDomains();
  }, [selectedOrgId]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // Re-trigger fetch by clearing and reloading
    setLoading(true);
    setDomains([]);
    setTimeout(() => {
      setIsRefreshing(false);
      setLoading(false);
    }, 500);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(domains, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `domains-${selectedOrgId}-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCreateDomain = () => {
    // TODO: Navigate to create domain page or open modal
    console.log('Creating new domain...');
  };

  // Define toolbar actions
  const toolbarActions: ToolbarAction[] = useMemo(
    () => [
      {
        icon: RefreshCw,
        label: 'Refresh',
        onClick: handleRefresh,
        disabled: isRefreshing,
        variant: 'ghost',
        tooltip: 'Refresh domain list',
      },
      {
        icon: Download,
        label: 'Export',
        onClick: handleExport,
        variant: 'ghost',
        tooltip: 'Export domain data',
      },
    ],
    [isRefreshing, domains]
  );

  if (loading) {
    return (
      <div className="flex flex-col h-full">
        <Toolbar actions={toolbarActions} />
        <LoadingState message="Loading domains..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <Toolbar actions={toolbarActions} />

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        <UnderConstruction
          className="mb-6"
          message="Domain management is under development. Creating and editing domains is not yet available."
        />
        {domains.length === 0 ? (
          <EmptyState
            title="No domains found"
            description={
              selectedOrgId
                ? `No domains configured for this organization. Domains help organize agents and resources.`
                : 'Please select an organization from the top navigation.'
            }
          />
        ) : (
          <div className="space-y-4">
            {/* Summary Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-fg-0">
                  Domains in {domains[0]?.organization_name || 'Organization'}
                </h2>
                <p className="text-sm text-fg-2 mt-1">
                  {domains.length} {domains.length === 1 ? 'domain' : 'domains'} configured
                </p>
              </div>
            </div>

            {/* Domains Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {domains.map((domain) => (
                <Card
                  key={domain.id}
                  className="p-4 bg-bg-1 border-white/10 hover:border-white/20 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                        <Globe className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-fg-0">
                          {domain.display_name || domain.name}
                        </h3>
                        <p className="text-xs text-fg-3">{domain.id}</p>
                      </div>
                    </div>
                    {domain.status && (
                      <Badge
                        variant="outline"
                        className={
                          domain.status === 'active'
                            ? 'border-green-500/30 text-green-400'
                            : 'border-gray-500/30 text-gray-400'
                        }
                      >
                        {domain.status}
                      </Badge>
                    )}
                  </div>

                  {domain.description && (
                    <p className="text-sm text-fg-2 mb-3">{domain.description}</p>
                  )}

                  <div className="space-y-2 text-xs">
                    <div className="flex items-center gap-2 text-fg-2">
                      <Building2 className="w-3.5 h-3.5" />
                      <span>{domain.organization_name}</span>
                    </div>
                    <div className="flex items-center gap-2 text-fg-2">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Created {new Date(domain.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2 text-fg-2">
                      <span className="font-mono">v{domain.version}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
