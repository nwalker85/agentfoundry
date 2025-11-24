"""
Investigate room_service
"""

import livekit.api as lkapi

print("=== Checking room_service ===")
print(f"Type: {type(lkapi.room_service)}")
print(f"Value: {lkapi.room_service}")

if callable(lkapi.room_service):
    print("\n✓ room_service is callable (it's a function)")
    print("\nTrying to call room_service()...")
    try:
        service = lkapi.room_service()
        print(f"✓ Returns: {type(service)}")
        print(f"  Class name: {service.__class__.__name__}")

        # Check methods
        methods = [m for m in dir(service) if not m.startswith("_") and callable(getattr(service, m))]
        print(f"\n  Available methods ({len(methods)}):")
        for method in methods[:20]:
            print(f"    - {method}")
        if len(methods) > 20:
            print(f"    ... and {len(methods) - 20} more")
    except Exception as e:
        print(f"✗ Error calling room_service(): {e}")
        import traceback

        traceback.print_exc()
else:
    print("\n✗ room_service is not callable")
    print(f"  It's a: {type(lkapi.room_service)}")

# Also check if there's a RoomService class
print("\n=== Looking for RoomService class ===")
for name in dir(lkapi):
    if name.lower() == "roomservice":
        print(f"Found: {name}")
        obj = getattr(lkapi, name)
        print(f"  Type: {type(obj)}")
        if isinstance(obj, type):
            print("  It's a class!")

# Check LiveKitAPI
print("\n=== Checking LiveKitAPI ===")
try:
    from livekit.api import LiveKitAPI

    print("✓ LiveKitAPI found")
    print(f"  It's a: {type(LiveKitAPI)}")

    # Try to instantiate
    api = LiveKitAPI("ws://localhost:7880", "devkey", "secret")
    print("✓ LiveKitAPI instantiated")

    # Check if it has room service
    if hasattr(api, "room"):
        print("✓ API has 'room' attribute")
        print(f"  Type: {type(api.room)}")
        methods = [m for m in dir(api.room) if not m.startswith("_") and callable(getattr(api.room, m))]
        print(f"  Methods ({len(methods)}):")
        for method in methods[:15]:
            print(f"    - {method}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
