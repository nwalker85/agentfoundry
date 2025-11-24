"""
Redis Backup and Management Utilities

Provides backup/restore and key management for Redis.
"""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import redis

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "backups" / "redis"

# Redis connection from environment (use admin-specific URL)
REDIS_URL = os.getenv("REDIS_ADMIN_URL", os.getenv("REDIS_URL", "redis://redis:6379"))


@dataclass
class RedisBackup:
    filename: str
    path: Path
    size_bytes: int
    created_at: datetime
    label: str | None = None
    created_by: str | None = None
    created_by_email: str | None = None


def get_redis_client() -> redis.Redis:
    """Get Redis client connection"""
    # Don't decode responses automatically to handle binary data
    return redis.from_url(REDIS_URL, decode_responses=False)


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


def _safe_decode(value: Any) -> Any:
    """
    Safely decode Redis values, handling both strings and binary data.
    Binary data is base64 encoded and marked with a special format.
    """
    if value is None:
        return None

    if isinstance(value, bytes):
        try:
            # Try to decode as UTF-8 string
            return value.decode("utf-8")
        except UnicodeDecodeError:
            # If it fails, base64 encode and mark as binary
            return {"_binary": True, "data": base64.b64encode(value).decode("utf-8")}
    elif isinstance(value, list) or isinstance(value, set):
        return [_safe_decode(v) for v in value]
    elif isinstance(value, dict):
        return {_safe_decode(k): _safe_decode(v) for k, v in value.items()}
    elif isinstance(value, tuple):
        # Handle zset scores (member, score) tuples
        return tuple(_safe_decode(v) for v in value)
    else:
        return value


def create_backup(label: str | None = None, user_name: str | None = None, user_email: str | None = None) -> RedisBackup:
    """
    Create Redis backup by exporting all keys to JSON format.
    Uses SCAN to iterate through all keys and GET to retrieve values.
    """
    _ensure_paths()
    client = get_redis_client()

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    suffix = ""
    sanitized_label = _sanitize_label(label)
    if sanitized_label:
        suffix = f"-{sanitized_label}"

    backup_path = BACKUP_DIR / f"redis_{timestamp}{suffix}.json"

    # Export all keys to JSON
    data = {}
    cursor = 0

    while True:
        cursor, keys = client.scan(cursor=cursor, count=100)
        for key in keys:
            # Decode key safely
            key_str = _safe_decode(key)
            if isinstance(key_str, dict) and key_str.get("_binary"):
                # Skip binary keys - too complex to handle
                continue

            key_type = client.type(key).decode("utf-8") if isinstance(client.type(key), bytes) else client.type(key)

            if key_type == "string":
                data[key_str] = {"type": "string", "value": _safe_decode(client.get(key))}
            elif key_type == "list":
                data[key_str] = {"type": "list", "value": _safe_decode(client.lrange(key, 0, -1))}
            elif key_type == "set":
                data[key_str] = {"type": "set", "value": _safe_decode(list(client.smembers(key)))}
            elif key_type == "zset":
                data[key_str] = {"type": "zset", "value": _safe_decode(client.zrange(key, 0, -1, withscores=True))}
            elif key_type == "hash":
                data[key_str] = {"type": "hash", "value": _safe_decode(client.hgetall(key))}

            # Store TTL if exists
            ttl = client.ttl(key)
            if ttl > 0:
                data[key_str]["ttl"] = ttl

        if cursor == 0:
            break

    # Write to file with user audit info
    with open(backup_path, "w") as f:
        json.dump(
            {
                "created_at": datetime.utcnow().isoformat(),
                "label": label,
                "created_by": user_name,
                "created_by_email": user_email,
                "keys": data,
            },
            f,
            indent=2,
        )

    return _build_backup_info(backup_path)


def list_backups() -> list[RedisBackup]:
    """List all Redis backups"""
    _ensure_paths()
    backups = sorted(
        BACKUP_DIR.glob("redis_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [_build_backup_info(path) for path in backups]


def restore_backup(filename: str) -> dict[str, int]:
    """
    Restore Redis backup from JSON file.
    Returns statistics about restored keys.
    """
    _ensure_paths()
    target = _resolve_backup(filename)

    if not target.exists():
        raise FileNotFoundError(f"Backup not found: {filename}")

    client = get_redis_client()

    with open(target) as f:
        backup_data = json.load(f)

    keys_data = backup_data.get("keys", {})
    stats = {"total": 0, "restored": 0, "failed": 0}

    for key, value_data in keys_data.items():
        stats["total"] += 1
        try:
            key_type = value_data.get("type")
            value = value_data.get("value")
            ttl = value_data.get("ttl")

            if key_type == "string":
                client.set(key, value)
            elif key_type == "list":
                client.delete(key)
                if value:
                    client.rpush(key, *value)
            elif key_type == "set":
                client.delete(key)
                if value:
                    client.sadd(key, *value)
            elif key_type == "zset":
                client.delete(key)
                if value:
                    # value is list of (member, score) tuples
                    for item in value:
                        if isinstance(item, (list, tuple)) and len(item) == 2:
                            client.zadd(key, {item[0]: item[1]})
            elif key_type == "hash":
                client.delete(key)
                if value:
                    client.hset(key, mapping=value)

            # Set TTL if it existed
            if ttl and ttl > 0:
                client.expire(key, ttl)

            stats["restored"] += 1
        except Exception as e:
            print(f"Failed to restore key {key}: {e}")
            stats["failed"] += 1

    return stats


def get_backup_file(filename: str) -> Path:
    """Get path to backup file"""
    return _resolve_backup(filename)


def get_redis_info() -> dict[str, Any]:
    """Get Redis server information"""
    client = get_redis_client()
    info = client.info()

    return {
        "version": info.get("redis_version"),
        "uptime_seconds": info.get("uptime_in_seconds"),
        "connected_clients": info.get("connected_clients"),
        "used_memory_human": info.get("used_memory_human"),
        "total_keys": client.dbsize(),
        "db_stats": {},
    }


def list_keys(pattern: str = "*", limit: int = 100) -> list[dict[str, Any]]:
    """List Redis keys with metadata"""
    client = get_redis_client()
    keys_info = []

    cursor = 0
    count = 0

    while count < limit:
        cursor, keys = client.scan(cursor=cursor, match=pattern, count=50)

        for key in keys:
            if count >= limit:
                break

            key_type = client.type(key)
            ttl = client.ttl(key)

            # Get size estimate
            if key_type == "string":
                size = len(client.get(key) or "")
            elif key_type == "list":
                size = client.llen(key)
            elif key_type == "set":
                size = client.scard(key)
            elif key_type == "zset":
                size = client.zcard(key)
            elif key_type == "hash":
                size = client.hlen(key)
            else:
                size = 0

            keys_info.append({"key": key, "type": key_type, "ttl": ttl if ttl > 0 else None, "size": size})
            count += 1

        if cursor == 0:
            break

    return keys_info


def get_key_value(key: str) -> dict[str, Any]:
    """Get value of a specific key"""
    client = get_redis_client()

    if not client.exists(key):
        raise KeyError(f"Key not found: {key}")

    key_type = client.type(key)
    ttl = client.ttl(key)

    result = {"key": key, "type": key_type, "ttl": ttl if ttl > 0 else None, "value": None}

    if key_type == "string":
        result["value"] = client.get(key)
    elif key_type == "list":
        result["value"] = client.lrange(key, 0, -1)
    elif key_type == "set":
        result["value"] = list(client.smembers(key))
    elif key_type == "zset":
        result["value"] = client.zrange(key, 0, -1, withscores=True)
    elif key_type == "hash":
        result["value"] = client.hgetall(key)

    return result


def delete_key(key: str) -> bool:
    """Delete a Redis key"""
    client = get_redis_client()
    return client.delete(key) > 0


def flush_db() -> bool:
    """Flush all keys from current database (WARNING: destructive)"""
    client = get_redis_client()
    client.flushdb()
    return True


def _resolve_backup(filename: str) -> Path:
    """Resolve backup file path"""
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate
    if filename.startswith("backups/"):
        return PROJECT_ROOT / filename
    return BACKUP_DIR / filename


def _build_backup_info(path: Path) -> RedisBackup:
    """Build backup info from file"""
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_mtime)
    label = _parse_label(path.name)

    # Try to load user info from JSON backup file
    created_by = None
    created_by_email = None
    try:
        with open(path) as f:
            backup_data = json.load(f)
            created_by = backup_data.get("created_by")
            created_by_email = backup_data.get("created_by_email")
    except Exception:
        pass  # If can't read, just skip user info

    return RedisBackup(
        filename=path.name,
        path=path,
        size_bytes=stat.st_size,
        created_at=created_at,
        label=label,
        created_by=created_by,
        created_by_email=created_by_email,
    )
