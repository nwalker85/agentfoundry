# Database Import/Export Guide

## Overview

Agent Foundry provides comprehensive import/export capabilities for all 4
databases:

- **SQLite** - Control plane database
- **Redis** - Caching and session store
- **PostgreSQL** - Relational data
- **MongoDB** - Document store

---

## How to Export Data

### Method 1: Create and Download Backups

1. Navigate to **Admin → Manage Databases**
2. Select the database tab (SQLite, Redis, PostgreSQL, or MongoDB)
3. Enter an optional label (e.g., "before-migration" or "prod-backup-2024")
4. Click **"Create Backup"**
5. Wait for the backup to appear in the list
6. Click the **Download** icon (⬇️) to download the backup file

**File Formats:**

- SQLite: `.db` file
- Redis: `.json` file
- PostgreSQL: `.dump` file (pg_dump custom format)
- MongoDB: `.archive` file (gzip compressed)

### Method 2: Export Individual Tables/Collections

**PostgreSQL:**

- Click on a table in the browser
- Click **"Export SQL"** button
- Downloads a `.sql` file with INSERT statements

**MongoDB:**

- Click on a collection in the browser
- Click **"Export JSON"** button
- Downloads a `.json` file with all documents

---

## How to Import Data

### Step-by-Step Import Process

1. Navigate to **Admin → Manage Databases**
2. Select the appropriate database tab
3. Click the **"Import"** button (📤 Upload icon)
4. Select your backup file from your local machine
5. Confirm the import operation (will show warning about overwriting data)
6. Wait for the import to complete
7. Check the success message

### Import Examples

#### Example 1: Restore SQLite Database

You have a file:
`/Users/nwalker/Downloads/foundry_2025-11-18_012428-foundry_11-17-25-1924-all.db`

**Steps:**

1. Go to **Admin → Manage Databases**
2. Click the **SQLite** tab
3. Click **"Import"** button
4. Select your `.db` file from Downloads folder
5. Confirm: "Import backup will overwrite the current database"
6. After import completes, **restart the backend** for changes to take effect:
   ```bash
   docker-compose restart foundry-backend
   ```

#### Example 2: Import Redis Data

You have a Redis backup: `redis_2025-11-17_153022-session-backup.json`

**Steps:**

1. Go to **Admin → Manage Databases**
2. Click the **Redis** tab
3. Click **"Import"** button
4. Select your `.json` file
5. Confirm the import
6. Redis data is immediately available (no restart needed)

#### Example 3: Import PostgreSQL Data

You have a PostgreSQL dump: `postgres_2025-11-17_120000-before-migration.dump`

**Steps:**

1. Go to **Admin → Manage Databases**
2. Click the **PostgreSQL** tab
3. Click **"Import"** button
4. Select your `.dump` or `.sql` file
5. Confirm the import
6. Data is restored using pg_restore

#### Example 4: Import MongoDB Archive

You have a MongoDB archive: `mongodb_2025-11-17_090000-full-backup.archive`

**Steps:**

1. Go to **Admin → Manage Databases**
2. Click the **MongoDB** tab
3. Click **"Import"** button
4. Select your `.archive` file
5. Confirm the import
6. Collections are restored using mongorestore

---

## Supported File Formats

| Database   | Export Format | Import Format     | Notes                        |
| ---------- | ------------- | ----------------- | ---------------------------- |
| SQLite     | `.db`         | `.db`             | Binary SQLite database file  |
| Redis      | `.json`       | `.json`           | JSON export of all keys      |
| PostgreSQL | `.dump`       | `.dump`, `.sql`   | pg_dump custom format or SQL |
| MongoDB    | `.archive`    | `.archive`, `.gz` | mongodump gzip archive       |

---

## Important Notes

### ⚠️ Before Importing

1. **Create a backup** of your current database before importing
2. **Verify the file** you're importing is from a trusted source
3. **Check compatibility** - ensure the backup is from a compatible version
4. **Plan for downtime** - some imports may require restarting services

### After Importing

**For SQLite:**

- **Must restart the backend** for changes to take effect
- Run: `docker-compose restart foundry-backend`

**For Redis:**

- Changes are immediate
- Existing keys may be overwritten

**For PostgreSQL/MongoDB:**

- Changes are immediate
- Existing tables/collections may be overwritten
- Use the "clean/drop" options carefully

---

## Workflow Examples

### Scenario 1: Moving from Development to Production

**On Development:**

1. Export SQLite database (contains RBAC, users, agents)
2. Export PostgreSQL tables (contains domain intelligence)
3. Download both backups

**On Production:**

1. Import SQLite backup
2. Restart backend
3. Import PostgreSQL backup
4. Verify data loaded correctly

### Scenario 2: Disaster Recovery

**Regular Backups (Automated):**

```bash
# Create backups via API
curl -X POST http://localhost:8000/api/admin/sqlite/backups \
  -H "Content-Type: application/json" \
  -d '{"label": "daily-backup"}'

curl -X POST http://localhost:8000/api/admin/postgres/backups \
  -H "Content-Type: application/json" \
  -d '{"label": "daily-backup"}'

curl -X POST http://localhost:8000/api/admin/mongodb/backups \
  -H "Content-Type: application/json" \
  -d '{"label": "daily-backup"}'
```

**Recovery:**

1. Use the Import button for each database
2. Select the most recent backup
3. Confirm and restore

### Scenario 3: Testing Migrations

**Before Migration:**

1. Create labeled backup: "before-migration-v2"
2. Run your migration
3. Test thoroughly

**If Issues Occur:**

1. Click Import
2. Select "before-migration-v2" backup
3. Restore to previous state

---

## API Endpoints for Automation

### Import via API (Advanced)

**SQLite:**

```bash
curl -X POST http://localhost:8000/api/admin/sqlite/import \
  -F "file=@/path/to/backup.db"
```

**Redis:**

```bash
curl -X POST http://localhost:8000/api/admin/redis/import \
  -F "file=@/path/to/backup.json"
```

**PostgreSQL:**

```bash
curl -X POST http://localhost:8000/api/admin/postgres/import \
  -F "file=@/path/to/backup.dump"
```

**MongoDB:**

```bash
curl -X POST http://localhost:8000/api/admin/mongodb/import \
  -F "file=@/path/to/backup.archive"
```

---

## Troubleshooting

### Import Failed

**Check:**

1. File format is correct for the database type
2. File is not corrupted
3. Backend has enough disk space
4. Database service is running

**View Logs:**

```bash
docker-compose logs --tail=50 foundry-backend
```

### "Restart Backend to Apply"

For SQLite imports, you must restart:

```bash
docker-compose restart foundry-backend
# Or
docker-compose down && docker-compose up -d
```

### Permission Errors

**PostgreSQL/MongoDB:**

- Check that admin credentials are configured
- Verify connection URLs in `.env` file

---

## Best Practices

1. **Label Your Backups** - Use descriptive labels like "before-v2-upgrade"
2. **Regular Backups** - Create backups before any major changes
3. **Test Restores** - Periodically test that your backups can be restored
4. **Store Offsite** - Download important backups to a safe location
5. **Version Control** - Keep track of which backup corresponds to which app
   version
6. **Document Changes** - Note what changed since the last backup

---

## File Storage Locations

**Backend Container:**

- SQLite backups: `/app/backups/sqlite/`
- Redis backups: `/app/backups/redis/`
- PostgreSQL backups: `/app/backups/postgres/`
- MongoDB backups: `/app/backups/mongodb/`

**Downloaded Files:**

- Your browser's Downloads folder
- Can be imported from any location

---

## Summary

✅ **Export:** Create Backup → Download ✅ **Import:** Click Import → Select
File → Confirm ✅ **SQLite:** Requires backend restart after import ✅
**Others:** Changes are immediate

For your specific file:
`/Users/nwalker/Downloads/foundry_2025-11-18_012428-foundry_11-17-25-1924-all.db`

1. Go to SQLite tab
2. Click Import button
3. Select this file
4. Confirm import
5. Run: `docker-compose restart foundry-backend`
6. Verify data loaded correctly
