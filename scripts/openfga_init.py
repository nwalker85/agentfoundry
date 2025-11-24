"""
OpenFGA Initialization Script
------------------------------
Sets up OpenFGA store and authorization model for Agent Foundry.

Run this once after starting OpenFGA for the first time.

Usage:
    python scripts/openfga_init.py
"""

import asyncio
import sys
from pathlib import Path

import httpx

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config.services import SERVICES


async def create_store(client: httpx.AsyncClient) -> str:
    """Create a new OpenFGA store."""
    base_url = SERVICES.get_service_url("OPENFGA")

    response = await client.post(f"{base_url}/stores", json={"name": "agent-foundry"})
    response.raise_for_status()

    data = response.json()
    store_id = data["id"]
    print(f"✓ Store created: {store_id}")

    return store_id


async def load_authorization_model(client: httpx.AsyncClient, store_id: str) -> str:
    """Load the authorization model from .fga file."""
    base_url = SERVICES.get_service_url("OPENFGA")

    # Read the authorization model file
    model_path = Path(__file__).parent.parent / "openfga" / "authorization_model.fga"

    if not model_path.exists():
        raise FileNotFoundError(f"Authorization model not found: {model_path}")

    model_content = model_path.read_text()

    # Convert FGA DSL to JSON (simplified - in production use openfga CLI)
    # For now, we'll use the HTTP API format
    print("\n⚠️  Loading authorization model...")
    print("Note: In production, use `fga model write --file authorization_model.fga`")

    # Parse the model (simplified - would use proper FGA parser in production)
    model_json = _parse_fga_model(model_content)

    response = await client.post(f"{base_url}/stores/{store_id}/authorization-models", json=model_json)
    response.raise_for_status()

    data = response.json()
    model_id = data["authorization_model_id"]
    print(f"✓ Authorization model loaded: {model_id}")

    return model_id


def _parse_fga_model(fga_content: str) -> dict:
    """
    Parse FGA DSL to JSON format.

    Note: This is a simplified parser. In production, use the official
    FGA CLI or SDK to properly parse the .fga file.

    For now, returns a basic type definitions structure.
    """
    # Simplified model for initial setup
    # In production, use: `fga model transform --file authorization_model.fga`

    return {
        "schema_version": "1.1",
        "type_definitions": [
            {"type": "user"},
            {
                "type": "organization",
                "relations": {
                    "owner": {"this": {}},
                    "admin": {"this": {}},
                    "member": {"this": {}},
                    "viewer": {"this": {}},
                    "can_create_domain": {
                        "union": {
                            "child": [
                                {"this": {}},
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "admin"}},
                            ]
                        }
                    },
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "member"}},
                                {"computedUserset": {"relation": "admin"}},
                                {"computedUserset": {"relation": "owner"}},
                            ]
                        }
                    },
                },
            },
            {
                "type": "domain",
                "relations": {
                    "parent_org": {"this": {}},
                    "owner": {"this": {}},
                    "editor": {"this": {}},
                    "viewer": {"this": {}},
                    "can_create_agent": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {"computedUserset": {"relation": "editor"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_org"},
                                        "computedUserset": {"relation": "admin"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "editor"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_org"},
                                        "computedUserset": {"relation": "member"},
                                    }
                                },
                            ]
                        }
                    },
                },
            },
            {
                "type": "agent",
                "relations": {
                    "parent_domain": {"this": {}},
                    "owner": {"this": {}},
                    "executor": {"this": {}},
                    "editor": {"this": {}},
                    "viewer": {"this": {}},
                    "can_execute": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "executor"}},
                                {"computedUserset": {"relation": "editor"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_domain"},
                                        "computedUserset": {"relation": "editor"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "executor"}},
                                {"computedUserset": {"relation": "editor"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_domain"},
                                        "computedUserset": {"relation": "viewer"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_update": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "editor"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_domain"},
                                        "computedUserset": {"relation": "editor"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_delete": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_domain"},
                                        "computedUserset": {"relation": "owner"},
                                    }
                                },
                            ]
                        }
                    },
                },
            },
            {
                "type": "secret",
                "relations": {
                    "parent_org": {"this": {}},
                    "owner": {"this": {}},
                    "viewer": {"this": {}},
                    "can_read_status": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_org"},
                                        "computedUserset": {"relation": "member"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_update": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent_org"},
                                        "computedUserset": {"relation": "admin"},
                                    }
                                },
                            ]
                        }
                    },
                },
            },
        ],
    }


async def seed_initial_relationships(client: httpx.AsyncClient, store_id: str, auth_model_id: str):
    """Seed initial relationships for development/testing."""
    base_url = SERVICES.get_service_url("OPENFGA")

    # Create test organization with users
    tuples = [
        # Test org with admin
        {"user": "user:test-admin", "relation": "owner", "object": "organization:test-org"},
        # Test member
        {"user": "user:test-user", "relation": "member", "object": "organization:test-org"},
        # Test domain
        {"user": "organization:test-org", "relation": "parent_org", "object": "domain:test-domain"},
        {"user": "user:test-admin", "relation": "owner", "object": "domain:test-domain"},
        # Test agent
        {"user": "domain:test-domain", "relation": "parent_domain", "object": "agent:test-agent"},
        {"user": "user:test-admin", "relation": "owner", "object": "agent:test-agent"},
        {"user": "user:test-user", "relation": "executor", "object": "agent:test-agent"},
    ]

    response = await client.post(
        f"{base_url}/stores/{store_id}/write",
        json={"authorization_model_id": auth_model_id, "writes": {"tuple_keys": tuples}},
    )
    response.raise_for_status()

    print(f"✓ Seeded {len(tuples)} initial relationships")


async def verify_setup(client: httpx.AsyncClient, store_id: str, auth_model_id: str):
    """Verify the setup by running test authorization checks."""
    base_url = SERVICES.get_service_url("OPENFGA")

    test_checks = [
        {
            "name": "Test admin can create domain",
            "user": "user:test-admin",
            "relation": "can_create_domain",
            "object": "organization:test-org",
            "expected": True,
        },
        {
            "name": "Test user can execute agent",
            "user": "user:test-user",
            "relation": "can_execute",
            "object": "agent:test-agent",
            "expected": True,
        },
        {
            "name": "Test user cannot delete agent",
            "user": "user:test-user",
            "relation": "can_delete",
            "object": "agent:test-agent",
            "expected": False,
        },
    ]

    print("\n🔍 Running verification checks...\n")

    all_passed = True
    for check in test_checks:
        response = await client.post(
            f"{base_url}/stores/{store_id}/check",
            json={
                "authorization_model_id": auth_model_id,
                "tuple_key": {"user": check["user"], "relation": check["relation"], "object": check["object"]},
            },
        )
        response.raise_for_status()

        data = response.json()
        allowed = data.get("allowed", False)
        expected = check["expected"]
        passed = allowed == expected

        status_icon = "✓" if passed else "✗"
        print(f"{status_icon} {check['name']}: {allowed} (expected: {expected})")

        if not passed:
            all_passed = False

    if all_passed:
        print("\n✅ All verification checks passed!")
    else:
        print("\n❌ Some verification checks failed")
        sys.exit(1)


async def main():
    """Main initialization flow."""
    print("🚀 OpenFGA Initialization for Agent Foundry\n")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: Create store
            print("Step 1: Creating OpenFGA store...")
            store_id = await create_store(client)

            # Step 2: Load authorization model
            print("\nStep 2: Loading authorization model...")
            auth_model_id = await load_authorization_model(client, store_id)

            # Step 3: Seed initial relationships
            print("\nStep 3: Seeding test relationships...")
            await seed_initial_relationships(client, store_id, auth_model_id)

            # Step 4: Verify setup
            await verify_setup(client, store_id, auth_model_id)

            # Output configuration
            print("\n" + "=" * 60)
            print("✅ OpenFGA setup complete!")
            print("=" * 60)
            print("\nAdd these to your .env file:\n")
            print(f"OPENFGA_STORE_ID={store_id}")
            print(f"OPENFGA_AUTH_MODEL_ID={auth_model_id}")
            print("\nThen restart your backend service:")
            print("  docker-compose restart foundry-backend")
            print("=" * 60)

    except httpx.HTTPError as e:
        print(f"\n❌ Failed to initialize OpenFGA: {e}")
        print("\nMake sure OpenFGA is running:")
        print("  docker-compose up -d openfga")
        print("  curl http://localhost:8081/healthz")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
