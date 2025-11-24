"""
Store Zitadel Configuration in LocalStack
------------------------------------------
Stores Zitadel OIDC configuration (client_id, client_secret, issuer) in LocalStack
instead of .env files.

Usage:
    python scripts/zitadel_setup_localstack.py <client_id> <client_secret> [--issuer URL]

Example:
    python scripts/zitadel_setup_localstack.py 123456789@agentfoundry secret123 --issuer http://localhost:8082
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.secrets import secrets_manager


async def store_zitadel_config(
    client_id: str,
    client_secret: str,
    issuer_url: str = "http://zitadel:8080",
):
    """Store Zitadel OIDC configuration in LocalStack"""

    print("📦 Storing Zitadel configuration in LocalStack...")
    print(f"   Client ID: {client_id}")
    print(f"   Issuer URL: {issuer_url}")
    print()

    # Build JWKS URL from issuer
    jwks_url = f"{issuer_url}/.well-known/jwks.json"

    # Package as JSON
    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "issuer_url": issuer_url,
        "jwks_url": jwks_url,
        "token_endpoint": f"{issuer_url}/oauth/v2/token",
        "authorization_endpoint": f"{issuer_url}/oauth/v2/authorize",
        "userinfo_endpoint": f"{issuer_url}/oidc/v1/userinfo",
        "created_at": "2025-11-24",
        "description": "Zitadel OIDC client configuration for Agent Foundry",
    }

    # Store in LocalStack as platform-level secret
    success = await secrets_manager.upsert_secret(
        organization_id="platform",
        secret_name="zitadel_config",
        secret_value=json.dumps(config),
        domain_id=None,
        description="Zitadel OIDC client credentials and endpoints",
    )

    if success:
        print("✅ Zitadel configuration stored in LocalStack")
        print()
        print("Configuration is now in LocalStack, not .env!")
        print()
        print("Secret path: agentfoundry/dev/platform/zitadel_config")
        print()
        print("Backend will automatically retrieve it at startup.")
        print()
        print("To verify:")
        print("  docker-compose restart foundry-backend")
        print("  docker-compose logs foundry-backend | grep Zitadel")
    else:
        print("❌ Failed to store configuration")
        sys.exit(1)


def print_usage():
    """Print usage instructions"""
    print("Usage: python scripts/zitadel_setup_localstack.py <client_id> <client_secret> [--issuer URL]")
    print()
    print("Arguments:")
    print("  client_id      - Zitadel application client ID (e.g., 123456789@agentfoundry)")
    print("  client_secret  - Zitadel application client secret")
    print("  --issuer URL   - Zitadel issuer URL (default: http://zitadel:8080)")
    print()
    print("Example:")
    print("  # Using default issuer (internal Docker network)")
    print("  python scripts/zitadel_setup_localstack.py 123456789@agentfoundry mysecret")
    print()
    print("  # Using custom issuer (external access)")
    print("  python scripts/zitadel_setup_localstack.py 123456789@agentfoundry mysecret --issuer http://localhost:8082")
    print()
    print("Notes:")
    print("  - Run this AFTER creating an application in Zitadel console (http://localhost:8082)")
    print("  - The client_id and client_secret come from the Zitadel application setup")
    print("  - For local dev, use 'http://zitadel:8080' for backend (Docker DNS)")
    print("  - For browser access, use 'http://localhost:8082'")


if __name__ == "__main__":
    # Parse arguments
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    issuer_url = "http://zitadel:8080"  # Default to Docker internal URL

    # Check for --issuer flag
    if "--issuer" in sys.argv:
        idx = sys.argv.index("--issuer")
        if idx + 1 < len(sys.argv):
            issuer_url = sys.argv[idx + 1]
        else:
            print("Error: --issuer requires a URL argument")
            print_usage()
            sys.exit(1)

    asyncio.run(store_zitadel_config(client_id, client_secret, issuer_url))
