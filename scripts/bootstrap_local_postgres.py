#!/usr/bin/env python3
"""
Simple bootstrapper for a local Postgres database used by Agent Foundry.

It creates the `foundry` role/database if missing, then runs
`backend.db.init_db()` to build the schema and seed the default rows.

Set any overrides via environment variables (`PG_HOST`, `PG_PORT`, `PG_SUPERUSER`,
`PG_SUPERUSER_PASSWORD`, `PG_DB_USER`, `PG_DB_PASSWORD`, `PG_DB_NAME`) and then run:

    python scripts/bootstrap_local_postgres.py
"""

from __future__ import annotations

import os
import sys

import psycopg
from dotenv import load_dotenv
from psycopg import sql

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env.local"))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from backend import db as backend_db  # noqa: E402

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_SUPERUSER = os.getenv("PG_SUPERUSER", "postgres")
PG_SUPERUSER_PASSWORD = os.getenv("PG_SUPERUSER_PASSWORD", "")
PG_DB_USER = os.getenv("PG_DB_USER", "foundry")
PG_DB_PASSWORD = os.getenv("PG_DB_PASSWORD", "foundry")
PG_DB_NAME = os.getenv("PG_DB_NAME", "foundry")


def superuser_conninfo() -> str:
    parts = [
        f"host={PG_HOST}",
        f"port={PG_PORT}",
        f"user={PG_SUPERUSER}",
        "dbname=postgres",
    ]
    if PG_SUPERUSER_PASSWORD:
        parts.append(f"password={PG_SUPERUSER_PASSWORD}")
    return " ".join(parts)


def run_sql_as_superuser(query, params: tuple = ()) -> None:
    conninfo = superuser_conninfo()
    with psycopg.connect(conninfo, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute(query, params)


def role_exists() -> bool:
    conninfo = superuser_conninfo()
    with psycopg.connect(conninfo) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (PG_DB_USER,))
        return cur.fetchone() is not None


def create_or_update_role() -> None:
    identifier = sql.Identifier(PG_DB_USER)
    if role_exists():
        print(f"🔐 Updating password for role '{PG_DB_USER}'")
        run_sql_as_superuser(
            sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s").format(identifier),
            (PG_DB_PASSWORD,),
        )
    else:
        print(f"🧱 Creating role '{PG_DB_USER}'")
        run_sql_as_superuser(
            sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(identifier),
            (PG_DB_PASSWORD,),
        )


def database_exists() -> bool:
    conninfo = superuser_conninfo()
    with psycopg.connect(conninfo) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (PG_DB_NAME,))
        return cur.fetchone() is not None


def create_database_if_missing() -> None:
    if database_exists():
        print(f"🗄️  Database '{PG_DB_NAME}' already exists")
        return

    print(f"📝 Creating database '{PG_DB_NAME}'")
    query = sql.SQL("CREATE DATABASE {} OWNER {}").format(
        sql.Identifier(PG_DB_NAME),
        sql.Identifier(PG_DB_USER),
    )
    run_sql_as_superuser(query)


def main() -> None:
    print(f"👉 Bootstrapping Postgres @ {PG_HOST}:{PG_PORT}")
    create_or_update_role()
    create_database_if_missing()

    database_url = f"postgresql://{PG_DB_USER}:{PG_DB_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
    os.environ["DATABASE_URL"] = database_url

    print("📚 Running backend.db.init_db()")
    backend_db.init_db()

    print()
    print("✅ Bootstrap complete")
    print(f"Export DATABASE_URL={database_url} before running the app")


if __name__ == "__main__":
    main()
