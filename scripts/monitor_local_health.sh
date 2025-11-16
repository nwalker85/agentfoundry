#!/usr/bin/env bash
# Agent Foundry - Local Stack Health Monitor
#
# Checks Docker, core containers, and key localhost endpoints so you can quickly
# see whether your local Agent Foundry environment is healthy.

set -euo pipefail

PROJECT_ROOT="/Users/nwalker/Development/Projects/agentfoundry"
cd "$PROJECT_ROOT"

echo "🔍 Agent Foundry - Local Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Docker Status
echo "1️⃣  Docker Status:"
if docker info >/dev/null 2>&1; then
  echo "   ✅ Docker is running"
else
  echo "   ❌ Docker is NOT running - start Docker Desktop first."
  exit 1
fi
echo ""

# 2. Container Status
echo "2️⃣  Container Status:"
docker compose ps
echo ""

# 3. Port Status
echo "3️⃣  Port Status:"
PORTS=(7880 7881 6379 8000 8002)
for port in "${PORTS[@]}"; do
  if lsof -i :"${port}" >/dev/null 2>&1; then
    echo "   ✅ Port ${port} in use"
  else
    echo "   ❌ Port ${port} NOT in use"
  fi
done
echo ""

# 4. HTTP Health Checks
echo "4️⃣  HTTP Health Checks:"

check_http() {
  local url="$1"
  local label="$2"

  if curl -sf -m 5 "$url" >/dev/null 2>&1; then
    echo "   ✅ ${label} (${url})"
  else
    echo "   ❌ ${label} (${url})"
  fi
}

check_http "http://localhost:8000/health" "Backend"
check_http "http://localhost:8002/health" "Compiler"
check_http "http://localhost:7880"        "LiveKit HTTP"
echo ""

# 5. Recent Container Logs
echo "5️⃣  Recent Container Logs:"
echo "   ─────────────────────────"

echo "   LiveKit:"
docker compose logs livekit --tail=10 2>&1 | sed 's/^/   /' || echo "   (no logs)"
echo ""

echo "   Redis:"
docker compose logs redis --tail=5 2>&1 | sed 's/^/   /' || echo "   (no logs)"
echo ""

echo "   Backend:"
docker compose logs foundry-backend --tail=10 2>&1 | sed 's/^/   /' || echo "   (no logs)"
echo ""

echo "   Compiler:"
docker compose logs foundry-compiler --tail=10 2>&1 | sed 's/^/   /' || echo "   (no logs)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Local health check complete."
echo ""
echo "Tips:"
echo "  • Restart services: docker compose restart"
echo "  • Full rebuild:    docker compose down && docker compose up -d --build"
echo "  • Follow logs:     docker compose logs -f foundry-backend"
echo ""

