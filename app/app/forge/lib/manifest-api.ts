'use client';

import { Node, Edge } from 'reactflow';
import { graphToYAML } from './graph-to-yaml';
import type { StateSchema, TriggerDefinition } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface RegisterAgentPayload {
  agentId: string;
  nodes: Node[];
  edges: Edge[];
  yamlPath?: string;
  stateSchema?: StateSchema | null;
  triggers?: TriggerDefinition[];

  organizationId: string;
  organizationName: string;
  domainId: string;
  domainName: string;
  environment: 'dev' | 'staging' | 'prod';
  instanceId: string;

  author: string;
  lastEditor?: string;
  tags?: string[];
  isSystemAgent?: boolean;
  systemTier?: 0 | 1;

  // Optional metadata overrides
  displayName?: string;
  description?: string;
  version?: string;
}

export async function registerAgentInManifest(payload: RegisterAgentPayload) {
  const {
    agentId,
    nodes,
    edges,
    organizationId,
    organizationName,
    domainId,
    domainName,
    environment,
    author,
    lastEditor,
    tags,
    isSystemAgent,
    stateSchema,
    triggers,
    displayName,
    description,
    version,
  } = payload;

  // Build the graph data structure that the backend expects
  // The backend's upsert_graph reads from metadata + spec structure
  // Note: If agentId looks like a UUID, it's an existing agent ID; use displayName for the name field
  const isExistingAgent = agentId.includes('-') && agentId.length > 30; // UUID pattern
  const graphData = {
    // Include the ID at the top level for existing agents
    ...(isExistingAgent && { id: agentId }),
    metadata: {
      // If existing agent, include the ID in metadata too
      ...(isExistingAgent && { id: agentId }),
      // Use displayName for the 'name' field (searchable name), not the UUID
      name: displayName || agentId,
      display_name: displayName || agentId,
      description: description || `Agent created via Forge: ${displayName || agentId}`,
      type: 'user',
      organization_id: organizationId,
      domain_id: domainId,
      environment,
      version: version || '0.0.1',
      status: 'active',
      created_by: author,
      updated_by: lastEditor ?? author,
      tags: tags ?? [],
      is_system_agent: isSystemAgent ?? false,
    },
    spec: {
      state_schema_id: stateSchema?.id ?? null,
      triggers: triggers ?? [],
      graph: {
        nodes,
        edges,
      },
    },
  };

  // Always use POST - the backend's /api/graphs endpoint handles upsert
  // (creates if new, updates if existing based on name)
  const response = await fetch(`${API_BASE_URL}/api/graphs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(graphData),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || err.error || `Save failed (${response.status})`);
  }

  return response.json();
}
