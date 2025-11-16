import os
from typing import Optional

import psycopg

DB_URL = os.getenv("DATABASE_URL", "postgresql://foundry:foundry@postgres:5432/foundry")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db_schema.sql")


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DB_URL)


def init_db() -> None:
    """Initialize the control-plane database (run schema migrations and seed)."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"⚠️ DB schema not found at {SCHEMA_PATH}")
        return

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(schema_sql)
            conn.commit()
        print("✅ Database schema initialized")
    except Exception as e:
        print(f"⚠️ Failed to initialize database schema: {e}")
        return

    # Seed initial data for convenience (CIBC / Card Services / dev)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Organization
                cur.execute(
                    """
                    INSERT INTO organizations (id, name, tier)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    ("cibc", "CIBC", "enterprise"),
                )

                # Domain
                cur.execute(
                    """
                    INSERT INTO domains (id, organization_id, name, display_name, version)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    ("card-services", "cibc", "card-services", "Card Services", "0.1.0"),
                )

                # Instance
                cur.execute(
                    """
                    INSERT INTO instances (id, organization_id, domain_id, environment, instance_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    ("cibc-card-services-dev", "cibc", "card-services", "dev", "dev"),
                )

            conn.commit()
        print("✅ Seeded initial org/domain/instance (cibc / card-services / dev)")
    except Exception as e:
        print(f"⚠️ Failed to seed initial data: {e}")


