"""
Admin Database Management API Routes

Provides REST API endpoints for managing all database systems:
- SQLite (control plane)
- Redis (caching/sessions)
- PostgreSQL (relational data)
- MongoDB (document store)
"""

import logging
import shutil
import tempfile
from typing import Any

from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class BackupCreate(BaseModel):
    label: str | None = None


class BackupRestore(BaseModel):
    filename: str
    clean: bool = False  # For PostgreSQL
    drop: bool = False  # For MongoDB


class BackupInfo(BaseModel):
    filename: str
    size_bytes: int
    created_at: str
    label: str | None = None


class KeyInfo(BaseModel):
    key: str
    type: str
    ttl: int | None = None
    size: int


class KeyValue(BaseModel):
    key: str
    type: str
    ttl: int | None = None
    value: Any


# ============================================================================
# REDIS Routes
# ============================================================================


@router.get("/api/admin/redis/info")
async def get_redis_info():
    """Get Redis server information"""
    try:
        from backend.utils.redis_backup import get_redis_info

        return get_redis_info()
    except Exception as exc:
        logger.error("Failed to get Redis info: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/redis/backups")
async def list_redis_backups():
    """List all Redis backups"""
    try:
        from backend.utils.redis_backup import list_backups

        backups = list_backups()
        return {
            "items": [
                {
                    "filename": b.filename,
                    "size_bytes": b.size_bytes,
                    "created_at": b.created_at.isoformat(),
                    "label": b.label,
                    "created_by": b.created_by,
                    "created_by_email": b.created_by_email,
                }
                for b in backups
            ]
        }
    except Exception as exc:
        logger.error("Failed to list Redis backups: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/redis/backups")
async def create_redis_backup(data: BackupCreate, request: Request):
    """Create a new Redis backup"""
    try:
        # Extract user info from headers (set by NextAuth frontend)
        user_name = request.headers.get("x-user-name")
        user_email = request.headers.get("x-user-email")

        from backend.utils.redis_backup import create_backup

        backup = create_backup(label=data.label, user_name=user_name, user_email=user_email)
        return {
            "filename": backup.filename,
            "size_bytes": backup.size_bytes,
            "created_at": backup.created_at.isoformat(),
            "label": backup.label,
        }
    except Exception as exc:
        logger.error("Failed to create Redis backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/redis/backups/restore")
async def restore_redis_backup(data: BackupRestore):
    """Restore Redis from backup"""
    try:
        from backend.utils.redis_backup import restore_backup

        stats = restore_backup(data.filename)
        return stats
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as exc:
        logger.error("Failed to restore Redis backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/redis/backups/download")
async def download_redis_backup(filename: str):
    """Download a Redis backup file"""
    try:
        from backend.utils.redis_backup import get_backup_file

        backup_path = get_backup_file(filename)
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        with open(backup_path, "rb") as f:
            content = f.read()

        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("Failed to download Redis backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/redis/keys")
async def list_redis_keys(pattern: str = "*", limit: int = 100):
    """List Redis keys"""
    try:
        from backend.utils.redis_backup import list_keys

        keys = list_keys(pattern=pattern, limit=limit)
        return {"items": keys}
    except Exception as exc:
        logger.error("Failed to list Redis keys: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/redis/keys/{key}")
async def get_redis_key(key: str):
    """Get value of a specific Redis key"""
    try:
        from backend.utils.redis_backup import get_key_value

        return get_key_value(key)
    except KeyError:
        raise HTTPException(status_code=404, detail="Key not found")
    except Exception as exc:
        logger.error("Failed to get Redis key: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/api/admin/redis/keys/{key}")
async def delete_redis_key(key: str):
    """Delete a Redis key"""
    try:
        from backend.utils.redis_backup import delete_key

        success = delete_key(key)
        if not success:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"message": "Key deleted successfully"}
    except Exception as exc:
        logger.error("Failed to delete Redis key: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# POSTGRESQL Routes
# ============================================================================


@router.get("/api/admin/postgres/info")
async def get_postgres_info():
    """Get PostgreSQL server information"""
    try:
        from backend.utils.postgres_backup import get_postgres_info

        return get_postgres_info()
    except Exception as exc:
        logger.error("Failed to get PostgreSQL info: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/backups")
async def list_postgres_backups():
    """List all PostgreSQL backups"""
    try:
        from backend.utils.postgres_backup import list_backups

        backups = list_backups()
        return {
            "items": [
                {
                    "filename": b.filename,
                    "size_bytes": b.size_bytes,
                    "created_at": b.created_at.isoformat(),
                    "label": b.label,
                    "created_by": b.created_by,
                    "created_by_email": b.created_by_email,
                }
                for b in backups
            ]
        }
    except Exception as exc:
        logger.error("Failed to list PostgreSQL backups: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/postgres/backups")
async def create_postgres_backup(data: BackupCreate, request: Request):
    """Create a new PostgreSQL backup"""
    try:
        # Extract user info from headers (set by NextAuth frontend)
        user_name = request.headers.get("x-user-name")
        user_email = request.headers.get("x-user-email")

        from backend.utils.postgres_backup import create_backup

        backup = create_backup(label=data.label, user_name=user_name, user_email=user_email)
        return {
            "filename": backup.filename,
            "size_bytes": backup.size_bytes,
            "created_at": backup.created_at.isoformat(),
            "label": backup.label,
        }
    except Exception as exc:
        logger.error("Failed to create PostgreSQL backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/postgres/backups/restore")
async def restore_postgres_backup(data: BackupRestore):
    """Restore PostgreSQL from backup"""
    try:
        from backend.utils.postgres_backup import restore_backup

        result = restore_backup(data.filename, clean=data.clean)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as exc:
        logger.error("Failed to restore PostgreSQL backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/backups/download")
async def download_postgres_backup(filename: str):
    """Download a PostgreSQL backup file"""
    try:
        from backend.utils.postgres_backup import get_backup_file

        backup_path = get_backup_file(filename)
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        with open(backup_path, "rb") as f:
            content = f.read()

        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("Failed to download PostgreSQL backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/tables")
async def list_postgres_tables():
    """List all PostgreSQL tables"""
    try:
        from backend.utils.postgres_backup import list_tables

        tables = list_tables()
        return {"items": tables}
    except Exception as exc:
        logger.error("Failed to list PostgreSQL tables: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/tables/{table_name}/schema")
async def get_postgres_table_schema(table_name: str):
    """Get schema for a PostgreSQL table"""
    try:
        from backend.utils.postgres_backup import get_table_schema

        schema = get_table_schema(table_name)
        return {"columns": schema}
    except Exception as exc:
        logger.error("Failed to get PostgreSQL table schema: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/tables/{table_name}/rows")
async def get_postgres_table_rows(table_name: str, limit: int = 100, offset: int = 0):
    """Get rows from a PostgreSQL table"""
    try:
        from backend.utils.postgres_backup import get_table_rows

        rows = get_table_rows(table_name, limit=limit, offset=offset)
        return {"items": rows}
    except Exception as exc:
        logger.error("Failed to get PostgreSQL table rows: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/postgres/tables/{table_name}/export")
async def export_postgres_table(table_name: str):
    """Export a PostgreSQL table to SQL"""
    try:
        from backend.utils.postgres_backup import export_table_sql

        sql_content = export_table_sql(table_name)

        return Response(
            content=sql_content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{table_name}.sql"'},
        )
    except Exception as exc:
        logger.error("Failed to export PostgreSQL table: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# MONGODB Routes
# ============================================================================


@router.get("/api/admin/mongodb/info")
async def get_mongodb_info():
    """Get MongoDB server information"""
    try:
        from backend.utils.mongo_backup import get_mongo_info

        return get_mongo_info()
    except Exception as exc:
        logger.error("Failed to get MongoDB info: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/backups")
async def list_mongodb_backups():
    """List all MongoDB backups"""
    try:
        from backend.utils.mongo_backup import list_backups

        backups = list_backups()
        return {
            "items": [
                {
                    "filename": b.filename,
                    "size_bytes": b.size_bytes,
                    "created_at": b.created_at.isoformat(),
                    "label": b.label,
                    "created_by": b.created_by,
                    "created_by_email": b.created_by_email,
                }
                for b in backups
            ]
        }
    except Exception as exc:
        logger.error("Failed to list MongoDB backups: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/mongodb/backups")
async def create_mongodb_backup(data: BackupCreate, request: Request):
    """Create a new MongoDB backup"""
    try:
        # Extract user info from headers (set by NextAuth frontend)
        user_name = request.headers.get("x-user-name")
        user_email = request.headers.get("x-user-email")

        from backend.utils.mongo_backup import create_backup

        backup = create_backup(label=data.label, user_name=user_name, user_email=user_email)
        return {
            "filename": backup.filename,
            "size_bytes": backup.size_bytes,
            "created_at": backup.created_at.isoformat(),
            "label": backup.label,
        }
    except Exception as exc:
        logger.error("Failed to create MongoDB backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/mongodb/backups/restore")
async def restore_mongodb_backup(data: BackupRestore):
    """Restore MongoDB from backup"""
    try:
        from backend.utils.mongo_backup import restore_backup

        result = restore_backup(data.filename, drop=data.drop)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as exc:
        logger.error("Failed to restore MongoDB backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/backups/download")
async def download_mongodb_backup(filename: str):
    """Download a MongoDB backup file"""
    try:
        from backend.utils.mongo_backup import get_backup_file

        backup_path = get_backup_file(filename)
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        with open(backup_path, "rb") as f:
            content = f.read()

        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("Failed to download MongoDB backup: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/collections")
async def list_mongodb_collections():
    """List all MongoDB collections"""
    try:
        from backend.utils.mongo_backup import list_collections

        collections = list_collections()
        return {"items": collections}
    except Exception as exc:
        logger.error("Failed to list MongoDB collections: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/collections/{collection_name}/schema")
async def get_mongodb_collection_schema(collection_name: str):
    """Get schema for a MongoDB collection"""
    try:
        from backend.utils.mongo_backup import get_collection_schema

        schema = get_collection_schema(collection_name)
        return schema
    except Exception as exc:
        logger.error("Failed to get MongoDB collection schema: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/collections/{collection_name}/documents")
async def get_mongodb_collection_documents(collection_name: str, limit: int = 100, skip: int = 0):
    """Get documents from a MongoDB collection"""
    try:
        from backend.utils.mongo_backup import get_collection_documents

        documents = get_collection_documents(collection_name, limit=limit, skip=skip)
        return {"items": documents}
    except Exception as exc:
        logger.error("Failed to get MongoDB collection documents: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/admin/mongodb/collections/{collection_name}/export")
async def export_mongodb_collection(collection_name: str):
    """Export a MongoDB collection to JSON"""
    try:
        from backend.utils.mongo_backup import export_collection_json

        json_content = export_collection_json(collection_name)

        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{collection_name}.json"'},
        )
    except Exception as exc:
        logger.error("Failed to export MongoDB collection: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# FILE IMPORT Endpoints
# ============================================================================


@router.post("/api/admin/redis/import")
async def import_redis_data(file: UploadFile = File(...)):
    """Import Redis data from JSON file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Restore from the uploaded file
        from backend.utils.redis_backup import restore_backup

        stats = restore_backup(tmp_path)

        # Clean up
        import os

        os.unlink(tmp_path)

        return {"message": "Redis data imported successfully", "stats": stats}
    except Exception as exc:
        logger.error("Failed to import Redis data: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/postgres/import")
async def import_postgres_data(file: UploadFile = File(...), clean: bool = False):
    """Import PostgreSQL data from dump file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dump") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Restore from the uploaded file
        from backend.utils.postgres_backup import restore_backup

        result = restore_backup(tmp_path, clean=clean)

        # Clean up
        import os

        os.unlink(tmp_path)

        return {"message": "PostgreSQL data imported successfully", "result": result}
    except Exception as exc:
        logger.error("Failed to import PostgreSQL data: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/mongodb/import")
async def import_mongodb_data(file: UploadFile = File(...), drop: bool = False):
    """Import MongoDB data from archive file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".archive") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Restore from the uploaded file
        from backend.utils.mongo_backup import restore_backup

        result = restore_backup(tmp_path, drop=drop)

        # Clean up
        import os

        os.unlink(tmp_path)

        return {"message": "MongoDB data imported successfully", "result": result}
    except Exception as exc:
        logger.error("Failed to import MongoDB data: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/api/admin/sqlite/import")
async def import_sqlite_data(file: UploadFile = File(...)):
    """Import SQLite data from backup file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # Restore from the uploaded file
        from backend.utils.sqlite_backup import restore_backup

        restore_backup(tmp_path)

        # Clean up
        import os

        os.unlink(tmp_path)

        return {"message": "SQLite data imported successfully"}
    except Exception as exc:
        logger.error("Failed to import SQLite data: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
