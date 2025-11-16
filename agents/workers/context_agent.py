"""
Context Agent - Session state management and user context enrichment

Responsibilities:
- Load current session state from Redis
- Load user profile and history (future: from PostgreSQL)
- Enrich requests with session + user context
- Persist updated session state

Platform agent (always available, not domain-specific).
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ContextAgent:
    """
    Platform agent for managing session state and user context.
    Enriches requests with conversation history and user profile data.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize Context Agent.
        
        Args:
            redis_client: Redis client for session state storage (optional, uses in-memory for now)
        """
        self.redis_client = redis_client
        self.llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        
        # In-memory session store (fallback if Redis not available)
        self._session_store: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ContextAgent initialized")
    
    async def process(
        self,
        session_id: str,
        user_id: str,
        current_input: str
    ) -> Dict[str, Any]:
        """
        Process context enrichment workflow.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            current_input: Current user message
        
        Returns:
            Enriched context dictionary with session and user data
        """
        logger.info(f"Processing context for session: {session_id}")
        
        # Load session state
        session_state = await self._load_session(session_id)
        
        # Load user context
        user_context = await self._load_user_context(user_id)
        
        # Enrich request
        enriched_context = await self._enrich_request(
            session_state=session_state,
            user_context=user_context,
            current_input=current_input
        )
        
        # Note: Session state is updated separately via update_session_state()
        # after supervisor processes the full request
        
        logger.info(f"Context enrichment complete for session: {session_id}")
        
        return enriched_context
    
    async def _load_session(self, session_id: str) -> Dict[str, Any]:
        """
        Load current session state from Redis (or in-memory store).
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session state dictionary
        """
        logger.debug(f"Loading session state: {session_id}")
        
        try:
            if self.redis_client:
                # TODO: Load from Redis when integrated
                # session_data = await self.redis_client.get(f"session:{session_id}")
                # if session_data:
                #     return json.loads(session_data)
                pass
            
            # Fallback to in-memory store
            session_state = self._session_store.get(session_id, {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "message_count": 0,
                "conversation_history": [],
                "metadata": {}
            })
            
            logger.debug(f"Session loaded: {session_id} ({session_state['message_count']} messages)")
            return session_state
            
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}", exc_info=True)
            # Return empty session on error
            return {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "message_count": 0,
                "conversation_history": [],
                "metadata": {}
            }
    
    async def _load_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Load user profile and history (future: from PostgreSQL).
        
        Args:
            user_id: User identifier
        
        Returns:
            User context dictionary
        """
        logger.debug(f"Loading user context: {user_id}")
        
        try:
            # TODO: Load from PostgreSQL when user service is implemented
            # For now, return basic user context
            user_context = {
                "user_id": user_id,
                "profile": {
                    "created_at": datetime.now().isoformat(),
                    "preferences": {},
                    "metadata": {}
                },
                "history": {
                    "total_sessions": 0,
                    "total_messages": 0,
                    "last_seen": None
                }
            }
            
            logger.debug(f"User context loaded: {user_id}")
            return user_context
            
        except Exception as e:
            logger.error(f"Error loading user context {user_id}: {e}", exc_info=True)
            # Return empty context on error
            return {
                "user_id": user_id,
                "profile": {},
                "history": {}
            }
    
    async def _enrich_request(
        self,
        session_state: Dict[str, Any],
        user_context: Dict[str, Any],
        current_input: str
    ) -> Dict[str, Any]:
        """
        Combine session + user context with current request.
        
        Args:
            session_state: Current session data
            user_context: User profile and history
            current_input: Current user message
        
        Returns:
            Enriched context combining all sources
        """
        logger.debug("Enriching request with context")
        
        # Build enriched context
        enriched = {
            "session": {
                "id": session_state.get("session_id"),
                "message_count": session_state.get("message_count", 0),
                "created_at": session_state.get("created_at"),
                "last_updated": session_state.get("last_updated"),
                "recent_history": session_state.get("conversation_history", [])[-10:],  # Last 10 messages
                "metadata": session_state.get("metadata", {})
            },
            "user": {
                "id": user_context.get("user_id"),
                "profile": user_context.get("profile", {}),
                "history_summary": user_context.get("history", {})
            },
            "current_request": {
                "input": current_input,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        logger.debug(f"Request enriched (session: {enriched['session']['message_count']} msgs)")
        return enriched
    
    async def update_session_state(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str
    ) -> None:
        """
        Persist updated session state after supervisor processes request.
        
        Args:
            session_id: Session identifier
            user_message: User's message
            assistant_response: Assistant's response
        """
        logger.debug(f"Updating session state: {session_id}")
        
        try:
            # Load current session
            session_state = await self._load_session(session_id)
            
            # Update conversation history
            conversation_history = session_state.get("conversation_history", [])
            conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "assistant": assistant_response
            })
            
            # Update session metadata
            session_state.update({
                "last_updated": datetime.now().isoformat(),
                "message_count": session_state.get("message_count", 0) + 1,
                "conversation_history": conversation_history[-50:]  # Keep last 50 exchanges
            })
            
            # Persist to storage
            if self.redis_client:
                # TODO: Save to Redis when integrated
                # await self.redis_client.set(
                #     f"session:{session_id}",
                #     json.dumps(session_state),
                #     ex=86400  # 24 hour TTL
                # )
                pass
            
            # Always update in-memory store
            self._session_store[session_id] = session_state
            
            logger.debug(f"Session state updated: {session_id} ({session_state['message_count']} messages)")
            
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}", exc_info=True)
            # Don't raise - session state updates are non-critical
    
    async def clear_session(self, session_id: str) -> None:
        """
        Clear session state (for testing or explicit user reset).
        
        Args:
            session_id: Session to clear
        """
        logger.info(f"Clearing session: {session_id}")
        
        try:
            if self.redis_client:
                # TODO: Delete from Redis when integrated
                # await self.redis_client.delete(f"session:{session_id}")
                pass
            
            # Clear from in-memory store
            self._session_store.pop(session_id, None)
            
            logger.info(f"Session cleared: {session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing session {session_id}: {e}", exc_info=True)
    
    async def checkpoint_state(
        self,
        session_id: str,
        checkpoint_id: str,
        state: Dict[str, Any]
    ) -> None:
        """
        Create a checkpoint of current state (for long-running conversations).
        
        Args:
            session_id: Session identifier
            checkpoint_id: Unique checkpoint identifier
            state: State to checkpoint
        """
        logger.info(f"Creating checkpoint: {session_id}:{checkpoint_id}")
        
        checkpoint_key = f"{session_id}:checkpoint:{checkpoint_id}"
        
        checkpoint_data = {
            'session_id': session_id,
            'checkpoint_id': checkpoint_id,
            'timestamp': datetime.now().isoformat(),
            'state': state
        }
        
        try:
            if self.redis_client:
                # TODO: Store in Redis when integrated
                # await self.redis_client.set(
                #     f"checkpoint:{checkpoint_key}",
                #     json.dumps(checkpoint_data),
                #     ex=86400 * 7  # 7 days TTL
                # )
                pass
            
            # Store in in-memory (for now)
            if not hasattr(self, '_checkpoints'):
                self._checkpoints = {}
            self._checkpoints[checkpoint_key] = checkpoint_data
            
            logger.info(f"Checkpoint created: {checkpoint_key}")
            
        except Exception as e:
            logger.error(f"Error creating checkpoint {checkpoint_key}: {e}", exc_info=True)
    
    async def restore_checkpoint(
        self,
        session_id: str,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Restore state from a checkpoint.
        
        Args:
            session_id: Session identifier
            checkpoint_id: Checkpoint identifier
        
        Returns:
            Checkpoint state or None if not found
        """
        logger.info(f"Restoring checkpoint: {session_id}:{checkpoint_id}")
        
        checkpoint_key = f"{session_id}:checkpoint:{checkpoint_id}"
        
        try:
            if self.redis_client:
                # TODO: Load from Redis when integrated
                # checkpoint_data = await self.redis_client.get(f"checkpoint:{checkpoint_key}")
                # if checkpoint_data:
                #     return json.loads(checkpoint_data)
                pass
            
            # Load from in-memory
            if hasattr(self, '_checkpoints') and checkpoint_key in self._checkpoints:
                checkpoint_data = self._checkpoints[checkpoint_key]
                logger.info(f"Checkpoint restored: {checkpoint_key}")
                return checkpoint_data['state']
            
            logger.warning(f"Checkpoint not found: {checkpoint_key}")
            return None
            
        except Exception as e:
            logger.error(f"Error restoring checkpoint {checkpoint_key}: {e}", exc_info=True)
            return None
    
    async def get_state_snapshot(
        self,
        session_id: str,
        node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a snapshot of current state (for debugging).
        
        Args:
            session_id: Session identifier
            node_id: Optional node context
        
        Returns:
            State snapshot
        """
        logger.debug(f"Creating state snapshot: {session_id}")
        
        session_state = await self._load_session(session_id)
        
        snapshot = {
            'session_id': session_id,
            'node_id': node_id,
            'timestamp': datetime.now().isoformat(),
            'session_state': session_state,
            'message_count': session_state.get('message_count', 0),
            'conversation_history': session_state.get('conversation_history', [])[-10:]  # Last 10
        }
        
        return snapshot
    
    async def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List of checkpoint metadata
        """
        logger.debug(f"Listing checkpoints for session: {session_id}")
        
        checkpoints = []
        
        try:
            if self.redis_client:
                # TODO: Query Redis when integrated
                pass
            
            # Query in-memory checkpoints
            if hasattr(self, '_checkpoints'):
                for key, checkpoint in self._checkpoints.items():
                    if checkpoint['session_id'] == session_id:
                        checkpoints.append({
                            'checkpoint_id': checkpoint['checkpoint_id'],
                            'timestamp': checkpoint['timestamp'],
                            'session_id': checkpoint['session_id']
                        })
            
            logger.debug(f"Found {len(checkpoints)} checkpoints for {session_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error listing checkpoints for {session_id}: {e}", exc_info=True)
            return []
    
    async def get_conversation_context(
        self,
        session_id: str,
        lookback: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation context (last N turns).
        
        Args:
            session_id: Session identifier
            lookback: Number of recent turns to retrieve
        
        Returns:
            List of conversation turns
        """
        logger.debug(f"Getting conversation context: {session_id} (last {lookback})")
        
        session_state = await self._load_session(session_id)
        conversation_history = session_state.get('conversation_history', [])
        
        return conversation_history[-lookback:]