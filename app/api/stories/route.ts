import { NextRequest, NextResponse } from 'next/server';

const MCP_SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    
    // Build request body for MCP server (it expects POST with JSON body)
    const requestBody: any = {
      limit: parseInt(searchParams.get('limit') || '50')
    };
    
    const priorities = searchParams.getAll('priorities');
    if (priorities.length > 0) {
      requestBody.priorities = priorities;
    }
    
    const statuses = searchParams.getAll('status');
    if (statuses.length > 0) {
      requestBody.status = statuses;
    }
    
    const epicTitle = searchParams.get('epic_title');
    if (epicTitle) {
      requestBody.epic_title = epicTitle;
    }
    
    // Call MCP server with POST method
    const url = `${MCP_SERVER_URL}/api/tools/notion/list-stories`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[Stories API] Error from MCP server:', errorText);
      return NextResponse.json(
        { error: `MCP server error: ${response.status}` },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    return NextResponse.json(data);
    
  } catch (error) {
    console.error('[Stories API] Error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to fetch stories' },
      { status: 500 }
    );
  }
}
