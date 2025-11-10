#!/bin/bash
# Start MCP Server for Engineering Department

echo "🚀 Starting Engineering Department MCP Server..."
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run: python3 -m venv venv"
    echo "   Then: source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check for .env.local
if [ ! -f ".env.local" ]; then
    echo "⚠️  Warning: .env.local not found!"
    echo "   Copy .env.example to .env.local and configure your tokens"
fi

# Kill any existing processes on port 8001
echo "🔍 Checking for existing processes on port 8001..."
lsof -ti:8001 | xargs -r kill -9 2>/dev/null

# Start the server
echo "📡 Starting MCP server on http://localhost:8001"
echo "   Press Ctrl+C to stop"
echo ""
python mcp_server.py
