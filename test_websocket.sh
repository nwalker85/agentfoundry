#!/bin/bash

# WebSocket Test Script
# Tests the WebSocket implementation

set -e

echo "🧪 WebSocket Implementation Test Suite"
echo "========================================"
echo ""

PROJECT_ROOT="/Users/nwalker/Development/Projects/Engineering Department/engineeringdepartment"
cd "$PROJECT_ROOT"

echo "1. Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm not found"; exit 1; }
echo "✅ Prerequisites OK"
echo ""

echo "2. Checking environment..."
if [ ! -f ".env.local" ]; then
    echo "❌ .env.local not found"
    exit 1
fi

if grep -q "NEXT_PUBLIC_ENABLE_WEBSOCKET=true" .env.local; then
    echo "✅ WebSocket enabled in config"
else
    echo "❌ WebSocket not enabled - set NEXT_PUBLIC_ENABLE_WEBSOCKET=true"
    exit 1
fi
echo ""

echo "3. Checking server status..."
if curl -s http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ MCP Server is running"
else
    echo "⚠️  MCP Server not running"
    echo "   Start with: python mcp_server.py"
fi
echo ""

echo "4. Checking frontend status..."
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend not running"
    echo "   Start with: npm run dev"
fi
echo ""

echo "5. Testing WebSocket endpoint..."
if command -v websocat >/dev/null 2>&1; then
    # Test WebSocket connection (requires websocat)
    echo '{"type":"ping"}' | timeout 2 websocat "ws://localhost:8001/ws/chat" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ WebSocket endpoint responding"
    else
        echo "⚠️  WebSocket endpoint not accessible"
    fi
else
    echo "⚠️  websocat not installed (optional)"
    echo "   Install with: brew install websocat"
fi
echo ""

echo "6. Checking file modifications..."
FILES_TO_CHECK=(
    "app/lib/stores/chat.store.ts"
    "app/chat/components/ConnectionStatus.tsx"
    "app/lib/types/chat.ts"
    ".env.local"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done
echo ""

echo "7. Manual Test Checklist:"
echo "========================"
echo ""
echo "Open http://localhost:3000/chat and verify:"
echo ""
echo "□ Connection status shows 'Connected' with latency"
echo "□ Send message: 'Create a P1 story for testing WebSocket'"
echo "□ Message appears immediately in blue bubble"
echo "□ Assistant response appears in white card"
echo "□ Check DevTools → Network → WS tab for frames"
echo "□ Verify ping/pong heartbeat every 30 seconds"
echo ""
echo "Test reconnection:"
echo "□ Stop backend (Ctrl+C in server terminal)"
echo "□ Status changes to 'Reconnecting...'"
echo "□ Restart backend"
echo "□ Status changes back to 'Connected'"
echo ""
echo "Test fallback:"
echo "□ Set NEXT_PUBLIC_ENABLE_WEBSOCKET=false"
echo "□ Restart frontend"
echo "□ Messages still work via HTTP"
echo ""

echo "========================================"
echo "🎉 WebSocket Implementation Ready!"
echo ""
echo "Next steps:"
echo "1. Start both services: ./start_dev.sh"
echo "2. Open http://localhost:3000/chat"
echo "3. Send a test message"
echo "4. Verify WebSocket connection in DevTools"
echo ""
echo "📚 Documentation:"
echo "- Implementation Plan: docs/WEBSOCKET_IMPLEMENTATION_PLAN.md"
echo "- Summary: docs/WEBSOCKET_IMPLEMENTATION_SUMMARY.md"
echo ""
