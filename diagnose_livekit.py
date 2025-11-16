"""
Diagnose LiveKit SDK structure
"""
import sys

try:
    import livekit
    print(f"✓ livekit version: {livekit.__version__}")
    print(f"✓ livekit location: {livekit.__file__}")
    print("\nAvailable in livekit module:")
    print([x for x in dir(livekit) if not x.startswith('_')])
    print()
except Exception as e:
    print(f"✗ Error importing livekit: {e}")
    sys.exit(1)

try:
    import livekit.api
    print("✓ livekit.api imported")
    print("\nAvailable in livekit.api:")
    print([x for x in dir(livekit.api) if not x.startswith('_')])
    print()
except Exception as e:
    print(f"✗ Error importing livekit.api: {e}")

try:
    # Try different import paths
    from livekit.api import RoomServiceClient
    print("✓ Found RoomServiceClient")
except ImportError:
    print("✗ No RoomServiceClient")

try:
    from livekit.api import RoomService
    print("✓ Found RoomService")
except ImportError:
    print("✗ No RoomService")

try:
    from livekit import rtc
    print("✓ livekit.rtc available")
    print("  Contents:", [x for x in dir(rtc) if not x.startswith('_')][:10])
except ImportError:
    print("✗ No livekit.rtc")

# Check for room service in different locations
print("\n--- Searching for room-related classes ---")
import livekit.api as lkapi
for name in dir(lkapi):
    if 'room' in name.lower() or 'Room' in name:
        print(f"  Found: {name}")

# Try to instantiate RoomServiceClient
print("\n--- Testing RoomServiceClient ---")
try:
    from livekit.api import RoomServiceClient
    client = RoomServiceClient(
        "ws://localhost:7880",
        "devkey",
        "secret"
    )
    print("✓ RoomServiceClient created successfully")
    print("  Available methods:")
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    for method in methods:
        print(f"    - {method}")
except Exception as e:
    print(f"✗ Error creating RoomServiceClient: {e}")
    import traceback
    traceback.print_exc()
