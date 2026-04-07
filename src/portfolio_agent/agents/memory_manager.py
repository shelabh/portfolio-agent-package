"""
Memory Manager for portfolio-agent.

This module provides conversation context and history management
for maintaining coherent multi-turn conversations.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    turn_id: str
    user_query: str
    agent_response: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class ConversationContext:
    """Context for a conversation session."""
    session_id: str
    turns: List[ConversationTurn]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]

class MemoryManager:
    """Memory manager for conversation context and history."""
    
    def __init__(
        self,
        max_turns: int = 10,
        max_context_length: int = 2000,
        persistence_enabled: bool = True
    ):
        """Initialize memory manager.
        
        Args:
            max_turns: Maximum number of turns to keep in memory
            max_context_length: Maximum length of context to maintain
            persistence_enabled: Whether to persist conversation history
        """
        self.max_turns = max_turns
        self.max_context_length = max_context_length
        self.persistence_enabled = persistence_enabled
        
        # In-memory storage for conversations
        self.conversations: Dict[str, ConversationContext] = {}
        
        logger.info("Memory manager initialized")
    
    def start_conversation(
        self,
        session_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Start a new conversation session.
        
        Args:
            session_id: Unique identifier for the conversation session
            initial_context: Optional initial context information
            
        Returns:
            ConversationContext for the new session
        """
        now = datetime.now().isoformat()
        
        context = ConversationContext(
            session_id=session_id,
            turns=[],
            created_at=now,
            updated_at=now,
            metadata=initial_context or {}
        )
        
        self.conversations[session_id] = context
        
        logger.info(f"Started new conversation: {session_id}")
        return context
    
    def add_turn(
        self,
        session_id: str,
        user_query: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationTurn:
        """Add a turn to the conversation.
        
        Args:
            session_id: Session identifier
            user_query: User's query
            agent_response: Agent's response
            metadata: Optional metadata for the turn
            
        Returns:
            ConversationTurn that was added
        """
        if session_id not in self.conversations:
            logger.warning(f"Session {session_id} not found, creating new conversation")
            self.start_conversation(session_id)
        
        # Create turn
        turn_id = f"{session_id}_turn_{len(self.conversations[session_id].turns) + 1}"
        now = datetime.now().isoformat()
        
        turn = ConversationTurn(
            turn_id=turn_id,
            user_query=user_query,
            agent_response=agent_response,
            timestamp=now,
            metadata=metadata or {}
        )
        
        # Add to conversation
        self.conversations[session_id].turns.append(turn)
        self.conversations[session_id].updated_at = now
        
        # Trim old turns if necessary
        self._trim_conversation(session_id)
        
        logger.info(f"Added turn to conversation {session_id}")
        return turn
    
    def get_conversation_context(
        self,
        session_id: str,
        max_turns: Optional[int] = None
    ) -> Optional[ConversationContext]:
        """Get conversation context for a session.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of turns to include (None for all)
            
        Returns:
            ConversationContext or None if not found
        """
        if session_id not in self.conversations:
            return None
        
        context = self.conversations[session_id]
        
        if max_turns is not None and len(context.turns) > max_turns:
            # Return context with limited turns
            limited_context = ConversationContext(
                session_id=context.session_id,
                turns=context.turns[-max_turns:],
                created_at=context.created_at,
                updated_at=context.updated_at,
                metadata=context.metadata
            )
            return limited_context
        
        return context
    
    def get_recent_turns(
        self,
        session_id: str,
        num_turns: int = 3
    ) -> List[ConversationTurn]:
        """Get recent conversation turns.
        
        Args:
            session_id: Session identifier
            num_turns: Number of recent turns to retrieve
            
        Returns:
            List of recent ConversationTurns
        """
        if session_id not in self.conversations:
            return []
        
        turns = self.conversations[session_id].turns
        return turns[-num_turns:] if turns else []
    
    def get_conversation_summary(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a summary of the conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with conversation summary or None if not found
        """
        if session_id not in self.conversations:
            return None
        
        context = self.conversations[session_id]
        turns = context.turns
        
        # Calculate summary statistics
        total_turns = len(turns)
        total_user_chars = sum(len(turn.user_query) for turn in turns)
        total_agent_chars = sum(len(turn.agent_response) for turn in turns)
        
        # Get topics (simple keyword extraction)
        topics = set()
        for turn in turns:
            # Simple topic extraction - could be enhanced
            words = turn.user_query.lower().split()
            topics.update(word for word in words if len(word) > 4)
        
        return {
            "session_id": session_id,
            "total_turns": total_turns,
            "created_at": context.created_at,
            "updated_at": context.updated_at,
            "total_user_chars": total_user_chars,
            "total_agent_chars": total_agent_chars,
            "topics": list(topics)[:10],  # Top 10 topics
            "metadata": context.metadata
        }
    
    def clear_conversation(self, session_id: str) -> bool:
        """Clear a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if cleared, False if not found
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation: {session_id}")
            return True
        return False
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs.
        
        Returns:
            List of session IDs
        """
        return list(self.conversations.keys())
    
    def _trim_conversation(self, session_id: str):
        """Trim conversation to maintain memory limits.
        
        Args:
            session_id: Session identifier
        """
        if session_id not in self.conversations:
            return
        
        context = self.conversations[session_id]
        
        # Trim by number of turns
        if len(context.turns) > self.max_turns:
            context.turns = context.turns[-self.max_turns:]
        
        # Trim by context length
        total_length = sum(
            len(turn.user_query) + len(turn.agent_response)
            for turn in context.turns
        )
        
        if total_length > self.max_context_length:
            # Remove oldest turns until under limit
            while (total_length > self.max_context_length and 
                   len(context.turns) > 1):
                removed_turn = context.turns.pop(0)
                total_length -= len(removed_turn.user_query) + len(removed_turn.agent_response)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory manager statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        total_turns = sum(len(context.turns) for context in self.conversations.values())
        
        return {
            "active_sessions": len(self.conversations),
            "total_turns": total_turns,
            "max_turns": self.max_turns,
            "max_context_length": self.max_context_length,
            "persistence_enabled": self.persistence_enabled
        }

# Convenience function for easy access
def create_memory_manager(**kwargs) -> MemoryManager:
    """Create a memory manager with default settings.
    
    Args:
        **kwargs: Arguments to pass to MemoryManager
        
    Returns:
        Configured MemoryManager instance
    """
    return MemoryManager(**kwargs)