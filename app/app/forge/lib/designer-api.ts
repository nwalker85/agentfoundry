'use client';

import type {
  StateSchema,
  StateField,
  TriggerDefinition,
  ChannelWorkflow,
  ChannelWorkflowInput,
  GraphTriggerMapping,
} from '@/types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const mapFieldFromApi = (field: any): StateField => ({
  id: field.id,
  name: field.name,
  type: field.type,
  reducer: field.reducer,
  description: field.description,
  defaultValue: field.default_value ?? field.defaultValue,
  required: field.required ?? true,
  sensitive: field.sensitive ?? false,
});

const mapSchemaFromApi = (schema: any): StateSchema => ({
  id: schema.id,
  name: schema.name,
  description: schema.description,
  version: schema.version,
  fields: Array.isArray(schema.fields) ? schema.fields.map(mapFieldFromApi) : [],
  initialState: schema.initial_state ?? schema.initialState ?? {},
  tags: schema.tags ?? [],
  createdAt: schema.created_at,
  updatedAt: schema.updated_at,
});

const mapTriggerFromApi = (trigger: any): TriggerDefinition => ({
  id: trigger.id,
  name: trigger.name,
  type: trigger.type,
  description: trigger.description,
  channel: trigger.channel,
  config: trigger.config ?? {},
  isActive: trigger.is_active ?? trigger.isActive ?? true,
  createdAt: trigger.created_at,
  updatedAt: trigger.updated_at,
});

const mapGraphTrigger = (mapping: any): GraphTriggerMapping => ({
  id: mapping.id,
  targetType: mapping.target_type,
  targetId: mapping.target_id,
  triggerId: mapping.trigger_id,
  triggerName: mapping.trigger_name,
  triggerType: mapping.trigger_type,
  startNodeId: mapping.start_node_id,
  config: mapping.config ?? {},
});

const mapWorkflowFromApi = (workflow: any): ChannelWorkflow => ({
  id: workflow.id,
  channel: workflow.channel,
  name: workflow.name,
  description: workflow.description,
  nodes: workflow.nodes ?? [],
  edges: workflow.edges ?? [],
  stateSchemaId: workflow.state_schema_id ?? workflow.stateSchemaId,
  metadata: workflow.metadata ?? {},
  createdAt: workflow.created_at,
  updatedAt: workflow.updated_at,
});

const normalizeFieldsForApi = (fields: StateField[]) =>
  fields.map((field) => ({
    id: field.id,
    name: field.name,
    type: field.type,
    reducer: field.reducer,
    description: field.description,
    default_value: field.defaultValue,
    required: field.required ?? true,
    sensitive: field.sensitive ?? false,
  }));

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const error = await response.json();
      detail = error.detail || JSON.stringify(error);
    } catch {
      // ignore
    }
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return response.json();
}

// =========================
// State Schemas
// =========================

export interface SaveStateSchemaInput {
  id?: string;
  name: string;
  description?: string;
  version?: string;
  fields: StateField[];
  initialState?: Record<string, any>;
  tags?: string[];
}

export async function listStateSchemas(): Promise<StateSchema[]> {
  const result = await request<{ items: any[] }>('/api/forge/state-schemas');
  return (result.items ?? []).map(mapSchemaFromApi);
}

export async function saveStateSchema(payload: SaveStateSchemaInput): Promise<StateSchema> {
  const body = {
    ...payload,
    fields: normalizeFieldsForApi(payload.fields || []),
    initial_state: payload.initialState ?? {},
  };
  const saved = await request<any>('/api/forge/state-schemas', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return mapSchemaFromApi(saved);
}

export async function deleteStateSchema(schemaId: string): Promise<void> {
  await request(`/api/forge/state-schemas/${schemaId}`, {
    method: 'DELETE',
  });
}

// =========================
// Trigger Registry
// =========================

export interface SaveTriggerInput {
  id?: string;
  name: string;
  type: TriggerDefinition['type'];
  description?: string;
  channel?: string;
  config?: Record<string, any>;
  isActive?: boolean;
}

export async function listTriggers(channel?: string): Promise<TriggerDefinition[]> {
  const qs = channel ? `?channel=${encodeURIComponent(channel)}` : '';
  const result = await request<{ items: any[] }>(`/api/forge/triggers${qs}`);
  return (result.items ?? []).map(mapTriggerFromApi);
}

export async function saveTrigger(payload: SaveTriggerInput): Promise<TriggerDefinition> {
  const saved = await request<any>('/api/forge/triggers', {
    method: 'POST',
    body: JSON.stringify({
      ...payload,
      is_active: payload.isActive ?? true,
    }),
  });
  return mapTriggerFromApi(saved);
}

export async function deleteTrigger(triggerId: string): Promise<void> {
  await request(`/api/forge/triggers/${triggerId}`, {
    method: 'DELETE',
  });
}

// =========================
// Graph Trigger Assignment
// =========================

export async function listGraphTriggers(
  targetType: 'agent' | 'channel',
  targetId: string
): Promise<GraphTriggerMapping[]> {
  const qs = `?target_type=${encodeURIComponent(targetType)}&target_id=${encodeURIComponent(targetId)}`;
  const result = await request<{ items: any[] }>(`/api/forge/graph-triggers${qs}`);
  return (result.items ?? []).map(mapGraphTrigger);
}

export async function saveGraphTriggers(payload: {
  targetType: 'agent' | 'channel';
  targetId: string;
  triggerIds: string[];
  startNodeId?: string;
}): Promise<void> {
  await request('/api/forge/graph-triggers', {
    method: 'POST',
    body: JSON.stringify({
      target_type: payload.targetType,
      target_id: payload.targetId,
      trigger_ids: payload.triggerIds,
      start_node_id: payload.startNodeId,
    }),
  });
}

// =========================
// Channel Workflows
// =========================

export async function listChannelWorkflows(channel?: string): Promise<ChannelWorkflow[]> {
  const qs = channel ? `?channel=${encodeURIComponent(channel)}` : '';
  const result = await request<{ items: any[] }>(`/api/forge/channel-workflows${qs}`);
  return (result.items ?? []).map(mapWorkflowFromApi);
}

export async function getChannelWorkflow(workflowId: string): Promise<ChannelWorkflow> {
  const workflow = await request<any>(`/api/forge/channel-workflows/${workflowId}`);
  return mapWorkflowFromApi(workflow);
}

export async function saveChannelWorkflow(
  workflow: ChannelWorkflowInput
): Promise<ChannelWorkflow> {
  const body = {
    ...workflow,
    state_schema_id: workflow.stateSchemaId,
  };
  const saved = await request<any>('/api/forge/channel-workflows', {
    method: 'POST',
    body: JSON.stringify(body),
  });
  return mapWorkflowFromApi(saved);
}

export async function deleteChannelWorkflow(workflowId: string): Promise<void> {
  await request(`/api/forge/channel-workflows/${workflowId}`, {
    method: 'DELETE',
  });
}
