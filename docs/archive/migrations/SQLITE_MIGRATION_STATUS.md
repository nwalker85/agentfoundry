# PostgreSQL → SQLite Migration Status

## Overview

This document tracks the migration from PostgreSQL to SQLite for the Agent
Foundry project.

## ✅ Completed Tasks

### 1. Schema Conversion

- ✅ **backend/db_schema_sqlite.sql** - Created SQLite version of main schema

  - Converted TIMESTAMPTZ → TEXT with UTC ISO 8601 format
  - Converted BOOLEAN → INTEGER (0/1)
  - Converted JSONB → TEXT (JSON strings)
  - Converted TEXT[] → TEXT (JSON arrays)
  - Added PRAGMA foreign_keys = ON

- ✅ **backend/rbac_schema_sqlite.sql** - Created SQLite version of RBAC schema

  - Converted UUID → TEXT (generated in Python)
  - Removed Row-Level Security policies (implemented in app layer)
  - Removed PL/pgSQL functions (implemented in rbac_service.py)
  - Converted BIGSERIAL → INTEGER PRIMARY KEY AUTOINCREMENT
  - Converted DECIMAL → REAL

- ✅ **backend/seed_rbac_sqlite.py** - Python script to seed RBAC data
  - Generates UUIDs for all roles and permissions
  - Creates 44+ permissions
  - Creates 10 roles (platform, org, and service roles)
  - Creates all role-permission mappings

### 2. Database Client Migration

- ✅ **backend/db.py** - Converted from psycopg to sqlite3
  - Replaced psycopg.connect() with sqlite3.connect()
  - Added dict_factory for row-as-dictionary support
  - Added PRAGMA foreign_keys = ON
  - Added PRAGMA journal_mode = WAL for better concurrency
  - Converted all SQL parameters from %s (PostgreSQL) to ? (SQLite)
  - Converted INSERT...ON CONFLICT to INSERT OR IGNORE
  - Converted NOW() to datetime.utcnow().isoformat()
  - Added JSON serialization for tags and metadata fields
  - Created backup: backend/db_postgres_backup.py

---

## ⚠️ Remaining Tasks

### 3. RBAC Service Migration (HIGH PRIORITY)

**File:** `backend/rbac_service.py` (472 lines)

**Required Changes:**

- Replace `import psycopg` with `import sqlite3`
- Replace `psycopg.connect()` with SQLite connection
- Remove `dict_row` factory, use custom dict_factory
- Convert all SQL parameters from `%s` to `?`
- Convert `INSERT...RETURNING` to separate INSERT + SELECT
- Update `get_connection()` method
- Test all RBAC operations

### 4. RBAC Middleware (MEDIUM PRIORITY)

**File:** `backend/rbac_middleware.py` (416 lines)

**Required Changes:**

- Remove or comment out `set_rls_context()` function (PostgreSQL RLS not
  supported in SQLite)
- RLS is already enforced in application layer via permission checks
- Update any database connection calls if needed

### 5. Agent Files (HIGH PRIORITY)

**Files:**

- `agent/data_agent.py` - SQL query generation agent
- `agent/object_admin_agent.py` - CRUD operations agent

**Required Changes:**

- Replace `import psycopg` with `import sqlite3`
- Update `DB_URL` import from `backend.db`
- Convert SQL parameters from `%s` to `?`
- Update connection handling

### 6. Dependencies (CRITICAL)

**File:** `requirements.txt`

**Required Changes:**

- Remove: `psycopg[binary]==3.2.1`
- Note: `sqlite3` is built into Python, no installation needed

### 7. Docker Configuration (CRITICAL)

**File:** `docker-compose.yml`

**Required Changes:**

- Remove entire `postgres:` service (lines 274-291)
- Remove `postgres-data:` volume from volumes section
- Update `DATABASE_URL` environment variable in all services:
  - `foundry-backend`: Change to `sqlite:///data/foundry.db`
  - `foundry-compiler`: Change to `sqlite:///data/foundry.db`
- Add volume mount for SQLite database file:
  ```yaml
  volumes:
    - ./data:/app/data
  ```

### 8. Environment Configuration

**File:** `.env.example`

**Required Changes:**

- Update DATABASE_URL line:
  ```
  DATABASE_URL=sqlite:///data/foundry.db
  ```
- This is already correct in .env.example!

### 9. Bootstrap Scripts (OPTIONAL)

**Files:**

- `scripts/bootstrap_local_postgres.py` - Currently creates PostgreSQL database

**Options:**

- Delete this file (no longer needed for SQLite)
- Or create `scripts/bootstrap_local_sqlite.py` for manual initialization

---

## Migration Strategy

### Phase 1: Core Backend (In Progress)

1. ✅ db.py
2. ⚠️ rbac_service.py
3. ⚠️ rbac_middleware.py

### Phase 2: Agent Layer

1. ⚠️ data_agent.py
2. ⚠️ object_admin_agent.py

### Phase 3: Configuration & Deployment

1. ⚠️ requirements.txt
2. ⚠️ docker-compose.yml
3. ⚠️ Test database initialization
4. ⚠️ Test all CRUD operations

---

## Testing Checklist

Once migration is complete, test:

- [ ] Database initialization (`init_db()`)
- [ ] RBAC seed data loading
- [ ] User authentication
- [ ] Permission checking
- [ ] Agent CRUD operations
- [ ] Integration config CRUD
- [ ] Session tracking
- [ ] Audit logging
- [ ] LLM usage tracking
- [ ] API key management
- [ ] Org/Domain/Instance management

---

## Key SQLite Differences

| Feature         | PostgreSQL                   | SQLite                                  |
| --------------- | ---------------------------- | --------------------------------------- |
| UUID Generation | `gen_random_uuid()`          | Python `uuid.uuid4()`                   |
| Timestamp       | `TIMESTAMPTZ`, `NOW()`       | TEXT with ISO 8601, `datetime.utcnow()` |
| Boolean         | `BOOLEAN`                    | INTEGER (0/1)                           |
| JSON            | `JSONB`                      | TEXT with `json.dumps/loads`            |
| Arrays          | `TEXT[]`                     | TEXT with JSON array                    |
| Auto Increment  | `BIGSERIAL`                  | INTEGER PRIMARY KEY AUTOINCREMENT       |
| Decimal         | `DECIMAL(10,6)`              | REAL                                    |
| Parameters      | `%s`                         | `?`                                     |
| Upsert          | `ON CONFLICT DO UPDATE`      | `INSERT OR IGNORE` + `UPDATE`           |
| RLS             | `ALTER TABLE ... ENABLE RLS` | Application layer only                  |
| Foreign Keys    | On by default                | `PRAGMA foreign_keys = ON`              |
| Concurrency     | High (multi-process)         | WAL mode (better, but limited)          |

---

## Database File Location

**Path:** `data/foundry.db`

This will be created automatically on first `init_db()` call.

For Docker:

- Mount `./data:/app/data` to persist database
- Database will be stored at `./data/foundry.db` on host

---

## Rollback Plan

If migration fails:

1. Restore `backend/db_postgres_backup.py` to `backend/db.py`
2. Keep PostgreSQL service in docker-compose.yml
3. Revert DATABASE_URL to PostgreSQL connection string

---

## Next Steps

1. Complete rbac_service.py migration
2. Update rbac_middleware.py
3. Update agent files
4. Update requirements.txt and docker-compose.yml
5. Test full stack
6. Remove PostgreSQL backup files if successful

---

## Notes

- SQLite is **single-file** - much easier to backup and deploy
- SQLite is **built into Python** - zero external dependencies
- SQLite **WAL mode** provides good concurrency for read-heavy workloads
- For **very high write concurrency**, consider connection pooling or eventual
  PostgreSQL return
- **Row-Level Security** is now enforced at application layer
  (rbac_middleware.py already does this)
