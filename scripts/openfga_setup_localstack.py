"""
Store OpenFGA Configuration in LocalStack
------------------------------------------
Stores OpenFGA store_id and model_id in LocalStack instead of .env

Usage:
    python scripts/openfga_setup_localstack.py <store_id> <model_id>
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.secrets import secrets_manager


async def store_openfga_config(store_id: str, model_id: str):
    """Store OpenFGA configuration in LocalStack"""

    print("📦 Storing OpenFGA configuration in LocalStack...")
    print(f"   Store ID: {store_id}")
    print(f"   Model ID: {model_id}")
    print()

    # Package as JSON
    config = {
        "store_id": store_id,
        "model_id": model_id,
        "created_at": "2025-11-24",
        "description": "OpenFGA store and authorization model configuration",
    }

    # Store in LocalStack as platform-level secret
    success = await secrets_manager.upsert_secret(
        organization_id="platform",
        secret_name="openfga_config",
        secret_value=json.dumps(config),
        domain_id=None,
        description="OpenFGA store and authorization model IDs",
    )

    if success:
        print("✅ OpenFGA configuration stored in LocalStack")
        print()
        print("Configuration is now in LocalStack, not .env!")
        print()
        print("Backend will automatically retrieve it at startup.")
        print()
        print("To verify:")
        print("  docker-compose restart foundry-backend")
        print("  docker-compose logs foundry-backend | grep OpenFGA")
    else:
        print("❌ Failed to store configuration")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/openfga_setup_localstack.py <store_id> <model_id>")
        print()
        print("Example:")
        print("  python scripts/openfga_setup_localstack.py 01KATFSA1G5FRN6682HGAJX6XR 01KXXXX...")
        sys.exit(1)

    store_id = sys.argv[1]
    model_id = sys.argv[2]

    asyncio.run(store_openfga_config(store_id, model_id))
