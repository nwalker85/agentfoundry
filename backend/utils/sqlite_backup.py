from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Go up to /app level
DB_PATH = PROJECT_ROOT / "data" / "foundry.db"
BACKUP_DIR = PROJECT_ROOT / "backups" / "sqlite"


@dataclass
class SqliteBackup:
    filename: str
    path: Path
    size_bytes: int
    created_at: datetime
    label: str | None = None
    created_by: str | None = None
    created_by_email: str | None = None


def _ensure_paths() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _sanitize_label(label: str | None) -> str | None:
    if not label:
        return None
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "-", label.strip())
    return sanitized or None


def _parse_label(filename: str) -> str | None:
    base = Path(filename).stem  # foundry_2025-...
    parts = base.split("-", 4)  # allow hyphen in timestamp
    if len(parts) <= 4:
        return None
    # label is everything after timestamp (third and fourth include time)
    # original format: foundry_{YYYY}-{MM}-{DD}_{HHMMSS}-{label}
    label = "-".join(parts[4:])
    return label or None


def create_backup(
    label: str | None = None, user_name: str | None = None, user_email: str | None = None
) -> SqliteBackup:
    _ensure_paths()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    suffix = ""
    sanitized_label = _sanitize_label(label)
    if sanitized_label:
        suffix = f"-{sanitized_label}"
    backup_path = BACKUP_DIR / f"foundry_{timestamp}{suffix}.db"
    shutil.copy2(DB_PATH, backup_path)

    # Save metadata with user audit info
    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "label": label,
        "created_by": user_name,
        "created_by_email": user_email,
    }
    metadata_path = backup_path.with_suffix(".db.meta.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return _build_backup_info(backup_path)


def list_backups() -> list[SqliteBackup]:
    _ensure_paths()
    backups = sorted(
        BACKUP_DIR.glob("foundry_*.db"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [_build_backup_info(path) for path in backups]


def restore_backup(filename: str) -> None:
    _ensure_paths()
    target = _resolve_backup(filename)
    if not target.exists():
        raise FileNotFoundError(f"Backup not found: {filename}")
    shutil.copy2(target, DB_PATH)


def get_backup_file(filename: str) -> Path:
    return _resolve_backup(filename)


def _resolve_backup(filename: str) -> Path:
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate
    if filename.startswith("backups/"):
        return PROJECT_ROOT / filename
    return BACKUP_DIR / filename


def _build_backup_info(path: Path) -> SqliteBackup:
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_mtime)
    label = _parse_label(path.name)

    # Try to load metadata with user info
    created_by = None
    created_by_email = None
    metadata_path = path.with_suffix(".db.meta.json")
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
                created_by = metadata.get("created_by")
                created_by_email = metadata.get("created_by_email")
        except Exception:
            pass  # If metadata can't be read, just skip it

    return SqliteBackup(
        filename=path.name,
        path=path,
        size_bytes=stat.st_size,
        created_at=created_at,
        label=label,
        created_by=created_by,
        created_by_email=created_by_email,
    )
