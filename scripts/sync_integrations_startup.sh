#!/bin/bash
#
# Integration Sync Startup Script
#
# This script runs on container startup to:
# 1. Check if n8n source has changed (via checksum)
# 2. If changed, sync manifest from n8n integrations
# 3. Populate function catalog using UPSERT (only updates changed entries)
#
# Usage: ./scripts/sync_integrations_startup.sh

set -e

echo "🔄 Starting integration sync..."

# Configuration
N8N_URL="${N8N_BASE_URL:-http://n8n:5678}"
MAX_WAIT=60  # Maximum seconds to wait for n8n
WAIT_INTERVAL=2
MANIFEST_PATH="mcp/integration_server/config/integrations.manifest.json"
CHECKSUM_FILE="/tmp/.n8n_source_checksum"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to compute checksum of n8n source directory
compute_n8n_checksum() {
    local n8n_path="$1"
    if [ -d "$n8n_path/packages/nodes-base/nodes" ]; then
        # Hash the directory structure and file modification times
        find "$n8n_path/packages/nodes-base/nodes" -name "*.node.ts" -type f -exec stat -c '%n %Y' {} \; 2>/dev/null | sort | md5sum | cut -d' ' -f1
    else
        echo "no-source"
    fi
}

# Check if local n8n source is available (Docker mount or local path)
N8N_LOCAL_PATH="${N8N_SOURCE_PATH:-/n8n}"

# Check if we need to re-sync based on source changes
NEEDS_SYNC=false
CURRENT_CHECKSUM=""

if [ -d "$N8N_LOCAL_PATH/packages/nodes-base/nodes" ]; then
    CURRENT_CHECKSUM=$(compute_n8n_checksum "$N8N_LOCAL_PATH")

    if [ -f "$CHECKSUM_FILE" ]; then
        PREVIOUS_CHECKSUM=$(cat "$CHECKSUM_FILE")
        if [ "$CURRENT_CHECKSUM" = "$PREVIOUS_CHECKSUM" ]; then
            echo_info "✅ n8n source unchanged (checksum: ${CURRENT_CHECKSUM:0:8}...)"
            echo_info "Skipping manifest regeneration, running catalog sync only..."
            NEEDS_SYNC=false
        else
            echo_info "🔄 n8n source changed (${PREVIOUS_CHECKSUM:0:8}... -> ${CURRENT_CHECKSUM:0:8}...)"
            NEEDS_SYNC=true
        fi
    else
        echo_info "🆕 First run - will generate manifest"
        NEEDS_SYNC=true
    fi

    # Also check if manifest file exists
    if [ ! -f "$MANIFEST_PATH" ]; then
        echo_info "📄 Manifest file missing - will regenerate"
        NEEDS_SYNC=true
    fi
else
    echo_warn "Local n8n source not found at $N8N_LOCAL_PATH"
    # For API sync, always check if manifest exists
    if [ ! -f "$MANIFEST_PATH" ]; then
        NEEDS_SYNC=true
    fi
fi

# Only sync manifest if needed
if [ "$NEEDS_SYNC" = true ]; then
    # Wait for n8n to be ready (only if we need to sync)
    echo_info "Waiting for n8n at $N8N_URL..."
    elapsed=0

    while [ $elapsed -lt $MAX_WAIT ]; do
        if curl -sf "$N8N_URL" > /dev/null 2>&1; then
            echo_info "✅ n8n is ready!"
            break
        fi

        echo_info "Waiting for n8n... (${elapsed}s/${MAX_WAIT}s)"
        sleep $WAIT_INTERVAL
        elapsed=$((elapsed + WAIT_INTERVAL))
    done

    if [ $elapsed -ge $MAX_WAIT ]; then
        echo_warn "⚠️  n8n did not become ready in time. Skipping manifest sync."
        echo_warn "You can manually sync later with: python scripts/sync_n8n_manifest.py"
        # Still try to populate from existing manifest if it exists
        if [ -f "$MANIFEST_PATH" ]; then
            echo_info "Using existing manifest file..."
        else
            exit 0
        fi
    else
        # Sync manifest from n8n source code (if available) or API
        echo_info "Syncing integrations manifest..."

        if [ -d "$N8N_LOCAL_PATH/packages/nodes-base/nodes" ]; then
            echo_info "Mining node definitions from source code..."
            if python3 scripts/mine_n8n_nodes_local.py --n8n-path "$N8N_LOCAL_PATH"; then
                echo_info "✅ Mined all nodes from source code"
                # Save checksum for next run
                echo "$CURRENT_CHECKSUM" > "$CHECKSUM_FILE"
            else
                echo_error "❌ Failed to mine nodes from source"
                exit 1
            fi
        else
            echo_info "Falling back to n8n API sync..."
            if python3 scripts/sync_n8n_manifest.py; then
                echo_info "✅ Manifest synced from n8n API"
            else
                echo_error "❌ Failed to sync manifest"
                exit 1
            fi
        fi
    fi
fi

# Always populate function catalog (uses UPSERT - only updates changed entries)
if [ -f "$MANIFEST_PATH" ]; then
    echo_info "Populating function catalog from manifest (UPSERT mode)..."
    if python3 scripts/populate_function_catalog.py; then
        echo_info "✅ Function catalog synced successfully"
    else
        echo_error "❌ Failed to populate function catalog"
        exit 1
    fi
else
    echo_warn "⚠️  No manifest file found, skipping catalog population"
fi

echo_info "🎉 Integration sync complete!"
