#!/bin/bash
# Agent Foundry - Troubleshooting Script
set -e

PROJECT_ROOT="/Users/nwalker/Development/Projects/agentfoundry"
cd "$PROJECT_ROOT"

echo "🔍 Agent Foundry Diagnostics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Docker Status
echo ""
echo "1️⃣  Docker Status:"
if docker info >/dev/null 2>&1; then
    echo "   ✅ Docker is running"
else
    echo "   ❌ Docker is NOT running - Start Docker Desktop first!"
    exit 1
fi

# 2. Container Status
echo ""
echo "2️⃣  Container Status:"
docker compose ps

# 3. LiveKit Connectivity
echo ""
echo "3️⃣  LiveKit Connectivity:"
echo "   Testing HTTP on localhost:7880..."
if curl -sf -m 5 http://localhost:7880 >/dev/null 2>&1; then
    echo "   ✅ LiveKit HTTP responding"
else
    echo "   ❌ LiveKit HTTP not responding"
    echo ""
    echo "   Recent LiveKit logs:"
    docker compose logs livekit --tail=20
fi

# 4. Port Check
echo ""
echo "4️⃣  Port Status:"
for port in 7880 7881 6379 8000 8001 8002; do
    if lsof -i :$port >/dev/null 2>&1; then
        echo "   ✅ Port $port in use"
    else
        echo "   ❌ Port $port NOT in use"
    fi
done

# 5. Environment Variables
echo ""
echo "5️⃣  Environment Configuration:"
echo "   LIVEKIT_URL from .env: $(grep NEXT_PUBLIC_LIVEKIT_URL .env.local | cut -d '=' -f2)"
echo "   LIVEKIT_API_KEY: $(grep LIVEKIT_API_KEY .env | head -1 | cut -d '=' -f2)"

# 6. Recent Container Logs
echo ""
echo "6️⃣  Recent Container Logs:"
echo "   ─────────────────────────"
echo "   LiveKit:"
docker compose logs livekit --tail=10 2>&1 | sed 's/^/   /'
echo ""
echo "   Redis:"
docker compose logs redis --tail=5 2>&1 | sed 's/^/   /'
echo ""
echo "   Backend:"
docker compose logs foundry-backend --tail=5 2>&1 | sed 's/^/   /'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Common Fixes:"
echo "   • Restart services: docker compose restart"
echo "   • Full rebuild: docker compose down && docker compose up -d --build"
echo "   • View live logs: docker compose logs -f livekit"
echo ""
