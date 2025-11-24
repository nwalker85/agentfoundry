'use client';

/**
 * Secret Configuration Card Component
 *
 * Implements the "Blind Write" pattern for secret management:
 * - Shows "Configured" or "Not Configured" status
 * - Never displays actual secret values
 * - Allows rotation/update without revealing old value
 * - Provides immediate visual feedback
 *
 * Usage:
 *   <SecretConfigCard
 *     organizationId="acme-corp"
 *     secretName="openai_api_key"
 *     displayName="OpenAI API Key"
 *     description="API key for GPT models"
 *     placeholder="sk-..."
 *   />
 */

import { useState, useEffect } from 'react';
import { Check, X, Eye, EyeOff, AlertCircle, RefreshCw } from 'lucide-react';
import { getServiceUrl } from '@/lib/config/services';

interface SecretConfigCardProps {
  organizationId: string;
  domainId?: string;
  secretName: string;
  displayName: string;
  description: string;
  placeholder?: string;
  category?: string;
  onUpdate?: () => void;
}

export function SecretConfigCard({
  organizationId,
  domainId,
  secretName,
  displayName,
  description,
  placeholder = '••••••••',
  category,
  onUpdate,
}: SecretConfigCardProps) {
  const [isConfigured, setIsConfigured] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [newValue, setNewValue] = useState('');
  const [showValue, setShowValue] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch status on mount
  useEffect(() => {
    loadStatus();
  }, [organizationId, secretName, domainId]);

  async function loadStatus() {
    setLoading(true);
    setError(null);

    try {
      const apiUrl = getServiceUrl('backend');
      const url = domainId
        ? `${apiUrl}/api/secrets/${organizationId}/${secretName}?domain_id=${domainId}`
        : `${apiUrl}/api/secrets/${organizationId}/${secretName}`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to load status: ${response.statusText}`);
      }

      const data = await response.json();
      setIsConfigured(data.configured);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load status');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!newValue.trim()) {
      setError('Secret value cannot be empty');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const apiUrl = getServiceUrl('backend');
      const response = await fetch(`${apiUrl}/api/secrets/${organizationId}/${secretName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          secret_value: newValue,
          domain_id: domainId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save secret');
      }

      // Success!
      setIsConfigured(true);
      setIsEditing(false);
      setNewValue(''); // Clear from memory immediately
      setShowValue(false);

      // Notify parent
      onUpdate?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save secret');
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setIsEditing(false);
    setNewValue(''); // Clear from memory
    setShowValue(false);
    setError(null);
  }

  if (loading) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-2/3"></div>
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-gray-900">{displayName}</h3>
            {category && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {category}
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500">{description}</p>
        </div>

        {/* Status Badge */}
        <div className="ml-4">
          {isConfigured ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full">
              <Check className="w-3 h-3" />
              Configured
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              <X className="w-3 h-3" />
              Not Configured
            </span>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Action Area */}
      {!isEditing ? (
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsEditing(true)}
            className="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors flex items-center gap-1"
          >
            {isConfigured ? (
              <>
                <RefreshCw className="w-3 h-3" />
                Rotate Key
              </>
            ) : (
              <>Add Key</>
            )}
          </button>

          {isConfigured && (
            <span className="text-xs text-gray-500">
              Last updated: {new Date().toLocaleDateString()}
            </span>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {/* Input Field */}
          <div className="relative">
            <input
              type={showValue ? 'text' : 'password'}
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder={placeholder}
              className="w-full text-sm border border-gray-300 rounded px-3 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              type="button"
              onClick={() => setShowValue(!showValue)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              title={showValue ? 'Hide value' : 'Show value'}
            >
              {showValue ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={saving || !newValue.trim()}
              className="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? 'Saving...' : 'Save & Overwrite'}
            </button>
            <button
              onClick={handleCancel}
              disabled={saving}
              className="text-xs px-3 py-1.5 rounded border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
          </div>

          {/* Warning Text */}
          <p className="text-xs text-gray-500">
            ⚠️ Entering a new key will immediately overwrite the existing one. This action cannot be
            undone.
          </p>
        </div>
      )}
    </div>
  );
}
