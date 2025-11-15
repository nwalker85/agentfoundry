#!/bin/bash
# Agent Foundry - Start with Homebrew LiveKit
# Backend + Compiler in Docker, Frontend runs locally

set -e

echo "🏗️  Agent Foundry - Quick Start"
echo "================================"
echo ""

# Check if LiveKit is running
echo "🔍 Checking LiveKit..."
if ! curl -s http://localhost:7880 > /dev/null 2>&1; then
    echo "❌ LiveKit not detected on port 7880"
    echo ""
    echo "Please start LiveKit first:"
    echo "  livekit-server --dev"
    echo ""
    exit 1
else
    echo "✅ LiveKit running on port 7880"
fi

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ No .env.local found!"
    echo "Please create .env.local with required variables"
    exit 1
fi

# Create symlink from .env to .env.local (docker-compose needs .env)
if [ ! -f .env ]; then
    echo "🔗 Creating .env symlink to .env.local..."
    ln -s .env.local .env
fi

# Check for OpenAI API key
if ! grep -q "^OPENAI_API_KEY=sk-" .env.local; then
    echo "⚠️  OpenAI API key not set in .env.local"
    echo "Please add your OpenAI API key before starting."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running"
    echo ""
    echo "Please start Docker Desktop first, then run this script again."
    echo ""
    exit 1
fi

echo ""
echo "🐳 Starting Docker services (Backend, Compiler, Redis)..."
echo ""

# Build and start services
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 8

# Health checks
echo ""
echo "🏥 Health Checks:"
echo "=================="

# LiveKit (external)
echo "✅ LiveKit Server    - http://localhost:7880 (Homebrew)"

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis             - localhost:6379"
else
    echo "❌ Redis             - FAILED"
fi

# Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API       - http://localhost:8000"
else
    echo "⏳ Backend API       - Starting... (check logs: docker-compose logs foundry-backend)"
fi

# Compiler
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ Compiler API      - http://localhost:8002"
else
    echo "⏳ Compiler API      - Starting... (check logs: docker-compose logs foundry-compiler)"
fi

echo ""
echo "🎉 Docker services running!"
echo "=============================="
echo ""
echo "📍 Service URLs:"
echo "  Backend:    http://localhost:8000"
echo "  Compiler:   http://localhost:8002"
echo "  LiveKit:    ws://localhost:7880 (Homebrew)"
echo "  Redis:      localhost:6379"
echo ""
echo "▶️  Start Frontend (Next.js):"
echo "  npm run dev"
echo "  # Opens on http://localhost:3000"
echo ""
echo "🧪 Quick Tests:"
echo "  # Voice session"
echo "  curl -X POST http://localhost:8000/api/voice/session \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_id\":\"nate\",\"agent_id\":\"pm-agent\"}'"
echo ""
echo "  # List agents"
echo "  curl http://localhost:8000/api/agents"
echo ""
echo "  # Compiler health"
echo "  curl http://localhost:8002/health"
echo ""
echo "📚 Documentation:"
echo "  - START_HERE.md           - Quick start guide"
echo "  - LIVEKIT_SETUP.md        - LiveKit integration"
echo "  - INFRASTRUCTURE_STATUS.md - Current status"
echo ""
echo "🛑 To stop:"
echo "  docker-compose down"
echo "  # (Stop livekit-server and npm run dev separately)"
echo ""
echo "📜 To view logs:"
echo "  docker-compose logs -f [service]"
echo "  # Services: redis, foundry-backend, foundry-compiler"
echo ""
