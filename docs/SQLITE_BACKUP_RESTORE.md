# SQLite Backup & Restore Guide

The control-plane data (orgs/domains/instances/users/agents) lives in
`data/foundry.db`. To prevent accidental loss (e.g., when reseeding), use the
new helper script instead of manually copying files.

## 1. Create a backup

```bash
cd /Users/nwalker/Development/Projects/agentfoundry
python scripts/sqlite_backup.py backup --label cibc-card-services
```

This writes a timestamped copy to `backups/sqlite/`, e.g.
`backups/sqlite/foundry_2025-11-17_201530-cibc-card-services.db`.

## 2. List existing backups

```bash
python scripts/sqlite_backup.py list
# or limit the output
python scripts/sqlite_backup.py list --limit 5
```

## 3. Restore from a backup

```bash
python scripts/sqlite_backup.py restore --file backups/sqlite/foundry_2025-11-17_201530-cibc-card-services.db
```

This overwrites `data/foundry.db`. Restart the backend (or re-run
`start_foundry.sh`) after restoring.

## Notes

- The script uses regular file copies; no special SQLite commands are required.
- Backups include everything in the DB (organizations, domains, instances, RBAC
  seeds, etc.).
- If you run migrations that change schema, take a backup beforehand so you can
  roll back quickly.
