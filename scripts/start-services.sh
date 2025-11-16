#!/bin/bash
# Agent Foundry - Start All Services
set -e

PROJECT_ROOT="/Users/nwalker/Development/Projects/agentfoundry"
cd "$PROJECT_ROOT"

echo "🚀 Starting Agent Foundry Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# 2. Pull LiveKit image if needed
echo "📦 Pulling LiveKit image..."
docker pull livekit/livekit-server:latest

# 3. Stop any existing services
echo "🛑 Stopping existing services..."
docker compose down 2>/dev/null || true

# 4. Start services
echo "▶️  Starting Docker Compose stack..."
docker compose up -d

# 5. Wait for services to start
echo "⏳ Waiting for services to initialize (30 seconds)..."
sleep 30

# 6. Check service status
echo ""
echo "📊 Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose ps

# 7. Verify LiveKit health
echo ""
echo "🎙️  LiveKit Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -sf http://localhost:7880 >/dev/null; then
    echo "✅ LiveKit is responding on http://localhost:7880"
else
    echo "❌ LiveKit is not responding"
    echo ""
    echo "LiveKit Logs:"
    docker compose logs livekit --tail=50
    exit 1
fi

# 8. Verify Redis
echo ""
echo "💾 Redis Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker compose exec redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is not responding"
    exit 1
fi

# 9. Check backend
echo ""
echo "🔧 Backend Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend is responding on http://localhost:8000"
else
    echo "⚠️  Backend may still be starting..."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Agent Foundry Services Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Next Steps:"
echo "   1. Start frontend: cd $PROJECT_ROOT && npm run dev"
echo "   2. Open chat UI: http://localhost:3000/chat"
echo "   3. Test voice: Click 'Enable Voice' in the chat"
echo ""
echo "🔍 Monitoring:"
echo "   • View logs: docker compose logs -f"
echo "   • LiveKit logs: docker compose logs -f livekit"
echo "   • Backend logs: docker compose logs -f foundry-backend"
echo ""
