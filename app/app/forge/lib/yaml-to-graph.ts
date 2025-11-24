import { Node, Edge } from 'reactflow';
import yaml from 'js-yaml';

export interface YAMLToGraphResult {
  nodes: Node[];
  edges: Edge[];
  agentName: string;
  error?: string;
}

export function yamlToGraph(yamlString: string): YAMLToGraphResult {
  try {
    // Parse YAML
    const parsed = yaml.load(yamlString) as any;

    if (!parsed || typeof parsed !== 'object') {
      return {
        nodes: [],
        edges: [],
        agentName: 'untitled-agent',
        error: 'Invalid YAML: root must be an object',
      };
    }

    // Extract agent name
    const agentName = parsed.metadata?.name || 'untitled-agent';

    // Extract nodes
    const yamlNodes = parsed.spec?.graph?.nodes || [];
    const nodes: Node[] = yamlNodes.map((yamlNode: any, index: number) => {
      // Convert YAML node to React Flow node
      const node: Node = {
        id: yamlNode.id || `node-${index}`,
        type: yamlNode.type || 'process',
        position: {
          // Auto-layout: arrange in a grid
          x: (index % 3) * 250 + 100,
          y: Math.floor(index / 3) * 150 + 100,
        },
        data: {
          label: yamlNode.label || yamlNode.id,
          description: yamlNode.description || '',
        },
      };

      // Add type-specific data
      switch (yamlNode.type) {
        case 'process':
          node.data = {
            ...node.data,
            model: yamlNode.model || 'gpt-4o-mini',
            temperature: yamlNode.temperature || 0.7,
            maxTokens: yamlNode.max_tokens || 1000,
          };
          break;

        case 'toolCall':
          node.data = {
            ...node.data,
            tool: yamlNode.tool || '',
            parameters: yamlNode.parameters || {},
          };
          break;

        case 'decision':
          node.data = {
            ...node.data,
            conditions: yamlNode.conditions || [],
          };
          break;
      }

      return node;
    });

    // Extract edges
    const yamlEdges = parsed.spec?.graph?.edges || [];
    const edges: Edge[] = yamlEdges.map((yamlEdge: any, index: number) => {
      return {
        id: yamlEdge.id || `edge-${index}`,
        source: yamlEdge.source,
        target: yamlEdge.target,
        sourceHandle: yamlEdge.sourceHandle || undefined,
        targetHandle: yamlEdge.targetHandle || undefined,
        label: yamlEdge.label || undefined,
        animated: true,
      };
    });

    return {
      nodes,
      edges,
      agentName,
    };
  } catch (error: any) {
    console.error('Error converting YAML to graph:', error);
    return {
      nodes: [],
      edges: [],
      agentName: 'untitled-agent',
      error: `Failed to parse YAML: ${error.message}`,
    };
  }
}

/**
 * Auto-layout nodes using a simple force-directed approach
 */
export function autoLayoutNodes(nodes: Node[], edges: Edge[]): Node[] {
  // Simple hierarchical layout
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const visited = new Set<string>();
  const levels = new Map<string, number>();

  // Find entry points (nodes with no incoming edges)
  const entryPoints = nodes.filter((node) => !edges.some((edge) => edge.target === node.id));

  // BFS to assign levels
  const queue = entryPoints.map((n) => ({ id: n.id, level: 0 }));
  while (queue.length > 0) {
    const { id, level } = queue.shift()!;
    if (visited.has(id)) continue;

    visited.add(id);
    levels.set(id, level);

    // Add children
    const children = edges
      .filter((e) => e.source === id)
      .map((e) => ({ id: e.target, level: level + 1 }));
    queue.push(...children);
  }

  // Count nodes per level
  const levelCounts = new Map<number, number>();
  levels.forEach((level) => {
    levelCounts.set(level, (levelCounts.get(level) || 0) + 1);
  });

  // Position nodes
  const levelIndexes = new Map<number, number>();
  return nodes.map((node) => {
    const level = levels.get(node.id) || 0;
    const levelIndex = levelIndexes.get(level) || 0;
    levelIndexes.set(level, levelIndex + 1);

    const levelCount = levelCounts.get(level) || 1;
    const xOffset = (levelIndex - (levelCount - 1) / 2) * 250;

    return {
      ...node,
      position: {
        x: 400 + xOffset,
        y: 100 + level * 150,
      },
    };
  });
}
