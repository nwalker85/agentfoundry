"""
IO Agent - Handles all user input/output (voice + chat)

Responsibilities:
- Detect channel (voice, chat, API)
- Normalize input to standard format
- Pass to supervisor agent
- Format response for specific channel
- Deliver response to user

NO business logic - pure I/O adapter.
"""

import asyncio
import logging
from typing import Optional, Literal

from .supervisor_agent import SupervisorAgent
from .state import IOState

logger = logging.getLogger(__name__)


class IOAgent:
    """
    Pure I/O handler. Mediates between user interface and supervisor agent.
    Handles channel detection and format normalization.
    """
    
    def __init__(self, supervisor: Optional[SupervisorAgent] = None):
        """
        Initialize IO Agent.
        
        Args:
            supervisor: The supervisor agent to route messages to.
                       If None, creates a new supervisor instance.
        """
        self.supervisor = supervisor or SupervisorAgent()
        logger.info("IOAgent initialized")
    
    def detect_channel(
        self,
        channel_hint: Optional[str] = None,
        **metadata
    ) -> Literal["chat", "voice", "api"]:
        """
        Identify input channel (chat, voice, API).
        
        Args:
            channel_hint: Explicit channel identifier if provided
            **metadata: Additional metadata that may indicate channel
        
        Returns:
            Channel type
        """
        # If explicitly specified, use that
        if channel_hint in ["chat", "voice", "api"]:
            logger.debug(f"Channel detected (explicit): {channel_hint}")
            return channel_hint
        
        # Check for LiveKit room (indicates voice)
        if "room_name" in metadata:
            logger.debug("Channel detected: voice (LiveKit room present)")
            return "voice"
        
        # Check for WebSocket (could be chat)
        if "websocket_id" in metadata:
            logger.debug("Channel detected: chat (WebSocket)")
            return "chat"
        
        # Default to chat
        logger.debug("Channel detected: chat (default)")
        return "chat"
    
    def normalize_input(
        self,
        user_input: str,
        channel: str,
        **metadata
    ) -> str:
        """
        Convert channel-specific input to standard format.
        
        For now, this is a pass-through since we're dealing with text.
        Future: Handle voice transcription artifacts, API payload extraction, etc.
        
        Args:
            user_input: Raw user input
            channel: Detected channel
            **metadata: Channel-specific metadata
        
        Returns:
            Normalized input text
        """
        logger.debug(f"Normalizing input for channel: {channel}")
        
        # TODO: Channel-specific normalization
        # - Voice: Clean transcription artifacts
        # - API: Extract message from JSON payload
        # - Chat: Already clean
        
        normalized = user_input.strip()
        
        logger.debug(f"Input normalized ({len(normalized)} chars)")
        return normalized
    
    def format_output(
        self,
        response: str,
        channel: str,
        **metadata
    ) -> str:
        """
        Format response for specific channel.
        
        Args:
            response: Raw response from supervisor
            channel: Target channel
            **metadata: Channel-specific formatting hints
        
        Returns:
            Formatted response
        """
        logger.debug(f"Formatting output for channel: {channel}")
        
        # TODO: Channel-specific formatting
        # - Voice: Generate SSML markup for natural speech
        # - API: Wrap in JSON structure
        # - Chat: Keep as plain text
        
        if channel == "voice":
            # Future: Add SSML tags for better voice output
            # For now, keep plain text (TTS handles it)
            formatted = response
        
        elif channel == "api":
            # Future: Return structured JSON
            formatted = response
        
        else:  # chat
            formatted = response
        
        logger.debug(f"Output formatted for {channel} ({len(formatted)} chars)")
        return formatted
    
    async def process_message(
        self,
        user_message: str,
        session_id: str,
        user_id: str = "default_user",
        channel: Optional[str] = None,
        **metadata
    ) -> str:
        """
        Process a user message (voice or text) and return response.
        
        Args:
            user_message: The user's input text (transcribed if voice)
            session_id: Unique session identifier
            user_id: User identifier
            channel: Optional explicit channel type
            **metadata: Additional channel/context metadata
        
        Returns:
            Assistant response text (will be spoken if voice mode)
        """
        logger.info(f"[{session_id}] Processing message: {user_message[:100]}...")
        
        # Detect channel
        detected_channel = self.detect_channel(channel, **metadata)
        
        # Normalize input
        normalized_input = self.normalize_input(
            user_message,
            detected_channel,
            **metadata
        )
        
        # Create state for this interaction
        state = IOState(
            user_message=normalized_input,
            assistant_response="",
            session_id=session_id,
            user_id=user_id,
            channel=detected_channel
        )
        
        try:
            # Send to supervisor and get response
            response = await self.supervisor.process(state)
            
            # Format response for channel
            formatted_response = self.format_output(
                response,
                detected_channel,
                **metadata
            )
            
            logger.info(f"[{session_id}] Response generated ({len(formatted_response)} chars)")
            return formatted_response
            
        except Exception as e:
            logger.error(f"[{session_id}] Error processing message: {e}", exc_info=True)
            return "I'm having trouble processing that right now. Could you try again?"
    
    async def handle_chat_message(self, message: str, session_id: str) -> str:
        """
        Handle a text chat message.
        Convenience wrapper around process_message for chat UI.
        
        Args:
            message: User's chat message
            session_id: Session ID
        
        Returns:
            Response text
        """
        return await self.process_message(
            user_message=message,
            session_id=session_id,
            user_id=f"chat_user_{session_id}",
            channel="chat"
        )
    
    async def handle_voice_message(
        self,
        transcribed_text: str,
        session_id: str,
        room_name: str
    ) -> str:
        """
        Handle a voice message (already transcribed).
        Convenience wrapper around process_message for voice UI.
        
        Args:
            transcribed_text: User's speech (transcribed to text)
            session_id: Session ID
            room_name: LiveKit room name
        
        Returns:
            Response text (will be converted to speech by caller)
        """
        return await self.process_message(
            user_message=transcribed_text,
            session_id=session_id,
            user_id=f"voice_user_{room_name}",
            channel="voice",
            room_name=room_name
        )
