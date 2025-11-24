"""
Store SMTP Configuration in LocalStack
---------------------------------------
Stores SMTP/email configuration in LocalStack for the service registry pattern.
Defaults to Mailpit for local development.

Usage:
    python scripts/smtp_setup_localstack.py [--host HOST] [--port PORT] [--from EMAIL]

Example:
    # Use defaults (Mailpit)
    python scripts/smtp_setup_localstack.py

    # Custom SMTP server
    python scripts/smtp_setup_localstack.py --host smtp.example.com --port 587 --from noreply@example.com
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.secrets import secrets_manager


async def store_smtp_config(
    host: str = "mailpit",
    port: int = 1025,
    from_email: str = "noreply@agentfoundry.local",
    username: str | None = None,
    password: str | None = None,
    use_tls: bool = False,
):
    """Store SMTP configuration in LocalStack"""

    print("📧 Storing SMTP configuration in LocalStack...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   From: {from_email}")
    print(f"   TLS:  {use_tls}")
    print()

    # Package as JSON
    config = {
        "host": host,
        "port": port,
        "from_email": from_email,
        "from_name": "Agent Foundry",
        "use_tls": use_tls,
        "use_ssl": False,
        "created_at": "2025-11-24",
        "description": "SMTP configuration for Agent Foundry email notifications",
    }

    # Add credentials if provided
    if username:
        config["username"] = username
    if password:
        config["password"] = password

    # Store in LocalStack as platform-level secret
    success = await secrets_manager.upsert_secret(
        organization_id="platform",
        secret_name="smtp_config",
        secret_value=json.dumps(config),
        domain_id=None,
        description="SMTP server configuration for email delivery",
    )

    if success:
        print("SMTP configuration stored in LocalStack")
        print()
        print("Configuration is now in LocalStack, not .env!")
        print()
        print("Secret path: agentfoundry/dev/platform/smtp_config")
        print()
        print("Backend will automatically retrieve it at startup.")
        print()
        print("To verify:")
        print("  docker-compose restart foundry-backend")
        print("  docker-compose logs foundry-backend | grep SMTP")
        print()
        print("Mailpit Web UI: http://localhost:8025")
    else:
        print("Failed to store configuration")
        sys.exit(1)


def print_usage():
    """Print usage instructions"""
    print("Usage: python scripts/smtp_setup_localstack.py [OPTIONS]")
    print()
    print("Options:")
    print("  --host HOST      SMTP server hostname (default: mailpit)")
    print("  --port PORT      SMTP server port (default: 1025)")
    print("  --from EMAIL     From email address (default: noreply@agentfoundry.local)")
    print("  --username USER  SMTP username (optional)")
    print("  --password PASS  SMTP password (optional)")
    print("  --tls            Enable TLS (default: false)")
    print()
    print("Examples:")
    print("  # Use Mailpit defaults (local dev)")
    print("  python scripts/smtp_setup_localstack.py")
    print()
    print("  # Use external SMTP (production)")
    print("  python scripts/smtp_setup_localstack.py --host smtp.sendgrid.net --port 587 --tls")
    print()
    print("Notes:")
    print("  - For local development, Mailpit captures all emails at http://localhost:8025")
    print("  - Start Mailpit with: docker-compose up -d mailpit")
    print("  - Backend uses SVC_MAILPIT_HOST for service discovery")


if __name__ == "__main__":
    # Parse arguments
    host = "mailpit"
    port = 1025
    from_email = "noreply@agentfoundry.local"
    username = None
    password = None
    use_tls = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--help" or arg == "-h":
            print_usage()
            sys.exit(0)
        elif arg == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif arg == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        elif arg == "--from" and i + 1 < len(args):
            from_email = args[i + 1]
            i += 2
        elif arg == "--username" and i + 1 < len(args):
            username = args[i + 1]
            i += 2
        elif arg == "--password" and i + 1 < len(args):
            password = args[i + 1]
            i += 2
        elif arg == "--tls":
            use_tls = True
            i += 1
        else:
            print(f"Unknown argument: {arg}")
            print_usage()
            sys.exit(1)

    asyncio.run(store_smtp_config(host, port, from_email, username, password, use_tls))
