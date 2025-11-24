#!/bin/bash
#
# Backend Startup Script
#
# Runs initialization tasks before starting the FastAPI server:
# 1. Run database migrations
# 2. Sync n8n integrations
# 3. Start FastAPI server

set -e

echo "🚀 Starting Agent Foundry Backend..."

# Run integration sync (non-blocking - allow failure)
echo "📦 Syncing n8n integrations..."
if bash scripts/sync_integrations_startup.sh; then
    echo "✅ Integration sync complete"
else
    echo "⚠️  Integration sync failed, continuing anyway..."
fi

# Start FastAPI server
echo "🌐 Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --log-level info \
    --reload \
    --reload-exclude 'agents/*.py' \
    --reload-exclude 'agents/*_*_*_*_*_*.py'
