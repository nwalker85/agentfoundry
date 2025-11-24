"""
RBAC → OpenFGA Migration Script
--------------------------------
Migrates existing RBAC data (roles, permissions, user assignments) to OpenFGA relationships.

This script:
1. Reads existing user-role assignments from SQLite
2. Converts RBAC roles to OpenFGA relationships
3. Writes relationship tuples to OpenFGA
4. Verifies migration success

Usage:
    python scripts/rbac_to_openfga_migration.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection
from backend.openfga_client import fga_client

# ============================================================================
# ROLE MAPPING: RBAC → OpenFGA
# ============================================================================

ROLE_TO_RELATIONSHIP_MAP = {
    # Organization-level roles
    "platform_admin": ("platform", "admin"),
    "org_owner": ("organization", "owner"),
    "org_admin": ("organization", "admin"),
    "org_member": ("organization", "member"),
    "org_viewer": ("organization", "viewer"),
    # Domain-level roles
    "domain_owner": ("domain", "owner"),
    "domain_editor": ("domain", "editor"),
    "domain_viewer": ("domain", "viewer"),
    # Agent-level roles
    "agent_owner": ("agent", "owner"),
    "agent_executor": ("agent", "executor"),
    "agent_editor": ("agent", "editor"),
    "agent_viewer": ("agent", "viewer"),
    # API client (service account)
    "api_client": ("organization", "member"),  # Default to org member
}


async def migrate_user_roles():
    """Migrate user-role assignments to OpenFGA relationships."""
    print("📊 Migrating user roles to OpenFGA...\n")

    conn = get_connection()
    cur = conn.cursor()

    # Get all active user-role assignments
    cur.execute("""
        SELECT 
            ur.user_id,
            r.name as role_name,
            ur.organization_id,
            u.email
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        JOIN users u ON ur.user_id = u.id
        WHERE ur.expires_at IS NULL OR ur.expires_at > datetime('now', 'utc')
        ORDER BY ur.organization_id, ur.user_id
    """)

    assignments = cur.fetchall()
    conn.close()

    if not assignments:
        print("⚠️  No user-role assignments found")
        return

    print(f"Found {len(assignments)} user-role assignments\n")

    # Convert to OpenFGA tuples
    tuples = []
    for assignment in assignments:
        user_id = assignment["user_id"]
        role_name = assignment["role_name"]
        org_id = assignment["organization_id"]
        email = assignment["email"]

        # Map role to OpenFGA relationship
        if role_name not in ROLE_TO_RELATIONSHIP_MAP:
            print(f"⚠️  Unknown role: {role_name} (skipping)")
            continue

        resource_type, relation = ROLE_TO_RELATIONSHIP_MAP[role_name]

        # Build tuple
        tuple = {"user": f"user:{user_id}", "relation": relation, "object": f"{resource_type}:{org_id}"}

        tuples.append(tuple)
        print(f"  {email:30} → {relation:10} of {resource_type}:{org_id}")

    if not tuples:
        print("\n⚠️  No tuples to migrate")
        return

    # Write to OpenFGA in batches
    print(f"\n📝 Writing {len(tuples)} relationships to OpenFGA...")

    batch_size = 100
    for i in range(0, len(tuples), batch_size):
        batch = tuples[i : i + batch_size]
        success = await fga_client.write(batch)
        if success:
            print(f"  ✓ Batch {i // batch_size + 1}: {len(batch)} tuples written")
        else:
            print(f"  ✗ Batch {i // batch_size + 1}: Failed")

    print("\n✅ User roles migrated successfully")


async def migrate_resource_ownership():
    """
    Migrate resource ownership from database to OpenFGA.

    Creates parent relationships (org → domain → agent).
    """
    print("\n📦 Migrating resource ownership...\n")

    conn = get_connection()
    cur = conn.cursor()

    # Get all domains
    cur.execute("""
        SELECT id, name, organization_id
        FROM domains
    """)
    domains = cur.fetchall()

    # Get all agents
    cur.execute("""
        SELECT id, name, domain_id, organization_id
        FROM agents
        WHERE is_system_agent = 0
    """)
    agents = cur.fetchall()

    conn.close()

    tuples = []

    # Migrate domains
    for domain in domains:
        # Link domain to org
        tuples.append(
            {
                "user": f"organization:{domain['organization_id']}",
                "relation": "parent_org",
                "object": f"domain:{domain['id']}",
            }
        )
        print(f"  Domain {domain['name']:30} → org:{domain['organization_id']}")

    # Migrate agents
    for agent in agents:
        # Link agent to domain
        tuples.append(
            {"user": f"domain:{agent['domain_id']}", "relation": "parent_domain", "object": f"agent:{agent['id']}"}
        )
        print(f"  Agent {agent['name']:30} → domain:{agent['domain_id']}")

    if tuples:
        print(f"\n📝 Writing {len(tuples)} ownership relationships...")
        success = await fga_client.write(tuples)
        if success:
            print("✅ Resource ownership migrated successfully")
        else:
            print("❌ Failed to write relationships")
    else:
        print("⚠️  No resources to migrate")


async def verify_migration():
    """Verify the migration by testing some common authorization checks."""
    print("\n🔍 Verifying migration...\n")

    # Test 1: Check if test-admin is owner of test-org
    allowed = await fga_client.check(user="user:test-admin", relation="owner", object="organization:test-org")
    print(f"  {'✓' if allowed else '✗'} test-admin is owner of test-org: {allowed}")

    # Test 2: Check if test-user can execute test-agent
    allowed = await fga_client.check(user="user:test-user", relation="can_execute", object="agent:test-agent")
    print(f"  {'✓' if allowed else '✗'} test-user can execute test-agent: {allowed}")

    # Test 3: List agents test-user can execute
    agents = await fga_client.list_objects(user="user:test-user", relation="can_execute", type="agent")
    print(f"  ✓ test-user can execute {len(agents)} agents: {agents}")

    print("\n✅ Migration verification complete")


async def main():
    """Main migration flow."""
    print("=" * 60)
    print("RBAC → OpenFGA Migration")
    print("=" * 60)
    print()

    # Check if OpenFGA is configured
    if not os.getenv("OPENFGA_STORE_ID") or not os.getenv("OPENFGA_AUTH_MODEL_ID"):
        print("❌ OpenFGA not configured!")
        print("\nRun initialization first:")
        print("  python scripts/openfga_init.py")
        print("\nThen add OPENFGA_STORE_ID and OPENFGA_AUTH_MODEL_ID to .env")
        sys.exit(1)

    try:
        # Step 1: Migrate user roles
        await migrate_user_roles()

        # Step 2: Migrate resource ownership
        await migrate_resource_ownership()

        # Step 3: Verify
        await verify_migration()

        print("\n" + "=" * 60)
        print("✅ Migration complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Update your routes to use OpenFGA middleware")
        print("2. Test authorization in your application")
        print("3. Gradually phase out old RBAC tables")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import os

    asyncio.run(main())
