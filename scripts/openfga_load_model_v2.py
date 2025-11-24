"""
Load Enhanced OpenFGA Authorization Model
------------------------------------------
Loads the v2 authorization model directly via HTTP API.

Usage:
    python scripts/openfga_load_model_v2.py
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_fga_to_json(fga_content: str) -> dict:
    """
    Parse FGA DSL to JSON format for API.

    This is a simplified parser - in production you'd use the official FGA CLI.
    For now, we'll create the JSON manually based on the model structure.
    """

    # Complete JSON representation of the v2 model
    return {
        "schema_version": "1.1",
        "type_definitions": [
            {"type": "user"},
            {
                "type": "team",
                "relations": {
                    "organization": {"this": {}},
                    "lead": {"this": {}},
                    "member": {"union": {"child": [{"this": {}}, {"computedUserset": {"relation": "lead"}}]}},
                },
                "metadata": {
                    "relations": {
                        "organization": {"directly_related_user_types": [{"type": "organization"}]},
                        "lead": {"directly_related_user_types": [{"type": "user"}]},
                        "member": {"directly_related_user_types": [{"type": "user"}, {"type": "user", "wildcard": {}}]},
                    }
                },
            },
            {
                "type": "platform",
                "relations": {"global_admin": {"this": {}}},
                "metadata": {"relations": {"global_admin": {"directly_related_user_types": [{"type": "user"}]}}},
            },
            {
                "type": "tenant",
                "relations": {
                    "admin": {"this": {}},
                    "member": {"union": {"child": [{"this": {}}, {"computedUserset": {"relation": "admin"}}]}},
                    "billing_admin": {"union": {"child": [{"this": {}}, {"computedUserset": {"relation": "admin"}}]}},
                },
                "metadata": {
                    "relations": {
                        "admin": {"directly_related_user_types": [{"type": "user"}]},
                        "member": {"directly_related_user_types": [{"type": "user"}]},
                        "billing_admin": {"directly_related_user_types": [{"type": "user"}]},
                    }
                },
            },
            {
                "type": "organization",
                "relations": {
                    "tenant": {"this": {}},
                    "admin": {
                        "union": {
                            "child": [
                                {"this": {}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "tenant"},
                                        "computedUserset": {"object": "", "relation": "admin"},
                                    }
                                },
                            ]
                        }
                    },
                    "member": {"union": {"child": [{"this": {}}, {"computedUserset": {"relation": "admin"}}]}},
                    "can_read": {"union": {"child": [{"computedUserset": {"relation": "member"}}]}},
                    "can_write": {"union": {"child": [{"computedUserset": {"relation": "admin"}}]}},
                    "can_delete": {
                        "union": {
                            "child": [
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "tenant"},
                                        "computedUserset": {"object": "", "relation": "admin"},
                                    }
                                }
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "tenant": {"directly_related_user_types": [{"type": "tenant"}]},
                        "admin": {"directly_related_user_types": [{"type": "user"}]},
                        "member": {"directly_related_user_types": [{"type": "user"}]},
                    }
                },
            },
            {
                "type": "project",
                "relations": {
                    "organization": {"this": {}},
                    "admin": {"this": {}},
                    "team_visibility": {"this": {}},
                    "viewer": {
                        "union": {
                            "child": [
                                {"this": {}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "team_visibility"},
                                        "computedUserset": {"object": "", "relation": "member"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "can_read"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_write": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "can_write"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_delete": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "can_delete"},
                                    }
                                },
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "organization": {"directly_related_user_types": [{"type": "organization"}]},
                        "admin": {"directly_related_user_types": [{"type": "user"}]},
                        "team_visibility": {"directly_related_user_types": [{"type": "team"}]},
                        "viewer": {"directly_related_user_types": [{"type": "user"}]},
                    }
                },
            },
            {
                "type": "domain",
                "relations": {
                    "project": {"this": {}},
                    "parent": {"this": {}},
                    "admin": {"this": {}},
                    "compliance_officer": {"this": {}},
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "admin"}},
                                {"computedUserset": {"relation": "compliance_officer"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "project"},
                                        "computedUserset": {"object": "", "relation": "can_read"},
                                    }
                                },
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent"},
                                        "computedUserset": {"object": "", "relation": "can_read"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_write": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "project"},
                                        "computedUserset": {"object": "", "relation": "can_write"},
                                    }
                                },
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent"},
                                        "computedUserset": {"object": "", "relation": "can_write"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_delete": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "project"},
                                        "computedUserset": {"object": "", "relation": "can_delete"},
                                    }
                                },
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "parent"},
                                        "computedUserset": {"object": "", "relation": "can_delete"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_manage_compliance": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "compliance_officer"}},
                                {"computedUserset": {"relation": "admin"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "project"},
                                        "computedUserset": {"object": "", "relation": "can_write"},
                                    }
                                },
                            ]
                        }
                    },
                },
                "metadata": {
                    "relations": {
                        "project": {"directly_related_user_types": [{"type": "project"}]},
                        "parent": {"directly_related_user_types": [{"type": "domain"}]},
                        "admin": {"directly_related_user_types": [{"type": "user"}]},
                        "compliance_officer": {"directly_related_user_types": [{"type": "user"}]},
                    }
                },
            },
            {
                "type": "agent",
                "relations": {
                    "domain": {"this": {}},
                    "owner": {"this": {}},
                    "is_system": {"this": {}},
                    "can_read": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "domain"},
                                        "computedUserset": {"object": "", "relation": "can_read"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_write": {
                        "difference": {
                            "base": {
                                "union": {
                                    "child": [
                                        {"computedUserset": {"relation": "owner"}},
                                        {
                                            "tupleToUserset": {
                                                "tupleset": {"relation": "domain"},
                                                "computedUserset": {"object": "", "relation": "can_write"},
                                            }
                                        },
                                    ]
                                }
                            },
                            "subtract": {"computedUserset": {"relation": "is_system"}},
                        }
                    },
                    "can_delete": {
                        "difference": {
                            "base": {
                                "union": {
                                    "child": [
                                        {"computedUserset": {"relation": "owner"}},
                                        {
                                            "tupleToUserset": {
                                                "tupleset": {"relation": "domain"},
                                                "computedUserset": {"object": "", "relation": "can_delete"},
                                            }
                                        },
                                    ]
                                }
                            },
                            "subtract": {"computedUserset": {"relation": "is_system"}},
                        }
                    },
                    "can_deploy": {"computedUserset": {"relation": "can_write"}},
                    "can_execute": {"computedUserset": {"relation": "can_read"}},
                },
                "metadata": {
                    "relations": {
                        "domain": {"directly_related_user_types": [{"type": "domain"}]},
                        "owner": {"directly_related_user_types": [{"type": "user"}]},
                        "is_system": {"directly_related_user_types": [{"type": "platform"}]},
                    }
                },
            },
            {
                "type": "secret",
                "relations": {
                    "organization": {"this": {}},
                    "domain": {"this": {}},
                    "owner": {"this": {}},
                    "viewer": {"this": {}},
                    "can_read_status": {
                        "union": {
                            "child": [
                                {"computedUserset": {"relation": "viewer"}},
                                {"computedUserset": {"relation": "owner"}},
                                {
                                    "tupleToUserset": {
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "can_read"},
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
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "admin"},
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
                                        "tupleset": {"relation": "organization"},
                                        "computedUserset": {"object": "", "relation": "admin"},
                                    }
                                },
                            ]
                        }
                    },
                    "can_rotate": {"computedUserset": {"relation": "can_update"}},
                },
                "metadata": {
                    "relations": {
                        "organization": {"directly_related_user_types": [{"type": "organization"}]},
                        "domain": {"directly_related_user_types": [{"type": "domain"}]},
                        "owner": {"directly_related_user_types": [{"type": "user"}]},
                        "viewer": {"directly_related_user_types": [{"type": "user"}]},
                    }
                },
            },
        ],
    }


async def load_model():
    """Load authorization model via HTTP API"""

    print("🚀 Loading Enhanced OpenFGA Authorization Model\n")

    store_id = "01KATFSA1G5FRN6682HGAJX6XR"

    # Read and parse the model
    print("Step 1: Parsing authorization model...")
    model_json = parse_fga_to_json("")
    print("✓ Model parsed\n")

    # Load via HTTP API
    print("Step 2: Loading model into OpenFGA...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(f"http://localhost:9080/stores/{store_id}/authorization-models", json=model_json)

        if not response.is_success:
            print(f"❌ Failed to load model: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

        data = response.json()
        model_id = data["authorization_model_id"]

        print(f"✓ Model loaded: {model_id}\n")

    # Store in LocalStack
    print("Step 3: Storing configuration in LocalStack...")

    from backend.config.secrets import secrets_manager

    config = {
        "store_id": store_id,
        "model_id": model_id,
        "version": "v2",
        "features": [
            "5-level hierarchy",
            "team collaboration",
            "system agent protection",
            "8 asset types",
            "subdomain nesting",
            "compliance roles",
        ],
    }

    success = await secrets_manager.upsert_secret(
        organization_id="platform",
        secret_name="openfga_config",
        secret_value=json.dumps(config),
        description="OpenFGA v2 configuration with enhanced model",
    )

    if not success:
        print("❌ Failed to store in LocalStack")
        sys.exit(1)

    print("✓ Configuration stored in LocalStack\n")

    # Summary
    print("=" * 60)
    print("✅ OpenFGA Enhanced Model Loaded Successfully!")
    print("=" * 60)
    print()
    print(f"Store ID: {store_id}")
    print(f"Model ID: {model_id}")
    print()
    print("Configuration is in LocalStack (NOT .env!):")
    print("  platform/shared/openfga_config")
    print()
    print("Next steps:")
    print("  1. docker-compose restart foundry-backend")
    print("  2. python scripts/openfga_setup_initial_data.py")
    print("  3. python openfga/test_authorization_checks.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(load_model())
