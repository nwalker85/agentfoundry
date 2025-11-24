import { Node, Edge } from 'reactflow';

/**
 * Converts ReactFlow graph to Mermaid flowchart syntax
 * Useful for documentation, exports, and visual representation
 */

// Map node types to Mermaid node shapes
const NODE_SHAPES: Record<string, { start: string; end: string }> = {
  entryPoint: { start: '([', end: '])' }, // Stadium shape for entry points
  process: { start: '[', end: ']' }, // Rectangle for process nodes
  decision: { start: '{', end: '}' }, // Diamond for decision nodes
  router: { start: '{', end: '}' }, // Diamond for routers
  human: { start: '[[', end: ']]' }, // Subroutine for human nodes
  toolCall: { start: '[/', end: '/]' }, // Parallelogram for tool calls
  reactAgent: { start: '>', end: ']' }, // Flag shape for react agents
  deepPlanner: { start: '[', end: ']' }, // Rectangle
  deepExecutor: { start: '[', end: ']' }, // Rectangle
  deepCritic: { start: '[', end: ']' }, // Rectangle
  subAgent: { start: '[(', end: ')]' }, // Cylinder for sub-agents
  contextManager: { start: '[', end: ']' }, // Rectangle
  parallelGateway: { start: '{{', end: '}}' }, // Hexagon for parallel
  end: { start: '([', end: '])' }, // Stadium for end nodes
};

// Get node shape wrapper
function getNodeShape(nodeType: string): { start: string; end: string } {
  return NODE_SHAPES[nodeType] || { start: '[', end: ']' };
}

// Sanitize text for Mermaid (escape special characters)
function sanitizeText(text: string): string {
  if (!text) return 'Node';
  return text
    .replace(/"/g, '#quot;')
    .replace(/\n/g, '<br/>')
    .replace(/\[/g, '#91;')
    .replace(/\]/g, '#93;')
    .replace(/\{/g, '#123;')
    .replace(/\}/g, '#125;');
}

// Get node style class based on type
function getNodeClass(nodeType: string): string {
  const classMap: Record<string, string> = {
    entryPoint: 'entry',
    process: 'process',
    decision: 'decision',
    router: 'decision',
    human: 'human',
    toolCall: 'tool',
    reactAgent: 'agent',
    deepPlanner: 'deep',
    deepExecutor: 'deep',
    deepCritic: 'deep',
    subAgent: 'subagent',
    contextManager: 'context',
    parallelGateway: 'parallel',
    end: 'end',
  };
  return classMap[nodeType] || 'default';
}

/**
 * Convert ReactFlow graph to Mermaid flowchart
 */
export function graphToMermaid(
  nodes: Node[],
  edges: Edge[],
  options?: {
    direction?: 'TD' | 'LR' | 'RL' | 'BT'; // Top-Down, Left-Right, Right-Left, Bottom-Top
    includeDescriptions?: boolean;
    includeMetadata?: boolean;
  }
): string {
  const direction = options?.direction || 'TD';
  const includeDescriptions = options?.includeDescriptions ?? false;
  const includeMetadata = options?.includeMetadata ?? false;

  let mermaid = `flowchart ${direction}\n`;

  // Add nodes
  nodes.forEach((node) => {
    const shape = getNodeShape(node.type || 'process');
    const label = sanitizeText(node.data.label || node.id);
    const nodeClass = getNodeClass(node.type || 'process');

    // Basic node definition
    mermaid += `    ${node.id}${shape.start}"${label}"${shape.end}\n`;

    // Add node class for styling
    mermaid += `    class ${node.id} ${nodeClass}\n`;

    // Add description as a note if enabled
    if (includeDescriptions && node.data.description) {
      const desc = sanitizeText(node.data.description);
      mermaid += `    note${node.id}["📝 ${desc}"]\n`;
      mermaid += `    ${node.id} -.- note${node.id}\n`;
    }

    // Add Python implementation indicator if handler exists
    if (includeMetadata && node.data.handler) {
      mermaid += `    impl${node.id}["🐍 Python"]\n`;
      mermaid += `    ${node.id} -.- impl${node.id}\n`;
    }
  });

  // Add edges
  edges.forEach((edge) => {
    const label = edge.label ? `|${sanitizeText(String(edge.label))}|` : '';
    const sourceHandle = edge.sourceHandle || '';
    const targetHandle = edge.targetHandle || '';

    // Standard arrow connection
    mermaid += `    ${edge.source} -->${label} ${edge.target}\n`;
  });

  // Add style definitions
  mermaid += '\n    %% Style definitions\n';
  mermaid += `    classDef entry fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef process fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef decision fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef human fill:#06b6d4,stroke:#0891b2,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef tool fill:#8b5cf6,stroke:#7c3aed,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef agent fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef deep fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef subagent fill:#14b8a6,stroke:#0d9488,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef context fill:#a855f7,stroke:#9333ea,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef parallel fill:#f97316,stroke:#ea580c,stroke-width:2px,color:#fff\n`;
  mermaid += `    classDef end fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff\n`;

  return mermaid;
}

/**
 * Generate a simplified Mermaid diagram focusing on main flow
 */
export function graphToSimpleMermaid(nodes: Node[], edges: Edge[]): string {
  return graphToMermaid(nodes, edges, {
    direction: 'TD',
    includeDescriptions: false,
    includeMetadata: false,
  });
}

/**
 * Generate a detailed Mermaid diagram with all metadata
 */
export function graphToDetailedMermaid(nodes: Node[], edges: Edge[]): string {
  return graphToMermaid(nodes, edges, {
    direction: 'TD',
    includeDescriptions: true,
    includeMetadata: true,
  });
}

/**
 * Export Mermaid diagram as downloadable file content
 */
export function exportMermaidDiagram(
  nodes: Node[],
  edges: Edge[],
  agentName: string,
  detailed: boolean = false
): string {
  const mermaid = detailed
    ? graphToDetailedMermaid(nodes, edges)
    : graphToSimpleMermaid(nodes, edges);

  const header = `# ${agentName} - Agent Flow Diagram\n\n`;
  const instructions = `<!-- Copy the code below and paste into https://mermaid.live for visualization -->\n\n`;
  const footer = `\n\n<!-- Generated by Agent Foundry Forge -->\n`;

  return `${header}${instructions}\`\`\`mermaid\n${mermaid}\`\`\`${footer}`;
}
