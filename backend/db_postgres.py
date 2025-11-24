"""
PostgreSQL Database Layer with Row-Level Security (RLS)

This module provides:
1. Connection pooling via psycopg2.pool.ThreadedConnectionPool
2. Automatic RLS context injection (SET app.current_tenant)
3. Dict-like row factory for compatibility with existing code
4. Transaction management helpers

Usage:
    from backend.db_postgres import get_connection, execute_query

    # Context is automatically set from backend.context module
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agents")  # RLS filters automatically
        rows = cursor.fetchall()
"""

import json
import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2 import extras, pool
from psycopg2.extensions import connection as PgConnection, cursor as PgCursor

from backend.context import get_tenant_id

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://foundry:foundry@postgres:5432/foundry")


# Parse DATABASE_URL for pool config
# Format: postgresql://user:pass@host:port/dbname
def _parse_db_url(url: str) -> dict[str, Any]:
    """Parse PostgreSQL connection URL into components."""
    # Handle both postgresql:// and postgres:// schemes
    url = url.replace("postgres://", "postgresql://")

    if url.startswith("postgresql://"):
        url = url[13:]  # Remove scheme

    # Split user:pass@host:port/dbname
    if "@" in url:
        creds, rest = url.split("@", 1)
        user, password = creds.split(":", 1) if ":" in creds else (creds, "")
    else:
        user, password = "", ""
        rest = url

    if "/" in rest:
        hostport, dbname = rest.split("/", 1)
    else:
        hostport, dbname = rest, "foundry"

    if ":" in hostport:
        host, port = hostport.split(":", 1)
        port = int(port)
    else:
        host, port = hostport, 5432

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }


# Pool configuration
POOL_MIN_CONNECTIONS = int(os.getenv("DB_POOL_MIN", "2"))
POOL_MAX_CONNECTIONS = int(os.getenv("DB_POOL_MAX", "10"))

# Global connection pool (initialized lazily)
_connection_pool: pool.ThreadedConnectionPool | None = None


# =============================================================================
# CONNECTION POOL MANAGEMENT
# =============================================================================


def _get_pool() -> pool.ThreadedConnectionPool:
    """Get or create the connection pool."""
    global _connection_pool

    if _connection_pool is None:
        db_config = _parse_db_url(DATABASE_URL)
        logger.info(
            f"Creating PostgreSQL connection pool: {db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        )

        _connection_pool = pool.ThreadedConnectionPool(
            minconn=POOL_MIN_CONNECTIONS, maxconn=POOL_MAX_CONNECTIONS, **db_config
        )
        logger.info(f"Connection pool created (min={POOL_MIN_CONNECTIONS}, max={POOL_MAX_CONNECTIONS})")

    return _connection_pool


def close_pool() -> None:
    """Close the connection pool. Call on application shutdown."""
    global _connection_pool
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Connection pool closed")


# =============================================================================
# ROW FACTORY (Dict-like rows for compatibility)
# =============================================================================


class DictCursor(extras.RealDictCursor):
    """Cursor that returns rows as dictionaries."""

    pass


def dict_row_factory(cursor: PgCursor) -> dict[str, Any]:
    """Convert a row to a dictionary using column names."""
    if cursor.description is None:
        return {}
    columns = [col.name for col in cursor.description]
    return dict(zip(columns, cursor.fetchone() or []))


# =============================================================================
# RLS-AWARE CONNECTION WRAPPER
# =============================================================================


class RLSConnection:
    """
    Wrapper around psycopg2 connection that automatically sets RLS context.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents")
    """

    def __init__(self, conn: PgConnection, tenant_id: str | None = None):
        self._conn = conn
        self._tenant_id = tenant_id
        self._rls_set = False

    def _ensure_rls_context(self) -> None:
        """Set RLS context variables on the connection."""
        if self._rls_set:
            return

        tenant = self._tenant_id or get_tenant_id()

        with self._conn.cursor() as cur:
            if tenant:
                cur.execute("SET app.current_tenant = %s", (tenant,))
                logger.debug(f"RLS context set: tenant={tenant}")
            else:
                # Reset to empty (no filtering)
                cur.execute("RESET app.current_tenant")
                logger.debug("RLS context reset (no tenant)")

        self._rls_set = True

    def cursor(self, cursor_factory=None) -> PgCursor:
        """Get a cursor with RLS context set."""
        self._ensure_rls_context()
        return self._conn.cursor(cursor_factory=cursor_factory or DictCursor)

    def commit(self) -> None:
        """Commit the transaction."""
        self._conn.commit()

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._conn.rollback()

    def close(self) -> None:
        """Return connection to pool (don't actually close)."""
        # RLS context is reset when connection is returned to pool
        try:
            with self._conn.cursor() as cur:
                cur.execute("RESET app.current_tenant")
        except Exception:
            pass  # Best effort cleanup

        _get_pool().putconn(self._conn)

    # Allow using connection directly for execute
    def execute(self, query: str, params: tuple = None):
        """Execute a query directly."""
        cursor = self.cursor()
        cursor.execute(query, params)
        return cursor

    @property
    def raw_connection(self) -> PgConnection:
        """Access the underlying psycopg2 connection."""
        return self._conn


# =============================================================================
# CONNECTION HELPERS
# =============================================================================


@contextmanager
def get_connection(tenant_id: str | None = None) -> Generator[RLSConnection, None, None]:
    """
    Get a database connection with RLS context.

    Args:
        tenant_id: Optional tenant ID override. If not provided, uses context.

    Yields:
        RLSConnection wrapper with RLS context set

    Example:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM agents")
            rows = cur.fetchall()
    """
    pool = _get_pool()
    conn = pool.getconn()

    try:
        wrapper = RLSConnection(conn, tenant_id)
        yield wrapper
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        wrapper.close()


@contextmanager
def get_connection_no_rls() -> Generator[PgConnection, None, None]:
    """
    Get a raw connection WITHOUT RLS filtering.

    Use for admin operations, migrations, and system queries.
    Connection is automatically returned to pool when context exits.

    Example:
        with get_connection_no_rls() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            cur.execute("SELECT * FROM organizations")
            rows = cur.fetchall()
    """
    pool = _get_pool()
    conn = pool.getconn()

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# =============================================================================
# QUERY HELPERS
# =============================================================================


def execute_query(query: str, params: tuple = None, tenant_id: str | None = None, fetch: str = "all") -> Any:
    """
    Execute a query and return results.

    Args:
        query: SQL query string
        params: Query parameters (tuple)
        tenant_id: Optional tenant override
        fetch: "all", "one", or "none"

    Returns:
        Query results based on fetch mode
    """
    with get_connection(tenant_id) as conn:
        cur = conn.cursor()
        cur.execute(query, params)

        if fetch == "all":
            return cur.fetchall()
        elif fetch == "one":
            return cur.fetchone()
        else:
            return None


def execute_many(query: str, params_list: list[tuple], tenant_id: str | None = None) -> int:
    """
    Execute a query with multiple parameter sets.

    Args:
        query: SQL query string
        params_list: List of parameter tuples
        tenant_id: Optional tenant override

    Returns:
        Number of rows affected
    """
    with get_connection(tenant_id) as conn:
        cur = conn.cursor()
        cur.executemany(query, params_list)
        return cur.rowcount


# =============================================================================
# TRANSACTION HELPERS
# =============================================================================


@contextmanager
def transaction(tenant_id: str | None = None) -> Generator[RLSConnection, None, None]:
    """
    Context manager for explicit transaction handling.

    Commits on success, rolls back on exception.

    Example:
        with transaction() as conn:
            conn.execute("INSERT INTO ...")
            conn.execute("UPDATE ...")
            # Auto-commits if no exception
    """
    with get_connection(tenant_id) as conn:
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# =============================================================================
# SCHEMA INITIALIZATION
# =============================================================================


def init_schema(schema_path: str | None = None) -> None:
    """
    Initialize database schema from SQL file.

    Args:
        schema_path: Path to schema SQL file. Defaults to db_schema_postgres.sql
    """
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), "db_schema_postgres.sql")

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return

    logger.info(f"Initializing schema from {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        schema_sql = f.read()

    # Use raw connection for schema changes (no RLS)
    with get_connection_no_rls() as conn:
        try:
            cur = conn.cursor()
            cur.execute(schema_sql)
            logger.info("Schema initialized successfully")
        except Exception as e:
            logger.error(f"Schema initialization failed: {e}")
            raise


# =============================================================================
# JSON HELPERS (for JSONB columns)
# =============================================================================


def json_dumps(obj: Any) -> str:
    """Serialize object to JSON string for JSONB columns."""
    return json.dumps(obj, default=str)


def json_loads(s: str) -> Any:
    """Deserialize JSON string from JSONB columns."""
    if s is None:
        return None
    if isinstance(s, dict):
        return s  # Already parsed by psycopg2
    return json.loads(s)


# =============================================================================
# COMPATIBILITY LAYER
# =============================================================================
# These functions maintain API compatibility with the SQLite db.py module


def dict_factory(cursor, row) -> dict[str, Any]:
    """
    Compatibility function - not used with psycopg2.

    psycopg2 uses DictCursor/RealDictCursor for dict rows.
    """
    if cursor.description is None:
        return {}
    return dict(zip([col.name for col in cursor.description], row))


# Register JSON adapter for psycopg2
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
psycopg2.extensions.register_adapter(list, psycopg2.extras.Json)
