/**
 * Debugging Prompts for MCP Server
 * ---------------------------------
 * Pre-built prompts for debugging agent errors and performance issues.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { getServiceUrl } from '../config/services.js';

/**
 * Register debugging prompts
 */
export async function registerDebugPrompts(server: Server) {
  const currentHandler = server.requestHandlers.get('prompts/get');

  server.setRequestHandler('prompts/get', async (request) => {
    const name = request.params.name;
    const args = request.params.arguments || {};

    // ========================================================================
    // Prompt: debug_agent_error
    // ========================================================================

    if (name === 'debug_agent_error') {
      const { agent_id, error_message, session_id } = args as any;

      if (!agent_id || !error_message) {
        throw new Error('agent_id and error_message are required');
      }

      try {
        // Fetch agent configuration
        const agentUrl = `${getServiceUrl('backend')}/api/agents/${agent_id}`;
        const agentResponse = await fetch(agentUrl);
        const agent = await agentResponse.json();

        // Fetch session activities if provided
        let activities = '';
        if (session_id) {
          try {
            const actUrl = `${getServiceUrl('backend')}/api/monitoring/sessions/${session_id}/activities?limit=20`;
            const actResponse = await fetch(actUrl);
            const actData = await actResponse.json();
            activities = JSON.stringify(actData.activities, null, 2);
          } catch (error) {
            activities = 'Unable to fetch session activities';
          }
        }

        const debugPrompt = `Debug this LangGraph agent error:

**Agent:** ${agent.name} (${agent_id})
**Error:** ${error_message}

**Agent Configuration:**
\`\`\`json
${JSON.stringify(agent, null, 2)}
\`\`\`

${activities ? `**Recent Activities:**\n\`\`\`json\n${activities}\n\`\`\`` : ''}

**Analysis Required:**
1. **Root Cause**: What caused this error?
2. **Affected Component**: Which node, edge, or tool is problematic?
3. **Fix Strategy**: How to resolve this issue?
4. **Code Changes**: Specific YAML/Python changes needed
5. **Prevention**: How to prevent this in the future?
6. **Testing**: How to verify the fix works?

Provide concrete, actionable recommendations with code examples.`;

        return {
          description: 'Analyze and fix agent execution errors',
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: debugPrompt,
              },
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to create debug prompt: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // ========================================================================
    // Prompt: analyze_performance
    // ========================================================================

    if (name === 'analyze_performance') {
      const { agent_id, session_id } = args as any;

      if (!agent_id) {
        throw new Error('agent_id is required');
      }

      try {
        // Fetch agent metrics
        const metricsUrl = `${getServiceUrl('backend')}/api/agents/${agent_id}/status`;
        const metricsResponse = await fetch(metricsUrl);
        const metrics = await metricsResponse.json();

        const perfPrompt = `Analyze the performance of this LangGraph agent:

**Agent:** ${metrics.name} (${agent_id})

**Metrics:**
- Uptime: ${metrics.uptime_seconds}s
- Total Executions: ${metrics.total_executions}
- Success Rate: ${metrics.success_rate}%
- State: ${metrics.state}

**Analysis Required:**
1. **Performance Issues**: Identify bottlenecks and slow operations
2. **Success Rate**: Why is it ${metrics.success_rate}%? What's failing?
3. **Optimization Opportunities**: How to make it faster?
4. **Resource Usage**: Is it using too much memory/CPU?
5. **Recommendations**: Specific improvements to implement

${session_id ? `Session ID for detailed analysis: ${session_id}` : ''}

Provide specific, measurable recommendations with expected improvements.`;

        return {
          description: 'Analyze agent performance and suggest optimizations',
          messages: [
            {
              role: 'user',
              content: {
                type: 'text',
                text: perfPrompt,
              },
            },
          ],
        };
      } catch (error) {
        throw new Error(
          `Failed to create performance analysis prompt: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }

    // Delegate to existing handler
    if (currentHandler) {
      return await currentHandler(request);
    }

    throw new Error(`Unknown prompt: ${name}`);
  });

  // Add to prompt list
  const currentListHandler = server.requestHandlers.get('prompts/list');

  server.setRequestHandler('prompts/list', async (request) => {
    const existingPrompts = currentListHandler
      ? await currentListHandler(request)
      : { prompts: [] };

    const debugPrompts = [
      {
        name: 'debug_agent_error',
        description: 'Analyze and fix agent execution errors with detailed context',
        arguments: [
          {
            name: 'agent_id',
            description: 'Agent ID that encountered the error',
            required: true,
          },
          {
            name: 'error_message',
            description: 'Error message from execution',
            required: true,
          },
          {
            name: 'session_id',
            description: 'Session ID for additional context (optional)',
            required: false,
          },
        ],
      },
      {
        name: 'analyze_performance',
        description: 'Analyze agent performance metrics and suggest optimizations',
        arguments: [
          {
            name: 'agent_id',
            description: 'Agent ID to analyze',
            required: true,
          },
          {
            name: 'session_id',
            description: 'Specific session to analyze (optional)',
            required: false,
          },
        ],
      },
    ];

    return {
      prompts: [...(existingPrompts.prompts || []), ...debugPrompts],
    };
  });
}
