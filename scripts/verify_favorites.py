#!/usr/bin/env python3
"""
Verify Favorites Functionality

Script to verify that the favorites system is working correctly by:
1. Checking database schema
2. Querying existing favorites
3. Testing API endpoints
"""

import sqlite3

import requests

DATABASE_PATH = "/app/data/foundry.db"
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "bf20814a-6126-4cd5-b692-cd89e2880077"


def dict_factory(cursor, row):
    """Convert SQLite row to dictionary"""
    fields = [column[0] for column in cursor.description]
    return dict(zip(fields, row))


def check_database_schema():
    """Verify the user_tool_favorites table exists and has correct schema"""
    print("=" * 60)
    print("1. Checking Database Schema")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_tool_favorites'
        """)
        table_exists = cursor.fetchone()

        if table_exists:
            print("✅ user_tool_favorites table exists")

            # Check schema
            cursor.execute("PRAGMA table_info(user_tool_favorites)")
            columns = cursor.fetchall()

            print("\nTable Schema:")
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")

            # Check for unique constraint
            cursor.execute("""
                SELECT sql FROM sqlite_master
                WHERE type='table' AND name='user_tool_favorites'
            """)
            create_sql = cursor.fetchone()
            if create_sql and "UNIQUE" in create_sql["sql"]:
                print("✅ UNIQUE constraint on (user_id, tool_name) exists")

            return True
        else:
            print("❌ user_tool_favorites table does NOT exist")
            return False

    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return False
    finally:
        conn.close()


def check_existing_favorites():
    """Query and display existing favorites in the database"""
    print("\n" + "=" * 60)
    print("2. Checking Existing Favorites in Database")
    print("=" * 60)

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = dict_factory
        cursor = conn.cursor()

        # Get all favorites for test user
        cursor.execute(
            """
            SELECT id, user_id, tool_name, created_at
            FROM user_tool_favorites
            WHERE user_id = ?
            ORDER BY created_at DESC
        """,
            (TEST_USER_ID,),
        )

        favorites = cursor.fetchall()

        if favorites:
            print(f"✅ Found {len(favorites)} favorites for user {TEST_USER_ID}:\n")
            for i, fav in enumerate(favorites, 1):
                print(f"{i}. {fav['tool_name']}")
                print(f"   ID: {fav['id']}")
                print(f"   Created: {fav['created_at']}\n")
        else:
            print(f"⚠️  No favorites found for user {TEST_USER_ID}")

        # Get total count across all users
        cursor.execute("SELECT COUNT(*) as total FROM user_tool_favorites")
        total = cursor.fetchone()["total"]
        print(f"Total favorites across all users: {total}")

        return len(favorites) > 0

    except Exception as e:
        print(f"❌ Error querying favorites: {e}")
        return False
    finally:
        conn.close()


def test_api_endpoints():
    """Test the favorites API endpoints"""
    print("\n" + "=" * 60)
    print("3. Testing API Endpoints")
    print("=" * 60)

    success_count = 0
    total_tests = 0

    # Test 1: List favorites
    total_tests += 1
    print(f"\nTest 1: GET /api/users/{TEST_USER_ID}/favorites")
    try:
        response = requests.get(f"{API_BASE_URL}/api/users/{TEST_USER_ID}/favorites")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Returned {len(data)} favorites")
            success_count += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: Add a new favorite
    total_tests += 1
    test_tool = "test.verification.tool"
    print(f"\nTest 2: POST /api/users/{TEST_USER_ID}/favorites")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/users/{TEST_USER_ID}/favorites",
            json={"tool_name": test_tool},
            headers={"Content-Type": "application/json"},
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Added favorite: {data['tool_name']}")
            success_count += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Check if favorited
    total_tests += 1
    print(f"\nTest 3: GET /api/users/{TEST_USER_ID}/favorites/{test_tool}/check")
    try:
        response = requests.get(f"{API_BASE_URL}/api/users/{TEST_USER_ID}/favorites/{test_tool}/check")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Is favorited: {data['is_favorited']}")
            success_count += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 4: Remove the test favorite
    total_tests += 1
    print(f"\nTest 4: DELETE /api/users/{TEST_USER_ID}/favorites/{test_tool}")
    try:
        response = requests.delete(f"{API_BASE_URL}/api/users/{TEST_USER_ID}/favorites/{test_tool}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"   Message: {data['message']}")
            success_count += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 5: Get popular tools
    total_tests += 1
    print("\nTest 5: GET /api/tools/popular")
    try:
        response = requests.get(f"{API_BASE_URL}/api/tools/popular?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print("   Popular tools (top 5):")
            for i, tool in enumerate(data[:5], 1):
                print(f"   {i}. {tool['tool_name']} ({tool['favorite_count']} favorites)")
            success_count += 1
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print(f"\n{'=' * 60}")
    print(f"API Tests: {success_count}/{total_tests} passed")
    print("=" * 60)

    return success_count == total_tests


def main():
    """Run all verification checks"""
    print("\n🔍 FAVORITES FUNCTIONALITY VERIFICATION")
    print("=" * 60)

    results = {"schema": check_database_schema(), "data": check_existing_favorites(), "api": test_api_endpoints()}

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Database Schema: {'✅ PASS' if results['schema'] else '❌ FAIL'}")
    print(f"Database Data:   {'✅ PASS' if results['data'] else '⚠️  NO DATA'}")
    print(f"API Endpoints:   {'✅ PASS' if results['api'] else '❌ FAIL'}")

    if all([results["schema"], results["api"]]):
        print("\n🎉 All verification checks passed!")
        return 0
    else:
        print("\n⚠️  Some verification checks failed")
        return 1


if __name__ == "__main__":
    exit(main())
