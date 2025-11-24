'use client';

import { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetFooter,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { IntegrationConfigRequest } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Organization {
  id: string;
  name: string;
  tier: string;
}

interface Project {
  id: string;
  organization_id: string;
  name: string;
  display_name: string;
  description?: string;
}

interface Domain {
  id: string;
  organization_id: string;
  project_id?: string;
  name: string;
  display_name: string;
  version: string;
}

interface ConfigurationDrawerProps {
  toolName: string;
  toolDisplayName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
}

export function ConfigurationDrawer({
  toolName,
  toolDisplayName,
  open,
  onOpenChange,
  onSaved,
}: ConfigurationDrawerProps) {
  const [formData, setFormData] = useState<Partial<IntegrationConfigRequest>>({
    organization_id: '',
    project_id: '',
    domain_id: '',
    environment: 'development',
    instance_name: '',
    base_url: '',
    auth_method: 'oauth2',
    credentials: {},
    metadata: {},
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [credentialFields, setCredentialFields] = useState<Record<string, string>>({});

  // Hierarchy data
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [isLoadingOrgs, setIsLoadingOrgs] = useState(false);
  const [isLoadingProjects, setIsLoadingProjects] = useState(false);
  const [isLoadingDomains, setIsLoadingDomains] = useState(false);

  // Load organizations when drawer opens
  useEffect(() => {
    if (open) {
      loadOrganizations();
    }
  }, [open]);

  // Load projects when organization changes
  useEffect(() => {
    if (formData.organization_id) {
      loadProjects(formData.organization_id);
    } else {
      setProjects([]);
      setDomains([]);
    }
  }, [formData.organization_id]);

  // Load domains when project changes
  useEffect(() => {
    if (formData.project_id) {
      loadDomains(formData.organization_id!, formData.project_id);
    } else if (formData.organization_id && !formData.project_id) {
      // Load all domains for org if no project selected
      loadDomains(formData.organization_id!);
    } else {
      setDomains([]);
    }
  }, [formData.project_id, formData.organization_id]);

  const loadOrganizations = async () => {
    setIsLoadingOrgs(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/organizations`);
      if (res.ok) {
        const data = await res.json();
        setOrganizations(data);
      }
    } catch (err) {
      console.error('Failed to load organizations:', err);
    } finally {
      setIsLoadingOrgs(false);
    }
  };

  const loadProjects = async (orgId: string) => {
    setIsLoadingProjects(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects?organization_id=${orgId}`);
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const loadDomains = async (orgId: string, projectId?: string) => {
    setIsLoadingDomains(true);
    try {
      let url = `${API_BASE_URL}/api/domains?organization_id=${orgId}`;
      if (projectId) {
        url += `&project_id=${projectId}`;
      }
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setDomains(data);
      }
    } catch (err) {
      console.error('Failed to load domains:', err);
    } finally {
      setIsLoadingDomains(false);
    }
  };

  const handleOrganizationChange = (orgId: string) => {
    setFormData({
      ...formData,
      organization_id: orgId,
      project_id: '',
      domain_id: '',
    });
  };

  const handleProjectChange = (projectId: string) => {
    setFormData({
      ...formData,
      project_id: projectId,
      domain_id: '',
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);

    try {
      // Validate required fields
      if (!formData.organization_id || !formData.domain_id) {
        throw new Error('Organization and domain are required');
      }
      if (!formData.instance_name || !formData.base_url) {
        throw new Error('Instance name and base URL are required');
      }

      const payload: IntegrationConfigRequest = {
        organization_id: formData.organization_id,
        project_id: formData.project_id || undefined,
        domain_id: formData.domain_id,
        environment: formData.environment || 'development',
        instance_name: formData.instance_name,
        base_url: formData.base_url,
        auth_method: formData.auth_method || 'oauth2',
        credentials: credentialFields,
        metadata: formData.metadata || {},
      };

      const res = await fetch(`${API_BASE_URL}/api/integrations/configs/${toolName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || 'Failed to save configuration');
      }

      // Success
      onSaved?.();
      onOpenChange(false);
    } catch (err) {
      console.error('Failed to save configuration:', err);
      setError(err instanceof Error ? err.message : 'Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[500px] sm:w-[600px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Configure {toolDisplayName}</SheetTitle>
          <SheetDescription>
            Set up organization-specific configuration for this integration tool.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Organization Select */}
          <div className="space-y-2">
            <Label htmlFor="organization_id">
              Organization <span className="text-red-500">*</span>
            </Label>
            <Select
              value={formData.organization_id}
              onValueChange={handleOrganizationChange}
              disabled={isLoadingOrgs}
            >
              <SelectTrigger id="organization_id">
                <SelectValue placeholder={isLoadingOrgs ? 'Loading...' : 'Select organization'} />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-fg-2">The organization this configuration belongs to</p>
          </div>

          {/* Project Select */}
          <div className="space-y-2">
            <Label htmlFor="project_id">
              Project <span className="text-fg-2">(optional)</span>
            </Label>
            <Select
              value={formData.project_id || ''}
              onValueChange={handleProjectChange}
              disabled={!formData.organization_id || isLoadingProjects}
            >
              <SelectTrigger id="project_id">
                <SelectValue
                  placeholder={
                    !formData.organization_id
                      ? 'Select organization first'
                      : isLoadingProjects
                        ? 'Loading...'
                        : 'Select project (optional)'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-fg-2">Optional: Scope to a specific project</p>
          </div>

          {/* Domain Select */}
          <div className="space-y-2">
            <Label htmlFor="domain_id">
              Domain <span className="text-red-500">*</span>
            </Label>
            <Select
              value={formData.domain_id}
              onValueChange={(value) => setFormData({ ...formData, domain_id: value })}
              disabled={!formData.organization_id || isLoadingDomains}
            >
              <SelectTrigger id="domain_id">
                <SelectValue
                  placeholder={
                    !formData.organization_id
                      ? 'Select organization first'
                      : isLoadingDomains
                        ? 'Loading...'
                        : 'Select domain'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {domains.map((domain) => (
                  <SelectItem key={domain.id} value={domain.id}>
                    {domain.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-fg-2">The domain or team this configuration is for</p>
          </div>

          {/* Environment */}
          <div className="space-y-2">
            <Label htmlFor="environment">Environment</Label>
            <Select
              value={formData.environment}
              onValueChange={(value) => setFormData({ ...formData, environment: value })}
            >
              <SelectTrigger id="environment">
                <SelectValue placeholder="Select environment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="development">Development</SelectItem>
                <SelectItem value="staging">Staging</SelectItem>
                <SelectItem value="production">Production</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Instance Name */}
          <div className="space-y-2">
            <Label htmlFor="instance_name">
              Instance Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="instance_name"
              value={formData.instance_name}
              onChange={(e) => setFormData({ ...formData, instance_name: e.target.value })}
              placeholder="e.g., acme-servicenow-prod"
              required
            />
            <p className="text-xs text-fg-2">A unique name for this tool instance</p>
          </div>

          {/* Base URL */}
          <div className="space-y-2">
            <Label htmlFor="base_url">
              Base URL <span className="text-red-500">*</span>
            </Label>
            <Input
              id="base_url"
              type="url"
              value={formData.base_url}
              onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
              placeholder="https://api.example.com"
              required
            />
            <p className="text-xs text-fg-2">The base URL for the integration API</p>
          </div>

          {/* Auth Method */}
          <div className="space-y-2">
            <Label htmlFor="auth_method">Authentication Method</Label>
            <Select
              value={formData.auth_method}
              onValueChange={(value) => setFormData({ ...formData, auth_method: value })}
            >
              <SelectTrigger id="auth_method">
                <SelectValue placeholder="Select auth method" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                <SelectItem value="basic">Basic Auth</SelectItem>
                <SelectItem value="apikey">API Key</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Credentials based on auth method */}
          <div className="space-y-4">
            <Label>Credentials</Label>

            {formData.auth_method === 'oauth2' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="client_id">Client ID</Label>
                  <Input
                    id="client_id"
                    value={credentialFields.client_id || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, client_id: e.target.value })
                    }
                    placeholder="OAuth client ID"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="client_secret">Client Secret</Label>
                  <Input
                    id="client_secret"
                    type="password"
                    value={credentialFields.client_secret || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, client_secret: e.target.value })
                    }
                    placeholder="OAuth client secret"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="token_url">Token URL</Label>
                  <Input
                    id="token_url"
                    type="url"
                    value={credentialFields.token_url || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, token_url: e.target.value })
                    }
                    placeholder="https://auth.example.com/oauth/token"
                  />
                </div>
              </>
            )}

            {formData.auth_method === 'basic' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={credentialFields.username || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, username: e.target.value })
                    }
                    placeholder="Username"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={credentialFields.password || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, password: e.target.value })
                    }
                    placeholder="Password"
                  />
                </div>
              </>
            )}

            {formData.auth_method === 'apikey' && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="api_key">API Key</Label>
                  <Input
                    id="api_key"
                    type="password"
                    value={credentialFields.api_key || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, api_key: e.target.value })
                    }
                    placeholder="API key"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="header_name">Header Name (optional)</Label>
                  <Input
                    id="header_name"
                    value={credentialFields.header_name || ''}
                    onChange={(e) =>
                      setCredentialFields({ ...credentialFields, header_name: e.target.value })
                    }
                    placeholder="e.g., X-API-Key"
                  />
                  <p className="text-xs text-fg-2">
                    Leave blank to use default Authorization header
                  </p>
                </div>
              </>
            )}
          </div>

          {/* Metadata (optional) */}
          <div className="space-y-2">
            <Label htmlFor="metadata">Metadata (optional JSON)</Label>
            <Textarea
              id="metadata"
              value={JSON.stringify(formData.metadata || {}, null, 2)}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value);
                  setFormData({ ...formData, metadata: parsed });
                } catch {
                  // Invalid JSON, ignore
                }
              }}
              placeholder='{"key": "value"}'
              rows={4}
              className="font-mono text-sm"
            />
            <p className="text-xs text-fg-2">Additional metadata as JSON (optional)</p>
          </div>
        </div>

        <SheetFooter className="mt-6">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
            <X className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
