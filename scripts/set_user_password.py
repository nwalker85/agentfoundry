#!/usr/bin/env python3
"""
Set User Password Script
Sets or updates a user's password for local authentication.

Usage:
    python scripts/set_user_password.py <email> <password>
    python scripts/set_user_password.py nate@ravenhelm.co MySecurePassword123

The password must be at least 8 characters.
"""

import sys
from pathlib import Path

import bcrypt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.db import get_connection


def set_password(email: str, password: str) -> bool:
    """
    Set or update a user's password.

    Args:
        email: User email address
        password: Plain text password (will be hashed)

    Returns:
        True if successful, False otherwise
    """
    if len(password) < 8:
        print("Error: Password must be at least 8 characters")
        return False

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        with get_connection() as conn:
            cur = conn.cursor()

            # Check if user exists
            cur.execute("SELECT id, name FROM users WHERE email = ?", (email,))
            user = cur.fetchone()

            if not user:
                print(f"Error: User not found: {email}")
                return False

            user_id, name = user

            # Update password
            cur.execute(
                "UPDATE users SET password_hash = ?, updated_at = datetime('now', 'utc') WHERE email = ?",
                (password_hash, email),
            )
            conn.commit()

            print(f"Password set successfully for {name} ({email})")
            print(f"User ID: {user_id}")
            return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nConfigured users:")
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT email, name, password_hash IS NOT NULL as has_password FROM users")
                users = cur.fetchall()
                for email, name, has_password in users:
                    status = "has password" if has_password else "SSO only"
                    print(f"  - {email} ({name}) [{status}]")
        except Exception as e:
            print(f"  Could not list users: {e}")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    success = set_password(email, password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
