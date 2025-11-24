'use client';

/**
 * Secrets Management Panel
 *
 * Groups multiple secret configurations by category.
 * Displays all well-known secrets for an organization/domain.
 *
 * Usage:
 *   <SecretsManagementPanel
 *     organizationId="acme-corp"
 *     domainId="card-services"
 *   />
 */

import { useState, useEffect } from 'react';
import { Key, Loader2, AlertCircle } from 'lucide-react';
import { SecretConfigCard } from './SecretConfigCard';
import { getServiceUrl } from '@/lib/config/services';

interface SecretMetadata {
  secret_name: string;
  display_name: string;
  description: string;
  category: string;
}

interface SecretsManagementPanelProps {
  organizationId: string;
  domainId?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  llm: 'LLM Providers',
  voice: 'Voice Services',
  integration: 'Integrations',
  infrastructure: 'Infrastructure',
  other: 'Other',
};

const CATEGORY_DESCRIPTIONS: Record<string, string> = {
  llm: 'API keys for language model providers (OpenAI, Anthropic, etc.)',
  voice: 'API keys for speech-to-text and text-to-speech services',
  integration: 'Credentials for third-party integrations',
  infrastructure: 'Credentials for infrastructure services',
  other: 'Miscellaneous secrets',
};

export function SecretsManagementPanel({ organizationId, domainId }: SecretsManagementPanelProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [secretsByCategory, setSecretsByCategory] = useState<Record<string, SecretMetadata[]>>({});
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadWellKnownSecrets();
  }, []);

  async function loadWellKnownSecrets() {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = getServiceUrl('backend');
      const response = await fetch(`${apiUrl}/api/secrets/well-known`);

      if (!response.ok) {
        throw new Error('Failed to load secret types');
      }

      const data = await response.json();
      setSecretsByCategory(data.categories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets');
    } finally {
      setLoading(false);
    }
  }

  function handleSecretUpdate() {
    // Trigger refresh of all cards
    setRefreshKey((prev) => prev + 1);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-500">Loading secrets...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
        <AlertCircle className="w-5 h-5 text-red-600" />
        <div>
          <p className="text-sm font-medium text-red-900">Failed to load secrets</p>
          <p className="text-xs text-red-700">{error}</p>
        </div>
      </div>
    );
  }

  const categories = Object.keys(secretsByCategory);

  if (categories.length === 0) {
    return (
      <div className="text-center py-12">
        <Key className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-sm text-gray-500">No secrets configured yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Key className="w-5 h-5" />
          Secrets Management
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          Configure API keys and credentials for{' '}
          <span className="font-medium">{organizationId}</span>
          {domainId && (
            <>
              {' '}
              / <span className="font-medium">{domainId}</span>
            </>
          )}
        </p>
      </div>

      {/* Secrets by Category */}
      {categories.map((category) => {
        const secrets = secretsByCategory[category] || [];

        return (
          <div key={category}>
            {/* Category Header */}
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
                {CATEGORY_LABELS[category] || category}
              </h3>
              <p className="text-xs text-gray-500 mt-1">{CATEGORY_DESCRIPTIONS[category]}</p>
            </div>

            {/* Secret Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {secrets.map((secret) => (
                <SecretConfigCard
                  key={`${secret.secret_name}-${refreshKey}`}
                  organizationId={organizationId}
                  domainId={domainId}
                  secretName={secret.secret_name}
                  displayName={secret.display_name}
                  description={secret.description}
                  category={category}
                  onUpdate={handleSecretUpdate}
                />
              ))}
            </div>
          </div>
        );
      })}

      {/* Security Notice */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900">
            <p className="font-medium mb-1">Security & Privacy</p>
            <ul className="text-xs text-blue-800 space-y-1 list-disc list-inside">
              <li>Secrets are encrypted at rest using LocalStack/AWS Secrets Manager</li>
              <li>Secret values are never returned to your browser</li>
              <li>All secret operations are audit logged</li>
              <li>Rotating a key immediately overwrites the old value</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
