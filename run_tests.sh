#!/bin/bash
# Run E2E Tests for Engineering Department

echo "🧪 Running Engineering Department E2E Tests..."
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if MCP server is running
if ! curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo "⚠️  MCP server not running!"
    echo "   Start it in another terminal with: ./start_server.sh"
    echo "   Or: python mcp_server.py"
    exit 1
fi

echo "✅ MCP server detected at http://localhost:8001"
echo ""

# Run the tests
python test_e2e.py
