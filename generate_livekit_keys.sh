#!/bin/bash
# Generate LiveKit API keys for local development

set -e

echo "Generating LiveKit API credentials..."

# Generate random API key and secret
API_KEY="devkey"
API_SECRET=$(openssl rand -hex 32)

echo ""
echo "Add these to your .env.local file:"
echo ""
echo "LIVEKIT_API_KEY=$API_KEY"
echo "LIVEKIT_API_SECRET=$API_SECRET"
echo ""
echo "Also update docker-compose.yml environment:"
echo "LIVEKIT_KEYS=$API_KEY:$API_SECRET"
echo ""
