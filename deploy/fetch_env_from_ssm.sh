#!/usr/bin/env bash
# fetch_env_from_ssm.sh
# Fetch environment variables from AWS SSM Parameter Store
# Usage: ENVIRONMENT=dev ./fetch_env_from_ssm.sh

set -euo pipefail

PREFIX="/foundry/${ENVIRONMENT:-dev}"
OUTPUT_FILE="${OUTPUT_FILE:-/opt/agent-foundry/.env}"

echo "Fetching secrets from SSM path: $PREFIX"

# Create directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Clear existing file
> "$OUTPUT_FILE"

# Fetch all parameters under the prefix
aws ssm get-parameters-by-path \
  --path "$PREFIX" \
  --with-decryption \
  --query 'Parameters[*].[Name,Value]' \
  --output text | \
while IFS=$'\t' read -r name value; do
  # Strip prefix to get key name
  key="${name##*/}"
  echo "${key}=${value}" >> "$OUTPUT_FILE"
done

# Secure the file
chmod 600 "$OUTPUT_FILE"

echo "✅ Secrets fetched to $OUTPUT_FILE ($(wc -l < "$OUTPUT_FILE") variables)"
