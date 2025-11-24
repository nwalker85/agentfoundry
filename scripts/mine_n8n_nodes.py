#!/usr/bin/env python3
"""
Mine N8N Node Definitions from Source Code

Fetches n8n's open-source repository and extracts all node definitions
directly from the source code, bypassing the need for API authentication.

Usage:
    python scripts/mine_n8n_nodes.py
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# n8n GitHub repository
N8N_REPO = "n8n-io/n8n"
N8N_BRANCH = "master"
NODES_BASE_PATH = "packages/nodes-base/nodes"


def fetch_github_tree(repo: str, branch: str = "master", path: str = "") -> list[dict[str, Any]]:
    """
    Fetch directory tree from GitHub API.

    Args:
        repo: Repository in format "owner/repo"
        branch: Branch name
        path: Path within repository

    Returns:
        List of file/directory objects
    """
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={branch}"

    logger.info(f"Fetching GitHub tree: {url}")

    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    return response.json()


def fetch_file_content(repo: str, path: str, branch: str = "master") -> str:
    """
    Fetch raw file content from GitHub.

    Args:
        repo: Repository in format "owner/repo"
        path: File path within repository
        branch: Branch name

    Returns:
        File content as string
    """
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"

    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    return response.text


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

    # Extract group
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
        x in name_lower for x in ["slack", "discord", "telegram", "teams", "mail", "smtp", "twilio"]
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
        x in name_lower for x in ["openai", "anthropic", "cohere", "huggingface", "elevenlabs"]
    ):
        return "AI & ML"

    # Productivity
    if any(x in groups for x in ["productivity"]) or any(
        x in name_lower for x in ["drive", "dropbox", "sheets", "docs", "calendar", "airtable"]
    ):
        return "Productivity"

    # E-commerce
    if any(x in name_lower for x in ["stripe", "shopify", "woo", "commerce", "paypal"]):
        return "E-commerce"

    # Marketing
    if any(x in name_lower for x in ["mailchimp", "marketing", "campaign", "brevo", "klaviyo"]):
        return "Marketing"

    # Social
    if any(x in name_lower for x in ["twitter", "linkedin", "facebook", "instagram", "social"]):
        return "Social Media"

    return "Other"


def mine_n8n_nodes(output_path: str = "mcp/integration_server/config/integrations.manifest.json") -> int:
    """
    Mine all node definitions from n8n source code.

    Args:
        output_path: Path to write manifest file

    Returns:
        Number of nodes mined
    """
    logger.info("Starting n8n node mining from source code...")

    manifest = []

    try:
        # Fetch the nodes-base directory tree
        logger.info(f"Fetching node list from {N8N_REPO}...")
        tree = fetch_github_tree(N8N_REPO, N8N_BRANCH, NODES_BASE_PATH)

        # Process each directory (each directory is typically a node)
        node_count = 0
        for item in tree:
            if item["type"] == "dir":
                node_dir_name = item["name"]

                # Skip utility/internal directories
                if node_dir_name.startswith(".") or node_dir_name in ["_Base", "helpers"]:
                    continue

                try:
                    # Fetch the node directory contents
                    node_files = fetch_github_tree(N8N_REPO, N8N_BRANCH, f"{NODES_BASE_PATH}/{node_dir_name}")

                    # Find the main node file (usually matches directory name)
                    node_file = None
                    for file in node_files:
                        if file["type"] == "file" and file["name"].endswith(".node.ts"):
                            node_file = file
                            break

                    if not node_file:
                        continue

                    # Fetch and parse the node source code
                    logger.info(f"Mining node: {node_dir_name}")
                    source_code = fetch_file_content(
                        N8N_REPO, f"{NODES_BASE_PATH}/{node_dir_name}/{node_file['name']}", N8N_BRANCH
                    )

                    # Extract metadata
                    metadata = extract_node_metadata(source_code, node_dir_name)
                    if not metadata:
                        continue

                    # Determine category
                    category = categorize_node_from_metadata(metadata)

                    # Create manifest entry
                    tool_name = f"{node_dir_name.lower()}.execute"
                    entry = {
                        "toolName": tool_name,
                        "displayName": metadata["displayName"],
                        "description": metadata["description"],
                        "category": category,
                        "logo": node_dir_name.lower(),
                        "tags": metadata.get("group", []),
                        "metadata": {
                            "version": metadata.get("version", 1),
                            "source": "n8n-nodes-base",
                            "node_type": f"n8n-nodes-base.{node_dir_name}",
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

                    # Rate limiting - be nice to GitHub API
                    if node_count % 10 == 0:
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

    except Exception as exc:
        logger.error(f"Failed to mine n8n nodes: {exc}", exc_info=True)
        return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mine n8n node definitions from source code")
    parser.add_argument(
        "--output",
        "-o",
        default="mcp/integration_server/config/integrations.manifest.json",
        help="Output manifest file path",
    )

    args = parser.parse_args()

    try:
        count = mine_n8n_nodes(output_path=args.output)
        sys.exit(0 if count > 0 else 1)
    except Exception as exc:
        logger.error(f"Mining failed: {exc}", exc_info=True)
        sys.exit(1)
