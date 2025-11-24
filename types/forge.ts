import type { Edge, Node } from 'reactflow';

export type StateFieldType =
  | 'string'
  | 'int'
  | 'float'
  | 'bool'
  | 'list'
  | 'dict'
  | 'json'
  | 'message'
  | 'custom';

export type ReducerType = 'add' | 'replace' | 'merge' | 'sum' | 'max' | 'min' | 'custom';

export interface StateField {
  id?: string;
  name: string;
  type: StateFieldType;
  reducer?: ReducerType;
  description?: string;
  defaultValue?: any;
  required?: boolean;
  sensitive?: boolean;
}

export interface StateSchema {
  id: string;
  name: string;
  description?: string;
  version: string;
  fields: StateField[];
  initialState: Record<string, any>;
  tags: string[];
  createdAt?: string;
  updatedAt?: string;
}

export type TriggerType = 'webhook' | 'event' | 'cron' | 'stream' | 'manual' | 'custom';

export interface TriggerDefinition {
  id: string;
  name: string;
  type: TriggerType;
  description?: string;
  channel?: string;
  config: Record<string, any>;
  isActive: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface GraphTriggerMapping {
  id: string;
  targetType: 'agent' | 'channel';
  targetId: string;
  triggerId: string;
  triggerName?: string;
  triggerType?: TriggerType;
  startNodeId?: string;
  config?: Record<string, any>;
}

export interface ChannelWorkflow {
  id: string;
  channel: string;
  name: string;
  description?: string;
  nodes: Node[];
  edges: Edge[];
  stateSchemaId?: string;
  metadata: Record<string, any>;
  createdAt?: string;
  updatedAt?: string;
}

export interface ChannelWorkflowInput extends Omit<ChannelWorkflow, 'id'> {
  id?: string;
}
