# agents/persona.py - FIXED
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from ..config import settings
from ..utils import llm_chat

def persona_agent(state: MessagesState) -> Command[Literal["critic_agent","end"]]:
    """
    Enhanced persona agent that uses memory context and conversation history.
    Finalizes the response applying formal persona, citations, and polish.
    Expects state.ranked to exist (list of docs) or fallback to direct LLM.
    """
    try:
        persona_prompt = settings.PERSONA_PROMPT
        user_msg = state.messages[-1]["content"]

        # Build context from retrieved documents
        context_excerpt = ""
        ranked = state.__dict__.get("ranked", [])
        if ranked:
            # include top 3 citations
            for d in ranked[:3]:
                src = d.get("metadata", {}).get("source", d.get("id"))
                context_excerpt += f"\n[[{src}]]: {d.get('content')[:400]}"

        # Add memory context
        memory_context = ""
        memories = state.__dict__.get("memories", [])
        if memories:
            memory_context = "\n\nRelevant past interactions:\n"
            for mem in memories[:2]:  # Top 2 most relevant memories
                memory_context += f"- {mem.get('content', '')[:200]}\n"

        # Add conversation context
        conversation_context = ""
        conv_context = state.__dict__.get("conversation_context", [])
        if conv_context:
            conversation_context = "\n\nRecent conversation:\n"
            for msg in conv_context[-4:]:  # Last 4 messages
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role}: {msg['content']}\n"

        # Build comprehensive prompt
        full_context = f"{context_excerpt}{memory_context}{conversation_context}"
        
        messages = [
            {"role":"system","content": persona_prompt},
            {"role":"user","content": f"User asked: {user_msg}\n\nContext: {full_context}\n\nAnswer formally and include citations where appropriate. Use the conversation context to provide more personalized responses."}
        ]
        
        answer = llm_chat(messages, max_tokens=512)
        return Command(goto="critic_agent", update={"candidate_answer": answer})
        
    except Exception as e:
        # Fallback to simple response
        fallback_answer = "I apologize, but I'm experiencing technical difficulties. Please try again or rephrase your question."
        return Command(goto="critic_agent", update={"candidate_answer": fallback_answer})
