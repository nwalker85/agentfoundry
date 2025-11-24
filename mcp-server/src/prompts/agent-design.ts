/**
 * Agent Design Prompts for MCP Server
 * ------------------------------------
 * Pre-built prompt templates for designing LangGraph agents.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register agent design prompts
 */
export async function registerAgentPrompts(server: Server) {
  server.setRequestHandler('prompts/get', async (request) => {
    const name = request.params.name;
    const args = request.params.arguments || {};

    // ========================================================================
    // Prompt: create_agent_from_requirements
    // ========================================================================

    if (name === 'create_agent_from_requirements') {
      const { requirements, domain } = args as any;

      const systemPrompt = `You are an expert LangGraph agent designer for Agent Foundry.

Design a production-ready agent based on these requirements:

${requirements || 'No requirements provided'}

${domain ? `Domain: ${domain}` : ''}

Provide a complete agent design including:

1. **State Schema**: Define all state fields with types and reducers
2. **Nodes**: List each node with its purpose and logic
3. **Edges**: Define transitions between nodes (including conditional routing)
4. **Entry Point**: Specify where the workflow starts
5. **Error Handling**: Include error recovery strategies
6. **Tools**: List any external tools/APIs needed

Format your response as Agent YAML compatible with Forge visual designer:

\`\`\`yaml
metadata:
  id: agent-name
  name: Agent Name
  description: Brief description
  version: 1.0.0

spec:
  state_schema:
    fields:
      - name: messages
        type: list
        reducer: append
      - name: context
        type: dict
  
  workflow:
    type: graph
    entry_point: start
    
    nodes:
      - id: start
        type: function
        config:
          function: process_input
      
      - id: decision
        type: conditional
        config:
          condition: needs_approval
    
    edges:
      - source: start
        target: decision
      - source: decision
        target: end
        condition: approved
\`\`\``;

      return {
        description: 'Design a LangGraph agent from natural language requirements',
        messages: [
          {
            role: 'user',
            content: {
              type: 'text',
              text: systemPrompt,
            },
          },
        ],
      };
    }

    // ========================================================================
    // Prompt: refactor_agent_workflow
    // ========================================================================

    if (name === 'refactor_agent_workflow') {
      const { agent_id, improvement_goals } = args as any;

      if (!agent_id) {
        throw new Error('agent_id is required');
      }

      // Fetch current agent config
      try {
        const url = `${getServiceUrl('backend')}/api/agents/${agent_id}`;
        const response = await fetch(url);
        const agent = await response.json();

        const refactorPrompt = `Refactor this LangGraph agent workflow:

**Current Agent:**
${JSON.stringify(agent, null, 2)}

**Improvement Goals:**
${improvement_goals || 'Improve performance, error handling, and code quality'}

Provide:
1. Analysis of current workflow issues
2. Recommended changes
3. Updated YAML configuration
4. Migration strategy (if breaking changes)

Focus on:
- Reducing node complexity
- Adding error handling
- Improving conditional routing
- Optimizing tool calls`;

        return {
          description: 'Refactor an agent workflow for better performance and maintainability',
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: refactorPrompt,
              },
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to fetch agent for refactor prompt: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    throw new Error(`Unknown prompt: ${name}`);
  });

  // Register prompt list
  const currentListHandler = server.requestHandlers.get('prompts/list');

  server.setRequestHandler('prompts/list', async (request) => {
    const existingPrompts = currentListHandler
      ? await currentListHandler(request)
      : { prompts: [] };

    const agentPrompts = [
      {
        name: 'create_agent_from_requirements',
        description: 'Design a LangGraph agent from natural language requirements',
        arguments: [
          {
            name: 'requirements',
            description:
              'Natural language description of agent behavior, inputs, outputs, and workflow',
            required: true,
          },
          {
            name: 'domain',
            description: 'Business domain (e.g., "customer-service", "finance", "card-services")',
            required: false,
          },
        ],
      },
      {
        name: 'refactor_agent_workflow',
        description:
          'Refactor an existing agent workflow for better performance and maintainability',
        arguments: [
          {
            name: 'agent_id',
            description: 'ID of the agent to refactor',
            required: true,
          },
          {
            name: 'improvement_goals',
            description:
              'Specific goals for refactoring (e.g., "reduce latency", "add error handling")',
            required: false,
          },
        ],
      },
    ];

    return {
      prompts: [...(existingPrompts.prompts || []), ...agentPrompts],
    };
  });
}
