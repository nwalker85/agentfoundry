#!/usr/bin/env python3
"""
PostgreSQL Database Initialization Script

This script initializes the PostgreSQL database with:
1. Schema creation (tables + RLS policies)
2. RBAC roles and permissions
3. Initial seed data (organizations, domains, agents)

Usage:
    python scripts/init-postgres.py

    # Or from Docker:
    docker-compose exec foundry-backend python scripts/init-postgres.py
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Initialize PostgreSQL database with schema and seed data."""
    logger.info("=" * 60)
    logger.info("PostgreSQL Database Initialization")
    logger.info("=" * 60)

    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL", "postgresql://foundry:foundry@postgres:5432/foundry")
    logger.info(f"Database URL: {database_url.replace(database_url.split(':')[2].split('@')[0], '***')}")

    if "sqlite" in database_url.lower():
        logger.error("DATABASE_URL points to SQLite! This script requires PostgreSQL.")
        logger.error("Set DATABASE_URL=postgresql://foundry:foundry@postgres:5432/foundry")
        sys.exit(1)

    # Import after path setup
    try:
        from backend.db import init_db
        from backend.db_postgres import DictCursor, get_connection_no_rls
    except ImportError as e:
        logger.error(f"Failed to import database modules: {e}")
        logger.error("Make sure you're running from the project root or within Docker")
        sys.exit(1)

    # Test connection first
    logger.info("Testing database connection...")
    try:
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT version()")
            version = cur.fetchone()
            logger.info(f"Connected to: {version['version'][:50]}...")
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        logger.error("Make sure PostgreSQL is running: docker-compose up -d postgres")
        sys.exit(1)

    # Initialize database
    logger.info("Initializing database schema...")
    try:
        init_db()
        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Verify tables were created
    logger.info("Verifying table creation...")
    try:
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)

            # Count tables
            cur.execute("""
                SELECT COUNT(*) as count
                FROM pg_tables
                WHERE schemaname = 'public'
            """)
            table_count = cur.fetchone()["count"]
            logger.info(f"Created {table_count} tables")

            # List key tables
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            tables = [row["tablename"] for row in cur.fetchall()]
            logger.info(f"Tables: {', '.join(tables[:10])}...")

            # Check RLS is enabled
            cur.execute("""
                SELECT COUNT(*) as count
                FROM pg_tables t
                JOIN pg_class c ON c.relname = t.tablename
                WHERE t.schemaname = 'public'
                  AND c.relrowsecurity = true
            """)
            rls_count = cur.fetchone()["count"]
            logger.info(f"Tables with RLS enabled: {rls_count}")

            # Check seed data
            cur.execute("SELECT COUNT(*) as count FROM organizations")
            org_count = cur.fetchone()["count"]
            logger.info(f"Organizations seeded: {org_count}")

            cur.execute("SELECT COUNT(*) as count FROM agents")
            agent_count = cur.fetchone()["count"]
            logger.info(f"Agents seeded: {agent_count}")

            conn.commit()

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("PostgreSQL initialization complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Restart the backend: docker-compose restart foundry-backend")
    logger.info("  2. Verify health: curl http://localhost:8000/health")
    logger.info("  3. Check RLS: docker-compose exec postgres psql -U foundry -c '\\d+ agents'")
    logger.info("")


if __name__ == "__main__":
    main()
