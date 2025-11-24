#!/usr/bin/env python3
"""
Load CIBC tools from YAML file into the function_catalog table.
"""

import json
import sys
from pathlib import Path

import yaml

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection


def convert_tool_to_json_schema(tool):
    """Convert tool parameters to JSON Schema format."""
    parameters = tool.get("parameters", {})

    # Build JSON Schema properties
    properties = {}
    required = []

    for param_name, param_def in parameters.items():
        param_type = param_def.get("type", "string")
        param_schema = {"type": param_type, "description": param_def.get("description", "")}

        # Handle array types
        if param_type == "array":
            param_schema["items"] = param_def.get("items", {"type": "string"})
            if "minItems" in param_def:
                param_schema["minItems"] = param_def["minItems"]
            if "maxItems" in param_def:
                param_schema["maxItems"] = param_def["maxItems"]

        # Handle object types
        if param_type == "object":
            param_schema["properties"] = param_def.get("properties", {})

        # Handle enums
        if "enum" in param_def:
            param_schema["enum"] = param_def["enum"]

        # Handle formats
        if "format" in param_def:
            param_schema["format"] = param_def["format"]

        properties[param_name] = param_schema

        # Check if required
        if param_def.get("required", False):
            required.append(param_name)

    # Build complete JSON Schema
    input_schema = {"type": "object", "properties": properties, "required": required}

    # Build output schema
    returns = tool.get("returns", {})
    output_schema = {"type": returns.get("type", "object"), "properties": returns.get("properties", {})}

    return input_schema, output_schema


def load_cibc_tools():
    """Load all CIBC tools from YAML file into function_catalog."""

    # Path to CIBC tools YAML
    tools_file = Path(__file__).parent.parent / "app" / "tools" / "cibc_tools.yaml"

    if not tools_file.exists():
        print(f"❌ CIBC tools file not found: {tools_file}")
        return

    print(f"📁 Loading CIBC tools from: {tools_file}")
    print()

    # Read YAML file
    with open(tools_file, encoding="utf-8") as f:
        tools = yaml.safe_load(f)

    if not tools:
        print("❌ No tools found in YAML file")
        return

    print(f"📊 Found {len(tools)} tools to register")
    print()

    conn = get_connection()
    cur = conn.cursor()

    success_count = 0
    error_count = 0
    updated_count = 0

    for tool in tools:
        try:
            tool_name = tool.get("name")
            display_name = tool.get("display_name", tool_name)
            description = tool.get("description", "")
            category = tool.get("category", "custom")
            agent_group = tool.get("agent_group", "")

            # Generate unique ID from name
            tool_id = f"cibc-{tool_name}"

            # Convert parameters to JSON Schema
            input_schema, output_schema = convert_tool_to_json_schema(tool)

            # Prepare data
            tags = json.dumps(["cibc", category, agent_group])

            metadata = json.dumps(
                {"agent_group": agent_group, "category": category, "organization": "cibc", "domain": "card-services"}
            )

            # Check if tool already exists
            cur.execute("SELECT id FROM function_catalog WHERE id = ?", (tool_id,))
            exists = cur.fetchone()

            if exists:
                # Update existing
                cur.execute(
                    """
                    UPDATE function_catalog
                    SET display_name = ?,
                        description = ?,
                        category = ?,
                        type = 'custom',
                        input_schema = ?,
                        output_schema = ?,
                        tags = ?,
                        metadata = ?,
                        is_active = 1,
                        updated_at = datetime('now', 'utc')
                    WHERE id = ?
                """,
                    (
                        display_name,
                        description,
                        category,
                        json.dumps(input_schema),
                        json.dumps(output_schema),
                        tags,
                        metadata,
                        tool_id,
                    ),
                )
                print(f"♻️  Updated: {display_name}")
                updated_count += 1
            else:
                # Insert new
                cur.execute(
                    """
                    INSERT INTO function_catalog (
                        id, name, display_name, description, category, type,
                        input_schema, output_schema, tags, metadata, is_active,
                        created_by
                    )
                    VALUES (?, ?, ?, ?, ?, 'custom', ?, ?, ?, ?, 1, 'system')
                """,
                    (
                        tool_id,
                        tool_name,
                        display_name,
                        description,
                        category,
                        json.dumps(input_schema),
                        json.dumps(output_schema),
                        tags,
                        metadata,
                    ),
                )
                print(f"✅ Registered: {display_name}")
                success_count += 1

            print(f"   ID: {tool_id}")
            print(f"   Category: {category}")
            print(f"   Agent Group: {agent_group}")
            print()

        except Exception as e:
            print(f"❌ Error loading {tool.get('name', 'unknown')}: {e}")
            print()
            error_count += 1

    conn.commit()
    conn.close()

    print("=" * 60)
    print("📊 Summary:")
    print(f"   ✅ Newly registered: {success_count} tools")
    print(f"   ♻️  Updated: {updated_count} tools")
    print(f"   ❌ Errors: {error_count}")
    print()

    # Verify in database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as count
        FROM function_catalog
        WHERE id LIKE 'cibc-%'
    """)
    count = cur.fetchone()["count"]
    conn.close()

    print(f"🗄️  Total CIBC tools in catalog: {count}")
    print()


if __name__ == "__main__":
    print("🚀 CIBC Tools Loader")
    print("=" * 60)
    print()
    load_cibc_tools()
    print("✅ Done!")
