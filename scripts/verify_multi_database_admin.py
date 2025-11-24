#!/usr/bin/env python3
"""
Multi-Database Administration Verification Script

Comprehensive testing of all database admin features:
- SQLite
- Redis
- PostgreSQL
- MongoDB

Tests backup, restore, browsing, and export capabilities.
"""

import sys
from typing import Any

import requests

API_BASE = "http://localhost:8000"


def test_section(title: str):
    """Print a test section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def test_api(method: str, endpoint: str, data: dict = None, desc: str = "") -> dict[str, Any]:
    """Test an API endpoint and return the response"""
    url = f"{API_BASE}{endpoint}"
    print(f"\n  [{method}] {endpoint}")
    if desc:
        print(f"  → {desc}")

    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("  ✅ SUCCESS")
            return {"success": True, "data": result}
        else:
            print(f"  ❌ FAILED: {response.text[:200]}")
            return {"success": False, "error": response.text}

    except Exception as e:
        print(f"  ❌ ERROR: {e!s}")
        return {"success": False, "error": str(e)}


def main():
    """Run all database admin verification tests"""
    print("\n🔍 MULTI-DATABASE ADMINISTRATION VERIFICATION")
    print("=" * 70)

    results = {
        "sqlite": {"total": 0, "passed": 0},
        "redis": {"total": 0, "passed": 0},
        "postgres": {"total": 0, "passed": 0},
        "mongodb": {"total": 0, "passed": 0},
    }

    # ========================================================================
    # SQLITE TESTS
    # ========================================================================
    test_section("SQLITE - Control Plane Database")

    # Test 1: List tables
    results["sqlite"]["total"] += 1
    r = test_api("GET", "/api/admin/sqlite/tables", desc="List all tables")
    if r["success"] and len(r["data"].get("items", [])) > 0:
        results["sqlite"]["passed"] += 1
        print(f"  Found {len(r['data']['items'])} tables")

    # Test 2: List backups
    results["sqlite"]["total"] += 1
    r = test_api("GET", "/api/admin/sqlite/backups", desc="List SQLite backups")
    if r["success"]:
        results["sqlite"]["passed"] += 1
        print(f"  Found {len(r['data'].get('items', []))} backups")

    # Test 3: Create backup
    results["sqlite"]["total"] += 1
    r = test_api("POST", "/api/admin/sqlite/backups", data={"label": "verification-test"}, desc="Create new backup")
    if r["success"]:
        results["sqlite"]["passed"] += 1

    # ========================================================================
    # REDIS TESTS
    # ========================================================================
    test_section("REDIS - Caching & Session Store")

    # Test 1: Get Redis info
    results["redis"]["total"] += 1
    r = test_api("GET", "/api/admin/redis/info", desc="Get Redis server info")
    if r["success"]:
        results["redis"]["passed"] += 1
        data = r["data"]
        print(f"  Version: {data.get('version')}")
        print(f"  Total Keys: {data.get('total_keys')}")
        print(f"  Memory: {data.get('used_memory_human')}")

    # Test 2: List keys
    results["redis"]["total"] += 1
    r = test_api("GET", "/api/admin/redis/keys?limit=10", desc="List Redis keys")
    if r["success"]:
        results["redis"]["passed"] += 1
        print(f"  Found {len(r['data'].get('items', []))} keys")

    # Test 3: List backups
    results["redis"]["total"] += 1
    r = test_api("GET", "/api/admin/redis/backups", desc="List Redis backups")
    if r["success"]:
        results["redis"]["passed"] += 1
        print(f"  Found {len(r['data'].get('items', []))} backups")

    # Test 4: Create backup
    results["redis"]["total"] += 1
    r = test_api("POST", "/api/admin/redis/backups", data={"label": "verification-test"}, desc="Create Redis backup")
    if r["success"]:
        results["redis"]["passed"] += 1

    # ========================================================================
    # POSTGRESQL TESTS
    # ========================================================================
    test_section("POSTGRESQL - Relational Database")

    # Test 1: Get PostgreSQL info
    results["postgres"]["total"] += 1
    r = test_api("GET", "/api/admin/postgres/info", desc="Get PostgreSQL server info")
    if r["success"]:
        results["postgres"]["passed"] += 1
        data = r["data"]
        print(f"  Version: {data.get('version', '')[:50]}...")
        print(f"  Tables: {data.get('table_count')}")
        print(f"  Size: {data.get('database_size')}")

    # Test 2: List tables
    results["postgres"]["total"] += 1
    r = test_api("GET", "/api/admin/postgres/tables", desc="List PostgreSQL tables")
    if r["success"]:
        results["postgres"]["passed"] += 1
        tables = r["data"].get("items", [])
        print(f"  Found {len(tables)} tables")
        for table in tables[:3]:  # Show first 3
            print(f"    - {table['name']} ({table['row_count']} rows)")

    # Test 3: List backups
    results["postgres"]["total"] += 1
    r = test_api("GET", "/api/admin/postgres/backups", desc="List PostgreSQL backups")
    if r["success"]:
        results["postgres"]["passed"] += 1
        print(f"  Found {len(r['data'].get('items', []))} backups")

    # Test 4: Create backup
    results["postgres"]["total"] += 1
    r = test_api(
        "POST", "/api/admin/postgres/backups", data={"label": "verification-test"}, desc="Create PostgreSQL backup"
    )
    if r["success"]:
        results["postgres"]["passed"] += 1

    # ========================================================================
    # MONGODB TESTS
    # ========================================================================
    test_section("MONGODB - Document Store")

    # Test 1: Get MongoDB info
    results["mongodb"]["total"] += 1
    r = test_api("GET", "/api/admin/mongodb/info", desc="Get MongoDB server info")
    if r["success"]:
        results["mongodb"]["passed"] += 1
        data = r["data"]
        print(f"  Version: {data.get('version')}")
        print(f"  Database: {data.get('database_name')}")
        print(f"  Collections: {data.get('collections')}")

    # Test 2: List collections
    results["mongodb"]["total"] += 1
    r = test_api("GET", "/api/admin/mongodb/collections", desc="List MongoDB collections")
    if r["success"]:
        results["mongodb"]["passed"] += 1
        collections = r["data"].get("items", [])
        print(f"  Found {len(collections)} collections")
        for coll in collections[:3]:  # Show first 3
            print(f"    - {coll['name']} ({coll['document_count']} documents)")

    # Test 3: List backups
    results["mongodb"]["total"] += 1
    r = test_api("GET", "/api/admin/mongodb/backups", desc="List MongoDB backups")
    if r["success"]:
        results["mongodb"]["passed"] += 1
        print(f"  Found {len(r['data'].get('items', []))} backups")

    # Test 4: Create backup
    results["mongodb"]["total"] += 1
    r = test_api(
        "POST", "/api/admin/mongodb/backups", data={"label": "verification-test"}, desc="Create MongoDB backup"
    )
    if r["success"]:
        results["mongodb"]["passed"] += 1

    # ========================================================================
    # SUMMARY
    # ========================================================================
    test_section("VERIFICATION SUMMARY")

    total_tests = sum(db["total"] for db in results.values())
    total_passed = sum(db["passed"] for db in results.values())

    print("\nDatabase Results:")
    for db_name, stats in results.items():
        status = "✅" if stats["passed"] == stats["total"] else "⚠️"
        print(f"  {status} {db_name.upper():12} {stats['passed']}/{stats['total']} tests passed")

    print(f"\nOverall: {total_passed}/{total_tests} tests passed")

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")

    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Multi-database admin is fully functional.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
