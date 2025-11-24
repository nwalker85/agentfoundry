"""
Apply Schema Changes for Unified Graphs
Adds graph_type, channel, and yaml_content columns to agents table.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection


def apply_schema_changes():
    """
    Apply schema changes to agents table.

    Adds:
    - graph_type TEXT DEFAULT 'user'
    - channel TEXT (nullable)
    - yaml_content TEXT (nullable)
    """
    conn = get_connection()
    cur = conn.cursor()

    print("=" * 70)
    print("APPLYING SCHEMA CHANGES: Unified Graphs")
    print("=" * 70)
    print()

    try:
        # Check if columns already exist
        cur.execute("PRAGMA table_info(agents)")
        columns = cur.fetchall()
        # Handle both dict rows and tuple rows
        if columns and isinstance(columns[0], dict):
            column_names = [col["name"] for col in columns]
        else:
            column_names = [col[1] for col in columns]

        changes_needed = []

        if "graph_type" not in column_names:
            changes_needed.append("graph_type")

        if "channel" not in column_names:
            changes_needed.append("channel")

        if "yaml_content" not in column_names:
            changes_needed.append("yaml_content")

        if not changes_needed:
            print("✓ All schema changes already applied. Nothing to do.")
            print()
            conn.close()
            return

        print(f"Columns to add: {', '.join(changes_needed)}")
        print()

        # Add graph_type column
        if "graph_type" in changes_needed:
            print("Adding graph_type column...")
            cur.execute("""
                ALTER TABLE agents
                ADD COLUMN graph_type TEXT DEFAULT 'user'
            """)
            print("  ✓ Added graph_type column")

        # Add channel column
        if "channel" in changes_needed:
            print("Adding channel column...")
            cur.execute("""
                ALTER TABLE agents
                ADD COLUMN channel TEXT
            """)
            print("  ✓ Added channel column")

        # Add yaml_content column
        if "yaml_content" in changes_needed:
            print("Adding yaml_content column...")
            cur.execute("""
                ALTER TABLE agents
                ADD COLUMN yaml_content TEXT
            """)
            print("  ✓ Added yaml_content column")

        # Create indexes
        print()
        print("Creating indexes...")

        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_graph_type
                ON agents(graph_type)
            """)
            print("  ✓ Created idx_agents_graph_type")
        except Exception as e:
            print(f"  ⚠ Index idx_agents_graph_type may already exist: {e}")

        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_channel
                ON agents(channel)
            """)
            print("  ✓ Created idx_agents_channel")
        except Exception as e:
            print(f"  ⚠ Index idx_agents_channel may already exist: {e}")

        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_org_domain
                ON agents(organization_id, domain_id)
            """)
            print("  ✓ Created idx_agents_org_domain")
        except Exception as e:
            print(f"  ⚠ Index idx_agents_org_domain may already exist: {e}")

        conn.commit()

        print()
        print("=" * 70)
        print("SCHEMA CHANGES APPLIED SUCCESSFULLY")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run migration script: python scripts/migrate_to_unified_graphs.py")
        print("  2. Restart backend: docker-compose restart foundry-backend")
        print("  3. Test unified graphs UI at /app/graphs")
        print()

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Failed to apply schema changes: {e}")
        raise

    finally:
        conn.close()


def main():
    """Run the schema migration"""
    try:
        apply_schema_changes()
        return 0
    except Exception as e:
        print(f"\n✗ Schema migration failed: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
