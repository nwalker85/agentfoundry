#!/bin/bash
#
# Manual Integration Sync Script
#
# Run this script anytime to manually sync n8n integrations to Agent Foundry.
# This is useful when you add new integrations to n8n or want to refresh the catalog.
#
# Usage:
#   ./scripts/sync_integrations.sh

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Agent Foundry - N8N Integration Sync${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Sync manifest from n8n
echo -e "${GREEN}[1/2]${NC} Syncing integrations from n8n..."
python3 scripts/sync_n8n_manifest.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Manifest synced successfully"
    echo ""
else
    echo -e "${YELLOW}✗${NC} Failed to sync manifest"
    exit 1
fi

# Step 2: Populate function catalog
echo -e "${GREEN}[2/2]${NC} Updating function catalog..."
python3 scripts/populate_function_catalog.py --clear

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Function catalog updated"
    echo ""
else
    echo -e "${YELLOW}✗${NC} Failed to update function catalog"
    exit 1
fi

# Success!
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Sync complete!${NC}"
echo ""
echo "All n8n integrations are now available in:"
echo "  • Tool Catalog UI: http://localhost:3000/app/tools"
echo "  • Function Catalog API: http://localhost:8000/api/function-catalog"
echo "  • MCP Integration Gateway: http://localhost:8100/tools"
echo ""
echo "To restart services and see changes, run:"
echo "  docker-compose restart foundry-backend mcp-integration"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
