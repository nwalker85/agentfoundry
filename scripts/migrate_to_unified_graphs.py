"""
Migration Script: Channel Workflows to Unified Graphs
Migrates existing channel_workflows from DB to YAML files and agents table.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection
from backend.utils import yaml_storage


def migrate_channel_workflows():
    """
    Migrate channel workflows from channel_workflows table to unified graphs system.

    Steps:
    1. Read all channel_workflows from DB
    2. Convert to unified YAML format
    3. Write to agents/channels/{channel}/{workflow_name}.yaml
    4. Insert into agents table with graph_type='channel'
    5. Backup old channel_workflows table data
    """
    conn = get_connection()
    cur = conn.cursor()

    print("=" * 70)
    print("MIGRATION: Channel Workflows → Unified Graphs")
    print("=" * 70)
    print()

    # Step 1: Read existing channel workflows
    print("Step 1: Reading existing channel workflows from DB...")
    cur.execute("SELECT * FROM channel_workflows")
    workflows = cur.fetchall()

    if not workflows:
        print("  ✓ No channel workflows found. Nothing to migrate.")
        conn.close()
        return

    print(f"  ✓ Found {len(workflows)} workflows to migrate")
    print()

    # Step 2: Backup to JSON file
    print("Step 2: Creating backup...")
    backup_dir = Path(__file__).parent.parent / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_file = backup_dir / f"channel_workflows_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    backup_data = []
    for workflow in workflows:
        backup_data.append(dict(workflow))

    with open(backup_file, "w") as f:
        json.dump(backup_data, f, indent=2, default=str)

    print(f"  ✓ Backup created: {backup_file}")
    print()

    # Step 3: Ensure directory structure
    print("Step 3: Ensuring YAML directory structure...")
    yaml_storage.ensure_directories()
    print("  ✓ Directories created")
    print()

    # Step 4: Migrate each workflow
    print("Step 4: Migrating workflows to YAML and agents table...")
    migrated_count = 0
    errors = []

    for workflow in workflows:
        try:
            # Parse existing data
            workflow_id = workflow["id"]
            channel = workflow["channel"]
            name = workflow["name"] or f"{channel}-workflow"
            description = workflow["description"] or f"Channel workflow for {channel}"

            # Parse nodes and edges
            nodes_json = workflow["nodes_json"]
            edges_json = workflow["edges_json"]

            nodes = json.loads(nodes_json) if nodes_json else []
            edges = json.loads(edges_json) if edges_json else []

            # Parse metadata
            metadata_json = workflow["metadata_json"]
            metadata = json.loads(metadata_json) if metadata_json else {}

            # Create unified graph YAML structure
            graph_data = {
                "apiVersion": "foundry.ai/v1",
                "kind": "AgentGraph",
                "metadata": {
                    "id": workflow_id,
                    "name": name,
                    "display_name": name,
                    "description": description,
                    "type": "channel",
                    "channel": channel,
                    "version": "1.0.0",
                    "created": workflow["created_at"] or datetime.utcnow().isoformat() + "Z",
                    "updated": workflow["updated_at"] or datetime.utcnow().isoformat() + "Z",
                    **metadata,
                },
                "spec": {
                    "state_schema_id": workflow.get("state_schema_id"),
                    "triggers": [],
                    "graph": {"nodes": nodes, "edges": edges},
                },
            }

            # Write YAML file
            yaml_path = yaml_storage.write_graph_yaml(graph_data)

            # Insert into agents table
            cur.execute(
                """
                INSERT OR REPLACE INTO agents (
                    id, organization_id, domain_id, name, display_name, description,
                    version, status, environment, yaml_path, is_system_agent, system_tier,
                    created_by, tags, graph_type, channel, yaml_content, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow_id,
                    None,  # organization_id (NULL for channel workflows)
                    None,  # domain_id (NULL for channel workflows)
                    name,
                    name,  # display_name
                    description,
                    "1.0.0",  # version
                    "active",  # status
                    "dev",  # environment
                    yaml_path,
                    0,  # is_system_agent
                    None,  # system_tier
                    workflow.get("created_by", "system"),
                    "[]",  # tags
                    "channel",  # graph_type
                    channel,
                    json.dumps(graph_data),  # yaml_content
                    workflow["created_at"],
                    workflow["updated_at"],
                ),
            )

            print(f"  ✓ Migrated: {name} ({channel})")
            migrated_count += 1

        except Exception as e:
            error_msg = f"Failed to migrate workflow {workflow.get('id', 'unknown')}: {e!s}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")

    conn.commit()
    print()
    print(f"  ✓ Successfully migrated {migrated_count}/{len(workflows)} workflows")
    print()

    # Step 5: Report
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Total workflows found: {len(workflows)}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Errors: {len(errors)}")
    print(f"Backup location: {backup_file}")
    print()

    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()

    # Step 6: Ask about cleanup
    print("Next steps:")
    print("  1. Verify migrated data in /agents/channels/ directory")
    print("  2. Test the unified graphs UI at /app/graphs")
    print("  3. If everything looks good, you can manually drop the channel_workflows table:")
    print("     DROP TABLE channel_workflows;")
    print()

    conn.close()


def main():
    """Run the migration"""
    try:
        migrate_channel_workflows()
        print("✓ Migration completed successfully!")
        return 0
    except Exception as e:
        print(f"\n✗ Migration failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
