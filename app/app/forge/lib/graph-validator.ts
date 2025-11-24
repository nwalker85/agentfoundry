/**
 * Graph Validation Utility
 * Validates agent graphs for LangGraph compatibility
 */

import { Node, Edge } from 'reactflow';

export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  cycles: Cycle[];
}

export interface Cycle {
  nodes: string[];
  hasExitCondition: boolean;
  hasMaxIterations: boolean;
}

/**
 * Validate agent graph for LangGraph compatibility
 * Allows cycles but validates they have proper exit conditions
 */
export function validateAgentGraph(nodes: Node[], edges: Edge[]): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];

  // 1. Check for entry point
  const entryPoints = nodes.filter((n) => n.type === 'entryPoint');
  if (entryPoints.length === 0) {
    errors.push('No entry point node found. Add an Entry Point node.');
  } else if (entryPoints.length > 1) {
    errors.push('Multiple entry points found. Only one Entry Point is allowed.');
  }

  // 2. Check for reachability from entry point
  if (entryPoints.length === 1) {
    const reachable = getReachableNodes(entryPoints[0].id, nodes, edges);
    const unreachable = nodes.filter((n) => !reachable.has(n.id) && n.id !== entryPoints[0].id);

    if (unreachable.length > 0) {
      warnings.push(
        `${unreachable.length} node(s) unreachable from entry point: ${unreachable.map((n) => n.data.label || n.id).join(', ')}`
      );
    }
  }

  // 3. Detect cycles
  const cycles = detectCycles(nodes, edges);

  // 4. Validate cycles (must have exit conditions)
  for (const cycle of cycles) {
    const cycleNodes = nodes.filter((n) => cycle.nodes.includes(n.id));
    const hasRouter = cycleNodes.some((n) => n.type === 'router' || n.type === 'decision');
    const hasMaxIterCheck = cycleNodes.some(
      (n) =>
        n.data.max_iterations !== undefined ||
        n.data.conditions?.some((c: any) => c.field?.includes('iteration'))
    );

    if (!hasRouter && !hasMaxIterCheck) {
      errors.push(
        `Cycle detected without exit condition: ${cycle.nodes.join(' → ')}. Add a router/decision node or max_iterations check.`
      );
    } else {
      warnings.push(
        `Feedback loop detected: ${cycle.nodes.join(' → ')}. Ensure exit condition is properly configured.`
      );
    }
  }

  // 5. Check for dangling edges
  const nodeIds = new Set(nodes.map((n) => n.id));
  for (const edge of edges) {
    if (!nodeIds.has(edge.source)) {
      errors.push(`Edge references non-existent source node: ${edge.source}`);
    }
    if (!nodeIds.has(edge.target)) {
      errors.push(`Edge references non-existent target node: ${edge.target}`);
    }
  }

  // 6. Check for end nodes
  const endNodes = nodes.filter((n) => n.type === 'end');
  if (endNodes.length === 0) {
    warnings.push('No end node found. Workflow may not terminate properly.');
  }

  // 7. Validate router nodes have routes
  const routers = nodes.filter((n) => n.type === 'router');
  for (const router of routers) {
    if (!router.data.routes || router.data.routes.length === 0) {
      warnings.push(`Router "${router.data.label}" has no routes defined.`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    cycles,
  };
}

/**
 * Get all nodes reachable from a starting node (BFS)
 */
function getReachableNodes(startId: string, nodes: Node[], edges: Edge[]): Set<string> {
  const reachable = new Set<string>();
  const queue = [startId];
  reachable.add(startId);

  while (queue.length > 0) {
    const current = queue.shift()!;

    // Find all outgoing edges
    const outgoing = edges.filter((e) => e.source === current);

    for (const edge of outgoing) {
      if (!reachable.has(edge.target)) {
        reachable.add(edge.target);
        queue.push(edge.target);
      }
    }
  }

  return reachable;
}

/**
 * Detect cycles in the graph using DFS
 * Returns list of cycles found
 */
function detectCycles(nodes: Node[], edges: Edge[]): Cycle[] {
  const cycles: Cycle[] = [];
  const visited = new Set<string>();
  const recStack = new Set<string>();
  const path: string[] = [];

  const dfs = (nodeId: string) => {
    visited.add(nodeId);
    recStack.add(nodeId);
    path.push(nodeId);

    // Find all outgoing edges
    const outgoing = edges.filter((e) => e.source === nodeId);

    for (const edge of outgoing) {
      const target = edge.target;

      if (!visited.has(target)) {
        dfs(target);
      } else if (recStack.has(target)) {
        // Cycle detected
        const cycleStartIndex = path.indexOf(target);
        const cycleNodes = path.slice(cycleStartIndex);

        cycles.push({
          nodes: cycleNodes,
          hasExitCondition: false, // Will be validated later
          hasMaxIterations: false,
        });
      }
    }

    path.pop();
    recStack.delete(nodeId);
  };

  // Start DFS from all nodes
  for (const node of nodes) {
    if (!visited.has(node.id)) {
      dfs(node.id);
    }
  }

  return cycles;
}

/**
 * Check if graph is a DAG (Directed Acyclic Graph)
 */
export function isDAG(nodes: Node[], edges: Edge[]): boolean {
  const cycles = detectCycles(nodes, edges);
  return cycles.length === 0;
}

/**
 * Get node by ID
 */
export function getNodeById(nodeId: string, nodes: Node[]): Node | undefined {
  return nodes.find((n) => n.id === nodeId);
}
