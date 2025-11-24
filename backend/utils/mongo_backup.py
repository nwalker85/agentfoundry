"""
MongoDB Backup and Management Utilities

Provides backup/restore and database management for MongoDB.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from bson import json_util
from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = PROJECT_ROOT / "backups" / "mongodb"

# MongoDB connection from environment (use admin-specific URL)
MONGO_URL = os.getenv("MONGODB_ADMIN_URL", os.getenv("MONGODB_URL", "mongodb://mongodb:27017"))
MONGO_DB_NAME = os.getenv("MONGODB_ADMIN_DATABASE", os.getenv("MONGODB_DATABASE", "agentfoundry"))


@dataclass
class MongoBackup:
    filename: str
    path: Path
    size_bytes: int
    created_at: datetime
    label: str | None = None
    created_by: str | None = None
    created_by_email: str | None = None


def get_mongo_client() -> MongoClient:
    """Get MongoDB client connection"""
    return MongoClient(MONGO_URL)


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
    # For MongoDB, we use archive files, so check for .archive extension
    if filename.endswith(".archive"):
        base = Path(filename).stem
    else:
        base = Path(filename).stem

    parts = base.split("-", 4)
    if len(parts) <= 4:
        return None
    label = "-".join(parts[4:])
    return label or None


def create_backup(label: str | None = None, user_name: str | None = None, user_email: str | None = None) -> MongoBackup:
    """
    Create MongoDB backup using mongodump with archive format.
    Creates a compressed archive of the entire database.
    """
    _ensure_paths()

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
    suffix = ""
    sanitized_label = _sanitize_label(label)
    if sanitized_label:
        suffix = f"-{sanitized_label}"

    backup_path = BACKUP_DIR / f"mongodb_{timestamp}{suffix}.archive"

    # Build mongodump command
    cmd = ["mongodump", "--uri", MONGO_URL, "--db", MONGO_DB_NAME, "--archive=" + str(backup_path), "--gzip"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mongodump failed: {e.stderr}")

    # Save metadata with user audit info
    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "label": label,
        "created_by": user_name,
        "created_by_email": user_email,
    }
    metadata_path = backup_path.with_suffix(".archive.meta.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return _build_backup_info(backup_path)


def list_backups() -> list[MongoBackup]:
    """List all MongoDB backups"""
    _ensure_paths()
    backups = sorted(
        BACKUP_DIR.glob("mongodb_*.archive"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [_build_backup_info(path) for path in backups]


def restore_backup(filename: str, drop: bool = False) -> dict[str, Any]:
    """
    Restore MongoDB backup using mongorestore.

    Args:
        filename: Backup filename to restore
        drop: If True, drop collections before restoring (WARNING: destructive)

    Returns:
        Dictionary with restore statistics
    """
    _ensure_paths()
    target = _resolve_backup(filename)

    if not target.exists():
        raise FileNotFoundError(f"Backup not found: {filename}")

    # Build mongorestore command
    cmd = ["mongorestore", "--uri", MONGO_URL, "--db", MONGO_DB_NAME, "--archive=" + str(target), "--gzip"]

    if drop:
        cmd.append("--drop")  # Drop collections before restoring

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        return {"success": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mongorestore failed: {e.stderr}")


def get_backup_file(filename: str) -> Path:
    """Get path to backup file"""
    return _resolve_backup(filename)


def get_mongo_info() -> dict[str, Any]:
    """Get MongoDB server information"""
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]

    # Get server info
    server_info = client.server_info()

    # Get collection count
    collection_names = db.list_collection_names()

    # Try to get database stats (may fail if database doesn't exist or insufficient permissions)
    try:
        db_stats = db.command("dbStats")
        data_size = db_stats.get("dataSize", 0)
        storage_size = db_stats.get("storageSize", 0)
        indexes = db_stats.get("indexes", 0)
        objects = db_stats.get("objects", 0)
    except Exception:
        # Database may not exist yet or insufficient permissions
        data_size = 0
        storage_size = 0
        indexes = 0
        objects = 0

    client.close()

    return {
        "version": server_info.get("version"),
        "database_name": MONGO_DB_NAME,
        "collections": len(collection_names),
        "data_size": data_size,
        "storage_size": storage_size,
        "indexes": indexes,
        "objects": objects,
    }


def list_collections() -> list[dict[str, Any]]:
    """List all MongoDB collections with document counts"""
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]

    collections = []
    for coll_name in db.list_collection_names():
        coll = db[coll_name]

        # Get collection stats
        try:
            stats = db.command("collStats", coll_name)
            doc_count = coll.count_documents({})

            collections.append(
                {
                    "name": coll_name,
                    "document_count": doc_count,
                    "size": stats.get("size", 0),
                    "storage_size": stats.get("storageSize", 0),
                    "indexes": stats.get("nindexes", 0),
                }
            )
        except Exception as e:
            # Some system collections might not allow stats
            collections.append(
                {"name": coll_name, "document_count": 0, "size": 0, "storage_size": 0, "indexes": 0, "error": str(e)}
            )

    client.close()

    return collections


def get_collection_schema(collection_name: str) -> dict[str, Any]:
    """
    Get schema information for a collection by analyzing documents.
    Returns field names and types found in the collection.
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    # Sample some documents to infer schema
    sample_size = min(100, coll.count_documents({}))
    documents = list(coll.find().limit(sample_size))

    # Collect all field names and types
    fields = {}
    for doc in documents:
        for key, value in doc.items():
            value_type = type(value).__name__
            if key not in fields:
                fields[key] = {"types": set(), "count": 0}
            fields[key]["types"].add(value_type)
            fields[key]["count"] += 1

    # Convert sets to lists for JSON serialization
    schema = []
    for field_name, info in fields.items():
        schema.append(
            {
                "field": field_name,
                "types": list(info["types"]),
                "frequency": info["count"] / len(documents) if documents else 0,
            }
        )

    client.close()

    return {
        "collection": collection_name,
        "sample_size": sample_size,
        "total_documents": coll.count_documents({}),
        "fields": schema,
    }


def get_collection_documents(
    collection_name: str, limit: int = 100, skip: int = 0, filter_query: dict | None = None
) -> list[dict[str, Any]]:
    """Get documents from a specific collection"""
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    query = filter_query or {}
    documents = list(coll.find(query).skip(skip).limit(limit))

    client.close()

    # Convert ObjectId and other BSON types to JSON-serializable format
    return json.loads(json_util.dumps(documents))


def export_collection_json(collection_name: str) -> str:
    """
    Export a collection to JSON format.
    Returns the JSON content as a string.
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    documents = list(coll.find())

    client.close()

    # Use json_util to handle BSON types properly
    return json_util.dumps(documents, indent=2)


def insert_document(collection_name: str, document: dict[str, Any]) -> str:
    """Insert a new document into a collection"""
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    result = coll.insert_one(document)

    client.close()

    return str(result.inserted_id)


def update_document(collection_name: str, document_id: str, document: dict[str, Any]) -> bool:
    """Update an existing document"""
    from bson.objectid import ObjectId

    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    result = coll.replace_one({"_id": ObjectId(document_id)}, document)

    client.close()

    return result.modified_count > 0


def delete_document(collection_name: str, document_id: str) -> bool:
    """Delete a document"""
    from bson.objectid import ObjectId

    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    coll = db[collection_name]

    result = coll.delete_one({"_id": ObjectId(document_id)})

    client.close()

    return result.deleted_count > 0


def _resolve_backup(filename: str) -> Path:
    """Resolve backup file path"""
    candidate = Path(filename)
    if candidate.is_absolute():
        return candidate
    if filename.startswith("backups/"):
        return PROJECT_ROOT / filename
    return BACKUP_DIR / filename


def _build_backup_info(path: Path) -> MongoBackup:
    """Build backup info from file"""
    stat = path.stat()
    created_at = datetime.fromtimestamp(stat.st_mtime)
    label = _parse_label(path.name)

    # Try to load metadata with user info
    created_by = None
    created_by_email = None
    metadata_path = path.with_suffix(".archive.meta.json")
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
                created_by = metadata.get("created_by")
                created_by_email = metadata.get("created_by_email")
        except Exception:
            pass  # If metadata can't be read, just skip it

    return MongoBackup(
        filename=path.name,
        path=path,
        size_bytes=stat.st_size,
        created_at=created_at,
        label=label,
        created_by=created_by,
        created_by_email=created_by_email,
    )
