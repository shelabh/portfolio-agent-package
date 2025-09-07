# agents/memory_manager.py - FIXED
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal, List, Dict, Any
from ..utils import nearest_neighbors, upsert_vector, llm_chat, client
from ..config import settings
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def memory_agent(state: MessagesState) -> Command[Literal["router_agent","end"]]:
    """
    Enhanced memory management that fetches relevant user context and conversation history.
    - Fetches long-term memory for the user (if user_id present in state)
    - Retrieves recent conversation context
    - Builds comprehensive memory context for better responses
    """
    try:
        user_id = getattr(state, "user_id", None)
        messages = state.messages if hasattr(state, "messages") else []
        
        # Extract current user query for context
        current_query = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                current_query = m.get("content", "")
                break
        
        mems = []
        
        if user_id and current_query:
            # Create user-specific memory queries
            memory_queries = [
                f"user {user_id} recent interactions",
                f"user {user_id} preferences and context",
                current_query  # Use current query to find relevant past interactions
            ]
            
            all_memories = []
            for query in memory_queries:
                try:
                    emb = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=query)
                    q_vec = emb.data[0].embedding
                    memories = nearest_neighbors(q_vec, top_k=3)
                    all_memories.extend(memories)
                except Exception as e:
                    logger.warning(f"Failed to fetch memories for query '{query}': {e}")
            
            # Deduplicate and rank memories
            seen_ids = set()
            for mem in all_memories:
                if mem["id"] not in seen_ids:
                    mems.append(mem)
                    seen_ids.add(mem["id"])
                    if len(mems) >= 5:  # Limit to top 5 most relevant memories
                        break
        
        # Add conversation context from recent messages
        conversation_context = []
        if len(messages) > 1:
            # Include last few exchanges for context
            recent_messages = messages[-6:]  # Last 3 exchanges (6 messages)
            for msg in recent_messages:
                if msg.get("role") in ["user", "assistant"]:
                    conversation_context.append({
                        "role": msg.get("role"),
                        "content": msg.get("content", "")[:200],  # Truncate for efficiency
                        "timestamp": datetime.now().isoformat()
                    })
        
        return Command(
            goto="router_agent", 
            update={
                "memories": mems,
                "conversation_context": conversation_context,
                "memory_timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Memory agent failed: {e}")
        # Fallback: continue with empty memory
        return Command(goto="router_agent", update={"memories": [], "conversation_context": []})
