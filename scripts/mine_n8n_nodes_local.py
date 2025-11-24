#!/usr/bin/env python3
"""
Mine N8N Node Definitions from Local Source Code

Parses n8n's local repository and extracts all node definitions
directly from the TypeScript source files.

Usage:
    python scripts/mine_n8n_nodes_local.py --n8n-path /path/to/n8n
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_node_metadata(source_code: str, node_name: str) -> dict[str, Any] | None:
    """
    Extract node metadata from TypeScript source code.

    Args:
        source_code: TypeScript source code
        node_name: Node name (e.g., "Slack")

    Returns:
        Dictionary with node metadata or None if parsing fails
    """
    metadata = {
        "name": node_name,
        "displayName": node_name,
        "description": "",
        "group": [],
        "version": 1,
        "properties": [],
        "outputs": [],
        "credentials": [],
    }

    # Extract display name
    display_name_match = re.search(r'displayName:\s*[\'"]([^\'"]+)[\'"]', source_code)
    if display_name_match:
        metadata["displayName"] = display_name_match.group(1)

    # Extract description
    description_match = re.search(r'description:\s*[\'"]([^\'"]+)[\'"]', source_code)
    if description_match:
        metadata["description"] = description_match.group(1)

    # Extract group/category
    group_match = re.search(r"group:\s*\[(.*?)\]", source_code, re.DOTALL)
    if group_match:
        group_str = group_match.group(1)
        groups = re.findall(r'[\'"]([^\'"]+)[\'"]', group_str)
        metadata["group"] = groups

    # Extract version
    version_match = re.search(r"version:\s*(\d+)", source_code)
    if version_match:
        metadata["version"] = int(version_match.group(1))

    # Extract subtitle (often contains useful categorization info)
    subtitle_match = re.search(r'subtitle:\s*[\'"]([^\'"]+)[\'"]', source_code)
    if subtitle_match:
        metadata["subtitle"] = subtitle_match.group(1)

    return metadata


def get_icon_name(node_name: str) -> str:
    """
    Get the icon name for a node, suitable for use with Simple Icons.

    Args:
        node_name: Node directory name

    Returns:
        Icon name in lowercase
    """
    # Map common node names to Simple Icons names
    icon_map = {
        "ActiveCampaign": "activecampaign",
        "Airtable": "airtable",
        "Asana": "asana",
        "Aws": "amazonaws",
        "Baserow": "baserow",
        "Bitbucket": "bitbucket",
        "Box": "box",
        "Calendly": "calendly",
        "CircleCi": "circleci",
        "ClickUp": "clickup",
        "Cloudflare": "cloudflare",
        "Coda": "coda",
        "Contentful": "contentful",
        "CustomerIo": "customerdotio",
        "Discord": "discord",
        "Dropbox": "dropbox",
        "Elastic": "elasticsearch",
        "Facebook": "facebook",
        "Figma": "figma",
        "Freshdesk": "freshdesk",
        "Github": "github",
        "Gitlab": "gitlab",
        "Google": "google",
        "Grafana": "grafana",
        "Hubspot": "hubspot",
        "Intercom": "intercom",
        "Jenkins": "jenkins",
        "Jira": "jira",
        "Linear": "linear",
        "LinkedIn": "linkedin",
        "Mailchimp": "mailchimp",
        "Mattermost": "mattermost",
        "Medium": "medium",
        "Microsoft": "microsoft",
        "MondayCom": "mondaydotcom",
        "MongoDb": "mongodb",
        "MySql": "mysql",
        "Netlify": "netlify",
        "Notion": "notion",
        "OpenAi": "openai",
        "Paddle": "paddle",
        "PayPal": "paypal",
        "Pipedrive": "pipedrive",
        "Postgres": "postgresql",
        "PostHog": "posthog",
        "Reddit": "reddit",
        "Redis": "redis",
        "Rocketchat": "rocketdotchat",
        "Salesforce": "salesforce",
        "Segment": "segment",
        "SendGrid": "sendgrid",
        "ServiceNow": "servicenow",
        "Shopify": "shopify",
        "Slack": "slack",
        "Snowflake": "snowflake",
        "Spotify": "spotify",
        "Stripe": "stripe",
        "Supabase": "supabase",
        "Telegram": "telegram",
        "Trello": "trello",
        "Twilio": "twilio",
        "Twitter": "x",
        "Typeform": "typeform",
        "Webflow": "webflow",
        "WooCommerce": "woocommerce",
        "Wordpress": "wordpress",
        "Zendesk": "zendesk",
        "Zoom": "zoom",
        "Zulip": "zulip",
    }

    # Return mapped icon or lowercase node name as fallback
    return icon_map.get(node_name, node_name.lower())


def categorize_node_from_metadata(metadata: dict[str, Any]) -> str:
    """
    Categorize a node based on its metadata.

    Args:
        metadata: Node metadata dictionary

    Returns:
        Category string
    """
    name_lower = metadata["name"].lower()
    description_lower = metadata["description"].lower()
    groups = [g.lower() for g in metadata.get("group", [])]

    # Communication
    if any(x in groups for x in ["communication"]) or any(
        x in name_lower for x in ["slack", "discord", "telegram", "teams", "mail", "smtp", "twilio", "whatsapp"]
    ):
        return "Communication"

    # CRM
    if any(x in groups for x in ["crm"]) or any(
        x in name_lower for x in ["salesforce", "hubspot", "pipedrive", "zoho", "crm"]
    ):
        return "CRM"

    # Project Management
    if any(x in groups for x in ["project"]) or any(
        x in name_lower for x in ["jira", "asana", "trello", "notion", "clickup", "monday", "linear"]
    ):
        return "Project Management"

    # ITSM
    if any(x in groups for x in ["itsm"]) or any(
        x in name_lower for x in ["servicenow", "freshservice", "zendesk", "pagerduty", "opsgenie"]
    ):
        return "ITSM"

    # Analytics
    if any(x in groups for x in ["analytics"]) or any(
        x in name_lower for x in ["analytics", "mixpanel", "segment", "amplitude"]
    ):
        return "Analytics"

    # Cloud Services
    if any(x in groups for x in ["cloud"]) or any(
        x in name_lower for x in ["aws", "gcp", "azure", "s3", "lambda", "github", "gitlab"]
    ):
        return "Cloud Services"

    # Databases
    if any(x in groups for x in ["database"]) or any(
        x in name_lower for x in ["postgres", "mysql", "mongodb", "redis", "sql", "database"]
    ):
        return "Database"

    # AI & ML
    if any(x in groups for x in ["ai"]) or any(
        x in name_lower for x in ["openai", "anthropic", "cohere", "huggingface", "elevenlabs", "stability"]
    ):
        return "AI & ML"

    # Productivity
    if any(x in groups for x in ["productivity"]) or any(
        x in name_lower for x in ["drive", "dropbox", "sheets", "docs", "calendar", "airtable"]
    ):
        return "Productivity"

    # E-commerce
    if any(x in name_lower for x in ["stripe", "shopify", "woo", "commerce", "paypal", "square"]):
        return "E-commerce"

    # Marketing
    if any(x in name_lower for x in ["mailchimp", "marketing", "campaign", "brevo", "klaviyo"]):
        return "Marketing"

    # Social
    if any(x in name_lower for x in ["twitter", "linkedin", "facebook", "instagram", "social", "youtube"]):
        return "Social Media"

    return "Other"


def mine_n8n_nodes_local(
    n8n_path: str, output_path: str = "mcp/integration_server/config/integrations.manifest.json"
) -> int:
    """
    Mine all node definitions from local n8n source code.

    Args:
        n8n_path: Path to n8n repository root
        output_path: Path to write manifest file

    Returns:
        Number of nodes mined
    """
    logger.info(f"Starting n8n node mining from local repository: {n8n_path}")

    # Path to nodes-base directory
    nodes_base_path = Path(n8n_path) / "packages" / "nodes-base" / "nodes"

    if not nodes_base_path.exists():
        logger.error(f"Nodes directory not found: {nodes_base_path}")
        return 0

    manifest = []
    node_count = 0

    # Iterate through all subdirectories in nodes-base
    for node_dir in sorted(nodes_base_path.iterdir()):
        if not node_dir.is_dir():
            continue

        node_dir_name = node_dir.name

        # Skip utility/internal directories
        if node_dir_name.startswith(".") or node_dir_name in ["_Base", "helpers"]:
            continue

        try:
            # Find the main node file (*.node.ts)
            node_files = list(node_dir.glob("*.node.ts"))

            if not node_files:
                # Some nodes might be in subdirectories
                node_files = list(node_dir.glob("**/*.node.ts"))

            if not node_files:
                continue

            # Use the first node file found
            node_file = node_files[0]

            # Read and parse the source code
            logger.info(f"Mining node: {node_dir_name}")
            source_code = node_file.read_text(encoding="utf-8")

            # Extract metadata
            metadata = extract_node_metadata(source_code, node_dir_name)
            if not metadata:
                continue

            # Determine category and icon
            category = categorize_node_from_metadata(metadata)
            icon = get_icon_name(node_dir_name)

            # Create manifest entry
            tool_name = f"{node_dir_name.lower()}.execute"
            entry = {
                "toolName": tool_name,
                "displayName": metadata["displayName"],
                "description": metadata["description"] or f"Work with {metadata['displayName']}",
                "category": category,
                "logo": icon,
                "icon": icon,
                "tags": metadata.get("group", []),
                "metadata": {
                    "version": metadata.get("version", 1),
                    "source": "n8n-nodes-base",
                    "node_type": f"n8n-nodes-base.{node_dir_name}",
                    "source_file": str(node_file.relative_to(n8n_path)),
                },
                "n8n": {"type": "webhook", "url": f"http://n8n:5678/webhook/{node_dir_name.lower()}-execute"},
                "inputSchema": {"type": "object", "properties": {}, "required": []},
                "outputSchema": {
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}},
                },
            }

            manifest.append(entry)
            node_count += 1

            if node_count % 50 == 0:
                logger.info(f"Progress: {node_count} nodes mined...")

        except Exception as e:
            logger.warning(f"Failed to process node {node_dir_name}: {e}")
            continue

    # Write manifest file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"✅ Successfully mined {len(manifest)} nodes from n8n source code")
    logger.info(f"✅ Manifest written to {output_path}")

    # Print category breakdown
    categories = {}
    for entry in manifest:
        cat = entry["category"]
        categories[cat] = categories.get(cat, 0) + 1

    logger.info("\nNodes by Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat}: {count}")

    return len(manifest)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mine n8n node definitions from local source code")
    parser.add_argument(
        "--n8n-path",
        "-n",
        default=os.getenv("N8N_SOURCE_PATH", "/n8n"),
        help="Path to n8n repository root (default: /n8n in Docker, or N8N_SOURCE_PATH env var)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="mcp/integration_server/config/integrations.manifest.json",
        help="Output manifest file path",
    )

    args = parser.parse_args()

    try:
        count = mine_n8n_nodes_local(n8n_path=args.n8n_path, output_path=args.output)
        sys.exit(0 if count > 0 else 1)
    except Exception as exc:
        logger.error(f"Mining failed: {exc}", exc_info=True)
        sys.exit(1)
