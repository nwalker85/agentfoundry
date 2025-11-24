#!/usr/bin/env python3
"""
N8N Manifest Sync Script

Automatically generates integrations.manifest.json from n8n's available node types.
This allows Agent Foundry to expose all n8n integrations as tools without manual configuration.

Usage:
    python scripts/sync_n8n_manifest.py

Environment Variables:
    N8N_BASE_URL - n8n instance URL (default: http://n8n:5678)
    N8N_API_KEY - n8n API key (optional)
    N8N_BASIC_AUTH_USER - n8n basic auth username (optional)
    N8N_BASIC_AUTH_PASSWORD - n8n basic auth password (optional)
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.tools.n8n_client import N8NClient, categorize_node, extract_logo_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def convert_n8n_properties_to_json_schema(properties: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Convert n8n node properties to JSON Schema format.

    n8n properties have format:
    {
        "displayName": "Channel",
        "name": "channel",
        "type": "string",
        "required": true,
        "description": "Channel name or ID"
    }

    Convert to JSON Schema:
    {
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "..."}
        },
        "required": ["channel"]
    }
    """
    schema_properties = {}
    required = []

    for prop in properties:
        name = prop.get("name", "")
        if not name:
            continue

        # Map n8n types to JSON Schema types
        n8n_type = prop.get("type", "string")
        json_type = "string"  # default

        if n8n_type in ["string", "number", "boolean"]:
            json_type = n8n_type
        elif n8n_type in ["options", "multiOptions"]:
            json_type = "string"
        elif n8n_type == "collection":
            json_type = "object"

        schema_properties[name] = {
            "type": json_type,
            "description": prop.get("description", ""),
        }

        # Add enum for options
        if "options" in prop and n8n_type == "options":
            options = prop["options"]
            if isinstance(options, list) and len(options) > 0:
                enum_values = [opt.get("value", opt.get("name", "")) for opt in options]
                if enum_values:
                    schema_properties[name]["enum"] = enum_values

        # Track required fields
        if prop.get("required", False):
            required.append(name)

    schema = {
        "type": "object",
        "properties": schema_properties,
    }

    if required:
        schema["required"] = required

    return schema


def generate_manifest_entry(node: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a manifest entry for an n8n node.

    Args:
        node: Node type definition from n8n

    Returns:
        Manifest entry dict
    """
    node_name = node["name"]
    display_name = node["displayName"]
    description = node.get("description", f"{display_name} integration")

    # Extract base name for toolName (e.g., "slack" from "n8n-nodes-base.slack")
    base_name = extract_logo_name(node_name)

    # Generate unique tool name (use node operation if available, otherwise use base name)
    tool_name = f"{base_name}.execute"

    # Categorize the node
    category = categorize_node(node_name, node)

    # Extract logo name
    logo = extract_logo_name(node_name)

    # Generate JSON schemas from node properties
    input_schema = convert_n8n_properties_to_json_schema(node.get("properties", []))

    # Simple output schema (n8n doesn't provide output schema)
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"},
        },
    }

    # Generate webhook URL (note: these are placeholder URLs)
    # In production, you'd need actual n8n webhooks configured
    webhook_url = f"http://n8n:5678/webhook/{base_name}-execute"

    # Extract tags
    tags = [base_name]
    if node.get("group"):
        tags.extend(node["group"])

    # Determine auth type from credentials
    auth_type = "none"
    credentials = node.get("credentials", [])
    if credentials:
        # Check credential types
        cred_types = [c.get("name", "").lower() for c in credentials]
        if any("oauth" in ct for ct in cred_types):
            auth_type = "oauth2"
        elif any("api" in ct for ct in cred_types):
            auth_type = "apikey"
        else:
            auth_type = "basic"

    return {
        "toolName": tool_name,
        "displayName": f"{display_name}",
        "description": description,
        "category": category,
        "logo": logo,
        "tags": tags,
        "n8n": {
            "type": "webhook",
            "url": webhook_url,
            "timeoutSeconds": 30,
            "nodeType": node_name,
        },
        "inputSchema": input_schema,
        "outputSchema": output_schema,
        "examples": [],
        "metadata": {
            "authType": auth_type,
            "n8nNodeType": node_name,
            "n8nVersion": node.get("version", 1),
        },
    }


def sync_manifest(
    output_path: str = "mcp/integration_server/config/integrations.manifest.json",
    max_nodes: int = 0,
) -> int:
    """
    Sync n8n integrations to manifest file.

    Args:
        output_path: Path to write manifest file
        max_nodes: Maximum number of nodes to include (0 = all)

    Returns:
        Number of integrations synced
    """
    logger.info("Starting n8n manifest sync...")

    # Initialize n8n client
    client = N8NClient()

    try:
        # Fetch node types from n8n
        logger.info("Fetching node types from n8n...")
        node_types = client.get_node_types()

        if not node_types:
            logger.warning("No node types found from n8n. Is n8n running?")
            return 0

        logger.info(f"Found {len(node_types)} node types from n8n")

        # Filter to only include integration nodes (exclude triggers, core nodes, etc.)
        integration_nodes = []
        for node in node_types:
            node_name = node["name"]

            # Skip internal/utility nodes
            if any(
                skip in node_name.lower()
                for skip in [
                    "trigger",
                    "webhook",
                    "schedule",
                    "start",
                    "set",
                    "if",
                    "switch",
                    "merge",
                    "split",
                    "function",
                    "code",
                    "http.request",
                    "item",
                    "no-op",
                    "sticky",
                ]
            ):
                continue

            # Only include nodes from standard packages
            if not node_name.startswith("n8n-nodes-base."):
                continue

            integration_nodes.append(node)

        logger.info(f"Filtered to {len(integration_nodes)} integration nodes")

        # Limit if requested
        if max_nodes > 0:
            integration_nodes = integration_nodes[:max_nodes]
            logger.info(f"Limited to {max_nodes} nodes")

        # Generate manifest entries
        manifest = []
        for node in integration_nodes:
            try:
                entry = generate_manifest_entry(node)
                manifest.append(entry)
            except Exception as exc:
                logger.warning(f"Failed to generate entry for {node['name']}: {exc}")
                continue

        # Write manifest file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with output_file.open("w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"✅ Synced {len(manifest)} integrations to {output_path}")

        # Print summary
        categories = {}
        for entry in manifest:
            cat = entry["category"]
            categories[cat] = categories.get(cat, 0) + 1

        logger.info("\nCategories:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            logger.info(f"  {cat}: {count}")

        return len(manifest)

    finally:
        client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync n8n integrations to manifest")
    parser.add_argument(
        "--output",
        "-o",
        default="mcp/integration_server/config/integrations.manifest.json",
        help="Output path for manifest file",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=0,
        help="Limit number of integrations (0 = all)",
    )

    args = parser.parse_args()

    try:
        count = sync_manifest(output_path=args.output, max_nodes=args.limit)
        sys.exit(0 if count > 0 else 1)
    except Exception as exc:
        logger.error(f"Failed to sync manifest: {exc}", exc_info=True)
        sys.exit(1)
