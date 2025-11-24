import { Node, Edge } from 'reactflow';
import yaml from 'js-yaml';
import type { StateSchema, TriggerDefinition } from '@/types';

interface AgentYAML {
  apiVersion: string;
  kind: string;
  metadata: {
    name: string;
    labels?: {
      [key: string]: string;
    };
  };
  spec: {
    graph: {
      nodes: any[];
      edges: any[];
    };
    state_schema?: {
      [key: string]: string;
    };
    initial_state?: Record<string, unknown>;
    triggers?: any[];
  };
}

export function graphToYAML(
  nodes: Node[],
  edges: Edge[],
  agentName: string,
  options?: {
    stateSchema?: StateSchema | null;
    triggers?: TriggerDefinition[];
  }
): string {
  const stateSchema = options?.stateSchema;
  const triggers = options?.triggers ?? [];

  // Build the agent YAML structure
  const agentYAML: AgentYAML = {
    apiVersion: 'foundry.ai/v1',
    kind: 'Agent',
    metadata: {
      name: agentName || 'untitled-agent',
      labels: {
        app: 'agent-foundry',
        tier: 'worker',
      },
    },
    spec: {
      graph: {
        nodes: nodes.map((node) => {
          const baseNode: any = {
            id: node.id,
            type: node.type,
            label: node.data.label,
            description: node.data.description,
          };

          // Add type-specific fields
          switch (node.type) {
            case 'process':
              return {
                ...baseNode,
                model: node.data.model,
                temperature: node.data.temperature,
                max_tokens: node.data.maxTokens,
              };

            case 'toolCall':
              return {
                ...baseNode,
                tool: node.data.tool,
                parameters: node.data.parameters || {},
              };

            case 'decision':
              return {
                ...baseNode,
                conditions: node.data.conditions || [],
              };

            default:
              return baseNode;
          }
        }),
        edges: edges.map((edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
          label: edge.label,
        })),
      },
      state_schema: stateSchema
        ? stateSchema.fields.reduce<Record<string, string>>((acc, field) => {
            acc[field.name] = field.type;
            return acc;
          }, {})
        : {
            messages: 'list',
            context: 'dict',
            current_node: 'string',
          },
      initial_state: stateSchema?.initialState,
      triggers:
        triggers.length > 0
          ? triggers.map((trigger) => ({
              id: trigger.id,
              name: trigger.name,
              type: trigger.type,
              channel: trigger.channel,
              config: trigger.config,
            }))
          : undefined,
    },
  };

  // Convert to YAML
  try {
    return yaml.dump(agentYAML, {
      indent: 2,
      lineWidth: 100,
      noRefs: true,
    });
  } catch (error) {
    console.error('Error converting graph to YAML:', error);
    return '# Error generating YAML\n';
  }
}

export function validateYAML(yamlString: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  try {
    const parsed = yaml.load(yamlString) as any;

    // Validate required fields
    if (!parsed.apiVersion) errors.push('Missing apiVersion');
    if (!parsed.kind) errors.push('Missing kind');
    if (!parsed.metadata?.name) errors.push('Missing metadata.name');
    if (!parsed.spec?.graph) errors.push('Missing spec.graph');

    // Validate graph structure
    if (parsed.spec?.graph) {
      if (!Array.isArray(parsed.spec.graph.nodes)) {
        errors.push('spec.graph.nodes must be an array');
      }
      if (!Array.isArray(parsed.spec.graph.edges)) {
        errors.push('spec.graph.edges must be an array');
      }

      // Check for entry point
      const hasEntryPoint = parsed.spec.graph.nodes?.some((n: any) => n.type === 'entryPoint');
      if (!hasEntryPoint) {
        errors.push('Graph must have at least one entry point node');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
    };
  } catch (error: any) {
    return {
      valid: false,
      errors: [`YAML parsing error: ${error.message}`],
    };
  }
}
