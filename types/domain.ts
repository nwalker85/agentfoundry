/**
 * Agent Foundry - Domain Type Definitions
 * Types for domain modeling, entities, and DIS (Domain Intelligence Schema)
 */

export interface Domain {
  id: string;
  name: string;
  display_name: string;
  description: string;
  version: string;

  // DIS Dossier
  dossier_json: any;
  dossier_valid: boolean;
  validation_errors?: string[];

  // Entities
  entities: Entity[];
  roles: Role[];
  applications: Application[];
  endpoints: Endpoint[];

  // Relationships
  relationships: Relationship[];

  // Metadata
  created_at: string;
  updated_at: string;
  created_by: string;
  tags: string[];

  // Usage
  used_by_agents: string[];
}

export interface Entity {
  id: string;
  domain_id: string;
  name: string;
  display_name: string;
  description: string;
  type: 'person' | 'organization' | 'system' | 'concept' | 'custom';
  attributes: EntityAttribute[];
  position?: { x: number; y: number }; // For visual editor
}

export interface EntityAttribute {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
  required: boolean;
  description?: string;
  default_value?: any;
}

export interface Role {
  id: string;
  domain_id: string;
  name: string;
  display_name: string;
  description: string;
  permissions: RolePermission[];
  function_bindings: FunctionBinding[];
}

export interface RolePermission {
  entity_id: string;
  actions: ('create' | 'read' | 'update' | 'delete' | 'execute')[];
}

export interface FunctionBinding {
  function_name: string;
  tool_id: string;
  parameters_mapping: Record<string, string>;
  access_gate?: AccessGate;
}

export interface AccessGate {
  id: string;
  name: string;
  condition: string; // Expression to evaluate
  required_roles: string[];
  required_permissions: string[];
}

export interface Application {
  id: string;
  domain_id: string;
  name: string;
  description: string;
  endpoints: string[]; // endpoint IDs
}

export interface Endpoint {
  id: string;
  application_id: string;
  domain_id: string;
  name: string;
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  description: string;
  request_schema?: any;
  response_schema?: any;
  function_binding_id?: string;
}

export interface Relationship {
  id: string;
  domain_id: string;
  from_entity_id: string;
  to_entity_id: string;
  type: 'has_many' | 'belongs_to' | 'has_one' | 'many_to_many' | 'depends_on';
  name: string;
  description?: string;
  cardinality: '1:1' | '1:N' | 'N:1' | 'N:N';
}

export interface DomainTemplate {
  id: string;
  name: string;
  description: string;
  category: 'banking' | 'healthcare' | 'ecommerce' | 'saas' | 'custom';
  dossier_json: any;
  verified: boolean;
  author: string;
  downloads: number;
}
