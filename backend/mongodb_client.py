"""
MongoDB Client for Agent Foundry
DIS 1.6.0 Compliant Dossier Storage

This module provides async MongoDB connection and CRUD operations
for dossier management with proper security and multi-tenancy isolation.
"""

import logging
import os
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    Async MongoDB client for dossier storage.

    Features:
    - Async operations using motor
    - Multi-tenancy isolation (organizationId)
    - Connection pooling
    - Error handling
    - Health checks
    """

    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None
        self._connected = False

        # Get configuration from environment
        self.mongodb_url = os.getenv(
            "MONGODB_URL", "mongodb://foundry_dossier:foundry@mongodb:27017/dossiers?authSource=dossiers"
        )
        self.database_name = os.getenv("MONGODB_DATABASE", "dossiers")

    async def connect(self):
        """
        Establish connection to MongoDB.
        Called on application startup.
        """
        if self._connected:
            logger.warning("MongoDB already connected")
            return

        try:
            logger.info(f"Connecting to MongoDB: {self.database_name}")

            # Create async MongoDB client
            self.client = AsyncIOMotorClient(
                self.mongodb_url, maxPoolSize=50, minPoolSize=10, serverSelectionTimeoutMS=5000
            )

            # Get database reference
            self.db = self.client[self.database_name]

            # Test connection
            await self.client.admin.command("ping")

            self._connected = True
            logger.info("✅ MongoDB connected successfully")

        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """
        Close MongoDB connection.
        Called on application shutdown.
        """
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB connection closed")

    async def health_check(self) -> dict[str, Any]:
        """
        Check MongoDB health status.

        Returns:
            dict: Health status with connection info
        """
        if not self._connected or not self.client:
            return {"status": "unhealthy", "error": "Not connected"}

        try:
            # Ping database
            await self.client.admin.command("ping")

            # Get server info
            server_info = await self.client.server_info()

            # Count documents in main collections
            dossier_count = await self.db.dossiers.count_documents({})
            version_count = await self.db.dossier_versions.count_documents({})
            operation_count = await self.db.dossier_operations.count_documents({})

            return {
                "status": "healthy",
                "database": self.database_name,
                "mongodb_version": server_info.get("version", "unknown"),
                "collections": {"dossiers": dossier_count, "versions": version_count, "operations": operation_count},
                "connected": True,
            }
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    # ============================================
    # Collection Accessors
    # ============================================

    @property
    def dossiers(self) -> AsyncIOMotorCollection:
        """Get dossiers collection"""
        return self.db.dossiers

    @property
    def versions(self) -> AsyncIOMotorCollection:
        """Get dossier_versions collection"""
        return self.db.dossier_versions

    @property
    def operations(self) -> AsyncIOMotorCollection:
        """Get dossier_operations collection"""
        return self.db.dossier_operations

    @property
    def locks(self) -> AsyncIOMotorCollection:
        """Get dossier_locks collection"""
        return self.db.dossier_locks

    # ============================================
    # Dossier CRUD Operations
    # ============================================

    async def create_dossier(self, dossier_data: dict[str, Any], organization_id: str, user_id: str) -> dict[str, Any]:
        """
        Create a new dossier with multi-tenancy isolation.

        Args:
            dossier_data: Dossier content (DIS 1.6.0 compliant)
            organization_id: Organization ID for isolation
            user_id: User creating the dossier

        Returns:
            dict: Created dossier with _id

        Raises:
            DuplicateKeyError: If dossierId already exists
        """
        # Add metadata
        dossier_data["organizationId"] = organization_id
        dossier_data["metadata"] = {
            "createdAt": datetime.utcnow(),
            "createdBy": user_id,
            "updatedAt": datetime.utcnow(),
            "updatedBy": user_id,
            "locked": False,
        }

        # Insert dossier
        result = await self.dossiers.insert_one(dossier_data)

        # Log operation
        await self._log_operation(
            dossier_id=dossier_data["dossierId"], operation_type="CREATE", user_id=user_id, status="SUCCESS"
        )

        dossier_data["_id"] = result.inserted_id
        return dossier_data

    async def get_dossier(
        self, dossier_id: str, organization_id: str, version: str | None = None
    ) -> dict[str, Any] | None:
        """
        Retrieve a dossier by ID with org isolation.

        Args:
            dossier_id: Dossier identifier
            organization_id: Organization ID for isolation
            version: Optional specific version

        Returns:
            dict: Dossier document or None
        """
        if version:
            # Get specific version from versions collection
            version_doc = await self.versions.find_one({"dossierId": dossier_id, "version": version})
            return version_doc["dossierSnapshot"] if version_doc else None

        # Get latest version from main collection
        return await self.dossiers.find_one({"dossierId": dossier_id, "organizationId": organization_id})

    async def list_dossiers(
        self, organization_id: str, filters: dict[str, Any] | None = None, limit: int = 50, skip: int = 0
    ) -> list[dict[str, Any]]:
        """
        List dossiers for an organization with optional filters.

        Args:
            organization_id: Organization ID for isolation
            filters: Optional query filters (status, tags, industry, etc.)
            limit: Max results to return
            skip: Number of results to skip (pagination)

        Returns:
            list: Dossier documents
        """
        query = {"organizationId": organization_id}

        # Apply filters
        if filters:
            if "status" in filters:
                query["header.dossierStatus"] = filters["status"]
            if "tags" in filters:
                query["header.tags"] = {"$in": filters["tags"]}
            if "industryVertical" in filters:
                query["header.industryVertical"] = filters["industryVertical"]
            if "dossierType" in filters:
                query["header.dossierType"] = filters["dossierType"]

        cursor = self.dossiers.find(query).sort("metadata.updatedAt", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def update_dossier(
        self, dossier_id: str, organization_id: str, updates: dict[str, Any], user_id: str
    ) -> bool:
        """
        Update a dossier.

        Args:
            dossier_id: Dossier identifier
            organization_id: Organization ID for isolation
            updates: Fields to update
            user_id: User making the update

        Returns:
            bool: True if updated
        """
        # Add update metadata
        updates["metadata.updatedAt"] = datetime.utcnow()
        updates["metadata.updatedBy"] = user_id

        result = await self.dossiers.update_one(
            {"dossierId": dossier_id, "organizationId": organization_id}, {"$set": updates}
        )

        if result.modified_count > 0:
            await self._log_operation(dossier_id=dossier_id, operation_type="UPDATE", user_id=user_id, status="SUCCESS")
            return True

        return False

    async def delete_dossier(self, dossier_id: str, organization_id: str, user_id: str) -> bool:
        """
        Delete a dossier (and all its versions).

        Args:
            dossier_id: Dossier identifier
            organization_id: Organization ID for isolation
            user_id: User deleting the dossier

        Returns:
            bool: True if deleted
        """
        result = await self.dossiers.delete_one({"dossierId": dossier_id, "organizationId": organization_id})

        if result.deleted_count > 0:
            # Also delete versions
            await self.versions.delete_many({"dossierId": dossier_id})

            await self._log_operation(dossier_id=dossier_id, operation_type="DELETE", user_id=user_id, status="SUCCESS")
            return True

        return False

    # ============================================
    # Versioning Operations
    # ============================================

    async def create_version(
        self, dossier_id: str, version: str, dossier_snapshot: dict[str, Any], change_info: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """
        Create a new version snapshot of a dossier.

        Args:
            dossier_id: Dossier identifier
            version: Version string (e.g., "2.1.0")
            dossier_snapshot: Complete dossier at this version
            change_info: Change management metadata
            user_id: User creating the version

        Returns:
            dict: Version document
        """
        version_doc = {
            "dossierId": dossier_id,
            "version": version,
            "snapshotDate": datetime.utcnow(),
            "dossierSnapshot": dossier_snapshot,
            "changeManagement": {**change_info, "changedBy": user_id},
            "tags": [],
        }

        result = await self.versions.insert_one(version_doc)
        version_doc["_id"] = result.inserted_id

        return version_doc

    # ============================================
    # Helper Methods
    # ============================================

    async def _log_operation(
        self,
        dossier_id: str,
        operation_type: str,
        user_id: str,
        status: str,
        agent_id: str | None = None,
        duration: int | None = None,
        errors: list[Any] | None = None,
    ):
        """Log dossier operation to audit trail"""
        operation_doc = {
            "operationId": f"{dossier_id}-{operation_type}-{int(datetime.utcnow().timestamp())}",
            "dossierId": dossier_id,
            "operationType": operation_type,
            "timestamp": datetime.utcnow(),
            "userId": user_id,
            "status": status,
        }

        if agent_id:
            operation_doc["agentId"] = agent_id
        if duration:
            operation_doc["duration"] = duration
        if errors:
            operation_doc["errors"] = errors

        try:
            await self.operations.insert_one(operation_doc)
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")


# Global MongoDB client instance
mongodb_client = MongoDBClient()


async def get_mongodb() -> MongoDBClient:
    """
    Dependency for FastAPI routes to get MongoDB client.

    Usage:
        @router.get("/dossiers")
        async def list_dossiers(db: MongoDBClient = Depends(get_mongodb)):
            ...
    """
    return mongodb_client
