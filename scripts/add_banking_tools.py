#!/usr/bin/env python3
"""
Add Major Banking Platform Tools

Adds the major banking core systems and platforms to the function catalog.
"""

import json
import sqlite3
import uuid

DATABASE_PATH = "/app/data/foundry.db"

banking_tools = [
    {
        "name": "fiserv.core",
        "display_name": "Fiserv Core Banking",
        "description": "One of the 'Big Three' core providers serving a significant majority of banks and credit unions in the United States. Provides comprehensive core banking solutions.",
        "category": "Banking Platform",
        "logo": "fiserv",
        "tags": ["banking", "core-banking", "financial-services", "enterprise"],
    },
    {
        "name": "fis.core",
        "display_name": "FIS Core Banking",
        "description": "Part of the 'Big Three' core providers. Leading global provider of technology solutions for merchants, banks and capital markets firms.",
        "category": "Banking Platform",
        "logo": "fis",
        "tags": ["banking", "core-banking", "financial-services", "enterprise"],
    },
    {
        "name": "jackhenry.core",
        "display_name": "Jack Henry & Associates",
        "description": "One of the 'Big Three' core providers. Leading provider of technology solutions and payment processing services for financial institutions.",
        "category": "Banking Platform",
        "logo": "jackhenry",
        "tags": ["banking", "core-banking", "financial-services", "credit-unions"],
    },
    {
        "name": "temenos.core",
        "display_name": "Temenos",
        "description": "Global leader serving banks and lenders in over 150 countries with its core, origination, and onboarding solutions. Cloud-native, API-first banking platform.",
        "category": "Banking Platform",
        "logo": "temenos",
        "tags": ["banking", "core-banking", "cloud-native", "api-first", "global"],
    },
    {
        "name": "finastra.fusion",
        "display_name": "Finastra",
        "description": "Supports more than 8,000 financial institutions worldwide, including a large percentage of the top 50 global banks, with a broad range of financial software solutions.",
        "category": "Banking Platform",
        "logo": "finastra",
        "tags": ["banking", "lending", "payments", "treasury", "global"],
    },
    {
        "name": "infosys.finacle",
        "display_name": "Infosys Finacle",
        "description": "Cloud-based core banking solutions serving over 1,300 clients in 100+ countries, powering banking for a vast number of end customers globally.",
        "category": "Banking Platform",
        "logo": "infosys",
        "tags": ["banking", "core-banking", "cloud-native", "digital-banking", "global"],
    },
    {
        "name": "oracle.flexcube",
        "display_name": "Oracle FLEXCUBE",
        "description": "Widely used in 140+ countries, powering accounts for a large percentage of the world's banked population. Enterprise-grade universal banking platform.",
        "category": "Banking Platform",
        "logo": "oracle",
        "tags": ["banking", "core-banking", "enterprise", "universal-banking", "global"],
    },
    {
        "name": "mambu.core",
        "display_name": "Mambu",
        "description": "Cloud-native, API-driven SaaS banking platform, especially popular with digital-first and challenger banks. Modern composable banking architecture.",
        "category": "Banking Platform",
        "logo": "mambu",
        "tags": ["banking", "cloud-native", "api-first", "saas", "digital-banking", "challenger-banks"],
    },
    {
        "name": "thoughtmachine.vault",
        "display_name": "Thought Machine Vault",
        "description": "Next-generation cloud-native core banking platform. API-driven, real-time processing, popular with digital-first banks and financial innovators.",
        "category": "Banking Platform",
        "logo": "thoughtmachine",
        "tags": ["banking", "cloud-native", "api-first", "real-time", "digital-banking", "modern-architecture"],
    },
]


def add_banking_tools():
    """Add banking platform tools to the function catalog"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    added_count = 0

    for tool in banking_tools:
        tool_id = str(uuid.uuid4())

        # Check if tool already exists
        cursor.execute("SELECT id FROM function_catalog WHERE name = ?", (tool["name"],))
        existing = cursor.fetchone()

        if existing:
            print(f"⚠️  {tool['display_name']} already exists, skipping...")
            continue

        cursor.execute(
            """
            INSERT INTO function_catalog (
                id, name, display_name, description, category, type,
                integration_tool_name, input_schema, output_schema,
                tags, metadata, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tool_id,
                tool["name"],
                tool["display_name"],
                tool["description"],
                tool["category"],
                "integration",  # Mark as integration type
                tool["name"],  # Use name as integration_tool_name
                json.dumps({"type": "object", "properties": {}, "required": []}),
                json.dumps(
                    {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}}
                ),
                json.dumps(tool["tags"]),
                json.dumps({"logo": tool["logo"], "icon": tool["logo"], "docsUrl": None, "authType": "oauth2"}),
                1,  # is_active
            ),
        )
        print(f"✅ Added {tool['display_name']}")
        added_count += 1

    conn.commit()
    conn.close()

    print(f"\n🎉 Successfully added {added_count} banking platform tools!")
    print("\nBanking platforms added:")
    for tool in banking_tools:
        print(f"  - {tool['display_name']}")


if __name__ == "__main__":
    add_banking_tools()
