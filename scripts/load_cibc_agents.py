#!/usr/bin/env python3
"""
Load all CIBC agent graphs from YAML templates into the platform database.
"""

import sys
from pathlib import Path

import yaml

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


from backend.db import get_connection, upsert_graph


def load_cibc_agents():
    """Load all CIBC agent graphs from templates directory."""

    # Path to CIBC agent templates
    templates_dir = Path(__file__).parent.parent / "agents" / "templates"

    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    # Find all CIBC agent YAML files
    cibc_files = sorted(templates_dir.glob("cibc-*.yaml"))

    if not cibc_files:
        print(f"❌ No CIBC agent files found in {templates_dir}")
        return

    print(f"📁 Found {len(cibc_files)} CIBC agent files")
    print()

    success_count = 0
    error_count = 0

    for yaml_path in cibc_files:
        try:
            # Read YAML file
            with open(yaml_path, encoding="utf-8") as f:
                agent_data = yaml.safe_load(f)

            # Extract metadata
            metadata = agent_data.get("metadata", {})
            name = metadata.get("name", yaml_path.stem)

            # Generate unique ID from name
            agent_id = f"cibc-{yaml_path.stem}"

            # Build graph data structure for upsert_graph
            graph_data = {
                "id": agent_id,
                "metadata": {
                    "id": agent_id,
                    "name": name,
                    "display_name": name,
                    "description": metadata.get("description", ""),
                    "version": metadata.get("version", "1.0.0"),
                    "type": metadata.get("type", "system"),
                    "status": "active",
                    "environment": "dev",
                    "organization_id": "cibc",
                    "domain_id": "card-services",
                    "created_by": "system",
                    "tags": metadata.get("tags", []),
                },
                "spec": agent_data.get("spec", {}),
            }

            # Register in database
            result = upsert_graph(graph_data)

            print(f"✅ Loaded: {name}")
            print(f"   ID: {agent_id}")
            print(f"   File: {yaml_path.name}")
            print()

            success_count += 1

        except Exception as e:
            print(f"❌ Error loading {yaml_path.name}: {e}")
            print()
            error_count += 1

    print("=" * 60)
    print("📊 Summary:")
    print(f"   ✅ Successfully loaded: {success_count} agents")
    print(f"   ❌ Errors: {error_count}")
    print()

    # Verify in database
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as count
        FROM agents
        WHERE organization_id = 'cibc' AND domain_id = 'card-services'
    """)
    count = cur.fetchone()["count"]
    conn.close()

    print(f"🗄️  Total CIBC agents in database: {count}")
    print()


if __name__ == "__main__":
    print("🚀 CIBC Agent Loader")
    print("=" * 60)
    print()
    load_cibc_agents()
    print("✅ Done!")
