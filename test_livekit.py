"""
Quick test to verify LiveKit service works
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test env vars
os.environ["LIVEKIT_API_KEY"] = "devkey"
os.environ["LIVEKIT_API_SECRET"] = "secret"
os.environ["LIVEKIT_URL"] = "ws://localhost:7880"

try:
    from backend.livekit_service import LiveKitService
    
    print("✓ Imports successful")
    
    # Try to create service
    service = LiveKitService()
    print(f"✓ LiveKitService initialized")
    print(f"  - URL: {service.url}")
    print(f"  - API Key: {service.api_key[:10]}...")
    
    # Try to create a session
    print("\nCreating test session...")
    session = service.create_voice_session(
        user_id="test_user",
        agent_id="test_agent",
        session_duration_hours=1
    )
    
    print(f"✓ Session created:")
    print(f"  - Session ID: {session.session_id}")
    print(f"  - Room Name: {session.room_name}")
    print(f"  - Token: {session.token[:50]}...")
    print(f"  - Expires: {session.expires_at}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
