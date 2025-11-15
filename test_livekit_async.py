"""
Test LiveKit service with proper async pattern
"""
import asyncio
import logging
import sys
import os
from pathlib import Path

# Load environment variables from .env.local
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env.local'
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.livekit_service import LiveKitService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_voice_session():
    """Test creating a voice session."""
    logger.info("=== Testing LiveKit Voice Session Creation ===")
    
    service = LiveKitService()
    
    try:
        # Test 1: Create session
        logger.info("\n[Test 1] Creating voice session...")
        session = await service.create_voice_session(
            user_id="test-user",
            agent_id="pm-agent",
            session_duration_hours=1
        )
        
        logger.info("✅ Voice session created successfully")
        logger.info(f"  Session ID: {session.session_id}")
        logger.info(f"  Room: {session.room_name}")
        logger.info(f"  Token: {session.token[:50]}...")
        logger.info(f"  Expires: {session.expires_at}")
        
        # Test 2: Get room info
        logger.info("\n[Test 2] Getting room info...")
        room_info = await service.get_room_info(session.room_name)
        
        if "error" in room_info:
            logger.warning(f"⚠️  Room info returned error: {room_info['error']}")
        else:
            logger.info("✅ Room info retrieved")
            logger.info(f"  Participants: {room_info.get('num_participants', 0)}")
        
        # Test 3: Cleanup
        logger.info("\n[Test 3] Ending session...")
        deleted = await service.end_session(session.room_name)
        
        if deleted:
            logger.info("✅ Room deleted successfully")
        else:
            logger.warning("⚠️  Room deletion failed (may not exist)")
        
        # Cleanup API connection
        await service.close()
        logger.info("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {str(e)}", exc_info=True)
        await service.close()
        return False


async def test_token_generation():
    """Test just token generation (no server required)."""
    logger.info("\n=== Testing Token Generation (Standalone) ===")
    
    from livekit import api
    
    try:
        # Get credentials from environment
        api_key = os.getenv("LIVEKIT_API_KEY", "devkey")
        api_secret = os.getenv("LIVEKIT_API_SECRET", "secret")
        
        token = api.AccessToken(api_key, api_secret)
        token.with_identity("test-user")
        token.with_name("Test User")
        token.with_grants(api.VideoGrants(
            room_join=True,
            room="test-room",
            can_publish=True,
            can_subscribe=True,
        ))
        
        jwt = token.to_jwt()
        logger.info("✅ Token generated successfully")
        logger.info(f"  JWT: {jwt[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ Token generation failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    logger.info("Starting LiveKit Service Tests\n")
    
    # Check environment variables
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    
    logger.info(f"Environment check:")
    logger.info(f"  LIVEKIT_API_KEY: {'✅ set' if api_key else '❌ missing'}")
    logger.info(f"  LIVEKIT_API_SECRET: {'✅ set' if api_secret else '❌ missing'}")
    logger.info(f"  LIVEKIT_URL: {livekit_url or '❌ missing'}\n")
    
    # Test 1: Token generation (no server needed)
    token_ok = await test_token_generation()
    
    # Test 2: Full session creation (requires LiveKit server)
    session_ok = await test_voice_session()
    
    if token_ok and session_ok:
        logger.info("\n🎉 All tests PASSED")
        return 0
    elif token_ok:
        logger.warning("\n⚠️  Token generation works but session creation failed")
        logger.warning("    Make sure LiveKit server is running:")
        logger.warning("    brew services start livekit")
        logger.warning("    OR: docker run -p 7880:7880 livekit/livekit-server --dev")
        return 1
    else:
        logger.error("\n❌ Tests FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
