import { NextRequest, NextResponse } from 'next/server';

const MCP_SERVER_URL = process.env.MCP_SERVER_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, sessionId, messageHistory } = body;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Forward request to MCP server
    const response = await fetch(`${MCP_SERVER_URL}/api/agent/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId || 'default',
        message_history: messageHistory || []
      }),
    });

    if (!response.ok) {
      console.error('MCP server error:', response.status, response.statusText);
      
      // Try to parse error response
      let errorMessage = 'Failed to process request';
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorMessage;
      } catch {
        // If response isn't JSON, use status text
        errorMessage = `MCP server error: ${response.statusText}`;
      }

      return NextResponse.json(
        { error: errorMessage },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Transform response for frontend
    const transformedResponse = {
      response: data.response || 'Processing your request...',
      artifacts: data.artifacts || [],
      requiresClarification: data.requires_clarification || false,
      clarificationPrompt: data.clarification_prompt,
      currentState: data.current_state,
      sessionId: data.session_id || sessionId
    };

    return NextResponse.json(transformedResponse);
    
  } catch (error) {
    console.error('API route error:', error);
    
    // Check if MCP server is unreachable
    if (error instanceof Error && error.message.includes('fetch')) {
      return NextResponse.json(
        { 
          error: 'Cannot connect to MCP server. Please ensure the server is running on port 8001.',
          details: error.message
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET(request: NextRequest) {
  try {
    // Check MCP server health
    const response = await fetch(`${MCP_SERVER_URL}/health`);
    
    if (response.ok) {
      const data = await response.json();
      return NextResponse.json({
        status: 'healthy',
        mcp_server: data,
        api_version: '1.0.0'
      });
    }

    return NextResponse.json({
      status: 'degraded',
      mcp_server: 'unreachable',
      api_version: '1.0.0'
    });
    
  } catch (error) {
    return NextResponse.json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
      api_version: '1.0.0'
    }, { status: 503 });
  }
}
