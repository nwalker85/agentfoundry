/**
 * Format Converter: LangGraph Execution Format → ReactFlow Visual Format
 *
 * Converts agent definitions from LangGraph execution format (spec.workflow.nodes)
 * to ReactFlow visual format (spec.graph.nodes + spec.graph.edges) for UI rendering.
 */

interface LangGraphNode {
  id: string;
  handler: string;
  description?: string;
  next: string[];
  timeout_seconds?: number;
}

interface ReactFlowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    description?: string;
    handler?: string;
    timeout_seconds?: number;
    isLangGraphNode?: boolean;
    readonly?: boolean;
  };
}

interface ReactFlowEdge {
  id: string;
  source: string;
  target: string;
  animated?: boolean;
}

interface ConversionResult {
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
}

/**
 * Detect visual node type from handler path and node ID
 */
function detectNodeType(node: LangGraphNode, isEntryPoint: boolean): string {
  const nodeId = node.id.toLowerCase();
  const handler = node.handler?.toLowerCase() || '';

  // Entry point
  if (isEntryPoint) {
    return 'entryPoint';
  }

  // Human input nodes
  if (nodeId.includes('human_') || handler.includes('human_')) {
    return 'human';
  }

  // End/finalize nodes
  if (nodeId.includes('finalize') || nodeId.includes('end') || handler.includes('finalize')) {
    return 'end';
  }

  // Decision/classification nodes
  if (
    nodeId.includes('classify') ||
    nodeId.includes('decision') ||
    handler.includes('classify') ||
    handler.includes('decision')
  ) {
    return 'decision';
  }

  // Tool call nodes (if they exist in the future)
  if (nodeId.includes('tool') || handler.includes('tool')) {
    return 'toolCall';
  }

  // Default to process node
  return 'process';
}

/**
 * Format node label from ID (snake_case → Title Case)
 */
function formatNodeLabel(nodeId: string): string {
  return nodeId
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Generate grid layout positions
 * Simple grid pattern: 4 nodes per row, 300px horizontal spacing, 150px vertical spacing
 */
function generateGridPosition(index: number): { x: number; y: number } {
  const nodesPerRow = 4;
  const horizontalSpacing = 300;
  const verticalSpacing = 150;

  const row = Math.floor(index / nodesPerRow);
  const col = index % nodesPerRow;

  return {
    x: col * horizontalSpacing + 100,
    y: row * verticalSpacing + 100,
  };
}

/**
 * Convert LangGraph execution format to ReactFlow visual format
 */
export function convertLangGraphToReactFlow(
  langGraphNodes: LangGraphNode[],
  entryPoint?: string
): ConversionResult {
  const nodes: ReactFlowNode[] = [];
  const edges: ReactFlowEdge[] = [];

  // Convert nodes
  langGraphNodes.forEach((node, index) => {
    const isEntryPoint = node.id === entryPoint;
    const nodeType = detectNodeType(node, isEntryPoint);

    nodes.push({
      id: node.id,
      type: nodeType,
      position: generateGridPosition(index),
      data: {
        label: formatNodeLabel(node.id),
        description: node.description || '',
        handler: node.handler || '',
        timeout_seconds: node.timeout_seconds,
        // Mark as read-only LangGraph node
        isLangGraphNode: true,
        readonly: true,
      },
    });
  });

  // Generate edges from 'next' arrays
  langGraphNodes.forEach((node) => {
    if (node.next && Array.isArray(node.next)) {
      node.next.forEach((targetId, idx) => {
        // Skip END nodes (terminal state in LangGraph)
        if (targetId !== 'END' && targetId !== '__end__') {
          edges.push({
            id: `${node.id}-${targetId}-${idx}`,
            source: node.id,
            target: targetId,
            animated: true,
          });
        }
      });
    }
  });

  return { nodes, edges };
}

/**
 * Check if agent data uses LangGraph execution format
 */
export function isLangGraphFormat(agentData: any): boolean {
  return !!(
    agentData?.spec?.workflow?.nodes &&
    Array.isArray(agentData.spec.workflow.nodes) &&
    agentData.spec.workflow.nodes.length > 0
  );
}

/**
 * Check if agent data uses ReactFlow visual format
 */
export function isReactFlowFormat(agentData: any): boolean {
  return !!(
    agentData?.spec?.graph?.nodes &&
    Array.isArray(agentData.spec.graph.nodes) &&
    agentData.spec.graph.nodes.length > 0
  );
}
