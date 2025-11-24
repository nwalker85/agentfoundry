"""
PostgreSQL Backup and Management Utilities

Provides backup/restore and database management for PostgreSQL.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "backups" / "postgres"

# PostgreSQL connection from environment (use admin-specific URL)
# POSTGRES_ADMIN_URL is separate from DATABASE_URL which may be SQLite
POSTGRES_URL = os.getenv("POSTGRES_ADMIN_URL", "postgresql://foundry:foundry@postgres:5432/foundry")


@dataclass
class PostgresBackup:
    filename: str
    path: Path
    size_bytes: int
    created_at: datetime
    label: str | None = None
    created_by: str | None = None
    created_by_email: str | None = None


def get_pg_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(POSTGRES_URL)


def _parse_pg_url(url: str) -> dict[str, str]:
    """Parse PostgreSQL URL into components"""
    # postgresql://user:password@host:port/database
    import re

    pattern = r"postgresql://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)/(?P<database>.+)"
    match = re.match(pattern, url)
    if match:
        return match.groupdict()
    return {"user": "foundry", "password": "foundry", "host": "localhost", "port": "5432", "database": "foundry"}


def _ensure_paths() -> None:
    """Ensure backup directory exists"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize_label(label: str | None) -> str | None:
    """Sanitize backup label"""
    if not label:
        return None
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", label.strip())
    return sanitized or None


def _parse_label(filename: str) -> str | None:
    """Parse label from backup filename"""
    base = Path(filename).stem
    parts = base.split("-", 4)
    if len(parts) <= 4:
        return None
    label = "-".join(parts[4:])
    return label or None


def create_backup(
    label: str | None = None, user_name: str | None = None, user_email: str | None = None
) -> PostgresBackup:
    """
    Create PostgreSQL backup using pg_dump.
    Creates a custom format dump for best compression and flexibility.
    """
    _ensure_paths()

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    suffix = ""
    sanitized_label = _sanitize_label(label)
    if sanitized_label:
        suffix = f"-{sanitized_label}"

    backup_path = BACKUP_DIR / f"postgres_{timestamp}{suffix}.dump"

    # Parse POSTGRES_URL
    db_config = _parse_pg_url(POSTGRES_URL)

    # Set environment for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    # Run pg_dump
    cmd = [
        "pg_dump",
        "-h",
        db_config["host"],
        "-p",
        db_config["port"],
        "-U",
        db_config["user"],
        "-d",
        db_config["database"],
        "-F",
        "c",  # Custom format
        "-f",
        str(backup_path),
    ]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"pg_dump failed: {e.stderr}")

    # Save metadata with user audit info
    import json

    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "label": label,
        "created_by": user_name,
        "created_by_email": user_email,
    }
    metadata_path = backup_path.with_suffix(".dump.meta.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return _build_backup_info(backup_path)


def list_backups() -> list[PostgresBackup]:
    """List all PostgreSQL backups"""
    _ensure_paths()
    backups = sorted(
        BACKUP_DIR.glob("postgres_*.dump"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [_build_backup_info(path) for path in backups]


def restore_backup(filename: str, clean: bool = False) -> dict[str, Any]:
    """
    Restore PostgreSQL backup using pg_restore.

    Args:
        filename: Backup filename to restore
        clean: If True, drop database objects before recreating (WARNING: destructive)

    Returns:
        Dictionary with restore statistics
    """
    _ensure_paths()
    target = _resolve_backup(filename)

    if not target.exists():
        raise FileNotFoundError(f"Backup not found: {filename}")

    # Parse POSTGRES_URL
    db_config = _parse_pg_url(POSTGRES_URL)

    # Set environment for pg_restore
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    # Build pg_restore command
    cmd = [
        "pg_restore",
        "-h",
        db_config["host"],
        "-p",
        db_config["port"],
        "-U",
        db_config["user"],
        "-d",
        db_config["database"],
        "-v",  # Verbose
    ]

    if clean:
        cmd.append("-c")  # Clean (drop) database objects before recreating

    cmd.append(str(target))

    try:
        result = subprocess.run(cmd, check=False, env=env, capture_output=True, text=True)
        # pg_restore may have warnings but still succeed
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"pg_restore failed: {e.stderr}")


def get_backup_file(filename: str) -> Path:
    """Get path to backup file"""
    return _resolve_backup(filename)


def get_postgres_info() -> dict[str, Any]:
    """Get PostgreSQL server information"""
    conn = get_pg_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get version
    cursor.execute("SELECT version()")
    version = cursor.fetchone()["version"]

    # Get database size
    cursor.execute("""
        SELECT pg_size_pretty(pg_database_size(current_database())) as size
    """)
    db_size = cursor.fetchone()["size"]

    # Get table count
    cursor.execute("""
        SELECT COUNT(*) as table_count
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    table_count = cursor.fetchone()["table_count"]

    cursor.close()
    conn.close()

    return {"version": version, "database_size": db_size, "table_count": table_count}


def list_tables() -> list[dict[str, Any]]:
    """List all PostgreSQL tables with row counts"""
    conn = get_pg_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)

    tables = []
    for row in cursor.fetchall():
        table_name = row["tablename"]

        # Get row count
        cursor.execute(f'SELECT COUNT(*) as row_count FROM "{table_name}"')
        row_count = cursor.fetchone()["row_count"]

        tables.append({"name": table_name, "schema": row["schemaname"], "size": row["size"], "row_count": row_count})

    cursor.close()
    conn.close()

    return tables


def get_table_schema(table_name: str) -> list[dict[str, Any]]:
    """Get schema for a specific table"""
    conn = get_pg_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """,
        (table_name,),
    )

    columns = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(col) for col in columns]


def get_table_rows(table_name: str, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    """Get rows from a specific table"""
    conn = get_pg_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Safely quote table name to prevent SQL injection
    quoted_table = f'"{table_name}"'

    cursor.execute(
        f"""
        SELECT * FROM {quoted_table}
        LIMIT %s OFFSET %s
    """,
        (limit, offset),
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return [dict(row) for row in rows]


def export_table_sql(table_name: str) -> str:
    """
    Export a table to SQL format using pg_dump.
    Returns the SQL content as a string.
    """
    db_config = _parse_pg_url(POSTGRES_URL)

    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "pg_dump",
        "-h",
        db_config["host"],
        "-p",
        db_config["port"],
        "-U",
        db_config["user"],
        "-d",
        db_config["database"],
        "-t",
        table_name,  # Specific table
        "--inserts",  # Use INSERT statements instead of COPY
    ]

    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"pg_dump failed: {e.stderr}")


def _resolve_backup(filename: str) -> Path:
    """Resolve backup file path"""
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate
    if filename.startswith("backups/"):
        return PROJECT_ROOT / filename
    return BACKUP_DIR / filename


def _build_backup_info(path: Path) -> PostgresBackup:
    """Build backup info from file"""
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_mtime)
    label = _parse_label(path.name)

    # Try to load metadata with user info
    created_by = None
    created_by_email = None
    metadata_path = path.with_suffix(".dump.meta.json")
    if metadata_path.exists():
        try:
            import json

            with open(metadata_path) as f:
                metadata = json.load(f)
                created_by = metadata.get("created_by")
                created_by_email = metadata.get("created_by_email")
        except Exception:
            pass  # If metadata can't be read, just skip it

    return PostgresBackup(
        filename=path.name,
        path=path,
        size_bytes=stat.st_size,
        created_at=created_at,
        label=label,
        created_by=created_by,
        created_by_email=created_by_email,
    )
