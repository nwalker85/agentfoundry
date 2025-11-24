import { NextRequest, NextResponse } from 'next/server';

/**
 * HTTP Fallback Chat Endpoint
 *
 * Used when WebSocket connection is not available.
 * Forwards requests to the backend /api/agent/process endpoint.
 *
 * @route POST /api/chat
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, agentId, sessionId, messageHistory } = body;

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 });
    }

    if (!agentId) {
      return NextResponse.json({ error: 'Agent ID is required' }, { status: 400 });
    }

    // Use BACKEND_URL from environment (defined in .env.local)
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      throw new Error('BACKEND_URL not configured');
    }

    console.log(`[API /api/chat] Forwarding to ${backendUrl}/api/agent/invoke for agent ${agentId}`);

    const response = await fetch(`${backendUrl}/api/agent/invoke`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agent_id: agentId,
        input: message,
        session_id: sessionId,
        route_via_supervisor: true,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API /api/chat] Backend error ${response.status}:`, errorText);
      throw new Error(`Backend error: ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json({
      response: data.output,
      artifacts: data.artifacts || [],
      currentState: data.interrupted ? 'interrupted' : 'idle',
    });
  } catch (error) {
    console.error('[API /api/chat] Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}

// Health check endpoint
export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      return NextResponse.json(
        {
          status: 'misconfigured',
          error: 'BACKEND_URL not configured',
        },
        { status: 503 }
      );
    }

    // Check backend health
    const response = await fetch(`${backendUrl}/health`);

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json({
        status: 'healthy',
        backend: data,
        api_version: '1.0.0',
      });
    }

    return NextResponse.json({
      status: 'degraded',
      backend: 'unreachable',
      api_version: '1.0.0',
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
        api_version: '1.0.0',
      },
      { status: 503 }
    );
  }
}
