"""
LiveKit Integration Service
Handles voice session creation, token generation, and WebRTC room management.
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from livekit.api import (
    AccessToken,
    CreateRoomRequest,
    DeleteRoomRequest,
    ListParticipantsRequest,
    ListRoomsRequest,
    LiveKitAPI,
    VideoGrants,
)

logger = logging.getLogger(__name__)


@dataclass
class VoiceSession:
    """Voice session metadata"""

    session_id: str
    room_name: str
    user_id: str
    agent_id: str
    created_at: datetime
    expires_at: datetime
    token: str | None = None


class LiveKitService:
    """
    Manages LiveKit voice sessions and token generation.
    Integrates with LangGraph agents for stateful voice interactions.
    """

    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")

        # Use service discovery
        from backend.config.services import SERVICES

        self.url = SERVICES.get_service_url("LIVEKIT")

        if not self.api_key or not self.api_secret:
            raise ValueError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")

        # Initialize async API client lazily
        self._api: LiveKitAPI | None = None

    async def _get_api(self) -> LiveKitAPI:
        """Lazy-initialize LiveKitAPI in async context."""
        if self._api is None:
            self._api = LiveKitAPI(url=self.url, api_key=self.api_key, api_secret=self.api_secret)
            logger.info(f"Initialized LiveKitAPI for {self.url}")
        return self._api

    async def create_voice_session(
        self, user_id: str, agent_id: str, session_duration_hours: int = 4, session_id: str | None = None
    ) -> VoiceSession:
        """
        Create a new voice session with LiveKit room and access token.

        Args:
            user_id: User identifier (for session persistence)
            agent_id: Agent identifier (which agent to talk to)
            session_duration_hours: How long the session token is valid
            session_id: Optional frontend session ID for activity streaming (if None, generates new)

        Returns:
            VoiceSession with room details and access token
        """
        # Use provided session_id or generate new one
        if not session_id:
            session_id = f"sess_{secrets.token_urlsafe(16)}"
        room_name = f"foundry_{user_id}_{agent_id}_{session_id}"

        # Create LiveKit room using async API with protobuf request
        try:
            import json

            api = await self._get_api()

            # Store session_id and agent_id in room metadata for IO Agent
            room_metadata = json.dumps({"session_id": session_id, "agent_id": agent_id, "user_id": user_id})

            await api.room.create_room(
                CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,  # 5 min empty room timeout
                    max_participants=10,  # User + agent + observers
                    metadata=room_metadata,  # Store session_id for activity streaming
                )
            )
            logger.info(f"Created LiveKit room: {room_name} with session_id: {session_id}")
        except Exception as e:
            # Room might already exist, log but continue
            logger.warning(f"Room creation warning for {room_name}: {e}")

        # Generate access token for user
        token = AccessToken(self.api_key, self.api_secret)
        token.with_identity(user_id)
        token.with_name(f"User {user_id}")
        token.with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )

        # Token expiry
        expires_at = datetime.utcnow() + timedelta(hours=session_duration_hours)

        session = VoiceSession(
            session_id=session_id,
            room_name=room_name,
            user_id=user_id,
            agent_id=agent_id,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            token=token.to_jwt(),
        )

        logger.info(f"Created voice session {session_id} for user {user_id} with agent {agent_id}")
        return session

    async def get_room_info(self, room_name: str) -> dict[str, Any]:
        """Get current room information including participants"""
        try:
            api = await self._get_api()

            # Get room details using protobuf request
            response = await api.room.list_rooms(ListRoomsRequest(names=[room_name]))
            if not response.rooms:
                return {"error": f"Room {room_name} not found"}

            room = response.rooms[0]

            # Get participants using protobuf request
            participants_response = await api.room.list_participants(ListParticipantsRequest(room=room_name))

            return {
                "room_name": room.name,
                "sid": room.sid,
                "num_participants": room.num_participants,
                "participants": [
                    {
                        "identity": p.identity,
                        "name": p.name,
                        "sid": p.sid,
                    }
                    for p in participants_response.participants
                ],
                "created_at": room.creation_time,
            }
        except Exception as e:
            logger.error(f"Error getting room info for {room_name}: {e}", exc_info=True)
            return {"error": str(e)}

    async def end_session(self, room_name: str) -> bool:
        """End a voice session by closing the room"""
        try:
            api = await self._get_api()
            # Delete room using protobuf request
            await api.room.delete_room(DeleteRoomRequest(room=room_name))
            logger.info(f"Deleted room {room_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting room {room_name}: {e}", exc_info=True)
            return False

    async def close(self):
        """Close the API client connection."""
        if self._api is not None:
            await self._api.aclose()
            self._api = None
            logger.info("Closed LiveKitAPI connection")


# Singleton instance
_livekit_service: LiveKitService | None = None


def get_livekit_service() -> LiveKitService:
    """Get or create LiveKit service singleton"""
    global _livekit_service
    if _livekit_service is None:
        _livekit_service = LiveKitService()
    return _livekit_service
