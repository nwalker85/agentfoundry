#!/usr/bin/env python3
"""
Setup Admin User Script
Creates or updates the platform administrator user (nate@ravenhelm.co).
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection
from backend.rbac_models import UserRoleAssignmentCreate
from backend.rbac_service import rbac_service


def setup_admin_user():
    """
    Set up the admin user (nate@ravenhelm.co) with platform_owner role.
    """

    ADMIN_EMAIL = "nate@ravenhelm.co"
    ADMIN_NAME = "Nate Walker"

    print("🔐 Setting up platform administrator...")

    # 1. Ensure default organization exists
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Check if "Platform" org exists
            cur.execute("SELECT id FROM organizations WHERE id = 'platform'")
            org = cur.fetchone()

            if not org:
                print("Creating platform organization...")
                cur.execute(
                    """
                    INSERT INTO organizations (id, name, tier)
                    VALUES ('platform', 'Platform', 'enterprise')
                    ON CONFLICT (id) DO NOTHING
                    """
                )

            # Check if user exists
            cur.execute("SELECT id FROM users WHERE email = %s", (ADMIN_EMAIL,))
            user = cur.fetchone()

            if not user:
                print(f"Creating user: {ADMIN_EMAIL}...")
                user_id = ADMIN_EMAIL.split("@")[0]  # Use 'nate' as ID

                cur.execute(
                    """
                    INSERT INTO users (id, organization_id, email, name)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE
                    SET name = EXCLUDED.name
                    RETURNING id
                    """,
                    (user_id, "platform", ADMIN_EMAIL, ADMIN_NAME),
                )
                user = cur.fetchone()
                user_id = user[0]
                print(f"✅ User created: {user_id}")
            else:
                user_id = user[0]
                print(f"✅ User already exists: {user_id}")

        conn.commit()

    # 2. Assign platform_owner role
    print("Assigning platform_owner role...")

    try:
        assignment = UserRoleAssignmentCreate(
            user_id=user_id, role_name="platform_owner", organization_id="platform", granted_by="system"
        )

        result = rbac_service.assign_role(assignment)
        print("✅ Role assigned: platform_owner")
    except Exception as e:
        print(f"⚠️  Role assignment warning: {e}")
        # May already be assigned

    # 3. Verify permissions
    print("\nVerifying permissions...")
    permissions = rbac_service.get_user_permissions(user_id, "platform")

    print(f"✅ User has {len(permissions)} permissions")

    # Check key permissions
    key_permissions = [
        "org:read:platform",
        "org:update:platform",
        "user:read:platform",
        "agent:read:org",
        "audit:read:platform",
    ]

    for perm in key_permissions:
        has_perm = perm in permissions
        status = "✅" if has_perm else "❌"
        print(f"  {status} {perm}")

    # 4. Create API key for admin (optional)
    print("\n💡 To create an API key for this user, run:")
    print(f"   python scripts/create_api_key.py {user_id} platform 'Admin API Key'")

    print("\n" + "=" * 60)
    print("✅ Admin user setup complete!")
    print("=" * 60)
    print(f"Email: {ADMIN_EMAIL}")
    print(f"User ID: {user_id}")
    print("Organization: platform")
    print("Role: platform_owner")
    print(f"Permissions: {len(permissions)}")
    print("=" * 60)

    return user_id


if __name__ == "__main__":
    try:
        setup_admin_user()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
