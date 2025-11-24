"""
Simple LiveKit SDK diagnostic - no assumptions about structure
"""

import sys

print("=== Python Environment ===")
print(f"Python: {sys.version}")
print(f"Path: {sys.executable}")
print()

# Step 1: Can we import livekit at all?
print("=== Step 1: Import livekit ===")
try:
    import livekit

    print("✓ livekit imported successfully")
    print(f"  Location: {livekit.__file__}")

    # Don't assume __version__ exists
    if hasattr(livekit, "__version__"):
        print(f"  Version: {livekit.__version__}")
    else:
        print("  Version: (no __version__ attribute)")

    print("\n  Top-level attributes:")
    attrs = [x for x in dir(livekit) if not x.startswith("_")]
    for attr in attrs[:20]:  # First 20 only
        print(f"    - {attr}")
    if len(attrs) > 20:
        print(f"    ... and {len(attrs) - 20} more")

except ImportError as e:
    print(f"✗ Cannot import livekit: {e}")
    print("\nTry installing it:")
    print("  pip install livekit livekit-api")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Step 2: Can we import livekit.api?
print("\n=== Step 2: Import livekit.api ===")
try:
    import livekit.api as lkapi

    print("✓ livekit.api imported")

    print("\n  Available in livekit.api:")
    api_items = [x for x in dir(lkapi) if not x.startswith("_")]

    # Group by type
    classes = []
    functions = []
    others = []

    for item in api_items:
        obj = getattr(lkapi, item)
        if isinstance(obj, type):
            classes.append(item)
        elif callable(obj):
            functions.append(item)
        else:
            others.append(item)

    if classes:
        print(f"\n  Classes ({len(classes)}):")
        for cls in classes:
            print(f"    - {cls}")

    if functions:
        print(f"\n  Functions ({len(functions)}):")
        for func in functions[:10]:
            print(f"    - {func}")
        if len(functions) > 10:
            print(f"    ... and {len(functions) - 10} more")

except ImportError as e:
    print(f"✗ Cannot import livekit.api: {e}")
    print("\nTry installing it:")
    print("  pip install livekit-api")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Step 3: Look for RoomService variants
print("\n=== Step 3: Search for RoomService ===")
service_classes = []
for name in dir(lkapi):
    if "room" in name.lower() and "service" in name.lower():
        service_classes.append(name)

if service_classes:
    print(f"✓ Found {len(service_classes)} room service class(es):")
    for cls in service_classes:
        print(f"  - {cls}")
else:
    print("✗ No RoomService classes found")
    print("\n  All room-related items:")
    room_items = [x for x in dir(lkapi) if "room" in x.lower()]
    for item in room_items:
        print(f"    - {item}")

# Step 4: Try to instantiate RoomServiceClient
print("\n=== Step 4: Test RoomServiceClient ===")
try:
    from livekit.api import RoomServiceClient

    print("✓ RoomServiceClient class found")

    # Try to create instance
    client = RoomServiceClient("ws://localhost:7880", "devkey", "secret")
    print("✓ RoomServiceClient instantiated")

    # Check methods
    methods = [m for m in dir(client) if not m.startswith("_") and callable(getattr(client, m))]
    print(f"\n  Available methods ({len(methods)}):")
    for method in methods:
        print(f"    - {method}")

except ImportError as e:
    print(f"✗ Cannot import RoomServiceClient: {e}")
    print("\n  Try these alternatives:")
    print("    from livekit.api import RoomService")
    print("    from livekit import RoomService")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()

# Step 5: Check for AccessToken and VideoGrants
print("\n=== Step 5: Check AccessToken and VideoGrants ===")
try:
    from livekit.api import AccessToken, VideoGrants

    print("✓ AccessToken found")
    print("✓ VideoGrants found")

    # Try to create a token
    token = AccessToken("key", "secret")
    token.with_identity("test_user")
    token.with_grants(VideoGrants(room_join=True, room="test_room"))
    jwt = token.to_jwt()
    print("✓ Token generation works")
    print(f"  Sample token: {jwt[:50]}...")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
print("DIAGNOSTIC COMPLETE")
print("=" * 50)
