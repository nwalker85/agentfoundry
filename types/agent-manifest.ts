import type { Environment } from './agent';

/**
 * Manifest entry describing how an agent is bound into the platform graph of
 * organizations, domains, and environments/instances.
 */
export interface AgentManifestEntry {
  // Identity
  agent_id: string;
  yaml_path: string;

  // Org / domain / instance binding
  organization_id: string;
  organization_name?: string;
  domain_id: string;
  domain_name?: string;
  environment: Environment; // dev / staging / prod
  instance_id: string; // logical instance within an environment (e.g. "dev", "us-east-1")

  // System vs customer agents
  is_system_agent: boolean;
  system_tier?: 0 | 1; // 0 = foundation, 1 = production; undefined for customer agents

  // Metadata
  version: string;
  author: string;
  last_editor: string;
  tags: string[];
}

export interface AgentManifest {
  apiVersion: string;
  kind: 'AgentManifest';
  metadata: {
    description?: string;
    generated_at: string;
    version: string;
  };
  spec: {
    entries: AgentManifestEntry[];
  };
}
