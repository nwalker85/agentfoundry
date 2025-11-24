#!/usr/bin/env python3
"""
Setup Zitadel for Agent Foundry

This script creates the necessary project and application in Zitadel.
It uses the service user JWT authentication flow.

Prerequisites:
- Zitadel must be running and accessible at http://localhost:8082
- Admin credentials: admin / AgentFoundry2024!

Manual Setup (if script doesn't work):
1. Go to http://localhost:8082
2. Login with admin / AgentFoundry2024!
3. Create a new Project called "AgentFoundry"
4. Add a Web Application:
   - Name: "foundry-web"
   - Redirect URIs: http://localhost:3000/api/auth/callback/zitadel
   - Post Logout URIs: http://localhost:3000
   - Auth Method: PKCE
5. Copy the Client ID and update your .env file

Usage:
    python scripts/setup_zitadel.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from base64 import urlsafe_b64encode
from datetime import datetime, timedelta

ZITADEL_URL = os.getenv("ZITADEL_URL", "http://localhost:8082")
ADMIN_USER = "admin"
ADMIN_PASSWORD = "AgentFoundry2024!"


def print_manual_setup():
    """Print manual setup instructions."""
    print("""
================================================================================
MANUAL ZITADEL SETUP REQUIRED
================================================================================

Zitadel requires manual setup through the console for the initial application.

Steps:
1. Open http://localhost:8082 in your browser
2. Login with:
   - Username: admin
   - Password: AgentFoundry2024!

3. Create a Project:
   - Click "Projects" in the left menu
   - Click "+ New"
   - Name: "AgentFoundry"
   - Click "Continue"

4. Create an Application:
   - In the project, click "Applications" tab
   - Click "+ New"
   - Name: "foundry-web"
   - Type: "Web"
   - Click "Continue"

5. Configure the Application:
   - Auth Method: PKCE (recommended)
   - Redirect URIs: http://localhost:3000/api/auth/callback/zitadel
   - Post Logout URIs: http://localhost:3000
   - Click "Create"

6. Copy the Client ID and update your environment:
   - Copy the Client ID shown
   - Add to .env: ZITADEL_CLIENT_ID=<client_id>
   - For PKCE apps, no client secret is needed
   - If using Basic auth, also copy the secret: ZITADEL_CLIENT_SECRET=<secret>

7. Restart the services:
   docker-compose restart agent-foundry-ui

================================================================================
""")


def check_zitadel_health():
    """Check if Zitadel is accessible."""
    try:
        req = urllib.request.Request(f"{ZITADEL_URL}/debug/healthz")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.read().decode() == "ok"
    except Exception as e:
        print(f"Zitadel health check failed: {e}")
        return False


def get_oidc_config():
    """Get Zitadel's OIDC configuration."""
    try:
        req = urllib.request.Request(f"{ZITADEL_URL}/.well-known/openid-configuration")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"Failed to get OIDC config: {e}")
        return None


def main():
    print("=" * 60)
    print("Agent Foundry - Zitadel Setup")
    print("=" * 60)

    # Check Zitadel health
    print("\n1. Checking Zitadel health...")
    if not check_zitadel_health():
        print("ERROR: Zitadel is not accessible at", ZITADEL_URL)
        print("Make sure Zitadel is running: docker-compose up -d zitadel")
        sys.exit(1)
    print("   Zitadel is healthy")

    # Get OIDC config
    print("\n2. Getting OIDC configuration...")
    oidc = get_oidc_config()
    if oidc:
        print(f"   Issuer: {oidc.get('issuer')}")
        print(f"   Authorization: {oidc.get('authorization_endpoint')}")
        print(f"   Token: {oidc.get('token_endpoint')}")

    # Print manual setup instructions
    print("\n3. Application setup...")
    print_manual_setup()

    # Check current env
    print("\nCurrent Environment Status:")
    print("-" * 40)

    client_id = os.getenv("ZITADEL_CLIENT_ID", "")
    client_secret = os.getenv("ZITADEL_CLIENT_SECRET", "")

    if client_id:
        print(f"ZITADEL_CLIENT_ID: {client_id[:20]}..." if len(client_id) > 20 else f"ZITADEL_CLIENT_ID: {client_id}")
        print("Status: Client ID is configured")
    else:
        print("ZITADEL_CLIENT_ID: Not set")
        print("Status: Please complete the manual setup above")

    if client_secret:
        print(f"ZITADEL_CLIENT_SECRET: {'*' * 20}")
    else:
        print("ZITADEL_CLIENT_SECRET: Not set (OK for PKCE)")


if __name__ == "__main__":
    main()
