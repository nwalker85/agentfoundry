#!/bin/bash
set -e

echo "🚀 Starting PM Agent - Engineering Department"
echo "=============================================="
echo ""

if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.template to .env and add your Notion API key"
    exit 1
fi

if ! grep -q "NOTION_API_KEY=" .env || grep -q "NOTION_API_KEY=\"\"" .env || grep -q "NOTION_API_KEY=secret_" .env; then
    echo "⚠️  Warning: NOTION_API_KEY not configured in .env"
    echo "   Please add your Notion API key to .env"
    exit 1
fi

WORKING_DIR="/Users/nate/Documents/Engineering Department"
if [ ! -d "$WORKING_DIR" ]; then
    echo "📁 Creating working directory: $WORKING_DIR"
    mkdir -p "$WORKING_DIR"
fi

echo "🐳 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for Ollama service..."
sleep 10

echo "🤖 Checking for Ollama model..."
if ! docker exec pm_agent_ollama ollama list | grep -q "qwen2.5:7b"; then
    echo "📥 Pulling qwen2.5:7b model (this may take 3-5 minutes)..."
    docker exec pm_agent_ollama ollama pull qwen2.5:7b
else
    echo "✓ Model qwen2.5:7b already available"
fi

echo "⏳ Waiting for PM Agent to initialize..."
sleep 5

echo ""
echo "✅ PM Agent is running!"
echo ""
echo "Services:"
echo "  • Streamlit UI:  http://localhost:8501"
echo "  • Ollama API:    http://localhost:11434"
echo ""
echo "Logs:"
echo "  docker-compose logs -f pm_agent"
echo ""
echo "Stop:"
echo "  docker-compose down"
echo ""
