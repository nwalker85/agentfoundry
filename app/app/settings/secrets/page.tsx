'use client';

import { useState, useEffect } from 'react';
import { Key, AlertCircle } from 'lucide-react';
import { PageHeader } from '@/app/components/shared/PageHeader';
import { SecretsManagementPanel } from '@/components/secrets/SecretsManagementPanel';
import { Card } from '@/components/ui/card';

export default function SecretsSettingsPage() {
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [selectedDomainId, setSelectedDomainId] = useState<string | null>(null);

  // Load selected org/domain from localStorage (set by TopNav org selector)
  useEffect(() => {
    const orgId = localStorage.getItem('selectedOrgId');
    const domainId = localStorage.getItem('selectedDomainId');
    setSelectedOrgId(orgId);
    setSelectedDomainId(domainId);

    // Listen for changes to org selection
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'selectedOrgId') {
        setSelectedOrgId(e.newValue);
      }
      if (e.key === 'selectedDomainId') {
        setSelectedDomainId(e.newValue);
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  return (
    <div className="flex-1 overflow-auto">
      <div className="container mx-auto p-6 max-w-5xl">
        <PageHeader
          title="Secrets Management"
          description="Configure API keys, credentials, and sensitive configuration for your organization"
          icon={Key}
        />

        {!selectedOrgId ? (
          <Card className="mt-6 p-8">
            <div className="flex flex-col items-center justify-center text-center">
              <AlertCircle className="w-12 h-12 text-amber-500 mb-4" />
              <h3 className="text-lg font-semibold text-fg-0 mb-2">No Organization Selected</h3>
              <p className="text-sm text-fg-2 max-w-md">
                Please select an organization from the navigation bar to manage secrets. Secrets are
                scoped to organizations and domains for security.
              </p>
            </div>
          </Card>
        ) : (
          <div className="mt-6">
            <SecretsManagementPanel
              organizationId={selectedOrgId}
              domainId={selectedDomainId || undefined}
            />
          </div>
        )}
      </div>
    </div>
  );
}
