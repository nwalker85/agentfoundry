"""
Check what's inside the room_service module
"""

from livekit.api import room_service

print("=== Contents of room_service module ===")
items = [x for x in dir(room_service) if not x.startswith("_")]

classes = []
functions = []
others = []

for item in items:
    obj = getattr(room_service, item)
    if isinstance(obj, type):
        classes.append(item)
    elif callable(obj):
        functions.append(item)
    else:
        others.append(item)

if classes:
    print(f"\nClasses ({len(classes)}):")
    for cls in classes:
        print(f"  - {cls}")

if functions:
    print(f"\nFunctions ({len(functions)}):")
    for func in functions:
        print(f"  - {func}")

if others:
    print(f"\nOther ({len(others)}):")
    for other in others:
        print(f"  - {other}")

# Check for RoomService class specifically
print("\n=== Looking for RoomService class ===")
if hasattr(room_service, "RoomService"):
    print("✓ Found RoomService")
    RoomService = room_service.RoomService
    print(f"  Type: {type(RoomService)}")

    # Show its methods
    methods = [m for m in dir(RoomService) if not m.startswith("_")]
    print(f"\n  Available methods/attributes ({len(methods)}):")
    for method in methods[:20]:
        print(f"    - {method}")
else:
    print("✗ No RoomService class found")

# Try the async LiveKitAPI approach
print("\n=== Testing async LiveKitAPI ===")
import asyncio


async def test_livekit_api():
    from livekit.api import LiveKitAPI

    api = LiveKitAPI("ws://localhost:7880", "devkey", "secret")
    print("✓ LiveKitAPI created")

    # Check room attribute
    if hasattr(api, "room"):
        print("✓ Has 'room' attribute")
        print(f"  Type: {type(api.room)}")

        methods = [m for m in dir(api.room) if not m.startswith("_")]
        print(f"\n  Room methods ({len(methods)}):")
        for method in methods[:15]:
            print(f"    - {method}")

    await api.aclose()
    print("✓ API closed")


try:
    asyncio.run(test_livekit_api())
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
