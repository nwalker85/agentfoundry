#!/usr/bin/env python3
"""
Add Banking Tools to Integration Manifest

Adds the major banking platform tools to the integrations manifest JSON file.
"""

import json
from pathlib import Path

MANIFEST_PATH = "/app/mcp/integration_server/config/integrations.manifest.json"

banking_tools_manifest = [
    {
        "toolName": "fiserv.core",
        "displayName": "Fiserv Core Banking",
        "description": "One of the 'Big Three' core providers serving a significant majority of banks and credit unions in the United States. Provides comprehensive core banking solutions.",
        "category": "Banking Platform",
        "logo": "fiserv",
        "icon": "fiserv",
        "tags": ["banking", "core-banking", "financial-services", "enterprise"],
        "metadata": {"version": 1, "source": "banking-platforms", "node_type": "custom.Fiserv", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/fiserv-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "fis.core",
        "displayName": "FIS Core Banking",
        "description": "Part of the 'Big Three' core providers. Leading global provider of technology solutions for merchants, banks and capital markets firms.",
        "category": "Banking Platform",
        "logo": "fis",
        "icon": "fis",
        "tags": ["banking", "core-banking", "financial-services", "enterprise"],
        "metadata": {"version": 1, "source": "banking-platforms", "node_type": "custom.FIS", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/fis-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "jackhenry.core",
        "displayName": "Jack Henry & Associates",
        "description": "One of the 'Big Three' core providers. Leading provider of technology solutions and payment processing services for financial institutions.",
        "category": "Banking Platform",
        "logo": "jackhenry",
        "icon": "jackhenry",
        "tags": ["banking", "core-banking", "financial-services", "credit-unions"],
        "metadata": {
            "version": 1,
            "source": "banking-platforms",
            "node_type": "custom.JackHenry",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/jackhenry-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "temenos.core",
        "displayName": "Temenos",
        "description": "Global leader serving banks and lenders in over 150 countries with its core, origination, and onboarding solutions. Cloud-native, API-first banking platform.",
        "category": "Banking Platform",
        "logo": "temenos",
        "icon": "temenos",
        "tags": ["banking", "core-banking", "cloud-native", "api-first", "global"],
        "metadata": {"version": 1, "source": "banking-platforms", "node_type": "custom.Temenos", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/temenos-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "finastra.fusion",
        "displayName": "Finastra",
        "description": "Supports more than 8,000 financial institutions worldwide, including a large percentage of the top 50 global banks, with a broad range of financial software solutions.",
        "category": "Banking Platform",
        "logo": "finastra",
        "icon": "finastra",
        "tags": ["banking", "lending", "payments", "treasury", "global"],
        "metadata": {"version": 1, "source": "banking-platforms", "node_type": "custom.Finastra", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/finastra-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "infosys.finacle",
        "displayName": "Infosys Finacle",
        "description": "Cloud-based core banking solutions serving over 1,300 clients in 100+ countries, powering banking for a vast number of end customers globally.",
        "category": "Banking Platform",
        "logo": "infosys",
        "icon": "infosys",
        "tags": ["banking", "core-banking", "cloud-native", "digital-banking", "global"],
        "metadata": {
            "version": 1,
            "source": "banking-platforms",
            "node_type": "custom.InfosysFinacle",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/infosys-finacle-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "oracle.flexcube",
        "displayName": "Oracle FLEXCUBE",
        "description": "Widely used in 140+ countries, powering accounts for a large percentage of the world's banked population. Enterprise-grade universal banking platform.",
        "category": "Banking Platform",
        "logo": "oracle",
        "icon": "oracle",
        "tags": ["banking", "core-banking", "enterprise", "universal-banking", "global"],
        "metadata": {
            "version": 1,
            "source": "banking-platforms",
            "node_type": "custom.OracleFlexcube",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/oracle-flexcube-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "mambu.core",
        "displayName": "Mambu",
        "description": "Cloud-native, API-driven SaaS banking platform, especially popular with digital-first and challenger banks. Modern composable banking architecture.",
        "category": "Banking Platform",
        "logo": "mambu",
        "icon": "mambu",
        "tags": ["banking", "cloud-native", "api-first", "saas", "digital-banking", "challenger-banks"],
        "metadata": {"version": 1, "source": "banking-platforms", "node_type": "custom.Mambu", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/mambu-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "thoughtmachine.vault",
        "displayName": "Thought Machine Vault",
        "description": "Next-generation cloud-native core banking platform. API-driven, real-time processing, popular with digital-first banks and financial innovators.",
        "category": "Banking Platform",
        "logo": "thoughtmachine",
        "icon": "thoughtmachine",
        "tags": ["banking", "cloud-native", "api-first", "real-time", "digital-banking", "modern-architecture"],
        "metadata": {
            "version": 1,
            "source": "banking-platforms",
            "node_type": "custom.ThoughtMachine",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/thoughtmachine-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
]


def add_banking_to_manifest():
    """Add banking tools to the integration manifest"""
    manifest_file = Path(MANIFEST_PATH)

    # Load existing manifest
    with open(manifest_file) as f:
        manifest = json.load(f)

    print(f"📦 Current manifest has {len(manifest)} tools")

    # Check which tools already exist
    existing_tool_names = {tool["toolName"] for tool in manifest}
    new_tools = [tool for tool in banking_tools_manifest if tool["toolName"] not in existing_tool_names]

    if not new_tools:
        print("⚠️  All banking tools already exist in manifest")
        return

    # Add new tools
    manifest.extend(new_tools)

    # Save updated manifest
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Added {len(new_tools)} new banking tools")
    print(f"📦 Updated manifest now has {len(manifest)} tools")
    print("\nAdded banking platforms:")
    for tool in new_tools:
        print(f"  - {tool['displayName']}")


if __name__ == "__main__":
    add_banking_to_manifest()
