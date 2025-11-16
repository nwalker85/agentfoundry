#!/bin/bash
# Agent Foundry - Development Start Script
# Starts all services with hot reload enabled

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🏭 Agent Foundry - Development Mode"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running"
    echo ""
    echo "Please start Docker Desktop first, then run this script again."
    echo ""
    exit 1
fi

# Check for required env file
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local not found, copying from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env.local
        echo "✅ Created .env.local - please add your API keys"
        echo ""
    else
        echo "❌ No .env.example found. Please create .env.local manually."
        exit 1
    fi
fi

# Create symlink for docker-compose
if [ ! -f .env ] || [ ! -L .env ]; then
    echo "🔗 Creating .env symlink..."
    rm -f .env
    ln -s .env.local .env
fi

# Check for required API keys
if ! grep -q "^OPENAI_API_KEY=sk-" .env.local; then
    echo "⚠️  Warning: OPENAI_API_KEY not set in .env.local"
fi

if ! grep -q "^LIVEKIT_API_KEY=" .env.local; then
    echo "⚠️  Warning: LIVEKIT_API_KEY not set in .env.local"
fi

echo ""
echo "🐳 Starting Agent Foundry services..."
echo ""
echo "Mode: Development (hot reload enabled)"
echo "Compose files: docker-compose.yml + docker-compose.dev.yml"
echo ""

# Check if we should use dev override
if [ -f docker-compose.dev.yml ]; then
    COMPOSE_CMD="docker-compose -f docker-compose.yml -f docker-compose.dev.yml"
    echo "✅ Using development overrides"
else
    COMPOSE_CMD="docker-compose"
    echo "ℹ️  No docker-compose.dev.yml found, using standard config"
fi

# Start services
echo ""
$COMPOSE_CMD up -d

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 10

# Health checks
echo ""
echo "🏥 Service Health:"
echo "=================="

# Function to check HTTP endpoint
check_http() {
    local url=$1
    local name=$2
    if curl -sf "$url" > /dev/null 2>&1; then
        echo "✅ $name"
        return 0
    else
        echo "⏳ $name (starting...)"
        return 1
    fi
}

# Function to check container health
check_container() {
    local service=$1
    local name=$2
    local health=$(docker-compose ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    if [ "$health" = "healthy" ]; then
        echo "✅ $name"
        return 0
    elif [ "$health" = "starting" ]; then
        echo "⏳ $name (starting...)"
        return 1
    else
        echo "❌ $name (unhealthy or no healthcheck)"
        return 1
    fi
}

# Check services
check_container livekit "LiveKit Server    - ws://localhost:7880"
check_container redis "Redis             - localhost:6379"
check_http "http://localhost:8000/health" "Backend API       - http://localhost:8000"
check_http "http://localhost:8002/health" "Compiler API      - http://localhost:8002"
check_http "http://localhost:3000" "Frontend UI       - http://localhost:3000" || echo "⏳ Frontend UI      - Not started yet"

echo ""
echo "🎯 Development Environment Ready!"
echo "===================================="
echo ""
echo "📍 Service URLs:"
echo "  Frontend:   http://localhost:3000"
echo "  Backend:    http://localhost:8000"
echo "  Compiler:   http://localhost:8002"
echo "  LiveKit:    ws://localhost:7880"
echo "  Redis:      localhost:6379"
echo ""
echo "🔥 Hot Reload Enabled:"
echo "  Backend:    Edit backend/*.py  → auto-reload (2-3s)"
echo "  Frontend:   Edit app/*.tsx     → instant (Fast Refresh)"
echo "  Agent:      Edit agent/*.py    → auto-reload (2-3s)"
echo "  Compiler:   Restart manually or use dev override"
echo ""
echo "📝 Workflow:"
echo "  1. Edit files in your editor"
echo "  2. Save → changes auto-reload in containers"
echo "  3. No rebuild needed for code changes!"
echo ""
echo "📊 View Logs:"
echo "  docker-compose logs -f foundry-backend"
echo "  docker-compose logs -f agent-foundry-ui"
echo "  docker-compose logs -f voice-agent-worker"
echo "  docker-compose logs -f  # All services"
echo ""
echo "🔄 Restart Single Service:"
echo "  docker-compose restart foundry-backend"
echo ""
echo "🛑 Stop All Services:"
echo "  docker-compose down"
echo ""
echo "🔧 Rebuild (only when dependencies change):"
echo "  docker-compose build foundry-backend"
echo "  docker-compose up -d foundry-backend"
echo ""
echo "📚 Documentation:"
echo "  DOCKER_DEV_WORKFLOW.md - Complete workflow guide"
echo "  START_HERE.md          - Project overview"
echo "  LIVEKIT_DOCKER_MIGRATION.md - LiveKit setup"
echo ""
echo "✨ Happy coding! Edit files and watch them reload."
echo ""
