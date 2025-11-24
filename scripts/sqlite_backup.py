#!/usr/bin/env python3
"""
Quick backup/restore utility for the Agent Foundry SQLite control-plane DB.

Examples:
  python scripts/sqlite_backup.py backup
  python scripts/sqlite_backup.py backup --label pre-demo
  python scripts/sqlite_backup.py list
  python scripts/sqlite_backup.py restore --file backups/sqlite/foundry_2025-11-17_1930.db
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.utils.sqlite_backup import (  # noqa: E402
    BACKUP_DIR,
    create_backup,
    list_backups,
    restore_backup,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backup/restore the Agent Foundry SQLite database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create a timestamped backup")
    backup_parser.add_argument("--label", help="Optional label appended to the filename")

    restore_parser = subparsers.add_parser("restore", help="Restore from a backup file")
    restore_parser.add_argument("--file", required=True, help="Path to backup file under backups/sqlite/")

    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--limit", type=int, help="Limit output to N most recent backups")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "backup":
        backup_path = create_backup(args.label).path
        print(f"✅ Backup created: {backup_path}")
    elif args.command == "restore":
        target = Path(args.file)
        if not target.is_absolute():
            if target.parts[0].startswith("backups"):
                target = ROOT / target
            else:
                target = BACKUP_DIR / target.name
        restore_backup(str(target))
        print(f"✅ Restored DB from: {target}")
    elif args.command == "list":
        backups = list_backups()
        if args.limit:
            backups = backups[: args.limit]
        if not backups:
            print("No backups found.")
        else:
            for path in backups:
                ts = path.created_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{ts}  {path.path}")


if __name__ == "__main__":
    main()
