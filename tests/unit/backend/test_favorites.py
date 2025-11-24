"""
Unit Tests for User Favorites Functionality

Tests the favorites database operations and API endpoints.
"""

import pytest
import sqlite3
import tempfile
import os
import uuid
from pathlib import Path

# Add backend to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.routes.favorites import FavoritesDB, FavoriteCreate, FavoriteResponse


@pytest.fixture
def db_conn():
    """Create a temporary test database"""
    # Create temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Connect and set up schema
    conn = sqlite3.connect(db_path)
    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))

    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tool_favorites (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tool_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
            UNIQUE (user_id, tool_name)
        )
    """)

    # Insert test user
    test_user_id = "test-user-123"
    conn.execute(
        "INSERT INTO users (id, email, full_name) VALUES (?, ?, ?)",
        (test_user_id, "test@example.com", "Test User")
    )
    conn.commit()

    yield conn

    # Cleanup
    conn.close()
    os.unlink(db_path)


class TestFavoritesDB:
    """Test FavoritesDB class methods"""

    def test_add_favorite_new(self, db_conn):
        """Test adding a new favorite"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "salesforce.execute"

        result = db.add_favorite(user_id, tool_name)

        assert isinstance(result, FavoriteResponse)
        assert result.user_id == user_id
        assert result.tool_name == tool_name
        assert result.id is not None
        assert result.created_at is not None

    def test_add_favorite_duplicate(self, db_conn):
        """Test adding a duplicate favorite returns existing"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "servicenow.execute"

        # Add first time
        first = db.add_favorite(user_id, tool_name)

        # Add again
        second = db.add_favorite(user_id, tool_name)

        # Should return the same favorite
        assert first.id == second.id
        assert first.user_id == second.user_id
        assert first.tool_name == second.tool_name

    def test_list_favorites_empty(self, db_conn):
        """Test listing favorites when user has none"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"

        favorites = db.list_favorites(user_id)

        assert isinstance(favorites, list)
        assert len(favorites) == 0

    def test_list_favorites_multiple(self, db_conn):
        """Test listing multiple favorites"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"

        # Add multiple favorites
        tools = ["salesforce.execute", "servicenow.execute", "airtable.execute"]
        for tool in tools:
            db.add_favorite(user_id, tool)

        favorites = db.list_favorites(user_id)

        assert len(favorites) == 3
        tool_names = [f.tool_name for f in favorites]
        assert set(tool_names) == set(tools)

    def test_remove_favorite_exists(self, db_conn):
        """Test removing an existing favorite"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "slack.execute"

        # Add favorite
        db.add_favorite(user_id, tool_name)

        # Remove it
        result = db.remove_favorite(user_id, tool_name)

        assert result is True

        # Verify it's gone
        favorites = db.list_favorites(user_id)
        assert len(favorites) == 0

    def test_remove_favorite_not_exists(self, db_conn):
        """Test removing a non-existent favorite"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "nonexistent.execute"

        result = db.remove_favorite(user_id, tool_name)

        assert result is False

    def test_is_favorited_true(self, db_conn):
        """Test checking if a tool is favorited (true case)"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "github.execute"

        # Add favorite
        db.add_favorite(user_id, tool_name)

        # Check if favorited
        result = db.is_favorited(user_id, tool_name)

        assert result is True

    def test_is_favorited_false(self, db_conn):
        """Test checking if a tool is favorited (false case)"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "gitlab.execute"

        result = db.is_favorited(user_id, tool_name)

        assert result is False

    def test_get_popular_tools_empty(self, db_conn):
        """Test getting popular tools when none exist"""
        db = FavoritesDB(db_conn)

        popular = db.get_popular_tools(limit=10)

        assert isinstance(popular, list)
        assert len(popular) == 0

    def test_get_popular_tools_with_data(self, db_conn):
        """Test getting popular tools with multiple users"""
        db = FavoritesDB(db_conn)

        # Create additional test users
        user_ids = ["test-user-123"]
        for i in range(2, 5):
            user_id = f"test-user-{i}"
            db_conn.execute(
                "INSERT INTO users (id, email, full_name) VALUES (?, ?, ?)",
                (user_id, f"test{i}@example.com", f"Test User {i}")
            )
            user_ids.append(user_id)
        db_conn.commit()

        # Add favorites
        # salesforce: 3 users
        for user_id in user_ids[:3]:
            db.add_favorite(user_id, "salesforce.execute")

        # servicenow: 2 users
        for user_id in user_ids[:2]:
            db.add_favorite(user_id, "servicenow.execute")

        # slack: 1 user
        db.add_favorite(user_ids[0], "slack.execute")

        popular = db.get_popular_tools(limit=10)

        assert len(popular) == 3
        assert popular[0]["tool_name"] == "salesforce.execute"
        assert popular[0]["favorite_count"] == 3
        assert popular[1]["tool_name"] == "servicenow.execute"
        assert popular[1]["favorite_count"] == 2
        assert popular[2]["tool_name"] == "slack.execute"
        assert popular[2]["favorite_count"] == 1

    def test_get_popular_tools_limit(self, db_conn):
        """Test that limit parameter works correctly"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"

        # Add 5 different favorites
        tools = ["tool1.execute", "tool2.execute", "tool3.execute", "tool4.execute", "tool5.execute"]
        for tool in tools:
            db.add_favorite(user_id, tool)

        popular = db.get_popular_tools(limit=3)

        assert len(popular) == 3


class TestFavoritesIntegration:
    """Integration tests for the full favorites workflow"""

    def test_full_workflow(self, db_conn):
        """Test complete add, list, check, remove workflow"""
        db = FavoritesDB(db_conn)
        user_id = "test-user-123"
        tool_name = "jira.execute"

        # 1. Verify not favorited
        assert db.is_favorited(user_id, tool_name) is False

        # 2. Add favorite
        favorite = db.add_favorite(user_id, tool_name)
        assert favorite.tool_name == tool_name

        # 3. Verify favorited
        assert db.is_favorited(user_id, tool_name) is True

        # 4. List favorites
        favorites = db.list_favorites(user_id)
        assert len(favorites) == 1
        assert favorites[0].tool_name == tool_name

        # 5. Remove favorite
        removed = db.remove_favorite(user_id, tool_name)
        assert removed is True

        # 6. Verify removed
        assert db.is_favorited(user_id, tool_name) is False
        favorites = db.list_favorites(user_id)
        assert len(favorites) == 0

    def test_multiple_users_separate_favorites(self, db_conn):
        """Test that different users have separate favorites"""
        db = FavoritesDB(db_conn)

        # Create second user
        user1_id = "test-user-123"
        user2_id = "test-user-456"
        db_conn.execute(
            "INSERT INTO users (id, email, full_name) VALUES (?, ?, ?)",
            (user2_id, "test2@example.com", "Test User 2")
        )
        db_conn.commit()

        # Add different favorites for each user
        db.add_favorite(user1_id, "salesforce.execute")
        db.add_favorite(user2_id, "servicenow.execute")

        # Verify each user only sees their own favorites
        user1_favorites = db.list_favorites(user1_id)
        user2_favorites = db.list_favorites(user2_id)

        assert len(user1_favorites) == 1
        assert user1_favorites[0].tool_name == "salesforce.execute"

        assert len(user2_favorites) == 1
        assert user2_favorites[0].tool_name == "servicenow.execute"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
