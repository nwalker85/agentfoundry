/**
 * Graph to Python LangGraph Converter
 * Converts ReactFlow graph to executable Python LangGraph code
 */

import { Node, Edge } from 'reactflow';
import type { StateSchema, TriggerDefinition } from '@/types';

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

interface GraphToPythonOptions {
  stateSchema?: StateSchema | null;
  triggers?: TriggerDefinition[];
}

/**
 * Convert ReactFlow graph to Python LangGraph code
 */
export function graphToPython(
  nodes: Node[],
  edges: Edge[],
  agentName: string,
  options: GraphToPythonOptions = {}
): string {
  const { stateSchema = null, triggers = [] } = options;

  if (nodes.length === 0) {
    return '# No nodes to generate code from\n';
  }

  // Find entry point
  const entryNode = nodes.find((n) => n.type === 'entryPoint');
  if (!entryNode) {
    return '# Error: No entry point node found\n';
  }

  const code: string[] = [];

  // Header
  code.push('"""');
  code.push(`${agentName} - LangGraph Agent`);
  code.push('Auto-generated from Agent Foundry visual designer');
  code.push('"""');
  code.push('');
  if (stateSchema) {
    code.push(`# State Schema: ${stateSchema.name} v${stateSchema.version}`);
  }
  if (triggers.length > 0) {
    code.push('# Triggers:');
    triggers.forEach((trigger) => {
      code.push(`# - ${trigger.type?.toUpperCase?.() || 'CUSTOM'} :: ${trigger.name}`);
    });
  }
  code.push('');

  // Check if we have ReAct agents (need special imports)
  const hasReActAgent = nodes.some((n) => n.type === 'reactAgent');
  const hasHumanNode = nodes.some((n) => n.type === 'human');

  // Imports
  code.push('from typing import TypedDict, Annotated, Sequence');
  code.push('from langchain_core.messages import BaseMessage, HumanMessage');
  code.push('from langchain_openai import ChatOpenAI');
  code.push('from langchain_anthropic import ChatAnthropic');
  code.push('from langgraph.graph import StateGraph, END');
  code.push('from langgraph.prebuilt import ToolNode');
  if (hasReActAgent) {
    code.push('from langgraph.prebuilt import create_react_agent');
  }
  if (hasHumanNode) {
    code.push('from langgraph.graph import interrupt');
  }
  code.push('import operator');
  code.push('');

  // State definition
  code.push('# State definition');
  code.push('class AgentState(TypedDict):');
  code.push('    """State schema for the agent"""');
  if (stateSchema?.fields?.length) {
    stateSchema.fields.forEach((field) => {
      const pythonType = getPythonType(field.type);
      if (field.reducer && field.reducer !== 'replace') {
        code.push(
          `    ${field.name}: Annotated[${pythonType}, ${getReducerOperator(field.reducer)}]`
        );
      } else {
        code.push(`    ${field.name}: ${pythonType}`);
      }
    });
  } else {
    code.push('    messages: Annotated[Sequence[BaseMessage], operator.add]');
    code.push('    next_node: str');
  }
  code.push('');

  // Node functions
  code.push('# Node implementations');
  code.push('');

  // Generate function for each node
  for (const node of nodes) {
    if (node.type === 'entryPoint') {
      continue; // Entry point doesn't need a function
    }

    const functionName = getFunctionName(node);
    const nodeData = node.data;

    code.push(`def ${functionName}(state: AgentState) -> AgentState:`);
    code.push(`    """${nodeData.description || nodeData.label || 'Node function'}"""`);

    if (node.type === 'process') {
      // Process node with LLM
      const modelVar = getModelVariable(nodeData.model);
      code.push(`    `);
      code.push(`    # Initialize ${nodeData.model || 'LLM'}`);
      code.push(`    llm = ${modelVar}(`);
      code.push(`        temperature=${nodeData.temperature || 0.7},`);
      code.push(`        max_tokens=${nodeData.maxTokens || 1000},`);
      code.push(`    )`);
      code.push(`    `);
      code.push(`    # Process with LLM`);
      code.push(`    response = llm.invoke(state["messages"])`);
      code.push(`    `);
      code.push(`    return {`);
      code.push(`        "messages": [response],`);
      code.push(`        "next_node": "${getNextNode(node.id, edges) || 'END'}"`);
      code.push(`    }`);
    } else if (node.type === 'toolCall') {
      // Tool call node
      code.push(`    `);
      code.push(`    # Call tool: ${nodeData.tool || 'unknown'}`);
      code.push(`    # TODO: Implement tool call logic`);
      code.push(`    `);
      code.push(`    return {`);
      code.push(`        "messages": state["messages"],`);
      code.push(`        "next_node": "${getNextNode(node.id, edges) || 'END'}"`);
      code.push(`    }`);
    } else if (node.type === 'decision') {
      // Decision node with conditions
      code.push(`    `);
      code.push(`    # Decision logic`);
      if (nodeData.conditions && nodeData.conditions.length > 0) {
        for (const condition of nodeData.conditions) {
          const operator = condition.operator || '==';
          code.push(`    if state.get("${condition.field}") ${operator} "${condition.value}":`);
          code.push(`        return {"next_node": "${condition.target || 'END'}"}`);
        }
      }
      code.push(`    `);
      code.push(`    # Default path`);
      code.push(`    return {`);
      code.push(`        "messages": state["messages"],`);
      code.push(`        "next_node": "${getNextNode(node.id, edges) || 'END'}"`);
      code.push(`    }`);
    } else if (node.type === 'router') {
      // Router node with conditional routing
      code.push(`    `);
      code.push(`    # Router logic (${nodeData.routing_logic || 'conditional'})`);
      const routes = nodeData.routes || [];
      if (routes.length > 0) {
        for (let i = 0; i < routes.length; i++) {
          const route = routes[i];
          const condition = route.condition || `intent == '${route.name}'`;
          if (i === 0) {
            code.push(`    if ${condition}:`);
          } else {
            code.push(`    elif ${condition}:`);
          }
          code.push(`        return {"next_node": "${route.target || route.name || 'END'}"}`);
        }
        code.push(`    else:`);
        code.push(`        # Default route`);
        code.push(`        return {"next_node": "${getNextNode(node.id, edges) || 'END'}"}`);
      } else {
        code.push(`    # No routes defined`);
        code.push(`    return {"next_node": "${getNextNode(node.id, edges) || 'END'}"}`);
      }
    } else if (node.type === 'parallelGateway') {
      // Parallel gateway - fan out to multiple branches
      code.push(`    `);
      code.push(`    # Parallel execution - fan out to branches`);
      code.push(`    # Note: LangGraph will execute all branches in parallel`);
      code.push(`    return state`);
    } else if (node.type === 'human') {
      // Human-in-the-loop node
      code.push(`    `);
      code.push(`    # Human-in-the-loop: pause for human input`);
      code.push(`    # Prompt: ${nodeData.prompt || 'Please provide input'}`);
      code.push(`    # TODO: Implement interrupt() or human input mechanism`);
      code.push(`    # For now, we'll use a placeholder`);
      code.push(`    from langgraph.graph import interrupt`);
      code.push(`    `);
      code.push(`    user_input = interrupt("${nodeData.prompt || 'Please provide input'}")`);
      code.push(`    `);
      code.push(`    return {`);
      code.push(`        "messages": state["messages"] + [HumanMessage(content=user_input)],`);
      code.push(`        "next_node": "${getNextNode(node.id, edges) || 'END'}"`);
      code.push(`    }`);
    } else if (node.type === 'reactAgent') {
      // ReAct Agent - special composite node
      code.push(`    `);
      code.push(`    # ReAct Agent: LLM + Tools + Feedback Loop`);
      code.push(`    # This uses LangGraph's built-in create_react_agent`);
      code.push(`    # Tools: ${nodeData.tools?.map((t: any) => t.name).join(', ') || 'none'}`);
      code.push(`    # Max iterations: ${nodeData.max_iterations || 10}`);
      code.push(`    return state  # ReAct agent handles its own loop`);
    } else if (node.type === 'end') {
      // End node
      code.push(`    `);
      code.push(`    # Terminate workflow`);
      code.push(`    return state`);
    }

    code.push('');
    code.push('');
  }

  // Build graph
  code.push('# Build the agent graph');
  code.push('def create_agent():');
  code.push('    """Create and compile the agent graph"""');
  code.push('    workflow = StateGraph(AgentState)');
  code.push('    ');

  // Add nodes
  code.push('    # Add nodes');
  for (const node of nodes) {
    if (node.type === 'entryPoint') {
      continue;
    }
    const functionName = getFunctionName(node);

    // ReAct agents need special initialization
    if (node.type === 'reactAgent') {
      const nodeData = node.data;
      const modelClass = getModelVariable(nodeData.model);
      const toolNames = nodeData.tools?.map((t: any) => t.name).join(', ') || '';

      code.push(`    # ReAct Agent: ${functionName}`);
      code.push(
        `    ${functionName}_llm = ${modelClass}(model="${nodeData.model || 'gpt-4o-mini'}")`
      );
      code.push(`    ${functionName}_tools = [${toolNames}]  # Define your tools here`);
      code.push(`    ${functionName}_agent = create_react_agent(`);
      code.push(`        model=${functionName}_llm,`);
      code.push(`        tools=${functionName}_tools,`);
      code.push(`        max_iterations=${nodeData.max_iterations || 10}`);
      code.push(`    )`);
      code.push(`    workflow.add_node("${functionName}", ${functionName}_agent)`);
    } else {
      code.push(`    workflow.add_node("${functionName}", ${functionName})`);
    }
  }
  code.push('    ');

  // Set entry point
  code.push('    # Set entry point');
  const firstNode = getNextNode(entryNode.id, edges);
  if (firstNode) {
    const firstNodeObj = nodes.find((n) => n.id === firstNode);
    if (firstNodeObj) {
      code.push(`    workflow.set_entry_point("${getFunctionName(firstNodeObj)}")`);
    }
  }
  code.push('    ');

  // Add edges
  code.push('    # Add edges');
  for (const edge of edges) {
    const sourceNode = nodes.find((n) => n.id === edge.source);
    const targetNode = nodes.find((n) => n.id === edge.target);
    if (sourceNode && targetNode && sourceNode.type !== 'entryPoint') {
      const sourceName = getFunctionName(sourceNode);
      const targetName = targetNode.type === 'end' ? 'END' : getFunctionName(targetNode);
      code.push(`    workflow.add_edge("${sourceName}", "${targetName}")`);
    }
  }
  code.push('    ');

  // Compile
  code.push('    # Compile the graph');
  code.push('    app = workflow.compile()');
  code.push('    return app');
  code.push('');
  code.push('');

  // Main execution
  code.push('# Initialize and run');
  code.push('if __name__ == "__main__":');
  code.push('    agent = create_agent()');
  code.push('    ');
  code.push('    # Example usage');
  if (stateSchema?.initialState && Object.keys(stateSchema.initialState).length > 0) {
    const initialStateString = JSON.stringify(stateSchema.initialState, null, 8);
    code.push('    initial_state = ' + initialStateString.replace(/\n/g, '\n    '));
  } else {
    code.push('    initial_state = {');
    code.push('        "messages": [],');
    code.push('        "next_node": ""');
    code.push('    }');
  }
  code.push('    ');
  code.push('    result = agent.invoke(initial_state)');
  code.push('    print("Agent execution complete")');
  code.push('    print(result)');
  code.push('');

  return code.join('\n');
}

/**
 * Validate generated Python code
 */
export function validatePython(code: string): ValidationResult {
  const errors: string[] = [];

  if (!code || code.trim() === '') {
    errors.push('No code generated');
    return { valid: false, errors };
  }

  // Basic validation checks
  if (!code.includes('StateGraph')) {
    errors.push('Missing StateGraph import or usage');
  }

  if (!code.includes('class AgentState')) {
    errors.push('Missing AgentState definition');
  }

  if (!code.includes('def create_agent')) {
    errors.push('Missing create_agent function');
  }

  // Check for common syntax issues (basic)
  const lines = code.split('\n');
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Check for unbalanced quotes
    const singleQuotes = (line.match(/'/g) || []).length;
    const doubleQuotes = (line.match(/"/g) || []).length;

    if (singleQuotes % 2 !== 0 && !line.trim().startsWith('#')) {
      errors.push(`Line ${i + 1}: Unbalanced single quotes`);
    }
    if (doubleQuotes % 2 !== 0 && !line.trim().startsWith('#')) {
      errors.push(`Line ${i + 1}: Unbalanced double quotes`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Helper: Get function name from node
 */
function getFunctionName(node: Node): string {
  const label = node.data.label || node.type;
  // Convert to snake_case and make it a valid Python identifier
  return (
    label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .replace(/_{2,}/g, '_') || `node_${node.id.replace(/[^a-z0-9]/g, '')}`
  );
}

/**
 * Helper: Get model initialization code
 */
function getModelVariable(model: string): string {
  if (!model) return 'ChatOpenAI';

  if (model.includes('claude')) {
    return 'ChatAnthropic';
  }
  return 'ChatOpenAI';
}

/**
 * Helper: Get next node ID from edges
 */
function getNextNode(nodeId: string, edges: Edge[]): string | null {
  const edge = edges.find((e) => e.source === nodeId);
  return edge ? edge.target : null;
}

function getPythonType(fieldType: string): string {
  switch (fieldType) {
    case 'string':
      return 'str';
    case 'int':
      return 'int';
    case 'float':
      return 'float';
    case 'bool':
      return 'bool';
    case 'list':
      return 'list';
    case 'dict':
      return 'dict';
    case 'json':
      return 'dict';
    case 'message':
      return 'Sequence[BaseMessage]';
    default:
      return 'dict';
  }
}

function getReducerOperator(reducer?: string): string {
  switch (reducer) {
    case 'add':
      return 'operator.add';
    case 'merge':
      return 'operator.or_';
    case 'sum':
      return 'operator.add';
    default:
      return 'operator.add';
  }
}
