"""
User Favorites API Routes

Provides endpoints for managing user tool favorites.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import db

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Pydantic Models
# ============================================================================


class FavoriteCreate(BaseModel):
    tool_name: str


class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    tool_name: str
    created_at: str


# ============================================================================
# Database Operations
# ============================================================================


def list_favorites(user_id: str) -> list[FavoriteResponse]:
    """List all favorites for a user"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, tool_name, created_at FROM user_tool_favorites WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()

        favorites = []
        for row in rows:
            favorites.append(
                FavoriteResponse(
                    id=row["id"],
                    user_id=row["user_id"],
                    tool_name=row["tool_name"],
                    created_at=str(row["created_at"]),
                )
            )
        return favorites


def add_favorite(user_id: str, tool_name: str) -> FavoriteResponse:
    """Add a tool to user's favorites"""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Check if already favorited
        cursor.execute(
            "SELECT id, user_id, tool_name, created_at FROM user_tool_favorites WHERE user_id = %s AND tool_name = %s",
            (user_id, tool_name),
        )
        existing = cursor.fetchone()

        if existing:
            # Already favorited, return existing
            return FavoriteResponse(
                id=existing["id"],
                user_id=existing["user_id"],
                tool_name=existing["tool_name"],
                created_at=str(existing["created_at"]),
            )

        # Create new favorite
        favorite_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO user_tool_favorites (id, user_id, tool_name) VALUES (%s, %s, %s)",
            (favorite_id, user_id, tool_name),
        )
        conn.commit()

        cursor.execute(
            "SELECT id, user_id, tool_name, created_at FROM user_tool_favorites WHERE id = %s",
            (favorite_id,),
        )
        row = cursor.fetchone()

        return FavoriteResponse(
            id=row["id"],
            user_id=row["user_id"],
            tool_name=row["tool_name"],
            created_at=str(row["created_at"]),
        )


def remove_favorite(user_id: str, tool_name: str) -> bool:
    """Remove a tool from user's favorites"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_tool_favorites WHERE user_id = %s AND tool_name = %s",
            (user_id, tool_name),
        )
        conn.commit()
        return cursor.rowcount > 0


def is_favorited(user_id: str, tool_name: str) -> bool:
    """Check if a tool is favorited by the user"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM user_tool_favorites WHERE user_id = %s AND tool_name = %s",
            (user_id, tool_name),
        )
        return cursor.fetchone() is not None


def get_popular_tools_db(limit: int = 10) -> list[dict]:
    """Get most favorited tools across all users"""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT tool_name, COUNT(*) as favorite_count
            FROM user_tool_favorites
            GROUP BY tool_name
            ORDER BY favorite_count DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        popular = []
        for row in rows:
            popular.append(
                {
                    "tool_name": row["tool_name"],
                    "favorite_count": row["favorite_count"],
                }
            )
        return popular


# ============================================================================
# API Endpoints
# ============================================================================


def get_favorites_routes(db_conn=None):
    """Factory function to create routes (db_conn is ignored, we use context manager)"""

    @router.get("/api/users/{user_id}/favorites", response_model=list[FavoriteResponse])
    async def list_favorites_endpoint(user_id: str):
        """List all favorites for a user"""
        try:
            return list_favorites(user_id)
        except Exception as exc:
            logger.error("Failed to list favorites: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to list favorites")

    @router.post("/api/users/{user_id}/favorites", response_model=FavoriteResponse)
    async def add_favorite_endpoint(user_id: str, data: FavoriteCreate):
        """Add a tool to user's favorites"""
        try:
            return add_favorite(user_id, data.tool_name)
        except Exception as exc:
            logger.error("Failed to add favorite: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to add favorite")

    @router.delete("/api/users/{user_id}/favorites/{tool_name}")
    async def remove_favorite_endpoint(user_id: str, tool_name: str):
        """Remove a tool from user's favorites"""
        try:
            removed = remove_favorite(user_id, tool_name)
            if not removed:
                raise HTTPException(status_code=404, detail="Favorite not found")
            return {"message": "Favorite removed successfully"}
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to remove favorite: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to remove favorite")

    @router.get("/api/users/{user_id}/favorites/{tool_name}/check")
    async def check_favorite_endpoint(user_id: str, tool_name: str):
        """Check if a tool is favorited"""
        try:
            favorited = is_favorited(user_id, tool_name)
            return {"is_favorited": favorited}
        except Exception as exc:
            logger.error("Failed to check favorite: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to check favorite")

    @router.get("/api/tools/popular")
    async def get_popular_tools_endpoint(limit: int = 10):
        """Get most favorited tools"""
        try:
            return get_popular_tools_db(limit)
        except Exception as exc:
            logger.error("Failed to get popular tools: %s", exc, exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to get popular tools")

    return router
