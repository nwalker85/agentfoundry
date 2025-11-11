#!/bin/bash

# Start Engineering Department Development Environment
# Day 1 Frontend Implementation

echo "🚀 Starting Engineering Department Development Environment..."
echo ""

# Check if we're in the right directory
if [ ! -f "mcp_server.py" ]; then
    echo "❌ Error: Not in the Engineering Department directory"
    echo "Please run this script from: /Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
    exit 1
fi

# Function to check if port is in use
check_port() {
    lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null
}

echo "📋 Checking prerequisites..."

# Check Python environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Check Node modules
if [ ! -d "node_modules" ]; then
    echo "⚠️  Node modules not found. Installing..."
    npm install
fi

echo ""
echo "🔍 Checking port availability..."

if check_port 8001; then
    echo "⚠️  Port 8001 is already in use (MCP Server)"
    echo "   Run: lsof -i :8001 to see what's using it"
else
    echo "✅ Port 8001 is available"
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use (Next.js)"
    echo "   Run: lsof -i :3000 to see what's using it"
else
    echo "✅ Port 3000 is available"
fi

echo ""
echo "📝 Starting services in separate terminals..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Open 2 terminal windows and run:"
echo ""
echo "Terminal 1 - MCP Server:"
echo "  cd \"$(pwd)\""
echo "  source venv/bin/activate"
echo "  python mcp_server.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd \"$(pwd)\""
echo "  npm run dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Once both services are running:"
echo "  🌐 Visit: http://localhost:3000/chat"
echo "  📊 MCP Status: http://localhost:8001/"
echo "  🔧 API Health: http://localhost:3000/api/chat (GET)"
echo ""
echo "Test message examples:"
echo "  - \"Create a story for adding a healthcheck endpoint\""
echo "  - \"I need to build a user authentication system\""
echo "  - \"Help me plan a microservices migration\""
echo ""
echo "💡 Tip: Check ./logs/ for audit trails and debugging"
echo ""
