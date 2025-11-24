#!/usr/bin/env python3
"""
Function Catalog Population Script

Populates the function_catalog table from the integrations.manifest.json file.
This makes all n8n integrations available as tools in Agent Foundry.

Usage:
    python scripts/populate_function_catalog.py

Environment Variables:
    DATABASE_URL - Database connection string (default: postgresql://foundry:foundry@postgres:5432/foundry)
"""

import json
import logging
import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get database connection based on DATABASE_URL"""
    db_url = os.getenv("DATABASE_URL", "postgresql://foundry:foundry@postgres:5432/foundry")

    if db_url.startswith("sqlite"):
        import sqlite3

        # Extract file path from sqlite URL
        db_path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
        if not db_path.startswith("/"):
            # Relative path - resolve from project root
            db_path = Path(__file__).parent.parent / db_path

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        return conn, "sqlite"
    elif db_url.startswith("postgresql"):
        import psycopg2

        conn = psycopg2.connect(db_url)
        return conn, "postgres"
    else:
        raise NotImplementedError(f"Database type not supported: {db_url}")


def compute_entry_hash(entry: dict) -> str:
    """Compute a hash of the manifest entry for change detection."""
    import hashlib
    # Include only fields that matter for change detection
    relevant = {
        "toolName": entry.get("toolName"),
        "displayName": entry.get("displayName"),
        "description": entry.get("description", ""),
        "category": entry.get("category", "Other"),
        "tags": entry.get("tags", []),
        "metadata": entry.get("metadata", {}),
        "inputSchema": entry.get("inputSchema", {}),
        "outputSchema": entry.get("outputSchema", {}),
    }
    return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:16]


def populate_from_manifest(
    manifest_path: str = "mcp/integration_server/config/integrations.manifest.json",
    clear_existing: bool = False,
) -> int:
    """
    Populate function_catalog from manifest file using UPSERT semantics.

    Args:
        manifest_path: Path to integrations.manifest.json
        clear_existing: If True, delete existing integration tools first (deprecated, avoid using)

    Returns:
        Number of functions created/updated
    """
    logger.info("Starting function catalog population...")

    # Load manifest
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return 0

    with manifest_file.open("r") as f:
        manifest = json.load(f)

    logger.info(f"Loaded {len(manifest)} integrations from manifest")

    # Connect to database
    conn, db_type = get_db_connection()
    cur = conn.cursor()

    # Determine placeholder style
    placeholder = "?" if db_type == "sqlite" else "%s"

    try:
        # Clear existing integration tools if requested (deprecated behavior)
        if clear_existing:
            logger.warning("--clear flag is deprecated. Using UPSERT semantics instead.")

        # Build set of tool names from manifest for orphan detection
        manifest_tool_names = {entry["toolName"] for entry in manifest}

        # Get existing integrations with their content hashes
        cur.execute(
            "SELECT id, name, metadata FROM function_catalog WHERE type = 'integration'"
        )
        existing_rows = cur.fetchall()
        existing_by_name = {}
        for row in existing_rows:
            func_id, name, metadata_json = row
            # Extract stored hash from metadata
            try:
                metadata = json.loads(metadata_json) if metadata_json else {}
            except (json.JSONDecodeError, TypeError):
                metadata = {}
            existing_by_name[name] = {
                "id": func_id,
                "content_hash": metadata.get("_content_hash", ""),
            }

        # Track statistics
        created = 0
        updated = 0
        unchanged = 0
        removed = 0

        for entry in manifest:
            tool_name = entry["toolName"]
            display_name = entry["displayName"]
            description = entry.get("description", "")
            category = entry.get("category", "Other")
            tags = entry.get("tags", [])
            metadata = entry.get("metadata", {})
            input_schema = entry.get("inputSchema", {})
            output_schema = entry.get("outputSchema", {})

            # Compute content hash for change detection
            content_hash = compute_entry_hash(entry)
            metadata["_content_hash"] = content_hash

            existing = existing_by_name.get(tool_name)

            if existing:
                # Check if content actually changed
                if existing["content_hash"] == content_hash:
                    unchanged += 1
                    continue

                # Update existing (content changed)
                function_id = existing["id"]
                if db_type == "sqlite":
                    cur.execute(
                        """
                        UPDATE function_catalog
                        SET display_name = ?,
                            description = ?,
                            category = ?,
                            input_schema = ?,
                            output_schema = ?,
                            tags = ?,
                            metadata = ?,
                            integration_tool_name = ?,
                            updated_at = datetime('now', 'utc')
                        WHERE id = ?
                        """,
                        (
                            display_name,
                            description,
                            category,
                            json.dumps(input_schema),
                            json.dumps(output_schema),
                            json.dumps(tags),
                            json.dumps(metadata),
                            tool_name,
                            function_id,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE function_catalog
                        SET display_name = %s,
                            description = %s,
                            category = %s,
                            input_schema = %s,
                            output_schema = %s,
                            tags = %s,
                            metadata = %s,
                            integration_tool_name = %s,
                            updated_at = NOW()
                        WHERE id = %s
                        """,
                        (
                            display_name,
                            description,
                            category,
                            json.dumps(input_schema),
                            json.dumps(output_schema),
                            json.dumps(tags),
                            json.dumps(metadata),
                            tool_name,
                            function_id,
                        ),
                    )
                updated += 1
            else:
                # Create new
                function_id = str(uuid.uuid4())
                if db_type == "sqlite":
                    cur.execute(
                        """
                        INSERT INTO function_catalog (
                            id, name, display_name, description, category, type,
                            integration_tool_name, input_schema, output_schema,
                            tags, metadata, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            function_id,
                            tool_name,
                            display_name,
                            description,
                            category,
                            "integration",
                            tool_name,
                            json.dumps(input_schema),
                            json.dumps(output_schema),
                            json.dumps(tags),
                            json.dumps(metadata),
                            1,  # is_active
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO function_catalog (
                            id, name, display_name, description, category, type,
                            integration_tool_name, input_schema, output_schema,
                            tags, metadata, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            function_id,
                            tool_name,
                            display_name,
                            description,
                            category,
                            "integration",
                            tool_name,
                            json.dumps(input_schema),
                            json.dumps(output_schema),
                            json.dumps(tags),
                            json.dumps(metadata),
                            True,  # is_active (boolean for postgres)
                        ),
                    )
                created += 1

        # Remove orphaned integrations (in manifest before but not now)
        orphaned_names = set(existing_by_name.keys()) - manifest_tool_names
        if orphaned_names:
            for orphan_name in orphaned_names:
                cur.execute(
                    f"DELETE FROM function_catalog WHERE name = {placeholder} AND type = 'integration'",
                    (orphan_name,),
                )
                removed += 1

        conn.commit()

        logger.info(f"Created {created}, updated {updated}, unchanged {unchanged}, removed {removed}")

        # Print summary
        cur.execute(
            """
            SELECT category, COUNT(*) as count
            FROM function_catalog
            WHERE type = 'integration'
            GROUP BY category
            ORDER BY count DESC
            """
        )
        categories = cur.fetchall()

        logger.info("\nFunction Catalog by Category:")
        for cat, count in categories:
            logger.info(f"  {cat}: {count}")

        return created + updated

    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Populate function catalog from manifest")
    parser.add_argument(
        "--manifest",
        "-m",
        default="mcp/integration_server/config/integrations.manifest.json",
        help="Path to manifest file",
    )
    parser.add_argument(
        "--clear",
        "-c",
        action="store_true",
        help="Clear existing integration tools before populating",
    )

    args = parser.parse_args()

    try:
        count = populate_from_manifest(
            manifest_path=args.manifest,
            clear_existing=args.clear,
        )
        sys.exit(0 if count > 0 else 1)
    except Exception as exc:
        logger.error(f"Failed to populate function catalog: {exc}", exc_info=True)
        sys.exit(1)
